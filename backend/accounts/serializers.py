from django.contrib.auth.password_validation import (
    validate_password,
)
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import (
    AuthenticationFailed,
)
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)

from audit.services import record_event
from operations.models import VolunteerProfile

from .models import (
    PROTECTED_GOVERNANCE_ROLES,
    User,
    UserRole,
)


class OptionalEmailField(
    serializers.EmailField,
):
    def to_internal_value(self, data):
        if data is None:
            return None

        if (
            isinstance(data, str)
            and not data.strip()
        ):
            return None

        return super().to_internal_value(
            data,
        )

    def to_representation(self, value):
        return value or ""


def _normalize_email(value):
    if not value:
        return None

    return User.objects.normalize_email(
        value.strip()
    )


def _validate_unique_email(
    email,
    *,
    instance=None,
):
    if not email:
        return

    queryset = User.objects.filter(
        email__iexact=email,
    )

    if instance is not None:
        queryset = queryset.exclude(
            pk=instance.pk,
        )

    if queryset.exists():
        raise serializers.ValidationError(
            "An account with this email "
            "already exists."
        )


def _validate_phone_for_email_less_user(
    phone_number,
    *,
    instance=None,
):
    if not phone_number:
        raise serializers.ValidationError(
            "A phone number is required when "
            "no email address is provided."
        )

    queryset = User.objects.filter(
        phone_number=phone_number,
    )

    if instance is not None:
        queryset = queryset.exclude(
            pk=instance.pk,
        )

    if queryset.exists():
        raise serializers.ValidationError(
            "This phone number is already used "
            "by another account. Use an email "
            "address or a different phone number."
        )


class RegisterSerializer(
    serializers.ModelSerializer,
):
    email = OptionalEmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[],
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30,
    )
    password = serializers.CharField(
        write_only=True,
        validators=[
            validate_password,
        ],
    )
    account_type = serializers.ChoiceField(
        choices=[
            (
                UserRole.RESIDENT,
                "Resident",
            ),
            (
                UserRole.VOLUNTEER,
                "Volunteer",
            ),
        ],
        write_only=True,
        default=UserRole.RESIDENT,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "phone_number",
            "password",
            "account_type",
        ]

    def validate_email(self, value):
        email = _normalize_email(value)

        _validate_unique_email(
            email,
        )

        return email

    def validate(self, attrs):
        account_type = attrs.get(
            "account_type",
            UserRole.RESIDENT,
        )
        email = attrs.get(
            "email",
        )
        phone_number = (
            attrs.get(
                "phone_number",
                "",
            )
            or ""
        ).strip()

        attrs["phone_number"] = (
            phone_number
        )

        if (
            account_type
            == UserRole.VOLUNTEER
            and not email
        ):
            raise serializers.ValidationError(
                {
                    "email": (
                        "Email is required for "
                        "volunteer accounts."
                    )
                }
            )

        if (
            account_type
            == UserRole.RESIDENT
            and not email
        ):
            try:
                _validate_phone_for_email_less_user(
                    phone_number,
                )
            except serializers.ValidationError as exc:
                raise serializers.ValidationError(
                    {
                        "phone_number": (
                            exc.detail
                        )
                    }
                ) from exc

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        account_type = validated_data.pop(
            "account_type",
            UserRole.RESIDENT,
        )

        user = User.objects.create_user(
            **validated_data,
            role=account_type,
        )

        if (
            account_type
            == UserRole.VOLUNTEER
        ):
            VolunteerProfile.objects.create(
                user=user,
                active=False,
                safety_acknowledged=False,
            )

            record_event(
                actor=user,
                event_type=(
                    "volunteer."
                    "registration_submitted"
                ),
                summary=(
                    "Volunteer registration "
                    f"submitted by {user.email}"
                ),
                object_type="User",
                object_id=user.id,
            )

        return user


class LoginTokenSerializer(
    serializers.Serializer,
):
    login = serializers.CharField(
        required=False,
        write_only=True,
        trim_whitespace=True,
    )
    email = serializers.EmailField(
        required=False,
        write_only=True,
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        identifier = (
            attrs.get("login")
            or attrs.get("email")
            or ""
        ).strip()

        if not identifier:
            raise serializers.ValidationError(
                {
                    "login": (
                        "Enter your email address "
                        "or phone number."
                    )
                }
            )

        candidates = list(
            User.objects.filter(
                is_active=True,
            )
            .filter(
                Q(
                    email__iexact=identifier,
                )
                | Q(
                    phone_number=identifier,
                )
            )[:2]
        )

        if len(candidates) != 1:
            raise AuthenticationFailed(
                "No active account found with "
                "the given credentials."
            )

        user = candidates[0]

        if not user.check_password(
            attrs["password"]
        ):
            raise AuthenticationFailed(
                "No active account found with "
                "the given credentials."
            )

        refresh = RefreshToken.for_user(
            user,
        )

        user.last_login = timezone.now()
        user.save(
            update_fields=[
                "last_login",
            ]
        )

        return {
            "refresh": str(refresh),
            "access": str(
                refresh.access_token
            ),
        }


class MeSerializer(
    serializers.ModelSerializer,
):
    email = OptionalEmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[],
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "role",
            "must_change_password",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "role",
            "date_joined",
        ]

    def validate_email(self, value):
        email = _normalize_email(value)

        _validate_unique_email(
            email,
            instance=self.instance,
        )

        return email

    def validate(self, attrs):
        instance = self.instance

        email = attrs.get(
            "email",
            instance.email,
        )
        phone_number = (
            attrs.get(
                "phone_number",
                instance.phone_number,
            )
            or ""
        ).strip()

        attrs["phone_number"] = (
            phone_number
        )

        if (
            instance.role
            != UserRole.RESIDENT
            and not email
        ):
            raise serializers.ValidationError(
                {
                    "email": (
                        "Email is required for "
                        "this account."
                    )
                }
            )

        if (
            instance.role
            == UserRole.RESIDENT
            and not email
        ):
            try:
                _validate_phone_for_email_less_user(
                    phone_number,
                    instance=instance,
                )
            except serializers.ValidationError as exc:
                raise serializers.ValidationError(
                    {
                        "phone_number": (
                            exc.detail
                        )
                    }
                ) from exc

        return attrs


class UserAdminSerializer(
    serializers.ModelSerializer,
):
    email = OptionalEmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[],
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "date_joined",
            "password",
        ]
        read_only_fields = [
            "id",
            "date_joined",
        ]

    def validate_email(self, value):
        email = _normalize_email(value)

        _validate_unique_email(
            email,
            instance=self.instance,
        )

        return email

    def validate(self, attrs):
        instance = self.instance
        actor = self.context[
            "request"
        ].user

        requested_role = attrs.get(
            "role",
            getattr(
                instance,
                "role",
                UserRole.RESIDENT,
            ),
        )
        email = attrs.get(
            "email",
            getattr(
                instance,
                "email",
                None,
            ),
        )
        phone_number = (
            attrs.get(
                "phone_number",
                getattr(
                    instance,
                    "phone_number",
                    "",
                ),
            )
            or ""
        ).strip()

        attrs["phone_number"] = (
            phone_number
        )

        if (
            requested_role
            != UserRole.RESIDENT
            and not email
        ):
            raise serializers.ValidationError(
                {
                    "email": (
                        "Email is required for "
                        "non-resident accounts."
                    )
                }
            )

        if (
            requested_role
            == UserRole.RESIDENT
            and not email
        ):
            try:
                _validate_phone_for_email_less_user(
                    phone_number,
                    instance=instance,
                )
            except serializers.ValidationError as exc:
                raise serializers.ValidationError(
                    {
                        "phone_number": (
                            exc.detail
                        )
                    }
                ) from exc

        if (
            instance
            and instance.role
            in PROTECTED_GOVERNANCE_ROLES
        ):
            for field in (
                "email",
                "role",
                "is_active",
            ):
                if (
                    field in attrs
                    and attrs[field]
                    != getattr(
                        instance,
                        field,
                    )
                ):
                    raise serializers.ValidationError(
                        {
                            field: (
                                "Reserved governance "
                                "identities cannot be "
                                "changed here."
                            )
                        }
                    )

        if (
            requested_role
            in PROTECTED_GOVERNANCE_ROLES
            and (
                not instance
                or instance.role
                != requested_role
            )
        ):
            raise serializers.ValidationError(
                {
                    "role": (
                        "Reserved governance roles "
                        "are created only by the "
                        "bootstrap command."
                    )
                }
            )

        protected_admin_roles = {
            UserRole.PRINCIPAL_ADMIN,
            UserRole.OPERATIONS_ADMIN,
        }

        if (
            requested_role
            == UserRole.PRINCIPAL_ADMIN
            and actor.role
            not in {
                UserRole.FOUNDER_GUARDIAN,
                UserRole.FOUNDER_RECOVERY,
            }
        ):
            raise serializers.ValidationError(
                {
                    "role": (
                        "Only founder governance "
                        "authority may appoint a "
                        "Principal Administrator."
                    )
                }
            )

        if (
            instance
            and instance.role
            == UserRole.PRINCIPAL_ADMIN
            and actor.role
            not in {
                UserRole.FOUNDER_GUARDIAN,
                UserRole.FOUNDER_RECOVERY,
            }
        ):
            if any(
                field in attrs
                for field in (
                    "role",
                    "is_active",
                )
            ):
                raise serializers.ValidationError(
                    "Only founder governance "
                    "authority may alter a "
                    "Principal Administrator."
                )

        if (
            actor.role
            == UserRole.OPERATIONS_ADMIN
            and requested_role
            in protected_admin_roles
        ):
            raise serializers.ValidationError(
                {
                    "role": (
                        "Operations Administrators "
                        "cannot appoint "
                        "administrative roles."
                    )
                }
            )

        if (
            actor.role
            == UserRole.FOUNDER_RECOVERY
        ):
            allowed = {
                UserRole.PRINCIPAL_ADMIN,
                UserRole.OPERATIONS_ADMIN,
            }
            current_role = getattr(
                instance,
                "role",
                None,
            )

            if (
                requested_role not in allowed
                or (
                    current_role
                    and current_role
                    not in allowed
                )
            ):
                raise serializers.ValidationError(
                    "Founder Recovery is limited "
                    "to emergency administrator "
                    "management."
                )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop(
            "password",
            None,
        )

        if not password:
            raise serializers.ValidationError(
                {
                    "password": (
                        "A temporary password "
                        "is required."
                    )
                }
            )

        return User.objects.create_user(
            password=password,
            must_change_password=True,
            **validated_data,
        )

    def update(
        self,
        instance,
        validated_data,
    ):
        actor = self.context[
            "request"
        ].user
        previous_role = instance.role
        previous_active = (
            instance.is_active
        )

        password = validated_data.pop(
            "password",
            None,
        )

        updated = super().update(
            instance,
            validated_data,
        )

        if password:
            updated.set_password(
                password
            )
            updated.must_change_password = (
                True
            )
            updated.save()

        if (
            previous_role
            != updated.role
        ):
            record_event(
                actor=actor,
                event_type="user.role_changed",
                summary=(
                    f"Changed {updated} role "
                    f"from {previous_role} "
                    f"to {updated.role}"
                ),
                object_type="User",
                object_id=updated.id,
            )

        if (
            previous_active
            != updated.is_active
        ):
            record_event(
                actor=actor,
                event_type=(
                    "user.activation_changed"
                ),
                summary=(
                    f"Set {updated} active "
                    "status to "
                    f"{updated.is_active}"
                ),
                object_type="User",
                object_id=updated.id,
            )

        return updated


class GovernanceIdentitySerializer(
    serializers.ModelSerializer,
):
    role_label = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "role_label",
            "is_active",
            "date_joined",
            "updated_at",
        ]
        read_only_fields = fields


class ChangePasswordSerializer(
    serializers.Serializer,
):
    current_password = (
        serializers.CharField(
            write_only=True,
        )
    )
    new_password = (
        serializers.CharField(
            write_only=True,
            validators=[
                validate_password,
            ],
        )
    )

    def validate_current_password(
        self,
        value,
    ):
        if not self.context[
            "request"
        ].user.check_password(
            value
        ):
            raise serializers.ValidationError(
                "Current password is "
                "incorrect."
            )

        return value

    def save(self, **kwargs):
        user = self.context[
            "request"
        ].user

        user.set_password(
            self.validated_data[
                "new_password"
            ]
        )
        user.must_change_password = False
        user.save(
            update_fields=[
                "password",
                "must_change_password",
                "updated_at",
            ]
        )

        record_event(
            actor=user,
            event_type=(
                "user.password_changed"
            ),
            summary=(
                f"Password changed for {user}"
            ),
            object_type="User",
            object_id=user.id,
        )

        return user