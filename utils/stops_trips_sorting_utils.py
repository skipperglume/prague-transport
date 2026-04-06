from typing import Any

def find_routes_trips_through_stops(
    stops: dict[str, Any],
    all_trips: dict[str, Any] | list[dict[str, Any]],
    all_routes: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Find routes and trips that pass through the given stops.
    
    Args:
        stops: Dictionary containing stop information with stop_ids or features
        all_trips: All available trips (may be dict with 'data' key or list)
        all_routes: All available routes (may be dict with 'data' key or list)
    
    Returns:
        Dictionary with:
            - 'matching_trips': List of trip objects that visit the given stops
            - 'matching_routes': List of route objects used by matching trips
            - 'stop_ids': Set of stop IDs extracted from the stops parameter
    """
    # Extract stop IDs from the stops parameter
    target_stop_ids: set[str] = set()
    
    if isinstance(stops, dict):
        # Handle GeoJSON features format
        features = stops.get("features", [])
        for feature in features:
            if isinstance(feature, dict):
                properties = feature.get("properties", {})
                if isinstance(properties, dict):
                    stop_id = properties.get("stop_id")
                    if stop_id:
                        target_stop_ids.add(str(stop_id))

        # Handle direct stops list
        for stop_list in [stops.get("stops", []), stops.get("data", [])]:
            if isinstance(stop_list, list):
                for stop in stop_list:
                    if isinstance(stop, dict):
                        stop_id = stop.get("stop_id") or stop.get("id")
                        if stop_id:
                            target_stop_ids.add(str(stop_id))
    
    # Extract trips list from the all_trips parameter
    trips_list: list[dict[str, Any]] = []
    if isinstance(all_trips, dict):
        if "data" in all_trips:
            trips_list = all_trips["data"] if isinstance(all_trips["data"], list) else []
        elif "trips" in all_trips:
            trips_list = all_trips["trips"] if isinstance(all_trips["trips"], list) else []
    elif isinstance(all_trips, list):
        trips_list = all_trips
    
    # Extract routes list from the all_routes parameter
    routes_list: list[dict[str, Any]] = []
    if isinstance(all_routes, dict):
        if "data" in all_routes:
            routes_list = all_routes["data"] if isinstance(all_routes["data"], list) else []
        elif "routes" in all_routes:
            routes_list = all_routes["routes"] if isinstance(all_routes["routes"], list) else []
    elif isinstance(all_routes, list):
        routes_list = all_routes
    
    # Create a mapping of route_id to route object for quick lookup
    routes_by_id: dict[str, dict[str, Any]] = {}
    for route in routes_list:
        if isinstance(route, dict):
            route_id = route.get("route_id") or route.get("id")
            if route_id:
                routes_by_id[str(route_id)] = route
    
    # Find trips that visit any of the target stops
    matching_trips: list[dict[str, Any]] = []
    matching_route_ids: set[str] = set()
    
    for trip in trips_list:
        if not isinstance(trip, dict):
            continue
        
        # Check if trip has stop_times or stop_sequence information
        stop_times = trip.get("stop_times", [])
        stop_sequence = trip.get("stop_sequence", [])
        
        # Handle stop_times list format
        for stop_time in stop_times:
            if isinstance(stop_time, dict):
                stop_id = stop_time.get("stop_id")
                if stop_id and str(stop_id) in target_stop_ids:
                    matching_trips.append(trip)
                    route_id = trip.get("route_id")
                    if route_id:
                        matching_route_ids.add(str(route_id))
                    break
        
        # Handle stop_sequence list format (if no match found in stop_times)
        if trip not in matching_trips:
            for stop_id in stop_sequence:
                if isinstance(stop_id, dict):
                    stop_id = stop_id.get("id") or stop_id.get("stop_id")
                if stop_id and str(stop_id) in target_stop_ids:
                    matching_trips.append(trip)
                    route_id = trip.get("route_id")
                    if route_id:
                        matching_route_ids.add(str(route_id))
                    break
    
    # Get the matching routes
    matching_routes: list[dict[str, Any]] = [
        routes_by_id[route_id] for route_id in matching_route_ids
        if route_id in routes_by_id
    ]
    
    return {
        "matching_trips": matching_trips,
        "matching_routes": matching_routes,
        "stop_ids": target_stop_ids,
        "trip_count": len(matching_trips),
        "route_count": len(matching_routes),
    }