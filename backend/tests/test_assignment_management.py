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
        email="assignment-admin@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Assignment Administrator",
        role=UserRole.OPERATIONS_ADMIN,
    )


def create_volunteer_profile(
    *,
    email,
    full_name,
):
    user = User.objects.create_user(
        email=email,
        password="Strong-Test-Pass-123!",
        full_name=full_name,
        role=UserRole.VOLUNTEER,
    )

    return VolunteerProfile.objects.create(
        user=user,
        approval_status=VolunteerApprovalStatus.APPROVED,
        active=True,
        safety_acknowledged=False,
        service_areas="Dubai",
    )


def create_collection_request(
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


def create_assignment(
    *,
    request_obj,
    volunteer,
    assigned_by,
    assignment_status=AssignmentStatus.PROPOSED,
    instructions="Call before arrival.",
):
    return PickupAssignment.objects.create(
        request=request_obj,
        volunteer=volunteer,
        assigned_by=assigned_by,
        scheduled_for=timezone.now(),
        status=assignment_status,
        instructions=instructions,
    )


@pytest.mark.django_db
def test_admin_proposes_assignment_and_request_remains_scheduled(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="assignment-create-volunteer@example.com",
        full_name="Create Assignment Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.APPROVED,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    response = api_client.post(
        "/api/pickup-assignments/",
        {
            "request": str(
                collection_request.id,
            ),
            "volunteer": str(
                volunteer.id,
            ),
            "scheduled_for": (timezone.now().isoformat()),
            "instructions": ("Collect two laptops."),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assignment = PickupAssignment.objects.get(
        request=collection_request,
    )

    assert assignment.status == AssignmentStatus.PROPOSED
    assert assignment.assigned_by == operations_admin
    assert assignment.volunteer == volunteer

    collection_request.refresh_from_db()

    assert collection_request.status == RequestStatus.SCHEDULED

    event = AuditEvent.objects.get(
        event_type=("pickup.assignment_proposed"),
        object_type="PickupAssignment",
        object_id=str(
            assignment.id,
        ),
    )

    assert event.actor == operations_admin
    assert event.metadata["request_id"] == str(
        collection_request.id,
    )
    assert event.metadata["volunteer_profile_id"] == str(
        volunteer.id,
    )
    assert event.metadata["status"] == AssignmentStatus.PROPOSED


@pytest.mark.django_db
def test_assigned_volunteer_can_accept_assignment(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="accepting-volunteer@example.com",
        full_name="Accepting Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        volunteer.user,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/accept/"),
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.ACCEPTED
    assert assignment.accepted_at is not None
    assert assignment.declined_at is None
    assert assignment.decline_reason == ""

    assert collection_request.status == RequestStatus.ASSIGNED

    event = AuditEvent.objects.get(
        event_type=("pickup.assignment_accepted"),
        object_type="PickupAssignment",
        object_id=str(
            assignment.id,
        ),
    )

    assert event.actor == volunteer.user
    assert event.metadata["decision"] == AssignmentStatus.ACCEPTED


@pytest.mark.django_db
def test_another_volunteer_cannot_accept_assignment(
    api_client,
    operations_admin,
    resident,
):
    assigned_volunteer = create_volunteer_profile(
        email="assigned-volunteer@example.com",
        full_name="Assigned Volunteer",
    )
    another_volunteer = create_volunteer_profile(
        email="other-volunteer@example.com",
        full_name="Other Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=assigned_volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        another_volunteer.user,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/accept/"),
        {},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.PROPOSED
    assert collection_request.status == RequestStatus.SCHEDULED


@pytest.mark.django_db
def test_volunteer_decline_requires_reason(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="decline-reason-volunteer@example.com",
        full_name="Decline Reason Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        volunteer.user,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/decline/"),
        {
            "decline_reason": "",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "decline_reason" in response.data

    assignment.refresh_from_db()

    assert assignment.status == AssignmentStatus.PROPOSED
    assert assignment.declined_at is None


@pytest.mark.django_db
def test_assigned_volunteer_can_decline_assignment(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="declining-volunteer@example.com",
        full_name="Declining Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        volunteer.user,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/decline/"),
        {
            "decline_reason": ("Transport is unavailable."),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.DECLINED
    assert assignment.accepted_at is None
    assert assignment.declined_at is not None
    assert assignment.decline_reason == "Transport is unavailable."

    assert collection_request.status == RequestStatus.SCHEDULED

    event = AuditEvent.objects.get(
        event_type=("pickup.assignment_declined"),
        object_type="PickupAssignment",
        object_id=str(
            assignment.id,
        ),
    )

    assert event.actor == volunteer.user
    assert event.metadata["decision"] == AssignmentStatus.DECLINED
    assert event.metadata["decline_reason"] == "Transport is unavailable."


@pytest.mark.django_db
def test_admin_reassigning_declined_assignment_resets_response(
    api_client,
    operations_admin,
    resident,
):
    original_volunteer = create_volunteer_profile(
        email="original-volunteer@example.com",
        full_name="Original Volunteer",
    )
    replacement_volunteer = create_volunteer_profile(
        email="replacement-volunteer@example.com",
        full_name="Replacement Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=original_volunteer,
        assigned_by=operations_admin,
        assignment_status=(AssignmentStatus.DECLINED),
    )
    assignment.declined_at = timezone.now()
    assignment.decline_reason = "Original volunteer was unavailable."
    assignment.save(
        update_fields=[
            "declined_at",
            "decline_reason",
            "updated_at",
        ],
    )

    new_schedule = timezone.now() + timezone.timedelta(
        days=1,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    response = api_client.patch(
        (f"/api/pickup-assignments/{assignment.id}/"),
        {
            "volunteer": str(
                replacement_volunteer.id,
            ),
            "scheduled_for": (new_schedule.isoformat()),
            "instructions": ("Replacement volunteer proposed."),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    assert assignment.volunteer == replacement_volunteer
    assert assignment.status == AssignmentStatus.PROPOSED
    assert assignment.accepted_at is None
    assert assignment.declined_at is None
    assert assignment.decline_reason == ""
    assert assignment.instructions == "Replacement volunteer proposed."

    event = AuditEvent.objects.filter(
        event_type=("pickup.assignment_updated"),
        object_type="PickupAssignment",
        object_id=str(
            assignment.id,
        ),
    ).latest(
        "created_at",
    )

    assert event.metadata["previous_status"] == AssignmentStatus.DECLINED
    assert event.metadata["status"] == AssignmentStatus.PROPOSED
    assert event.metadata["reset_for_response"] is True


@pytest.mark.django_db
def test_admin_cannot_force_acceptance_through_patch(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="forced-accept-volunteer@example.com",
        full_name="Forced Accept Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    response = api_client.patch(
        (f"/api/pickup-assignments/{assignment.id}/"),
        {
            "status": (AssignmentStatus.ACCEPTED),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.PROPOSED
    assert assignment.accepted_at is None
    assert collection_request.status == RequestStatus.SCHEDULED


@pytest.mark.django_db
def test_proposed_assignment_cannot_be_completed(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="unaccepted-volunteer@example.com",
        full_name="Unaccepted Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.SCHEDULED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/complete/"),
        {
            "note": ("Pickup completed successfully."),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.PROPOSED
    assert collection_request.status == RequestStatus.SCHEDULED


@pytest.mark.django_db
def test_admin_completes_accepted_assignment(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="completed-assignment-volunteer@example.com",
        full_name="Completed Assignment Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.ASSIGNED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
        assignment_status=(AssignmentStatus.ACCEPTED),
    )
    assignment.accepted_at = timezone.now()
    assignment.save(
        update_fields=[
            "accepted_at",
            "updated_at",
        ],
    )

    api_client.force_authenticate(
        operations_admin,
    )

    response = api_client.post(
        (f"/api/pickup-assignments/{assignment.id}/complete/"),
        {
            "note": ("Pickup completed successfully."),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.COMPLETED
    assert collection_request.status == RequestStatus.COLLECTED

    transition = collection_request.status_history.get(
        to_status=RequestStatus.COLLECTED,
    )

    assert transition.actor == operations_admin
    assert transition.from_status == RequestStatus.ASSIGNED
    assert transition.note == "Pickup completed successfully."

    event = AuditEvent.objects.get(
        event_type=("pickup.assignment_completed"),
        object_type="PickupAssignment",
        object_id=str(
            assignment.id,
        ),
    )

    assert event.actor == operations_admin
    assert event.metadata["request_reference"] == collection_request.public_reference
    assert event.metadata["completion_note"] == "Pickup completed successfully."
