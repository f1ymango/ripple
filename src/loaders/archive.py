"""DATA.GOV.HK historical archive client (component A).

Every feed we replay -- Special Traffic News and the raw traffic detectors --
is served by the same archive API, so one client covers both:

    https://api.data.gov.hk/v1/historical-archive/list-file-versions
    https://api.data.gov.hk/v1/historical-archive/get-file

Measured cadence on 21 Sep 2026 (one call to list-file-versions per feed):

    detectors  901 snapshots/day, median gap 1 min, ~700 KB each
    segments   619 snapshots/day, median gap 2 min
    stn        127 snapshots/day, median gap 4 min

Downloading is the slow part of this project, not parsing, so:

  * every snapshot is cached under data/raw/<feed>/ and never fetched twice
  * the cache is gzipped (~10x smaller; a 4-hour detector window is ~170 MB
    of XML but ~17 MB on disk)
  * prefetch() downloads in parallel and is resumable -- stop it, run it
    again, and it picks up the snapshots it has not got yet

src/reader/sample.py keeps its own plain-.xml cache under data/raw/stn/.
We read those files when they are there, so nothing is downloaded twice,
and we never write into that layout or import from that module.

    python -m src.loaders.fetch prefetch --feed stn --start 2026-06-22 --end 2026-09-21
"""
from __future__ import annotations

import gzip
import io
import sys
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ARCHIVE_API = "https://api.data.gov.hk/v1/historical-archive"

FEEDS = {
    # The /en/ and /tc/ STN feeds are byte-identical: every message carries both languages.
    "stn": "https://www.td.gov.hk/en/special_news/trafficnews.xml",
    "detectors": "https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml",
    "segments": "https://resource.data.one.gov.hk/td/traffic-detectors/irnAvgSpeed-all.xml",
}

CACHE_ROOT = Path("data/raw")
REQUEST_PAUSE_S = 0.15  # per worker, to stay polite under concurrency

_local = threading.local()

# raise_on_status=False: once retries run out, hand back the last response so
# fetch() turns it into an ArchiveUnavailable. With the default, a persistent
# 503 escaped as requests.RetryError, which no caller catches, and ended
# hours-long runs on one bad minute.
RETRY = Retry(total=4, backoff_factor=2, raise_on_status=False,
              status_forcelist=[500, 502, 503, 504])


# The root element each feed's XML must start with. A 200 response that does
# not start with this -- an HTML error page, say -- is never cached.
ROOT_TAGS = {"stn": "list", "detectors": "raw_speed_volume_list",
             "segments": "segment_speed_list"}


class ArchiveError(RuntimeError):
    """Something went wrong getting a snapshot. Catch this to catch both kinds."""


class NotArchived(ArchiveError):
    """404: the archive lists this version but does not have it. Permanent --
    recorded on disk so no later run asks again."""


class ArchiveUnavailable(ArchiveError):
    """5xx, a network failure, or a body that is not the feed's XML, after
    retries. Transient -- not recorded, so the next run tries again."""


def _session() -> requests.Session:
    """One requests.Session per thread, with retries on the flaky S3 backend."""
    session = getattr(_local, "session", None)
    if session is None:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=RETRY)
        session.mount("https://", adapter)
        session.mount("http://", adapter)    # only ever used by tests' local stub
        _local.session = session
    return session


def _feed_url(feed: str) -> str:
    try:
        return FEEDS[feed]
    except KeyError:
        raise ArchiveError(f"unknown feed {feed!r}; known feeds: {', '.join(FEEDS)}") from None


def _compact(day: str) -> str:
    """'2026-09-21' or '20260921' -> '20260921'."""
    return day.replace("-", "")


def list_versions(feed: str, start: str, end: str) -> list[str]:
    """Archive timestamps ('YYYYMMDD-HHmm') of every snapshot from start to end, inclusive.

    The archive's latest available day is yesterday; asking for today returns
    nothing rather than an error, which is why callers should check the count.
    """
    try:
        resp = _session().get(
            f"{ARCHIVE_API}/list-file-versions",
            params={"url": _feed_url(feed), "start": _compact(start), "end": _compact(end)},
            timeout=60)
    except requests.RequestException as exc:
        raise ArchiveUnavailable(f"list-file-versions failed for {feed}: {exc}") from exc
    if resp.status_code != 200:
        raise ArchiveUnavailable(f"list-file-versions {resp.status_code} for {feed} "
                                 f"{start}..{end}: {resp.text[:200]}")
    return resp.json().get("timestamps", [])


def cache_path(feed: str, timestamp: str) -> Path:
    """Where we store a snapshot. Gzipped, so the cache stays laptop-sized."""
    return CACHE_ROOT / feed / f"{timestamp}.xml.gz"


def missing_marker(feed: str, timestamp: str) -> Path:
    """Zero-byte file recording that the archive 404'd on this version.

    About a third to a half of listed detector versions are a persistent 404.
    Without this, every rerun asked for all of them again. Delete the .404
    files to force a recheck.
    """
    return CACHE_ROOT / feed / f"{timestamp}.404"


def looks_like_feed(feed: str, body: bytes) -> bool:
    """Does this body start with the feed's own root element?

    Reads only the opening tag, so it is cheap enough to run on every cache read.
    """
    try:
        for _, element in ET.iterparse(io.BytesIO(body), events=("start",)):
            return element.tag == ROOT_TAGS[feed]
    except ET.ParseError:
        return False
    return False


def _legacy_path(feed: str, timestamp: str) -> Path:
    """The plain-.xml path src/reader/sample.py already caches STN snapshots at."""
    return CACHE_ROOT / feed / f"{timestamp}.xml"


def read_cached(feed: str, timestamp: str) -> bytes | None:
    """Snapshot bytes from disk, or None if we have no usable copy.

    A cached file that is not the feed's XML (an error page saved before this
    check existed) is dropped and refetched, never handed to a parser.
    """
    legacy = _legacy_path(feed, timestamp)
    if legacy.exists():
        body = legacy.read_bytes()
        if looks_like_feed(feed, body):      # the Reader's cache: read, never deleted
            return body
    path = cache_path(feed, timestamp)
    if path.exists():
        try:
            with gzip.open(path, "rb") as f:
                body = f.read()
        except (OSError, EOFError):
            body = None                      # truncated by an interrupted run
        if body is not None and looks_like_feed(feed, body):
            return body
        path.unlink(missing_ok=True)
    return None


def fetch(feed: str, timestamp: str) -> bytes:
    """One archived snapshot, downloaded once and cached.

    Raises NotArchived on a 404 (and records it, so it is never asked for
    again) and ArchiveUnavailable on anything transient. Both are ArchiveError,
    so a caller screening a long window catches one type and carries on.
    """
    cached = read_cached(feed, timestamp)
    if cached is not None:
        return cached
    marker = missing_marker(feed, timestamp)
    if marker.exists():
        raise NotArchived(f"no {feed} snapshot at {timestamp} (recorded earlier)")

    try:
        resp = _session().get(f"{ARCHIVE_API}/get-file",
                              params={"url": _feed_url(feed), "time": timestamp}, timeout=120)
    except requests.RequestException as exc:
        raise ArchiveUnavailable(f"get-file failed for {feed} {timestamp}: {exc}") from exc
    finally:
        time.sleep(REQUEST_PAUSE_S)          # after every request, 404s included

    if resp.status_code == 404:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        raise NotArchived(f"no {feed} snapshot at {timestamp}")
    if resp.status_code != 200:
        raise ArchiveUnavailable(f"get-file {resp.status_code} for {feed} {timestamp}: "
                                 f"{resp.text[:200]}")
    if not looks_like_feed(feed, resp.content):
        raise ArchiveUnavailable(f"get-file returned 200 for {feed} {timestamp} but the "
                                 f"body is not {ROOT_TAGS[feed]} XML: {resp.content[:80]!r}")

    path = cache_path(feed, timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")          # write via .part so an interrupted
    with gzip.open(tmp, "wb") as f:          # run never leaves a half file that
        f.write(resp.content)                # looks cached
    tmp.replace(path)
    return resp.content


def prefetch(feed: str, timestamps: list[str], workers: int = 6,
             log=sys.stderr) -> dict[str, int]:
    """Fill the cache in parallel. Resumable: already-cached snapshots are skipped.

    Returns counts of: cached, known_missing (404s recorded on an earlier run,
    not asked for again), downloaded, missing (new 404s, now recorded) and
    failed (transient -- run again to retry just those).
    """
    # One directory listing, not several stat() calls per timestamp, and no
    # decompression: prefetch only needs to know what to skip. A cached file
    # that turns out to be bad is still caught by read_cached() when read.
    folder = CACHE_ROOT / feed
    present = {f.name for f in folder.iterdir()} if folder.is_dir() else set()
    known = [ts for ts in timestamps if f"{ts}.404" in present]
    todo = [ts for ts in timestamps
            if f"{ts}.404" not in present
            and f"{ts}.xml.gz" not in present and f"{ts}.xml" not in present]
    counts = {"cached": len(timestamps) - len(todo) - len(known),
              "known_missing": len(known), "downloaded": 0, "missing": 0, "failed": 0}
    if not todo:
        print(f"{feed}: all {len(timestamps)} snapshots already cached", file=log)
        return counts

    print(f"{feed}: {counts['cached']} cached, {len(known)} known missing, "
          f"downloading {len(todo)} with {workers} workers", file=log)
    started = time.monotonic()
    done = 0

    def grab(ts: str) -> str:
        try:
            fetch(feed, ts)
            return "downloaded"
        except NotArchived:
            return "missing"
        except ArchiveUnavailable:
            return "failed"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for outcome in pool.map(grab, todo):
            done += 1
            counts[outcome] += 1
            if done % 100 == 0 or done == len(todo):
                rate = done / max(time.monotonic() - started, 1e-9)
                left = (len(todo) - done) / rate if rate else 0
                print(f"  {done}/{len(todo)}  {rate:.1f}/s  ~{left/60:.0f} min left",
                      file=log, flush=True)

    print(f"{feed}: {counts['downloaded']} downloaded, {counts['missing']} missing, "
          f"{counts['failed']} failed (rerun to retry those) "
          f"in {(time.monotonic() - started)/60:.1f} min", file=log)
    return counts


def iter_snapshots(feed: str, timestamps: list[str], skip_missing: bool = True):
    """Yield (timestamp, xml_bytes) in order, reading the cache one file at a time.

    Deliberately not parallel and deliberately not a list: three months of STN
    is ~11,000 snapshots, and holding them all in memory at once is how a
    laptop dies. Call prefetch() first if you want the download parallelised.
    """
    for ts in timestamps:
        try:
            yield ts, fetch(feed, ts)
        except NotArchived:
            if not skip_missing:
                raise
        except ArchiveUnavailable as exc:
            if not skip_missing:
                raise
            # Skipped like a 404 so one bad minute cannot end a long run -- but
            # said out loud, because unlike a 404 it would succeed next time.
            print(f"warning: skipped {feed} {ts} after retries: {exc}", file=sys.stderr)
