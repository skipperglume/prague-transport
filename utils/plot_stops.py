from typing import Any
import matplotlib.pyplot as plt
import os

from utils.plot_handler import FigureContent

def _extract_stop_points(all_stops: dict[str, Any] | list[dict[str, Any]]) -> list[tuple[float, float, str]]:
    points: list[tuple[float, float, str]] = []

    def add_point(lon_raw: Any, lat_raw: Any, name: str) -> None:
        try:
            lon = float(lon_raw)
            lat = float(lat_raw)
        except (TypeError, ValueError):
            return
        points.append((lon, lat, name))

    def extract_name(obj: dict[str, Any]) -> str:
        """Extract stop name from various possible fields."""
        # Check properties (GeoJSON format)
        properties = obj.get("properties", {})
        if isinstance(properties, dict):
            name = properties.get("stop_name") or properties.get("name")
            if name:
                return str(name)
        
        # Check direct fields
        name = obj.get("stop_name") or obj.get("name")
        if name:
            return str(name)
        
        return "Unknown"

    if isinstance(all_stops, dict):
        features = all_stops.get("features")
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                geometry = feature.get("geometry", {})
                coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
                if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
                    name = extract_name(feature)
                    add_point(coordinates[0], coordinates[1], name)

        for key in ("stops", "data"):
            stop_list = all_stops.get(key)
            if isinstance(stop_list, list):
                for stop in stop_list:
                    if not isinstance(stop, dict):
                        continue
                    name = extract_name(stop)
                    add_point(stop.get("lon"), stop.get("lat"), name)
                    add_point(stop.get("longitude"), stop.get("latitude"), name)

    if isinstance(all_stops, list):
        for stop in all_stops:
            if not isinstance(stop, dict):
                continue
            name = extract_name(stop)
            add_point(stop.get("lon"), stop.get("lat"), name)
            add_point(stop.get("longitude"), stop.get("latitude"), name)

    # Remove duplicate points but keep name from first occurrence
    seen = {}
    unique_points = []
    for lon, lat, name in points:
        key = (lon, lat)
        if key not in seen:
            seen[key] = True
            unique_points.append((lon, lat, name))
    return unique_points





def plot_stops_on_figure(
    figure: FigureContent | Any,
    all_stops: dict[str, Any] | list[dict[str, Any]],
    *,
    point_size: float = 4,
    alpha: float = 0.7,
    color: str = "tab:blue",
    plot_names: bool = True,
) -> Any:
    
    method_name = "plot_stops_on_figure"

    points = _extract_stop_points(all_stops)
    if not points:
        raise RuntimeError("No stop coordinates found in all_stops payload")

    figure_content = figure if isinstance(figure, FigureContent) else None
    matplotlib_figure = figure_content.figure if figure_content is not None else figure
    ax = matplotlib_figure.gca()
    longitudes = [p[0] for p in points]
    latitudes = [p[1] for p in points]
    
    print(f'{method_name}: plotting {len(points)} stops')

    ax.scatter(longitudes, latitudes, s=point_size, alpha=alpha, color=color, label="Stops")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    
    print(f'{method_name}: Stop name plotting:  [{plot_names}]')
    # Plot stop names if enabled, avoiding duplicates
    if plot_names:
        if figure_content is not None:
            for point in points:
                if figure_content.stop_name_is_plotted(point[2]):
                    continue
                ax.text(point[0], point[1], point[2], fontsize=8, ha="right", va="bottom")
                figure_content.add_plotted_stop_name(point[2])
        else:
            draw_names = set()
            for point in points:
                if point[2] in draw_names:
                    continue
                ax.text(point[0], point[1], point[2], fontsize=8, ha="right", va="bottom")
                draw_names.add(point[2])



    if figure_content is not None:
        figure_content.add_stops(points)
    return ax





def plot_stops_coordinates(all_stops: dict[str, Any] | list[dict[str, Any]], title:str, out_dir:str='images' ) -> None:
    fig = plt.figure(figsize=(10, 8))
    plot_stops_on_figure(fig, all_stops, title=title)
    plt.tight_layout()
    output_path = os.path.join(out_dir, f"{title.lower().replace(' ', '_')}_coordinates.png")
    plt.savefig(output_path, dpi=300)