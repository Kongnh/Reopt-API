"""Fetch PV production factor and irradiance series from NREL PVWatts v8.

Vietnam sites are outside NREL NSRDB coverage, so REopt.jl's built-in solar
dataset lookup times out. This client provides an 8760-length production
factor series (AC kW per kW DC installed) and the matching plane-of-array
irradiance series (W/m2), keyed on lat/lon and PVWatts parameters, with on-disk
caching so re-runs do not re-hit the API.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from urllib import parse, request


# NREL retired developer.nrel.gov on 2026-05-29; the developer API now lives at
# developer.nlr.gov. Override with NREL_PVWATTS_URL if the endpoint moves again.
PVWATTS_URL = os.environ.get(
    "NREL_PVWATTS_URL", "https://developer.nlr.gov/api/pvwatts/v8.json"
)
DEFAULT_PARAMS = {
    "tilt": 10,
    "azimuth": 180,
    "array_type": 1,
    "module_type": 0,
    "losses": 14,
    "dc_ac_ratio": 1.2,
}
CACHE_DIR = Path("outputs") / "pvwatts_cache"
ENV_FILE = Path("julia_src") / ".env"


def fetch_pv_series(latitude, longitude, overrides=None, api_key=None):
    """Return the PVWatts series for the site.

    ``{"production_factor": [...8760 AC kW per kW DC...],
       "poa_wm2": [...8760 plane-of-array irradiance in W/m2...]}``

    Both series come from a single PVWatts response and are cached together.
    ``poa_wm2`` is empty if PVWatts did not return an 8760-length ``poa`` array.
    """
    params = _resolve_params(overrides)
    cache_key = _cache_key(latitude, longitude, params)
    cached = _read_cache(cache_key)
    if isinstance(cached, dict) and "production_factor" in cached:
        return cached

    series = _fetch_pvwatts(latitude, longitude, params, api_key or _load_api_key())
    _write_cache(cache_key, series)
    return series


def fetch_production_factor_series(latitude, longitude, overrides=None, api_key=None):
    """Return an 8760-length AC/kW-DC production factor series for the site."""
    return fetch_pv_series(latitude, longitude, overrides, api_key)["production_factor"]


def _resolve_params(overrides):
    params = dict(DEFAULT_PARAMS)
    if overrides:
        unknown = set(overrides) - set(DEFAULT_PARAMS)
        if unknown:
            raise ValueError(
                f"Unsupported technologies.pv.pvwatts keys: {sorted(unknown)}. "
                f"Allowed: {sorted(DEFAULT_PARAMS)}."
            )
        params.update(overrides)
    return params


def _fetch_pvwatts(latitude, longitude, params, api_key):
    query = parse.urlencode({
        "api_key": api_key,
        "lat": latitude,
        "lon": longitude,
        "system_capacity": 1,
        "timeframe": "hourly",
        **params,
    })
    with request.urlopen(f"{PVWATTS_URL}?{query}") as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("errors"):
        raise RuntimeError(f"PVWatts API error: {body['errors']}")
    outputs = body.get("outputs", {})
    ac = outputs.get("ac") or []
    if len(ac) != 8760:
        raise RuntimeError(
            f"PVWatts returned {len(ac)} hourly values, expected 8760."
        )
    poa = outputs.get("poa") or []
    return {
        "production_factor": [round(value / 1000.0, 6) for value in ac],
        # Plane-of-array irradiance (W/m2) — the raw solar-resource signal shown
        # on the Dispatch sheet and used for the annual Performance Ratio.
        "poa_wm2": [round(value, 2) for value in poa] if len(poa) == 8760 else [],
    }


def _cache_key(latitude, longitude, params):
    payload = json.dumps(
        {"lat": latitude, "lon": longitude, **params},
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _read_cache(cache_key):
    path = CACHE_DIR / f"{cache_key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_cache(cache_key, series):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{cache_key}.json").write_text(
        json.dumps(series), encoding="utf-8"
    )


def _load_api_key():
    api_key = os.environ.get("NREL_DEVELOPER_API_KEY")
    if api_key:
        return api_key
    if ENV_FILE.exists():
        for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            match = re.match(
                r'^\s*NREL_DEVELOPER_API_KEY\s*=\s*"?([^"\s]+)"?\s*$',
                raw_line,
            )
            if match:
                return match.group(1)
    raise RuntimeError(
        "NREL_DEVELOPER_API_KEY not set. Export the env var or add it to "
        "julia_src/.env."
    )
