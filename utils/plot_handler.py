from typing import Any
from datetime import datetime
import matplotlib.pyplot as plt

class FigureContent:
    """Track information about what is plotted on a figure."""
    
    def __init__(self, title: str = "Untitled Figure", figure: Any | None = None) -> None:
        """
        Initialize figure content tracker.
        
        Args:
            title: The title of the figure
            figure: The matplotlib figure associated with this content
        """
        self.title = title
        self.figure = figure if figure is not None else plt.figure()
        self.districts: list[dict[str, Any]] = []
        self.district_names: list[str] = []
        self.stops: list[tuple[float, float, str]] = []
        self.stop_names: list[str] = []
        self.routes: list[list[tuple[float, float]]] = []
        self.created_at = datetime.now()
        self.plotted_stop_names: set[str] = set()

    def add_plotted_stop_name(self, name: str) -> None:
        """Add a stop name to the set of plotted names."""
        self.plotted_stop_names.add(name)

    def stop_name_is_plotted(self, name: str) -> bool:
        """Check if a stop name has already been plotted."""
        return name in self.plotted_stop_names
    
    def add_districts(self, districts: list[dict[str, Any]]) -> None:
        """
        Add district features to the content tracker.
        
        Args:
            districts: List of GeoJSON district features
        """
        self.districts.extend(districts)
        
        # Extract district names
        for district in districts:
            if not isinstance(district, dict):
                continue
            properties = district.get("properties", {})
            if isinstance(properties, dict):
                name = properties.get("NAZEV_MC") or properties.get("NAZEV_1")
                if name:
                    self.district_names.append(str(name))
        
        self.district_names = sorted(list(set(self.district_names)))
    
    def add_stops(self, stops: list[tuple[float, float, str]]) -> None:
        """
        Add stop points to the content tracker.
        
        Args:
            stops: List of (longitude, latitude, name) tuples
        """
        self.stops.extend(stops)
        
        # Extract unique stop names
        for stop in stops:
            if len(stop) >= 3:
                name = stop[2]
                if name and name not in self.stop_names:
                    self.stop_names.append(name)
        
        self.stop_names = sorted(self.stop_names)

    def add_routes(self, routes: list[list[tuple[float, float]]]) -> None:
        """
        Add plotted route line coordinates to the content tracker.
        
        Args:
            routes: List of route line coordinate sequences
        """
        for route in routes:
            if not isinstance(route, list) or len(route) < 2:
                continue
            cleaned_route: list[tuple[float, float]] = []
            for point in route:
                if not isinstance(point, tuple) or len(point) < 2:
                    continue
                try:
                    lon = float(point[0])
                    lat = float(point[1])
                except (TypeError, ValueError):
                    continue
                cleaned_route.append((lon, lat))
            if len(cleaned_route) >= 2:
                self.routes.append(cleaned_route)
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of the figure content.
        
        Returns:
            Dictionary with district and stop information
        """
        return {
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "district_count": len(set(self.district_names)),
            "district_names": self.district_names,
            "stop_count": len(set(self.stop_names)),
            "stop_names": self.stop_names,
            "route_count": len(self.routes),
            "total_geometries": len(self.districts),
            "total_route_segments": len(self.routes),
            "total_points": len(self.stops),
        }
    
    def __repr__(self) -> str:
        summary = self.get_summary()
        return (
            f"FigureContent(title='{summary['title']}', "
            f"districts={summary['district_count']}, "
            f"routes={summary['route_count']}, "
            f"stops={summary['stop_count']})"
        )
    
    def save_figure(self, filename: str) -> None:
        """
        Save the associated figure to a file.
        
        Args:
            filename: The path to save the figure to
        """
        if self.figure is not None:
            self.figure.tight_layout()
            self.figure.savefig(filename, dpi=300)
            