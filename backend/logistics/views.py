from decimal import Decimal

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from common.permissions import IsOperationalAdmin
from operations.models import CollectionRequest

from .models import RoutePlan, RouteStop
from .serializers import RoutePlanSerializer
from .services import GeoPoint, nearest_neighbour_route


class RoutePlanViewSet(viewsets.ModelViewSet):
    queryset = RoutePlan.objects.prefetch_related("stops__request").all()
    serializer_class = RoutePlanSerializer
    permission_classes = [IsOperationalAdmin]
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def optimize(self, request):
        request_ids = request.data.get("request_ids", [])
        if not request_ids:
            raise ValidationError({"request_ids": "Provide at least one collection request."})

        collection_requests = list(CollectionRequest.objects.filter(id__in=request_ids))
        if len(collection_requests) != len(set(request_ids)):
            raise ValidationError("One or more collection requests were not found.")

        missing = [
            obj.public_reference
            for obj in collection_requests
            if obj.latitude is None or obj.longitude is None
        ]
        if missing:
            raise ValidationError({"coordinates": f"Missing coordinates for: {', '.join(missing)}"})

        try:
            start = GeoPoint(
                "start",
                float(request.data["start_latitude"]),
                float(request.data["start_longitude"]),
            )
            route_date = request.data["route_date"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(
                "Valid route_date, start_latitude, and start_longitude are required."
            ) from exc

        points = [
            GeoPoint(str(obj.id), float(obj.latitude), float(obj.longitude))
            for obj in collection_requests
        ]
        ordered, total = nearest_neighbour_route(start, points)
        request_map = {str(obj.id): obj for obj in collection_requests}

        plan = RoutePlan.objects.create(
            name=request.data.get("name", "Optimized EcoRevive route"),
            route_date=route_date,
            start_latitude=Decimal(str(start.latitude)),
            start_longitude=Decimal(str(start.longitude)),
            estimated_distance_km=Decimal(str(round(total, 2))),
            created_by=request.user,
        )
        for sequence, (point, distance) in enumerate(ordered, start=1):
            RouteStop.objects.create(
                route=plan,
                request=request_map[point.identifier],
                sequence=sequence,
                distance_from_previous_km=Decimal(str(round(distance, 2))),
            )
        return Response(self.get_serializer(plan).data, status=status.HTTP_201_CREATED)
