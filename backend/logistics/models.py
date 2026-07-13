from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel
from operations.models import CollectionRequest


class RoutePlan(UUIDTimeStampedModel):
    name = models.CharField(max_length=160)
    route_date = models.DateField()
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    estimated_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    algorithm = models.CharField(max_length=80, default="nearest_neighbour_v1")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="route_plans",
    )

    class Meta:
        ordering = ["-route_date", "-created_at"]


class RouteStop(UUIDTimeStampedModel):
    route = models.ForeignKey(RoutePlan, on_delete=models.CASCADE, related_name="stops")
    request = models.ForeignKey(CollectionRequest, on_delete=models.PROTECT, related_name="route_stops")
    sequence = models.PositiveIntegerField()
    distance_from_previous_km = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["route", "sequence"], name="unique_route_sequence"),
            models.UniqueConstraint(fields=["route", "request"], name="unique_route_request"),
        ]
