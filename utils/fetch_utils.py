import requests
import os
import json
from typing import Any
from pathlib import Path

API_BASE_URL = "https://api.golemio.cz"
DEPARTURE_BOARDS_PATH = "/v2/pid/departureboards"
ALL_STOPS = "/v2/gtfs/stops"
ALL_ROUTES = "/v2/gtfs/routes"
ALL_TRIPS = "/v2/gtfs/trips"
SHAPES = "/v2/gtfs/shapes/{id}"
TRIPS = "/v2/gtfs/trips/{id}"



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
    url = f"{API_BASE_URL}{ALL_STOPS}"
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
    url = f"{API_BASE_URL}{ALL_ROUTES}"
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


def fetch_all_trips(api_key: str, *, page_size: int = 10_000) -> dict[str, Any]:
    """
    Fetch all trips from the API, paginating automatically when the total
    number of trips exceeds the per-request limit.

    Args:
        api_key: Golemio API access token
        page_size: Number of records to request per page (max 10 000)

    Returns:
        Dictionary with a ``data`` key containing all collected trip records
    """
    url = f"{API_BASE_URL}{ALL_TRIPS}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }

    all_records: list[Any] = []
    offset = 0

    while True:
        params = {"limit": page_size, "offset": offset}
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 401:
            raise RuntimeError("Unauthorized: API key is missing or invalid")
        if response.status_code >= 400:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")

        payload = response.json()
        page_records: list[Any] = payload.get("data", []) if isinstance(payload, dict) else payload
        if not isinstance(page_records, list):
            break

        all_records.extend(page_records)
        print(f"Fetched trips: {len(all_records)} (page offset {offset})")

        if len(page_records) < page_size:
            break
        offset += page_size

    return {"data": all_records}



def fetch_shape(api_key: str, shape_id: str) -> dict[str, Any]:
    method_name = "fetch_shape"
    if not str(shape_id).strip():
        raise ValueError("shape_id must be provided")

    safe_shape_id = str(shape_id).strip()
    cache_dir = Path("cache/shapes")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{safe_shape_id}.json"

    if cache_file.exists():
        try:
            cached_payload = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(cached_payload, dict):
                return cached_payload
        except json.JSONDecodeError:
            # Broken cache file; refetch and overwrite.
            pass

    url = f"{API_BASE_URL}{SHAPES.format(id=safe_shape_id)}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }
    print(f'[{method_name}] Fetching shape_id: {safe_shape_id} from API')
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Unauthorized: API key is missing or invalid")
    if response.status_code == 404:
        raise RuntimeError(f"Shape not found for id: {safe_shape_id}")
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    payload = response.json()
    cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload