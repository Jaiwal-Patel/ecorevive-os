from logistics.services import GeoPoint, haversine_km, nearest_neighbour_route


def test_haversine_zero():
    point = GeoPoint("a", 25.2048, 55.2708)
    assert haversine_km(point, point) == 0

def test_nearest_neighbour_closest_first():
    start = GeoPoint("start", 25.20, 55.27)
    near = GeoPoint("near", 25.21, 55.27)
    far = GeoPoint("far", 25.30, 55.27)
    ordered, total = nearest_neighbour_route(start, [far, near])
    assert ordered[0][0].identifier == "near"
    assert total > 0
