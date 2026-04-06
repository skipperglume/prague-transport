from typing import Any
import matplotlib.pyplot as plt




def draw_districts_on_figure(
	figure: Any,
	districts: list[dict[str, Any]],
	*,
	line_width: float = 1.0,
	line_alpha: float = 0.8,
	line_color: str = "tab:green",
	fill_alpha: float = 0.12,
	fill_color: str = "tab:green",
	title: str = "Prague Districts",
) -> Any:
	"""
	Draw district geometries on a matplotlib figure.

	Args:
		figure: Matplotlib figure instance
		districts: List of GeoJSON district features
		line_width: District border line width
		line_alpha: District border opacity
		line_color: District border color
		fill_alpha: District fill opacity
		fill_color: District fill color
		title: Axes title

	Returns:
		Matplotlib axes with drawn district geometries
	"""
	if not isinstance(districts, list) or not districts:
		raise RuntimeError("No districts provided")

	ax = figure.gca()
	has_drawn_geometry = False

	def draw_ring(ring: Any) -> bool:
		if not isinstance(ring, list) or len(ring) < 3:
			return False

		xs: list[float] = []
		ys: list[float] = []
		for point in ring:
			if not isinstance(point, (list, tuple)) or len(point) < 2:
				continue
			try:
				lon = float(point[0])
				lat = float(point[1])
			except (TypeError, ValueError):
				continue
			xs.append(lon)
			ys.append(lat)

		if len(xs) < 3:
			return False

		if xs[0] != xs[-1] or ys[0] != ys[-1]:
			xs.append(xs[0])
			ys.append(ys[0])

		ax.fill(xs, ys, color=fill_color, alpha=fill_alpha)
		ax.plot(xs, ys, color=line_color, linewidth=line_width, alpha=line_alpha)
		return True

	for district in districts:
		if not isinstance(district, dict):
			continue

		geometry = district.get("geometry", {})
		if not isinstance(geometry, dict):
			continue

		geometry_type = geometry.get("type")
		coordinates = geometry.get("coordinates")

		if geometry_type == "Polygon" and isinstance(coordinates, list):
			for ring in coordinates:
				if draw_ring(ring):
					has_drawn_geometry = True

		elif geometry_type == "MultiPolygon" and isinstance(coordinates, list):
			for polygon in coordinates:
				if not isinstance(polygon, list):
					continue
				for ring in polygon:
					if draw_ring(ring):
						has_drawn_geometry = True

	if not has_drawn_geometry:
		raise RuntimeError("No valid district geometries found")

	ax.set_xlabel("Longitude")
	ax.set_ylabel("Latitude")
	ax.set_title(title)
	ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
	ax.set_aspect("equal", adjustable="datalim")
	ax.autoscale_view()
	return ax



