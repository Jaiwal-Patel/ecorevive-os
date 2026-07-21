from django.db import transaction

from audit.services import record_event
from logistics.models import RoutePlan, RouteStop
from operations.models import (
    CollectionRequest,
    HandoverBatch,
    HandoverRequest,
    PickupAssignment,
    StatusTransition,
    VolunteerApprovalStatus,
    VolunteerProfile,
)
from organizations.models import Organization

from .models import User, UserRole

SYSTEM_ACTOR_EMAIL = "system-records@ecorevive.invalid"
SYSTEM_VOLUNTEER_EMAIL = "deleted-volunteer@ecorevive.invalid"

HIDDEN_SYSTEM_EMAILS = {
    SYSTEM_ACTOR_EMAIL,
    SYSTEM_VOLUNTEER_EMAIL,
}


def _get_system_actor():
    system_user, created = User.objects.get_or_create(
        email=SYSTEM_ACTOR_EMAIL,
        defaults={
            "full_name": "EcoRevive System Records",
            "phone_number": "",
            "role": UserRole.RESIDENT,
            "is_active": False,
            "is_staff": False,
            "is_superuser": False,
        },
    )

    if created:
        system_user.set_unusable_password()
        system_user.save(
            update_fields=[
                "password",
                "updated_at",
            ]
        )

    return system_user


def _get_deleted_volunteer_profile():
    volunteer_user, created = User.objects.get_or_create(
        email=SYSTEM_VOLUNTEER_EMAIL,
        defaults={
            "full_name": "Deleted Volunteer",
            "phone_number": "",
            "role": UserRole.VOLUNTEER,
            "is_active": False,
            "is_staff": False,
            "is_superuser": False,
        },
    )

    if created:
        volunteer_user.set_unusable_password()
        volunteer_user.save(
            update_fields=[
                "password",
                "updated_at",
            ]
        )

    profile, _created = VolunteerProfile.objects.get_or_create(
        user=volunteer_user,
        defaults={
            "approval_status": VolunteerApprovalStatus.REJECTED,
            "review_note": (
                "System placeholder used to preserve historical "
                "assignments after test accounts are purged."
            ),
            "service_areas": "",
            "has_vehicle": False,
            "vehicle_description": "",
            "capacity_kg": 0,
            "availability_notes": "",
            "active": False,
            "safety_acknowledged": False,
        },
    )

    return profile


@transaction.atomic
def purge_test_account(
    *,
    target_user,
    actor,
):
    target_id = str(target_user.id)
    target_email = target_user.email
    target_name = target_user.full_name
    target_role = target_user.role

    owned_requests = CollectionRequest.objects.filter(
        requester=target_user,
    )

    owned_request_ids = list(
        owned_requests.values_list(
            "id",
            flat=True,
        )
    )

    handover_links = HandoverRequest.objects.filter(
        request_id__in=owned_request_ids,
    ).count()

    route_links = RouteStop.objects.filter(
        request_id__in=owned_request_ids,
    ).count()

    if handover_links or route_links:
        blockers = []

        if handover_links:
            blockers.append(
                f"{handover_links} recycler handover link(s)"
            )

        if route_links:
            blockers.append(
                f"{route_links} route-plan stop(s)"
            )

        raise ValueError(
            "This account cannot be permanently purged because its "
            "collection requests are part of verified operational "
            f"history: {', '.join(blockers)}. Disable the account "
            "instead."
        )

    system_actor = _get_system_actor()
    deleted_volunteer = _get_deleted_volunteer_profile()

    volunteer_profile = VolunteerProfile.objects.filter(
        user=target_user,
    ).first()

    preserved_assignments = 0

    if volunteer_profile is not None:
        preserved_assignments = PickupAssignment.objects.filter(
            volunteer=volunteer_profile,
        ).exclude(
            request_id__in=owned_request_ids,
        ).update(
            volunteer=deleted_volunteer,
        )

    transferred_assignments = PickupAssignment.objects.filter(
        assigned_by=target_user,
    ).exclude(
        request_id__in=owned_request_ids,
    ).update(
        assigned_by=system_actor,
    )

    transferred_transitions = StatusTransition.objects.filter(
        actor=target_user,
    ).exclude(
        request_id__in=owned_request_ids,
    ).update(
        actor=system_actor,
    )

    transferred_handovers = HandoverBatch.objects.filter(
        recorded_by=target_user,
    ).update(
        recorded_by=system_actor,
    )

    transferred_routes = RoutePlan.objects.filter(
        created_by=target_user,
    ).update(
        created_by=system_actor,
    )

    transferred_organizations = Organization.objects.filter(
        created_by=target_user,
    ).update(
        created_by=system_actor,
    )

    deleted_request_count = owned_requests.count()

    owned_requests.delete()

    if volunteer_profile is not None:
        volunteer_profile.delete()

    target_user.delete()

    record_event(
        actor=actor,
        event_type="user.test_account_purged",
        summary=(
            f"Permanently purged test account {target_email}"
        ),
        object_type="User",
        object_id=target_id,
        metadata={
            "deleted_user_email": target_email,
            "deleted_user_name": target_name,
            "deleted_user_role": target_role,
            "deleted_request_count": deleted_request_count,
            "preserved_assignment_count": preserved_assignments,
            "transferred_assignment_creator_count": (
                transferred_assignments
            ),
            "transferred_status_transition_count": (
                transferred_transitions
            ),
            "transferred_handover_count": transferred_handovers,
            "transferred_route_count": transferred_routes,
            "transferred_organization_count": (
                transferred_organizations
            ),
        },
    )

    return {
        "deleted_user_id": target_id,
        "deleted_user_email": target_email,
        "deleted_request_count": deleted_request_count,
        "preserved_assignment_count": preserved_assignments,
    }