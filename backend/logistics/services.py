from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class GeoPoint:
    identifier: str
    latitude: float
    longitude: float


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    earth_radius_km = 6371.0088
    lat1, lon1, lat2, lon2 = map(
        radians, [a.latitude, a.longitude, b.latitude, b.longitude]
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(h))


def nearest_neighbour_route(start: GeoPoint, points: list[GeoPoint]):
    remaining = points.copy()
    current = start
    ordered: list[tuple[GeoPoint, float]] = []
    total = 0.0

    while remaining:
        next_point = min(remaining, key=lambda point: haversine_km(current, point))
        distance = haversine_km(current, next_point)
        ordered.append((next_point, distance))
        total += distance
        current = next_point
        remaining.remove(next_point)

    return ordered, total
