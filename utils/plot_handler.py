from typing import Any
from datetime import datetime

class FigureContent:
	"""Track information about what is plotted on a figure."""
	
	def __init__(self, title: str = "Untitled Figure") -> None:
		"""
		Initialize figure content tracker.
		
		Args:
			title: The title of the figure
		"""
		self.title = title
		self.districts: list[dict[str, Any]] = []
		self.district_names: list[str] = []
		self.stops: list[tuple[float, float, str]] = []
		self.stop_names: list[str] = []
		self.created_at = datetime.now()
	
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
			"total_geometries": len(self.districts),
			"total_points": len(self.stops),
		}
	
	def __repr__(self) -> str:
		summary = self.get_summary()
		return (
			f"FigureContent(title='{summary['title']}', "
			f"districts={summary['district_count']}, "
			f"stops={summary['stop_count']})"
		)