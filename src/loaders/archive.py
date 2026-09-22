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
import sys
import threading
import time
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


class ArchiveError(RuntimeError):
    """The archive refused a request we cannot retry our way out of."""


def _session() -> requests.Session:
    """One requests.Session per thread, with retries on the flaky S3 backend."""
    session = getattr(_local, "session", None)
    if session is None:
        session = requests.Session()
        session.mount("https://", HTTPAdapter(
            pool_connections=16, pool_maxsize=16,
            max_retries=Retry(total=4, backoff_factor=2,
                              status_forcelist=[500, 502, 503, 504])))
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
    resp = _session().get(
        f"{ARCHIVE_API}/list-file-versions",
        params={"url": _feed_url(feed), "start": _compact(start), "end": _compact(end)},
        timeout=60)
    if resp.status_code != 200:
        raise ArchiveError(f"list-file-versions {resp.status_code} for {feed} "
                           f"{start}..{end}: {resp.text[:200]}")
    return resp.json().get("timestamps", [])


def cache_path(feed: str, timestamp: str) -> Path:
    """Where we store a snapshot. Gzipped, so the cache stays laptop-sized."""
    return CACHE_ROOT / feed / f"{timestamp}.xml.gz"


def _legacy_path(feed: str, timestamp: str) -> Path:
    """The plain-.xml path src/reader/sample.py already caches STN snapshots at."""
    return CACHE_ROOT / feed / f"{timestamp}.xml"


def read_cached(feed: str, timestamp: str) -> bytes | None:
    """Snapshot bytes from disk, or None if we have not downloaded it yet."""
    legacy = _legacy_path(feed, timestamp)
    if legacy.exists():
        return legacy.read_bytes()
    path = cache_path(feed, timestamp)
    if path.exists():
        try:
            with gzip.open(path, "rb") as f:
                return f.read()
        except (OSError, EOFError):
            path.unlink(missing_ok=True)  # truncated by an interrupted run; refetch
    return None


def fetch(feed: str, timestamp: str) -> bytes:
    """One archived snapshot, downloaded once and cached.

    Raises ArchiveError on 404 -- that version genuinely does not exist, and
    retrying will not conjure it. Callers screening a long window should catch
    it and carry on rather than abandoning the whole pull.
    """
    cached = read_cached(feed, timestamp)
    if cached is not None:
        return cached

    resp = _session().get(f"{ARCHIVE_API}/get-file",
                          params={"url": _feed_url(feed), "time": timestamp}, timeout=120)
    if resp.status_code == 404:
        raise ArchiveError(f"no {feed} snapshot at {timestamp}")
    if resp.status_code != 200:
        raise ArchiveError(f"get-file {resp.status_code} for {feed} {timestamp}: "
                           f"{resp.text[:200]}")

    path = cache_path(feed, timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")          # write via .part so an interrupted
    with gzip.open(tmp, "wb") as f:          # run never leaves a half file that
        f.write(resp.content)                # looks cached
    tmp.replace(path)
    time.sleep(REQUEST_PAUSE_S)
    return resp.content


def prefetch(feed: str, timestamps: list[str], workers: int = 6,
             log=sys.stderr) -> dict[str, int]:
    """Fill the cache in parallel. Resumable: already-cached snapshots are skipped.

    Returns {'cached': n, 'downloaded': n, 'missing': n}. `missing` counts
    timestamps the archive 404s on, which happens and is not fatal.
    """
    todo = [ts for ts in timestamps if read_cached(feed, ts) is None]
    counts = {"cached": len(timestamps) - len(todo), "downloaded": 0, "missing": 0}
    if not todo:
        print(f"{feed}: all {len(timestamps)} snapshots already cached", file=log)
        return counts

    print(f"{feed}: {counts['cached']} cached, downloading {len(todo)} "
          f"with {workers} workers", file=log)
    started = time.monotonic()
    done = 0

    def grab(ts: str) -> str | None:
        try:
            fetch(feed, ts)
            return None
        except ArchiveError:
            return ts

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for missing in pool.map(grab, todo):
            done += 1
            if missing:
                counts["missing"] += 1
            else:
                counts["downloaded"] += 1
            if done % 100 == 0 or done == len(todo):
                rate = done / max(time.monotonic() - started, 1e-9)
                left = (len(todo) - done) / rate if rate else 0
                print(f"  {done}/{len(todo)}  {rate:.1f}/s  ~{left/60:.0f} min left",
                      file=log, flush=True)

    print(f"{feed}: {counts['downloaded']} downloaded, {counts['missing']} missing, "
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
        except ArchiveError:
            if not skip_missing:
                raise
