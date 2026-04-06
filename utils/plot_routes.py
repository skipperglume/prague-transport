from typing import Any
import matplotlib.pyplot as plt

def _extract_route_lines(routes: dict[str, Any] | list[dict[str, Any]]) -> list[list[tuple[float, float]]]:
    lines: list[list[tuple[float, float]]] = []

    def as_point(value: Any) -> tuple[float, float] | None:
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            return None
        try:
            lon = float(value[0])
            lat = float(value[1])
        except (TypeError, ValueError):
            return None
        return (lon, lat)

    def add_line(coords: Any) -> None:
        if not isinstance(coords, list):
            return
        line: list[tuple[float, float]] = []
        for candidate in coords:
            point = as_point(candidate)
            if point is not None:
                line.append(point)
        if len(line) >= 2:
            lines.append(line)

    def process_geometry(geometry: Any) -> None:
        if not isinstance(geometry, dict):
            return
        geometry_type = str(geometry.get("type", ""))
        coords = geometry.get("coordinates")
        if geometry_type == "LineString":
            add_line(coords)
        elif geometry_type == "MultiLineString" and isinstance(coords, list):
            for segment in coords:
                add_line(segment)

    if isinstance(routes, dict):
        features = routes.get("features")
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                process_geometry(feature.get("geometry"))

        for key in ("routes", "data"):
            route_list = routes.get(key)
            if isinstance(route_list, list):
                for route in route_list:
                    if not isinstance(route, dict):
                        continue
                    process_geometry(route.get("geometry"))

    if isinstance(routes, list):
        for route in routes:
            if not isinstance(route, dict):
                continue
            process_geometry(route.get("geometry"))

    return lines


def plot_routes_coordinates(routes: dict[str, Any] | list[dict[str, Any]]) -> None:
    fig = plt.figure(figsize=(10, 8))
    ax = plot_routes_on_figure(fig, routes)
    ax.set_title("Golemio Routes")
    plt.tight_layout()
    plt.savefig("images/routes_coordinates.png", dpi=300)


def plot_routes_on_figure(
    figure: Any,
    routes: dict[str, Any] | list[dict[str, Any]],
    *,
    line_width: float = 0.9,
    alpha: float = 0.6,
    color: str = "tab:red",
) -> Any:
    lines = _extract_route_lines(routes)
    if not lines:
        raise RuntimeError("No route geometries found in routes payload")

    ax = figure.gca()
    for line in lines:
        xs = [p[0] for p in line]
        ys = [p[1] for p in line]
        ax.plot(xs, ys, linewidth=line_width, alpha=alpha, color=color)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
    return ax