from utils.cache_utils import update_all_stops_cache, update_all_trips_cache, update_all_routes_cache
from utils.fetch_utils import fetch_all_stops, fetch_all_trips, fetch_all_routes, load_api_key

if __name__ == "__main__":
    api_key = load_api_key()
    
    update_all_stops_cache(api_key, fetch_all_stops)
    update_all_trips_cache(api_key, fetch_all_trips)
    update_all_routes_cache(api_key, fetch_all_routes)