"""Utility functions for filtering and sorting districts."""

import re
from typing import Any

def filter_districts_by_name(prague_districts: dict[str, Any], name_pattern: str) -> list[dict[str, Any]]:
    """
    Filter Prague district GeoJSON features by matching district names against a regex pattern.
    
    Args:
        prague_districts: Dictionary with a GeoJSON payload under the 'geojson' key
        name_pattern: Regex pattern string to match against NAZEV_1 / NAZEV_MC values
    
    Returns:
        List of GeoJSON district features whose names match the regex pattern
    """
    if not name_pattern:
        return []
    
    try:
        compiled_pattern = re.compile(name_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Warning: Invalid regex pattern '{name_pattern}': {e}")
        return []
    
    geojson = prague_districts.get("geojson", {})
    features = geojson.get("features", []) if isinstance(geojson, dict) else []
    if not isinstance(features, list):
        return []

    matching_districts: list[dict[str, Any]] = []

    for district in features:
        if not isinstance(district, dict):
            continue

        properties = district.get("properties", {})
        if not isinstance(properties, dict):
            continue

        district_name_1 = str(properties.get("NAZEV_1") or "")
        district_name_mc = str(properties.get("NAZEV_MC") or "")
        searchable_name = f"{district_name_1} {district_name_mc}".strip()

        if searchable_name and compiled_pattern.search(searchable_name):
            matching_districts.append(district)

    matching_districts.sort(
        key=lambda district: (
            str(district.get("properties", {}).get("NAZEV_1") or ""),
            str(district.get("properties", {}).get("NAZEV_MC") or ""),
        )
    )
    
    return matching_districts