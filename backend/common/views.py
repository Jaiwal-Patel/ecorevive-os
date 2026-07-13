from django.conf import settings
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@permission_classes([AllowAny])
def health_view(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return Response({"status": "ok", "time": timezone.now()})

@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
@permission_classes([AllowAny])
def public_config_view(request):
    return Response({
        "project_name": settings.PROJECT_NAME,
        "organization_name": settings.ORGANIZATION_NAME,
        "tagline": settings.PUBLIC_TAGLINE,
        "service_city": settings.SERVICE_CITY,
        "service_country": settings.SERVICE_COUNTRY,
        "public_site_url": settings.PUBLIC_SITE_URL,
    })
