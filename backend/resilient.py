"""
Retry + disk cache for the public APIs (Ensembl, gnomAD). Ensembl in particular
times out and returns 500/502/503/429 under load, so every call here:
  1. is answered from a local cache when it has been fetched before,
  2. retries with backoff (honouring Retry-After) on timeouts and 429/5xx,
  3. falls back to a stale cached copy if the service is still down.
Genome facts for a fixed variant do not change, so caching them is safe.
The cache lives in backend/.cache and can simply be deleted to refetch.
"""

import hashlib
import json
import pathlib
import time

import requests

CACHE_DIR = pathlib.Path(__file__).parent / ".cache"
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _key(method, url, params, body):
    raw = json.dumps([method, url, params, body], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def cached_request(method: str, url: str, *, params=None, json_body=None, headers=None,
                   timeout=45, retries=4, ttl=30 * 86400, as_text=False):
    """Returns (status_code, data). 4xx other than 429 are returned (and cached), not retried."""
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{_key(method, url, params, json_body)}.json"
    cached = None
    if path.exists():
        try:
            cached = json.loads(path.read_text())
            if time.time() - cached["t"] < ttl:
                return cached["status"], cached["data"]
        except Exception:
            cached = None

    last_err = None
    for attempt in range(retries):
        try:
            r = requests.request(method, url, params=params, json=json_body, headers=headers, timeout=timeout)
            if r.status_code in RETRY_STATUSES:
                last_err = f"HTTP {r.status_code}"
                wait = float(r.headers.get("Retry-After", 0) or 0) or (2 ** attempt)
                time.sleep(min(wait, 10))
                continue
            if r.status_code >= 500 or r.status_code in (401, 403, 404):
                last_err = f"HTTP {r.status_code}"
                break
            data = r.text if as_text else r.json()
            path.write_text(json.dumps({"t": time.time(), "status": r.status_code, "data": data}))
            return r.status_code, data
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = type(e).__name__
            time.sleep(min(2 ** attempt, 10))
    if cached:  # serve stale rather than fail
        return cached["status"], cached["data"]
    raise RuntimeError(f"{url.split('?')[0]} did not answer after {retries} tries ({last_err}). Try again in a minute.")
