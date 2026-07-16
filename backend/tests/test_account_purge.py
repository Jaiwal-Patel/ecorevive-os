import pytest
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
def principal_admin(db):
    return User.objects.create_user(
        email="principal-purge@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Principal Administrator",
        role=UserRole.PRINCIPAL_ADMIN,
    )


def create_resident(
    *,
    email,
    full_name="Test Resident",
):
    return User.objects.create_user(
        email=email,
        password="Strong-Test-Pass-123!",
        full_name=full_name,
        role=UserRole.RESIDENT,
    )


def create_volunteer(
    *,
    email,
    full_name="Test Volunteer",
):
    user = User.objects.create_user(
        email=email,
        password="Strong-Test-Pass-123!",
        full_name=full_name,
        role=UserRole.VOLUNTEER,
    )

    profile = VolunteerProfile.objects.create(
        user=user,
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
        safety_acknowledged=False,
    )

    return user, profile


def create_request(
    *,
    requester,
    request_status=RequestStatus.APPROVED,
):
    return CollectionRequest.objects.create(
        requester=requester,
        status=request_status,
        address_line="Al Ghozlan, The Greens",
        area="The Greens",
        city="Dubai",
        consent_to_contact=True,
        consent_to_data_processing=True,
    )


@pytest.mark.django_db
def test_admin_can_purge_resident_test_account_and_owned_requests(
    api_client,
    principal_admin,
):
    resident = create_resident(
        email="resident-to-purge@example.com",
    )
    collection_request = create_request(
        requester=resident,
    )

    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        f"/api/users/{resident.id}/purge-test-account/",
        {
            "confirmation_email": resident.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assert not User.objects.filter(
        id=resident.id,
    ).exists()

    assert not CollectionRequest.objects.filter(
        id=collection_request.id,
    ).exists()

    assert response.data["deleted_request_count"] == 1

    event = AuditEvent.objects.get(
        event_type="user.test_account_purged",
        object_type="User",
        object_id=str(resident.id),
    )

    assert event.actor == principal_admin
    assert (
        event.metadata["deleted_user_email"]
        == "resident-to-purge@example.com"
    )


@pytest.mark.django_db
def test_purge_requires_exact_email_confirmation(
    api_client,
    principal_admin,
):
    resident = create_resident(
        email="confirmation-required@example.com",
    )

    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        f"/api/users/{resident.id}/purge-test-account/",
        {
            "confirmation_email": "wrong@example.com",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "confirmation_email" in response.data

    assert User.objects.filter(
        id=resident.id,
    ).exists()


@pytest.mark.django_db
def test_admin_cannot_purge_own_account(
    api_client,
    principal_admin,
):
    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        (
            f"/api/users/{principal_admin.id}/"
            "purge-test-account/"
        ),
        {
            "confirmation_email": principal_admin.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert User.objects.filter(
        id=principal_admin.id,
    ).exists()


@pytest.mark.django_db
def test_admin_cannot_purge_operations_admin(
    api_client,
    principal_admin,
):
    operations_admin = User.objects.create_user(
        email="protected-operations@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Protected Operations Admin",
        role=UserRole.OPERATIONS_ADMIN,
    )

    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        (
            f"/api/users/{operations_admin.id}/"
            "purge-test-account/"
        ),
        {
            "confirmation_email": operations_admin.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert User.objects.filter(
        id=operations_admin.id,
    ).exists()


@pytest.mark.django_db
def test_resident_cannot_purge_another_account(
    api_client,
):
    actor = create_resident(
        email="resident-actor@example.com",
    )
    target = create_resident(
        email="resident-target@example.com",
    )

    api_client.force_authenticate(
        actor,
    )

    response = api_client.post(
        f"/api/users/{target.id}/purge-test-account/",
        {
            "confirmation_email": target.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert User.objects.filter(
        id=target.id,
    ).exists()


@pytest.mark.django_db
def test_purging_volunteer_preserves_unrelated_assignment(
    api_client,
    principal_admin,
):
    volunteer_user, volunteer_profile = create_volunteer(
        email="volunteer-to-purge@example.com",
        full_name="Volunteer To Purge",
    )

    resident = create_resident(
        email="resident-with-assignment@example.com",
    )

    collection_request = create_request(
        requester=resident,
        request_status=RequestStatus.ASSIGNED,
    )

    assignment = PickupAssignment.objects.create(
        request=collection_request,
        volunteer=volunteer_profile,
        assigned_by=principal_admin,
        scheduled_for="2026-07-20T10:00:00Z",
        status=AssignmentStatus.PROPOSED,
        instructions="Preserve this assignment.",
    )

    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        (
            f"/api/users/{volunteer_user.id}/"
            "purge-test-account/"
        ),
        {
            "confirmation_email": volunteer_user.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assert not User.objects.filter(
        id=volunteer_user.id,
    ).exists()

    assignment.refresh_from_db()

    assert (
        assignment.volunteer.user.email
        == "deleted-volunteer@ecorevive.invalid"
    )

    assert PickupAssignment.objects.filter(
        id=assignment.id,
    ).exists()

    assert CollectionRequest.objects.filter(
        id=collection_request.id,
    ).exists()


@pytest.mark.django_db
def test_purging_user_transfers_assignment_creator_reference(
    api_client,
    principal_admin,
):
    test_admin = create_resident(
        email="assignment-creator-to-purge@example.com",
        full_name="Assignment Creator To Purge",
    )

    volunteer_user, volunteer_profile = create_volunteer(
        email="preserved-volunteer@example.com",
        full_name="Preserved Volunteer",
    )

    resident = create_resident(
        email="preserved-resident@example.com",
    )

    collection_request = create_request(
        requester=resident,
        request_status=RequestStatus.ASSIGNED,
    )

    assignment = PickupAssignment.objects.create(
        request=collection_request,
        volunteer=volunteer_profile,
        assigned_by=test_admin,
        scheduled_for="2026-07-20T12:00:00Z",
        status=AssignmentStatus.PROPOSED,
        instructions="Preserve assignment creator history.",
    )

    api_client.force_authenticate(
        principal_admin,
    )

    response = api_client.post(
        f"/api/users/{test_admin.id}/purge-test-account/",
        {
            "confirmation_email": test_admin.email,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    assert (
        assignment.assigned_by.email
        == "system-records@ecorevive.invalid"
    )

    assert User.objects.filter(
        id=volunteer_user.id,
    ).exists()


@pytest.mark.django_db
def test_system_placeholder_accounts_are_hidden_from_user_list(
    api_client,
    principal_admin,
):
    volunteer_user, _profile = create_volunteer(
        email="placeholder-trigger@example.com",
    )

    api_client.force_authenticate(
        principal_admin,
    )

    purge_response = api_client.post(
        (
            f"/api/users/{volunteer_user.id}/"
            "purge-test-account/"
        ),
        {
            "confirmation_email": volunteer_user.email,
        },
        format="json",
    )

    assert purge_response.status_code == status.HTTP_200_OK

    response = api_client.get(
        "/api/users/?page_size=100",
    )

    assert response.status_code == status.HTTP_200_OK

    emails = {
        item["email"]
        for item in response.data["results"]
    }

    assert "system-records@ecorevive.invalid" not in emails
    assert "deleted-volunteer@ecorevive.invalid" not in emails