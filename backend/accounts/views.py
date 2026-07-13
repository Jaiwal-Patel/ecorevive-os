from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.permissions import CanManageUsers, IsGovernanceLeader

from .models import PROTECTED_GOVERNANCE_ROLES, User, UserRole
from .serializers import (
    ChangePasswordSerializer,
    GovernanceIdentitySerializer,
    MeSerializer,
    RegisterSerializer,
    UserAdminSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(
    methods=["GET"], responses=MeSerializer,
)
@extend_schema(
    methods=["PATCH"], request=MeSerializer, responses=MeSerializer,
)
@api_view(["GET", "PATCH"])
def me_view(request):
    if request.method == "GET":
        return Response(MeSerializer(request.user).data)
    serializer = MeSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@extend_schema(
    request=ChangePasswordSerializer, responses={200: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "Password changed successfully."})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [CanManageUsers]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = User.objects.exclude(role__in=PROTECTED_GOVERNANCE_ROLES)
        if self.request.user.role == UserRole.FOUNDER_RECOVERY:
            return queryset.filter(
                role__in={UserRole.PRINCIPAL_ADMIN, UserRole.OPERATIONS_ADMIN}
            )
        return queryset


class GovernanceIdentityViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.filter(role__in=PROTECTED_GOVERNANCE_ROLES)
    serializer_class = GovernanceIdentitySerializer
    permission_classes = [IsGovernanceLeader]
    http_method_names = ["get", "head", "options"]
