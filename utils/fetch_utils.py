import requests
import os
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


def fetch_all_trips(api_key: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{ALL_TRIPS}"
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



def fetch_shape(api_key: str, shape_id: str) -> dict[str, Any]:
    if not str(shape_id).strip():
        raise ValueError("shape_id must be provided")

    url = f"{API_BASE_URL}{SHAPES.format(id=shape_id)}"
    headers = {
        "X-Access-Token": api_key,
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Unauthorized: API key is missing or invalid")
    if response.status_code == 404:
        raise RuntimeError(f"Shape not found for id: {shape_id}")
    if response.status_code >= 400:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()