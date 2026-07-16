import pytest
from django.utils import timezone
from rest_framework import status

from accounts.models import User, UserRole
from audit.models import AuditEvent
from operations.models import (
    AssignmentStatus,
    CollectionRequest,
    PickupAssignment,
    RequestStatus,
    VolunteerApprovalStatus,
    VolunteerProfile,
)


@pytest.fixture
def operations_admin(db):
    return User.objects.create_user(
        email="operations-admin@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Operations Administrator",
        role=UserRole.OPERATIONS_ADMIN,
    )


@pytest.fixture
def volunteer_user(db):
    return User.objects.create_user(
        email="volunteer-applicant@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Volunteer Applicant",
        role=UserRole.VOLUNTEER,
    )


@pytest.fixture
def pending_volunteer(volunteer_user):
    return VolunteerProfile.objects.create(
        user=volunteer_user,
        approval_status=VolunteerApprovalStatus.PENDING,
        active=False,
        safety_acknowledged=False,
    )


def response_items(response):
    data = response.data

    if isinstance(data, dict) and "results" in data:
        return data["results"]

    return data


def create_volunteer_profile(
    *,
    email,
    approval_status,
    active=False,
    safety_acknowledged=False,
):
    user = User.objects.create_user(
        email=email,
        password="Strong-Test-Pass-123!",
        full_name="Test Volunteer",
        role=UserRole.VOLUNTEER,
    )

    return VolunteerProfile.objects.create(
        user=user,
        approval_status=approval_status,
        active=active,
        safety_acknowledged=safety_acknowledged,
    )


def create_approved_request(*, requester):
    return CollectionRequest.objects.create(
        requester=requester,
        status=RequestStatus.APPROVED,
        address_line="Al Ghozlan, The Greens",
        area="The Greens",
        city="Dubai",
        consent_to_contact=True,
        consent_to_data_processing=True,
    )


@pytest.mark.django_db
def test_admin_can_list_pending_volunteer_applications(
    api_client,
    operations_admin,
    pending_volunteer,
):
    approved_profile = create_volunteer_profile(
        email="approved-list@example.com",
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.get(
        "/api/volunteer-profiles/pending/",
    )

    assert response.status_code == status.HTTP_200_OK

    profile_ids = {
        item["id"]
        for item in response_items(response)
    }

    assert str(pending_volunteer.id) in profile_ids
    assert str(approved_profile.id) not in profile_ids


@pytest.mark.django_db
def test_admin_can_filter_profiles_by_approval_status(
    api_client,
    operations_admin,
    pending_volunteer,
):
    approved_profile = create_volunteer_profile(
        email="approved-filter@example.com",
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.get(
        "/api/volunteer-profiles/",
        {
            "approval_status": VolunteerApprovalStatus.APPROVED,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    profile_ids = {
        item["id"]
        for item in response_items(response)
    }

    assert str(approved_profile.id) in profile_ids
    assert str(pending_volunteer.id) not in profile_ids


@pytest.mark.django_db
def test_invalid_approval_status_filter_is_rejected(
    api_client,
    operations_admin,
):
    api_client.force_authenticate(operations_admin)

    response = api_client.get(
        "/api/volunteer-profiles/",
        {
            "approval_status": "not-a-real-status",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "approval_status" in response.data


@pytest.mark.django_db
def test_resident_cannot_list_pending_volunteer_applications(
    api_client,
    resident,
    pending_volunteer,
):
    api_client.force_authenticate(resident)

    response = api_client.get(
        "/api/volunteer-profiles/pending/",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_volunteer_cannot_list_all_pending_applications(
    api_client,
    volunteer_user,
    pending_volunteer,
):
    api_client.force_authenticate(volunteer_user)

    response = api_client.get(
        "/api/volunteer-profiles/pending/",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_approve_and_activate_pending_volunteer(
    api_client,
    operations_admin,
    pending_volunteer,
):
    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        (
            f"/api/volunteer-profiles/"
            f"{pending_volunteer.id}/review/"
        ),
        {
            "decision": VolunteerApprovalStatus.APPROVED,
            "review_note": "Identity and application reviewed.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    pending_volunteer.refresh_from_db()

    assert (
        pending_volunteer.approval_status
        == VolunteerApprovalStatus.APPROVED
    )
    assert pending_volunteer.reviewed_by == operations_admin
    assert pending_volunteer.reviewed_at is not None
    assert (
        pending_volunteer.review_note
        == "Identity and application reviewed."
    )
    assert pending_volunteer.active is True
    assert pending_volunteer.safety_acknowledged is False
    assert pending_volunteer.can_receive_assignments is True


@pytest.mark.django_db
def test_approval_creates_audit_event(
    api_client,
    operations_admin,
    pending_volunteer,
):
    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        (
            f"/api/volunteer-profiles/"
            f"{pending_volunteer.id}/review/"
        ),
        {
            "decision": VolunteerApprovalStatus.APPROVED,
            "review_note": "Approved after review.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    event = AuditEvent.objects.get(
        event_type="volunteer.application_reviewed",
        object_type="VolunteerProfile",
        object_id=str(pending_volunteer.id),
    )

    assert event.actor == operations_admin
    assert (
        event.metadata["previous_status"]
        == VolunteerApprovalStatus.PENDING
    )
    assert event.metadata["previous_active"] is False
    assert (
        event.metadata["decision"]
        == VolunteerApprovalStatus.APPROVED
    )
    assert event.metadata["active"] is True
    assert (
        event.metadata["review_note"]
        == "Approved after review."
    )


@pytest.mark.django_db
def test_rejection_requires_a_reason(
    api_client,
    operations_admin,
    pending_volunteer,
):
    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        (
            f"/api/volunteer-profiles/"
            f"{pending_volunteer.id}/review/"
        ),
        {
            "decision": VolunteerApprovalStatus.REJECTED,
            "review_note": "",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "review_note" in response.data

    pending_volunteer.refresh_from_db()

    assert (
        pending_volunteer.approval_status
        == VolunteerApprovalStatus.PENDING
    )
    assert pending_volunteer.reviewed_by is None
    assert pending_volunteer.reviewed_at is None
    assert pending_volunteer.active is False


@pytest.mark.django_db
def test_admin_can_reject_volunteer_and_deactivate_profile(
    api_client,
    operations_admin,
):
    profile = create_volunteer_profile(
        email="volunteer-to-reject@example.com",
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
        safety_acknowledged=True,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        f"/api/volunteer-profiles/{profile.id}/review/",
        {
            "decision": VolunteerApprovalStatus.REJECTED,
            "review_note": "Application no longer meets requirements.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    profile.refresh_from_db()

    assert (
        profile.approval_status
        == VolunteerApprovalStatus.REJECTED
    )
    assert profile.active is False
    assert profile.reviewed_by == operations_admin
    assert profile.reviewed_at is not None
    assert (
        profile.review_note
        == "Application no longer meets requirements."
    )
    assert profile.can_receive_assignments is False


@pytest.mark.django_db
def test_repeating_same_review_decision_is_rejected(
    api_client,
    operations_admin,
):
    profile = create_volunteer_profile(
        email="already-approved@example.com",
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        f"/api/volunteer-profiles/{profile.id}/review/",
        {
            "decision": VolunteerApprovalStatus.APPROVED,
            "review_note": "Approve again.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "decision" in response.data


@pytest.mark.django_db
def test_resident_cannot_review_volunteer_application(
    api_client,
    resident,
    pending_volunteer,
):
    api_client.force_authenticate(resident)

    response = api_client.post(
        (
            f"/api/volunteer-profiles/"
            f"{pending_volunteer.id}/review/"
        ),
        {
            "decision": VolunteerApprovalStatus.APPROVED,
            "review_note": "Unauthorized approval attempt.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    pending_volunteer.refresh_from_db()

    assert (
        pending_volunteer.approval_status
        == VolunteerApprovalStatus.PENDING
    )
    assert pending_volunteer.active is False


@pytest.mark.django_db
def test_pending_volunteer_cannot_be_activated(
    api_client,
    operations_admin,
    pending_volunteer,
):
    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/volunteer-profiles/{pending_volunteer.id}/",
        {
            "active": True,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "active" in response.data

    pending_volunteer.refresh_from_db()

    assert pending_volunteer.active is False


@pytest.mark.django_db
def test_rejected_volunteer_cannot_be_activated(
    api_client,
    operations_admin,
):
    profile = create_volunteer_profile(
        email="rejected-activation@example.com",
        approval_status=VolunteerApprovalStatus.REJECTED,
        active=False,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/volunteer-profiles/{profile.id}/",
        {
            "active": True,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "active" in response.data

    profile.refresh_from_db()

    assert profile.active is False


@pytest.mark.django_db
def test_admin_can_update_approved_volunteer_operational_details(
    api_client,
    operations_admin,
):
    profile = create_volunteer_profile(
        email="operational-details@example.com",
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
        safety_acknowledged=False,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/volunteer-profiles/{profile.id}/",
        {
            "service_areas": "The Greens, The Views",
            "has_vehicle": True,
            "vehicle_description": "SUV",
            "capacity_kg": "80.00",
            "availability_notes": "Available on weekends.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    profile.refresh_from_db()

    assert profile.service_areas == "The Greens, The Views"
    assert profile.has_vehicle is True
    assert profile.vehicle_description == "SUV"
    assert str(profile.capacity_kg) == "80.00"
    assert profile.availability_notes == "Available on weekends."
    assert profile.safety_acknowledged is False
    assert profile.can_receive_assignments is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "approval_status",
        "active",
    ),
    [
        (
            VolunteerApprovalStatus.PENDING,
            False,
        ),
        (
            VolunteerApprovalStatus.APPROVED,
            False,
        ),
        (
            VolunteerApprovalStatus.REJECTED,
            False,
        ),
        (
            VolunteerApprovalStatus.REJECTED,
            True,
        ),
    ],
)
def test_ineligible_volunteer_cannot_receive_assignment(
    api_client,
    operations_admin,
    resident,
    approval_status,
    active,
):
    profile = create_volunteer_profile(
        email=(
            "ineligible-"
            f"{approval_status}-"
            f"{int(active)}"
            "@example.com"
        ),
        approval_status=approval_status,
        active=active,
        safety_acknowledged=False,
    )
    collection_request = create_approved_request(
        requester=resident,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        "/api/pickup-assignments/",
        {
            "request": str(collection_request.id),
            "volunteer": str(profile.id),
            "scheduled_for": timezone.now().isoformat(),
            "status": AssignmentStatus.PROPOSED,
            "instructions": "Call the resident before arrival.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "volunteer" in response.data
    assert not PickupAssignment.objects.filter(
        request=collection_request,
    ).exists()

    collection_request.refresh_from_db()

    assert (
        collection_request.status
        == RequestStatus.APPROVED
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "safety_acknowledged",
    [
        False,
        True,
    ],
)
def test_approved_active_volunteer_can_receive_assignment(
    api_client,
    operations_admin,
    resident,
    safety_acknowledged,
):
    profile = create_volunteer_profile(
        email=(
            "eligible-volunteer-"
            f"{int(safety_acknowledged)}"
            "@example.com"
        ),
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
        safety_acknowledged=safety_acknowledged,
    )
    collection_request = create_approved_request(
        requester=resident,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        "/api/pickup-assignments/",
        {
            "request": str(collection_request.id),
            "volunteer": str(profile.id),
            "scheduled_for": timezone.now().isoformat(),
            "status": AssignmentStatus.PROPOSED,
            "instructions": "Call the resident before arrival.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assignment = PickupAssignment.objects.get(
        request=collection_request,
    )

    assert assignment.volunteer == profile
    assert assignment.assigned_by == operations_admin
    assert assignment.status == AssignmentStatus.PROPOSED

    collection_request.refresh_from_db()

    assert (
        collection_request.status
        == RequestStatus.ASSIGNED
    )