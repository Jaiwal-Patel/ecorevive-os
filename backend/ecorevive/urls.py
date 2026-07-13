from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.views import (
    GovernanceIdentityViewSet,
    RegisterView,
    UserViewSet,
    change_password_view,
    me_view,
)
from audit.views import AuditEventViewSet
from common.views import health_view, public_config_view
from impact.views import ImpactMetricViewSet, public_impact_view
from logistics.views import RoutePlanViewSet
from operations.views import (
    CollectionRequestViewSet,
    HandoverBatchViewSet,
    ItemCategoryViewSet,
    PickupAssignmentViewSet,
    VolunteerProfileViewSet,
)
from organizations.views import OrganizationViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("governance/identities", GovernanceIdentityViewSet, basename="governance-identity")
router.register("governance/audit-events", AuditEventViewSet, basename="audit-event")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("item-categories", ItemCategoryViewSet, basename="item-category")
router.register("collection-requests", CollectionRequestViewSet, basename="collection-request")
router.register("volunteer-profiles", VolunteerProfileViewSet, basename="volunteer-profile")
router.register("pickup-assignments", PickupAssignmentViewSet, basename="pickup-assignment")
router.register("handover-batches", HandoverBatchViewSet, basename="handover-batch")
router.register("route-plans", RoutePlanViewSet, basename="route-plan")
router.register("impact-metrics", ImpactMetricViewSet, basename="impact-metric")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_view, name="health"),
    path("api/public/config/", public_config_view, name="public-config"),
    path("api/public/impact/", public_impact_view, name="public-impact"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", me_view, name="me"),
    path("api/auth/change-password/", change_password_view, name="change-password"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
