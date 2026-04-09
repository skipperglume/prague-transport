from __future__ import annotations

import json
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
    cache_path: str | Path = "cache/all_stops_cache.pkl",
) -> None:
    _write_cache(fetch_all_stops(api_key), cache_path)


def get_all_stops_cache(cache_path: str | Path = "cache/all_stops_cache.pkl") -> dict[str, Any]:
    return _read_cache(cache_path, "Run update_all_stops_cache() first.")


def update_all_routes_cache(
    api_key: str,
    fetch_all_routes: Callable[[str], dict[str, Any]],
    cache_path: str | Path = "cache/all_routes_cache.pkl",
) -> None:
    _write_cache(fetch_all_routes(api_key), cache_path)


def get_all_routes_cache(cache_path: str | Path = "cache/all_routes_cache.pkl") -> dict[str, Any]:
    return _read_cache(cache_path, "Run update_all_routes_cache() first.")


def update_all_trips_cache(
    api_key: str,
    fetch_all_trips: Callable[[str], dict[str, Any]],
    cache_path: str | Path = "cache/all_trips_cache.pkl",
) -> None:
    _write_cache(fetch_all_trips(api_key), cache_path)


def get_all_trips_cache(cache_path: str | Path = "cache/all_trips_cache.pkl") -> dict[str, Any]:
    all_trips = _read_cache(cache_path, "Run update_all_trips_cache() first.")
    if isinstance(all_trips, dict) and "data" in all_trips:
        return all_trips["data"] if isinstance(all_trips["data"], list) else None
    


def load_prague_districts_info(
    geojson_path: str | Path = "cache/prague_districts.geojson",
) -> dict[str, Any]:
    """Load Prague districts GeoJSON and return stored data with basic summary."""
    path = Path(geojson_path)
    if not path.exists():
        raise RuntimeError(
            f"GeoJSON file {path} does not exist. Run the district data fetch step first."
        )

    try:
        with path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid GeoJSON content in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected GeoJSON structure in {path}: expected JSON object")

    features_raw = payload.get("features", [])
    features = features_raw if isinstance(features_raw, list) else []

    district_names: list[str] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        district_name = properties.get("NAZEV_MC") or properties.get("NAZEV_1")
        if district_name:
            district_names.append(str(district_name))

    unique_names = sorted(set(district_names))

    return {
        "geojson": payload,
        "feature_count": len(features),
        "district_names": unique_names,
        "district_count": len(unique_names),
    }


def load_prague_parks_info(
    geojson_path: str | Path = "cache/prague_parks.geojson",
) -> dict[str, Any]:
    """Load Prague parks GeoJSON and return stored data with basic summary."""
    path = Path(geojson_path)
    if not path.exists():
        raise RuntimeError(
            f"GeoJSON file {path} does not exist. Run the park data fetch step first."
        )

    try:
        with path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid GeoJSON content in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected GeoJSON structure in {path}: expected JSON object")

    features_raw = payload.get("features", [])
    features = features_raw if isinstance(features_raw, list) else []

    park_names: list[str] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        park_name = properties.get("NAZEV")
        if isinstance(park_name, str) and park_name.strip():
            park_names.append(park_name.strip())

    unique_names = sorted(set(park_names))

    return {
        "geojson": payload,
        "feature_count": len(features),
        "park_names": unique_names,
        "park_count": len(unique_names),
    }


