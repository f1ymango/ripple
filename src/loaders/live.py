"""Live poller (component A4): capture the feeds at full rate, starting now.

The historical archive keeps under half the detector minutes, and the missing
ones cannot be recovered from anywhere (docs/02-data.md section 3). The **live**
feed has no such gap: the Transport Department republishes every minute and we
can take every one of them.

So this is the one coverage fix that is not a workaround. It cannot help a past
incident, but from the moment it starts running every corridor incident is
captured at 100% coverage. Corridor incidents run roughly two a week, so a few
weeks of polling is likely to yield a better demo incident than anything in the
archive -- and a fully covered one makes the validation slide stronger.

It also answers the obvious Q&A question honestly: our coverage limitation is
an artefact of replaying history, not of the system. Deployed, Ripple reads
this feed.

    python -m src.loaders.fetch live --minutes 0        # run until stopped
    python -m src.loaders.fetch live --minutes 30       # or a fixed stretch

Needs a machine that stays awake. Files land in data/raw/live/<feed>/, named by
the data's own timestamp, so restarting after a laptop sleeps costs only the
minutes it slept and never corrupts what is already there.
"""
from __future__ import annotations

import datetime as dt
import gzip
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HK = dt.timezone(dt.timedelta(hours=8))
LIVE_ROOT = Path("data/raw/live")
POLL_SECONDS = 30      # the feed updates every 60s; poll twice to never miss one

LIVE_URLS = {
    "detectors": "https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml",
    "stn": "https://www.td.gov.hk/en/special_news/trafficnews.xml",
}

http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])))


def _stamp(feed: str, xml_bytes: bytes) -> str:
    """The data's own timestamp, so a file is named by when the traffic was.

    Never the wall clock: two polls of an unchanged feed must land on the same
    filename, which is what makes this idempotent and restart-safe.
    """
    root = ET.fromstring(xml_bytes)
    if feed == "detectors":
        day = (root.findtext("date") or "").strip()
        first = root.find("periods/period/period_from")
        moment = (first.text or "").strip() if first is not None else ""
        return f"{day.replace('-', '')}-{moment.replace(':', '')[:6]}"
    # STN carries no file-level time; fall back to the newest announcement.
    dates = sorted((m.findtext("ANNOUNCEMENT_DATE") or "").strip()
                   for m in root.findall("message"))
    newest = dates[-1] if dates else dt.datetime.now(HK).isoformat(timespec="seconds")
    return newest.replace("-", "").replace(":", "").replace("T", "-")[:15]


def poll_once(feed: str) -> tuple[str, bool]:
    """Fetch the live feed and store it if we do not already have that moment.

    Returns (stamp, stored). `stored` is False when the feed had not refreshed
    since the previous poll -- expected, and not an error.
    """
    resp = http.get(LIVE_URLS[feed], timeout=60)
    resp.raise_for_status()
    stamp = _stamp(feed, resp.content)
    path = LIVE_ROOT / feed / f"{stamp}.xml.gz"
    if path.exists():
        return stamp, False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    with gzip.open(tmp, "wb") as f:
        f.write(resp.content)
    tmp.replace(path)
    return stamp, True


def run(feeds: tuple[str, ...] = ("detectors", "stn"), minutes: int = 0,
        poll_seconds: int = POLL_SECONDS, log=print) -> dict[str, int]:
    """Poll until `minutes` have passed, or forever when minutes == 0.

    A network blip is logged and skipped rather than ending the run: a poller
    that dies overnight defeats the point.
    """
    deadline = time.monotonic() + minutes * 60 if minutes else None
    stored = {f: 0 for f in feeds}
    errors = 0
    log(f"polling {', '.join(feeds)} every {poll_seconds}s -> {LIVE_ROOT}/ "
        f"({'until stopped' if not minutes else f'for {minutes} min'}); Ctrl-C to stop")
    try:
        while deadline is None or time.monotonic() < deadline:
            for feed in feeds:
                try:
                    stamp, is_new = poll_once(feed)
                    if is_new:
                        stored[feed] += 1
                        log(f"  {feed:<10} {stamp}  (stored {stored[feed]})")
                except Exception as exc:                      # noqa: BLE001
                    errors += 1
                    log(f"  {feed:<10} poll failed ({type(exc).__name__}); carrying on")
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        log("\nstopped")
    log(f"stored: {stored}, failed polls: {errors}")
    return stored
