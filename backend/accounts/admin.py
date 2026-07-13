from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PROTECTED_GOVERNANCE_ROLES, User, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone_number")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "phone_number", "role")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser", "must_change_password")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "role", "password1", "password2")}),
    )
    readonly_fields = ("date_joined", "updated_at")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.role in {
            UserRole.FOUNDER_GUARDIAN,
            UserRole.FOUNDER_RECOVERY,
            UserRole.PRINCIPAL_ADMIN,
        }:
            return queryset
        return queryset.exclude(role=UserRole.FOUNDER_RECOVERY)

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.role in PROTECTED_GOVERNANCE_ROLES:
            fields.extend(["email", "role", "is_active"])
        return tuple(dict.fromkeys(fields))

    def has_delete_permission(self, request, obj=None):
        if obj and obj.role in PROTECTED_GOVERNANCE_ROLES:
            return False
        return super().has_delete_permission(request, obj)
