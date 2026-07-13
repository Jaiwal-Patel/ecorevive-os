import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class UserRole(models.TextChoices):
    FOUNDER_GUARDIAN = "founder_guardian", "Founder Guardian"
    FOUNDER_RECOVERY = "founder_recovery", "Founder Recovery"
    PRINCIPAL_ADMIN = "principal_admin", "Principal Administrator"
    OPERATIONS_ADMIN = "operations_admin", "Operations Administrator"
    VOLUNTEER = "volunteer", "Volunteer"
    CORPORATE_COORDINATOR = "corporate_coordinator", "Corporate Coordinator"
    RESIDENT = "resident", "Resident"


PROTECTED_GOVERNANCE_ROLES = {
    UserRole.FOUNDER_GUARDIAN,
    UserRole.FOUNDER_RECOVERY,
}


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.RESIDENT)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.PRINCIPAL_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=160)
    phone_number = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=40, choices=UserRole.choices, default=UserRole.RESIDENT)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["full_name", "email"]

    @property
    def is_reserved_governance_identity(self):
        return self.role in PROTECTED_GOVERNANCE_ROLES

    def save(self, *args, allow_governance_update=False, **kwargs):
        if self.pk:
            previous = User.objects.filter(pk=self.pk).only("email", "role", "is_active").first()
            if previous and previous.role in PROTECTED_GOVERNANCE_ROLES and not allow_governance_update:
                if (
                    previous.email != self.email
                    or previous.role != self.role
                    or previous.is_active != self.is_active
                ):
                    raise ValidationError(
                        "Reserved governance identity email, role, and active status cannot be changed through ordinary workflows."
                    )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.role in PROTECTED_GOVERNANCE_ROLES:
            raise ValidationError("Reserved governance identities cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.email
