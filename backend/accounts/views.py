from drf_spectacular.utils import (
    OpenApiTypes,
    extend_schema,
)
from rest_framework import (
    generics,
    mixins,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import (
    action,
    api_view,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.permissions import (
    CanManageUsers,
    IsGovernanceLeader,
)

from .models import (
    PROTECTED_GOVERNANCE_ROLES,
    User,
    UserRole,
)
from .serializers import (
    ChangePasswordSerializer,
    GovernanceIdentitySerializer,
    MeSerializer,
    RegisterSerializer,
    UserAdminSerializer,
)
from .services import (
    HIDDEN_SYSTEM_EMAILS,
    purge_test_account,
)


class PurgeTestAccountSerializer(serializers.Serializer):
    confirmation_email = serializers.EmailField()

    def validate_confirmation_email(self, value):
        target_user = self.context["target_user"]

        if value.strip().lower() != target_user.email.lower():
            raise serializers.ValidationError(
                "Enter the account email exactly to confirm permanent "
                "deletion."
            )

        return value


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(
    methods=["GET"],
    responses=MeSerializer,
)
@extend_schema(
    methods=["PATCH"],
    request=MeSerializer,
    responses=MeSerializer,
)
@api_view(["GET", "PATCH"])
def me_view(request):
    if request.method == "GET":
        return Response(
            MeSerializer(
                request.user,
            ).data
        )

    serializer = MeSerializer(
        request.user,
        data=request.data,
        partial=True,
    )
    serializer.is_valid(
        raise_exception=True,
    )
    serializer.save()

    return Response(
        serializer.data,
    )


@extend_schema(
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
    },
)
@api_view(["POST"])
def change_password_view(request):
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={
            "request": request,
        },
    )
    serializer.is_valid(
        raise_exception=True,
    )
    serializer.save()

    return Response(
        {
            "detail": "Password changed successfully.",
        }
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [CanManageUsers]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = (
            User.objects.exclude(
                role__in=PROTECTED_GOVERNANCE_ROLES,
            )
            .exclude(
                email__in=HIDDEN_SYSTEM_EMAILS,
            )
        )

        if self.request.user.role == UserRole.FOUNDER_RECOVERY:
            return queryset.filter(
                role__in={
                    UserRole.PRINCIPAL_ADMIN,
                    UserRole.OPERATIONS_ADMIN,
                }
            )

        return queryset

    @action(
        detail=True,
        methods=["post"],
        url_path="purge-test-account",
    )
    def purge_test_account_action(
        self,
        request,
        pk=None,
    ):
        target_user = self.get_object()
        actor = request.user

        if target_user == actor:
            return Response(
                {
                    "detail": (
                        "You cannot permanently purge your own account."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        protected_roles = {
            UserRole.FOUNDER_GUARDIAN,
            UserRole.FOUNDER_RECOVERY,
            UserRole.PRINCIPAL_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        }

        if target_user.role in protected_roles:
            return Response(
                {
                    "detail": (
                        "Founder and administrator accounts cannot be "
                        "permanently purged."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_user.email in HIDDEN_SYSTEM_EMAILS:
            return Response(
                {
                    "detail": (
                        "System placeholder accounts cannot be purged."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PurgeTestAccountSerializer(
            data=request.data,
            context={
                "target_user": target_user,
            },
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = purge_test_account(
                target_user=target_user,
                actor=actor,
            )
        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Test account and its unverified collection "
                    "requests were permanently deleted."
                ),
                **result,
            },
            status=status.HTTP_200_OK,
        )


class GovernanceIdentityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.filter(
        role__in=PROTECTED_GOVERNANCE_ROLES,
    )
    serializer_class = GovernanceIdentitySerializer
    permission_classes = [IsGovernanceLeader]
    http_method_names = [
        "get",
        "head",
        "options",
    ]