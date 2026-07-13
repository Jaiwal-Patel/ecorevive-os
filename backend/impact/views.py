from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.permissions import IsOperationalAdmin

from .models import ImpactMetric
from .serializers import ImpactMetricSerializer


@extend_schema(responses=ImpactMetricSerializer(many=True))
@api_view(["GET"])
@permission_classes([AllowAny])
def public_impact_view(request):
    return Response(
        ImpactMetricSerializer(ImpactMetric.objects.filter(public=True), many=True).data
    )

class ImpactMetricViewSet(viewsets.ModelViewSet):
    queryset = ImpactMetric.objects.all()
    serializer_class = ImpactMetricSerializer
    permission_classes = [IsOperationalAdmin]
    http_method_names = ["get", "post", "patch", "head", "options"]
