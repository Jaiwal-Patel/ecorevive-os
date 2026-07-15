from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from audit.services import record_event
from operations.models import VolunteerProfile

from .models import PROTECTED_GOVERNANCE_ROLES, User, UserRole


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    account_type = serializers.ChoiceField(
        choices=[
            (UserRole.RESIDENT, "Resident"),
            (UserRole.VOLUNTEER, "Volunteer"),
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

        if account_type == UserRole.VOLUNTEER:
            VolunteerProfile.objects.create(
                user=user,
                active=False,
                safety_acknowledged=False,
            )

            record_event(
                actor=user,
                event_type="volunteer.registration_submitted",
                summary=f"Volunteer registration submitted by {user.email}",
                object_type="User",
                object_id=user.id,
            )

        return user


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone_number", "role",
            "must_change_password", "date_joined",
        ]
        read_only_fields = ["id", "role", "date_joined"]


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone_number", "role",
            "is_active", "date_joined", "password",
        ]
        read_only_fields = ["id", "date_joined"]

    def validate(self, attrs):
        instance = self.instance
        actor = self.context["request"].user
        requested_role = attrs.get("role", getattr(instance, "role", None))

        if instance and instance.role in PROTECTED_GOVERNANCE_ROLES:
            for field in ("email", "role", "is_active"):
                if field in attrs and attrs[field] != getattr(instance, field):
                    raise serializers.ValidationError(
                        {field: "Reserved governance identities cannot be changed here."}
                    )
        if requested_role in PROTECTED_GOVERNANCE_ROLES and (
            not instance or instance.role != requested_role
        ):
            raise serializers.ValidationError(
                {"role": "Reserved governance roles are created only by the bootstrap command."}
            )

        protected_admin_roles = {UserRole.PRINCIPAL_ADMIN, UserRole.OPERATIONS_ADMIN}
        if requested_role == UserRole.PRINCIPAL_ADMIN and actor.role not in {
            UserRole.FOUNDER_GUARDIAN,
            UserRole.FOUNDER_RECOVERY,
        }:
            raise serializers.ValidationError(
                {"role": "Only founder governance authority may appoint a Principal Administrator."}
            )
        if instance and instance.role == UserRole.PRINCIPAL_ADMIN and actor.role not in {
            UserRole.FOUNDER_GUARDIAN,
            UserRole.FOUNDER_RECOVERY,
        }:
            if any(field in attrs for field in ("role", "is_active")):
                raise serializers.ValidationError(
                    "Only founder governance authority may alter a Principal Administrator."
                )
        if actor.role == UserRole.OPERATIONS_ADMIN and requested_role in protected_admin_roles:
            raise serializers.ValidationError(
                {"role": "Operations Administrators cannot appoint administrative roles."}
            )
        if actor.role == UserRole.FOUNDER_RECOVERY:
            allowed = {UserRole.PRINCIPAL_ADMIN, UserRole.OPERATIONS_ADMIN}
            current_role = getattr(instance, "role", None)
            if requested_role not in allowed or (current_role and current_role not in allowed):
                raise serializers.ValidationError(
                    "Founder Recovery is limited to emergency administrator management."
                )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "A temporary password is required."})
        return User.objects.create_user(password=password, must_change_password=True, **validated_data)

    def update(self, instance, validated_data):
        actor = self.context["request"].user
        previous_role = instance.role
        previous_active = instance.is_active
        password = validated_data.pop("password", None)
        updated = super().update(instance, validated_data)
        if password:
            updated.set_password(password)
            updated.must_change_password = True
            updated.save()
        if previous_role != updated.role:
            record_event(
                actor=actor,
                event_type="user.role_changed",
                summary=f"Changed {updated.email} role from {previous_role} to {updated.role}",
                object_type="User",
                object_id=updated.id,
            )
        if previous_active != updated.is_active:
            record_event(
                actor=actor,
                event_type="user.activation_changed",
                summary=f"Set {updated.email} active status to {updated.is_active}",
                object_type="User",
                object_id=updated.id,
            )
        return updated


class GovernanceIdentitySerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "role", "role_label",
            "is_active", "date_joined", "updated_at",
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        record_event(
            actor=user,
            event_type="user.password_changed",
            summary=f"Password changed for {user.email}",
            object_type="User",
            object_id=user.id,
        )
        return user
