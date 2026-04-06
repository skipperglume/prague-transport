#!/usr/bin/env python3
import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise RuntimeError(
        "matplotlib is required for plotting. Install it with: pip install matplotlib"
    ) from exc

from utils.cache_utils import (
    get_all_routes_cache,
    get_all_stops_cache,
    get_all_trips_cache,
    update_all_routes_cache,
    update_all_stops_cache,
    update_all_trips_cache,
    load_prague_districts_info,
)

from utils.fetch_utils import (
    fetch_all_routes,
    fetch_all_stops,
    fetch_all_trips,
    load_api_key,
    fetch_departures,
    fetch_shape,
    
)
from utils.districts_utils import (
    filter_districts_by_name,
)
from utils.stop_trips_sorting_utils import (
    filter_stops_by_name_regex,
    find_routes_trips_through_stops,
)

from utils.plot_districts import (
    draw_districts_on_figure,
)


from utils.plot_stops import (
    plot_stops_coordinates,
    plot_stops_on_figure,
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




def group_stops_by_zone_id(
    all_stops: dict[str, Any] | list[dict[str, Any]],
) -> dict[str | None, list[dict[str, Any]]]:
    grouped: dict[str | None, list[dict[str, Any]]] = {}

    def add_stop(zone_id: Any, stop_obj: dict[str, Any]) -> None:
        key = None if zone_id is None else str(zone_id)
        grouped.setdefault(key, []).append(stop_obj)

    if isinstance(all_stops, dict):
        features = all_stops.get("features")
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                properties = feature.get("properties", {})
                zone_id = properties.get("zone_id") if isinstance(properties, dict) else None
                add_stop(zone_id, feature)

        for key in ("stops", "data"):
            stop_list = all_stops.get(key)
            if isinstance(stop_list, list):
                for stop in stop_list:
                    if not isinstance(stop, dict):
                        continue
                    add_stop(stop.get("zone_id"), stop)

    if isinstance(all_stops, list):
        for stop in all_stops:
            if not isinstance(stop, dict):
                continue
            properties = stop.get("properties", {})
            if isinstance(properties, dict) and "zone_id" in properties:
                add_stop(properties.get("zone_id"), stop)
            else:
                add_stop(stop.get("zone_id"), stop)

    return grouped




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
    

    
    all_stops = get_all_stops_cache()
    all_routes = get_all_routes_cache()
    all_trips = get_all_trips_cache()

    prague_districts = load_prague_districts_info()

    grouped_stops = group_stops_by_zone_id(all_stops)
    print(f"Total stops: {len(all_stops.get('features', [])) if isinstance(all_stops, dict) else len(all_stops)}")
    print(f"Unique zone_ids: {len(grouped_stops)}")
    for zone_name in grouped_stops:
        print(f"Zone {zone_name}: {len(grouped_stops[zone_name])} stops")


    print(type(all_routes))
    print(all_routes[0:5])

    # plot_routes_coordinates(all_routes)

    # fetch_all_routes
    # get_all_routes_cache

    # print(group_stops_by_zone_id(all_stops).keys())

    # print(group_stops_by_zone_id(all_stops)['P'])

    print(type(all_stops))
    print(all_stops.keys())
    print(type(grouped_stops['P']))
    prague_zone_code = 'P'
    plot_stops_coordinates({'features': grouped_stops[prague_zone_code], 'type': 'FeatureCollection'}, title=f"Stops in Zone {prague_zone_code}")
    print()
    print(grouped_stops[prague_zone_code][0:5])
    print()


    
    
    print(all_stops['features'][0])
    print(all_routes[0])
    print(all_trips[0])

    print('prague_districts')
    print(prague_districts.keys())
    print(prague_districts['feature_count'])
    print(prague_districts['district_names'])
    print(prague_districts['district_count'])
    print(prague_districts['geojson'].keys())

    print(type(prague_districts['geojson']['type']))
    print(prague_districts['geojson']['type'])
    print(type(prague_districts['geojson']['crs']))
    print(prague_districts['geojson']['crs'].keys())
    print(type(prague_districts['geojson']['features']))
    print(type(prague_districts['geojson']['features'][0]))
    print(prague_districts['geojson']['features'][0].keys())
    print(prague_districts['geojson']['features'][0]['properties'])


    for district in prague_districts['geojson']['features']:
        print(f"[{district['properties']['NAZEV_1']}], [{district['properties']['NAZEV_MC']}]")


    filtered = filter_districts_by_name(prague_districts, "Praha .*")
    print(type(filtered))
    print(len(filtered))

    # dict_keys(['', '', ''])

    # print(prague_districts['Praha 1'])

    # print(fetch_shape(api_key, "L991V2"))

    # find_routes_trips_through_stops(all_stops, all_trips, all_routes)

    figure_prague = plt.figure(figsize=(40, 40))

    draw_districts_on_figure(
        figure_prague,
        filtered,
        line_width=0.8,
        line_alpha=0.7,
    )


    plot_stops_on_figure(
        figure_prague,
        {'features': grouped_stops[prague_zone_code], 'type': 'FeatureCollection'},
        point_size=10,
        alpha=0.9,
        color="tab:blue",
        title=f"Prague Districts and Stops in Zone {prague_zone_code}",
    )

    figure_prague.tight_layout()
    figure_prague.savefig("images/prague_districts.png", dpi=300)

if __name__ == "__main__":
    raise SystemExit(main())
