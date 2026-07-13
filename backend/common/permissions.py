from rest_framework.permissions import BasePermission


class HasAnyRole(BasePermission):
    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )

class IsGovernanceLeader(HasAnyRole):
    allowed_roles = {"founder_guardian", "founder_recovery", "principal_admin"}

class IsOperationalAdmin(HasAnyRole):
    allowed_roles = {
        "founder_guardian",
        "principal_admin",
        "operations_admin",
    }


class CanManageUsers(HasAnyRole):
    allowed_roles = {
        "founder_guardian",
        "founder_recovery",
        "principal_admin",
        "operations_admin",
    }
