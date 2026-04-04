from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Callable


def _write_cache(payload: dict[str, Any], cache_path: str | Path) -> None:
    path = Path(cache_path)
    with path.open("wb") as file_obj:
        pickle.dump(payload, file_obj)


def _read_cache(cache_path: str | Path, missing_hint: str) -> dict[str, Any]:
    path = Path(cache_path)
    if not path.exists():
        raise RuntimeError(f"Cache file {path} does not exist. {missing_hint}")
    with path.open("rb") as file_obj:
        return pickle.load(file_obj)


def update_all_stops_cache(
    api_key: str,
    fetch_all_stops: Callable[[str], dict[str, Any]],
    cache_path: str | Path = "all_stops_cache.pkl",
) -> None:
    _write_cache(fetch_all_stops(api_key), cache_path)


def get_all_stops_cache(cache_path: str | Path = "all_stops_cache.pkl") -> dict[str, Any]:
    return _read_cache(cache_path, "Run update_all_stops_cache() first.")


def update_all_routes_cache(
    api_key: str,
    fetch_all_routes: Callable[[str], dict[str, Any]],
    cache_path: str | Path = "all_routes_cache.pkl",
) -> None:
    _write_cache(fetch_all_routes(api_key), cache_path)


def get_all_routes_cache(cache_path: str | Path = "all_routes_cache.pkl") -> dict[str, Any]:
    return _read_cache(cache_path, "Run update_all_routes_cache() first.")


def update_all_trips_cache(
    api_key: str,
    fetch_all_trips: Callable[[str], dict[str, Any]],
    cache_path: str | Path = "all_trips_cache.pkl",
) -> None:
    _write_cache(fetch_all_trips(api_key), cache_path)


def get_all_trips_cache(cache_path: str | Path = "all_trips_cache.pkl") -> dict[str, Any]:
    return _read_cache(cache_path, "Run update_all_trips_cache() first.")