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

Needs a machine that stays awake. Files land in data/raw/live/<feed>/. A body is
stored only when its content differs from the last one kept, so an unrefreshed
or empty feed writes nothing, and a restart after a laptop sleeps costs only
the minutes it slept.
"""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.loaders.archive import FEEDS, looks_like_feed
from src.loaders.common import HK

LIVE_ROOT = Path("data/raw/live")
POLL_SECONDS = 30      # the feed updates every 60s; poll twice to never miss one
LIVE_FEEDS = ("detectors", "stn")   # URLs come from archive.FEEDS: one source of truth

http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])))

# Hash of the last body stored per feed. "Has the feed changed?" is decided by
# content, never by a timestamp read out of it: the STN feed has no file-level
# time, an empty feed has none at all, and the newest announcement moves
# BACKWARD when a CLOSED message disappears -- which is the very change this
# poller exists to catch.
_last_hash: dict[str, str] = {}


def _stamp(feed: str, xml_bytes: bytes, now: dt.datetime | None = None) -> str:
    """Filename stem for a stored body.

    Detectors: the data's own first period, so files sort by when the traffic
    was. STN: the moment we polled, since the feed carries no time of its own.
    """
    if feed == "detectors":
        root = ET.fromstring(xml_bytes)
        day = (root.findtext("date") or "").strip()
        first = root.find("periods/period/period_from")
        moment = (first.text or "").strip() if first is not None else ""
        return f"{day.replace('-', '')}-{moment.replace(':', '')[:6]}"
    return (now or dt.datetime.now(HK)).strftime("%Y%m%d-%H%M%S")


def _digest(body: bytes) -> str:
    return hashlib.sha1(body).hexdigest()


def _newest_stored_hash(feed: str) -> str | None:
    """So a restart does not store a duplicate of what was saved before it."""
    files = sorted((LIVE_ROOT / feed).glob("*.xml.gz"))
    if not files:
        return None
    with gzip.open(files[-1], "rb") as f:
        return _digest(f.read())


def poll_once(feed: str, now: dt.datetime | None = None) -> tuple[str, bool]:
    """Fetch the live feed and store it if its content changed since the last store.

    Returns (stamp, stored). `stored` is False when the body is identical to the
    last one kept -- an unrefreshed feed, or an empty STN feed at a quiet hour.
    """
    resp = http.get(FEEDS[feed], timeout=60)
    resp.raise_for_status()
    body = resp.content
    if not looks_like_feed(feed, body):
        raise ValueError(f"live {feed} returned something that is not its XML: {body[:80]!r}")

    digest = _digest(body)
    if feed not in _last_hash:
        _last_hash[feed] = _newest_stored_hash(feed)
    stamp = _stamp(feed, body, now)
    if digest == _last_hash[feed]:
        return stamp, False

    path = LIVE_ROOT / feed / f"{stamp}-{digest[:8]}.xml.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    with gzip.open(tmp, "wb") as f:
        f.write(body)
    tmp.replace(path)
    _last_hash[feed] = digest
    return stamp, True


def run(feeds: tuple[str, ...] = LIVE_FEEDS, minutes: int = 0,
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
