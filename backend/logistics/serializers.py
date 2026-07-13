from rest_framework import serializers

from .models import RoutePlan, RouteStop


class RouteStopSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(source="request.public_reference", read_only=True)
    area = serializers.CharField(source="request.area", read_only=True)

    class Meta:
        model = RouteStop
        fields = [
            "id", "request", "request_reference", "area",
            "sequence", "distance_from_previous_km",
        ]

class RoutePlanSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = RoutePlan
        fields = [
            "id", "name", "route_date", "start_latitude", "start_longitude",
            "estimated_distance_km", "algorithm", "created_by", "stops", "created_at",
        ]
        read_only_fields = [
            "id", "estimated_distance_km", "algorithm", "created_by", "created_at",
        ]
