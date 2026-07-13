from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import UserRole
from common.permissions import IsOperationalAdmin

from .models import Organization
from .serializers import OrganizationSerializer

ADMIN_ROLES = {
    UserRole.FOUNDER_GUARDIAN,
    UserRole.PRINCIPAL_ADMIN,
    UserRole.OPERATIONS_ADMIN,
}

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if self.request.user.role in ADMIN_ROLES:
            return Organization.objects.select_related("created_by").all()
        return Organization.objects.filter(members=self.request.user).select_related("created_by")

    def perform_create(self, serializer):
        organization = serializer.save(created_by=self.request.user)
        organization.organizationmembership_set.create(
            user=self.request.user, is_coordinator=True
        )

    @action(detail=True, methods=["post"], permission_classes=[IsOperationalAdmin])
    def approve(self, request, pk=None):
        organization = self.get_object()
        organization.approved = True
        organization.save(update_fields=["approved", "updated_at"])
        return Response(self.get_serializer(organization).data)
