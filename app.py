#!/usr/bin/env python3
import argparse
import json
import os
import sys
import pickle
from pathlib import Path
from typing import Any

import requests

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise RuntimeError(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc


API_BASE_URL = "https://api.golemio.cz"
DEPARTURE_BOARDS_PATH = "/v2/pid/departureboards"

STOPS = "/v2/gtfs/stops"
ROUTES = "/v2/gtfs/routes"
SHAPES = "/v2/gtfs/shapes/{id}"



def load_api_key() -> str:
    '''
    Load API key from environment variable or secrets.txt file.
    '''
    env_key = os.getenv("GOLEMIO_API_KEY", "").strip()
    if env_key:
        return env_key

    secrets_path = Path("secrets.txt")
    if secrets_path.exists():
        token = secrets_path.read_text(encoding="utf-8").strip()
        if token:
            return token

    raise RuntimeError(
        "Missing API key. Set GOLEMIO_API_KEY or add token to secrets.txt"
    )


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "stop_names": ["Anděl", "Karlovo náměstí"],
            "tram_lines": ["9", "22"],
            "minutes_after": 60,
            "minutes_before": 0,
            "limit": 40,
            "preferred_timezone": "Europe/Prague",
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config file must be a JSON object")
    return data


def parse_csv_arg(value: str | None) -> list[str] | None:
    if not value:
        return None
    out = [item.strip() for item in value.split(",") if item.strip()]
    return out or None


def build_params(config: dict[str, Any], override_stops: list[str] | None) -> list[tuple[str, str]]:
    stops = override_stops or config.get("stop_names") or []
    if not stops:
        raise ValueError("No stop names provided. Set stop_names in config or use --stops")

    params: list[tuple[str, str]] = []
    for stop_name in stops:
        # The API docs define array params as names[]/ids[] style.
        params.append(("names[]", str(stop_name)))

    params.append(("minutesAfter", str(config.get("minutes_after", 60))))
    params.append(("minutesBefore", str(config.get("minutes_before", 0))))
    params.append(("limit", str(config.get("limit", 40))))
    params.append(("preferredTimezone", str(config.get("preferred_timezone", "Europe/Prague"))))
    params.append(("order", "real"))
    return params


def fetch_departures(api_key: str, params: list[tuple[str, str]]) -> dict[str, Any]:
    url = f"{API_BASE_URL}{DEPARTURE_BOARDS_PATH}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }
    print(url)
    print(headers)
    print(params)
    response = requests.get(url, headers=headers, params=params, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Unauthorized: API key is missing or invalid")
    if response.status_code == 404:
        raise RuntimeError(
            "API returned 404 (no matching stops found). "
            "Use exact stop names including diacritics, or adjust --stops/config stop_names."
        )
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def fetch_all_stops(api_key: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{STOPS}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Unauthorized: API key is missing or invalid")
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def fetch_all_routes(api_key: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{ROUTES}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Unauthorized: API key is missing or invalid")
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def update_all_stops_cache(api_key: str, cache_path: Path='all_stops_cache.pkl') -> None:
    all_stops = fetch_all_stops(api_key)
    with open(cache_path, 'wb') as f:
        pickle.dump(all_stops, f)


def get_all_stops_cache(cache_path: Path='all_stops_cache.pkl') -> dict[str, Any] | None:
    if not os.path.exists(cache_path):
        raise RuntimeError(f"Cache file {cache_path} does not exist. Run update_all_stops_cache() first.")
    with open(cache_path, 'rb') as f:
        return pickle.load(f)


def update_all_routes_cache(api_key: str, cache_path: Path='all_routes_cache.pkl') -> None:
    all_routes = fetch_all_routes(api_key)
    with open(cache_path, 'wb') as f:
        pickle.dump(all_routes, f)


def get_all_routes_cache(cache_path: Path='all_routes_cache.pkl') -> dict[str, Any] | None:
    if not os.path.exists(cache_path):
        raise RuntimeError(f"Cache file {cache_path} does not exist. Run update_all_routes_cache() first.")
    with open(cache_path, 'rb') as f:
        return pickle.load(f)


def plot_stops_coordinates(all_stops: dict[str, Any] | list[dict[str, Any]]) -> None:
    

    points: list[tuple[float, float]] = []

    def add_point(lon_raw: Any, lat_raw: Any) -> None:
        try:
            lon = float(lon_raw)
            lat = float(lat_raw)
        except (TypeError, ValueError):
            return
        points.append((lon, lat))

    if isinstance(all_stops, dict):
        # GeoJSON-like shape from GTFS endpoints.
        features = all_stops.get("features")
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
                if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
                    add_point(coordinates[0], coordinates[1])

        # Flat list payload variants.
        for key in ("stops", "data"):
            stop_list = all_stops.get(key)
            if isinstance(stop_list, list):
                for stop in stop_list:
                    if not isinstance(stop, dict):
                        continue
                    add_point(stop.get("lon"), stop.get("lat"))
                    add_point(stop.get("longitude"), stop.get("latitude"))

    if isinstance(all_stops, list):
        for stop in all_stops:
            if not isinstance(stop, dict):
                continue
            add_point(stop.get("lon"), stop.get("lat"))
            add_point(stop.get("longitude"), stop.get("latitude"))

    unique_points = list(dict.fromkeys(points))
    if not unique_points:
        raise RuntimeError("No stop coordinates found in all_stops payload")

    longitudes = [p[0] for p in unique_points]
    latitudes = [p[1] for p in unique_points]

    plt.figure(figsize=(10, 8))
    plt.scatter(longitudes, latitudes, s=4, alpha=0.7)
    plt.title("Golemio Stops Coordinates")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    plt.tight_layout()
    plt.savefig("stops_coordinates.png", dpi=300)



def extract_tram_departures(
    payload: dict[str, Any],
    tram_lines: set[str] | None,
) -> list[dict[str, str]]:
    stops = payload.get("stops", [])
    stop_id_to_name: dict[str, str] = {}
    stop_id_to_platform: dict[str, str] = {}

    for stop in stops:
        stop_id = str(stop.get("stop_id", ""))
        if stop_id:
            stop_id_to_name[stop_id] = str(stop.get("stop_name", ""))
            stop_id_to_platform[stop_id] = str(stop.get("platform_code", ""))

    rows: list[dict[str, str]] = []
    for item in payload.get("departures", []):
        route = item.get("route", {})
        trip = item.get("trip", {})
        stop = item.get("stop", {})
        departure_timestamp = item.get("departure_timestamp", {})

        route_type = route.get("type")
        line = str(route.get("short_name", "")).strip()
        if route_type != 0:
            continue
        if tram_lines is not None and line not in tram_lines:
            continue

        stop_id = str(stop.get("id", ""))
        platform_code = str(stop.get("platform_code", "")) or stop_id_to_platform.get(stop_id, "")
        rows.append(
            {
                "minutes": str(departure_timestamp.get("minutes", "?")),
                "line": line,
                "destination": str(trip.get("headsign", "")),
                "stop": stop_id_to_name.get(stop_id, stop_id),
                "platform": platform_code,
                "scheduled": str(departure_timestamp.get("scheduled", "")),
                "predicted": str(departure_timestamp.get("predicted", "")),
            }
        )
    return rows


def print_table(rows: list[dict[str, str]]) -> None:
    if not rows:
        print("No matching tram departures found.")
        return

    headers = ["in(min)", "line", "destination", "stop", "platform", "scheduled", "predicted"]
    keys = ["minutes", "line", "destination", "stop", "platform", "scheduled", "predicted"]

    widths: list[int] = []
    for header, key in zip(headers, keys):
        max_cell = max(len(row.get(key, "")) for row in rows)
        widths.append(max(len(header), max_cell))

    def format_row(values: list[str]) -> str:
        return " | ".join(value.ljust(width) for value, width in zip(values, widths))

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row([row[key] for key in keys]))




def main() -> int:
    parser = argparse.ArgumentParser(description="List chosen tram departures from Golemio PID API")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to JSON config file (default: config.json)",
    )
    parser.add_argument(
        "--stops",
        default=None,
        help="Comma-separated exact stop names (override config stop_names)",
    )
    parser.add_argument(
        "--lines",
        default=None,
        help="Comma-separated tram line numbers (override config tram_lines)",
    )
    args = parser.parse_args()
    api_key = load_api_key()
    # try:
    #     config = load_config(Path(args.config))
    #     stop_overrides = parse_csv_arg(args.stops)
    #     line_overrides = parse_csv_arg(args.lines)

    #     line_source = line_overrides if line_overrides is not None else config.get("tram_lines", [])
    #     tram_lines = {str(line).strip() for line in line_source if str(line).strip()}
    #     tram_line_filter = tram_lines if tram_lines else None

    #     api_key = load_api_key()
    #     print('API key loaded successfully.')
    #     params = build_params(config, stop_overrides)
    #     print('API parameters built successfully.')
    #     payload = fetch_departures(api_key, params)
    #     print('API response fetched successfully.')
    #     rows = extract_tram_departures(payload, tram_line_filter)
    #     print('Tram departures extracted successfully.')
    #     print_table(rows)
    #     # return 0
    # except Exception as exc:
    #     print(f"Error: {exc}", file=sys.stderr)
    #     return 1
    

    # update_all_stops_cache(api_key)    
    all_stops = get_all_stops_cache()

    plot_stops_coordinates(all_stops)


    # fetch_all_routes
    update_all_routes_cache(api_key)
    # get_all_routes_cache


if __name__ == "__main__":
    raise SystemExit(main())
