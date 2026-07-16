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
def test_admin_creating_assignment_records_audit_event(
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
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.post(
        "/api/pickup-assignments/",
        {
            "request": str(collection_request.id),
            "volunteer": str(volunteer.id),
            "scheduled_for": timezone.now().isoformat(),
            "status": AssignmentStatus.PROPOSED,
            "instructions": "Collect two laptops.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED

    assignment = PickupAssignment.objects.get(
        request=collection_request,
    )

    event = AuditEvent.objects.get(
        event_type="pickup.assignment_created",
        object_type="PickupAssignment",
        object_id=str(assignment.id),
    )

    assert event.actor == operations_admin
    assert (
        event.metadata["request_id"]
        == str(collection_request.id)
    )
    assert (
        event.metadata["volunteer_id"]
        == str(volunteer.id)
    )
    assert (
        event.metadata["status"]
        == AssignmentStatus.PROPOSED
    )
    assert (
        event.metadata["instructions"]
        == "Collect two laptops."
    )

    collection_request.refresh_from_db()

    assert (
        collection_request.status
        == RequestStatus.ASSIGNED
    )


@pytest.mark.django_db
def test_admin_can_reassign_pickup_and_change_details(
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
        request_status=RequestStatus.ASSIGNED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=original_volunteer,
        assigned_by=operations_admin,
    )

    new_schedule = timezone.now() + timezone.timedelta(
        days=1,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/pickup-assignments/{assignment.id}/",
        {
            "volunteer": str(replacement_volunteer.id),
            "scheduled_for": new_schedule.isoformat(),
            "status": AssignmentStatus.ACCEPTED,
            "instructions": (
                "Replacement volunteer confirmed by phone."
            ),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    assert assignment.volunteer == replacement_volunteer
    assert assignment.status == AssignmentStatus.ACCEPTED
    assert (
        assignment.instructions
        == "Replacement volunteer confirmed by phone."
    )

    event = AuditEvent.objects.get(
        event_type="pickup.assignment_updated",
        object_type="PickupAssignment",
        object_id=str(assignment.id),
    )

    changes = event.metadata["changes"]

    assert changes["volunteer"]["from_name"] == "Original Volunteer"
    assert (
        changes["volunteer"]["to_name"]
        == "Replacement Volunteer"
    )
    assert (
        changes["status"]["from"]
        == AssignmentStatus.PROPOSED
    )
    assert (
        changes["status"]["to"]
        == AssignmentStatus.ACCEPTED
    )
    assert "scheduled_for" in changes
    assert "instructions" in changes


@pytest.mark.django_db
def test_declined_assignment_keeps_request_assigned_and_editable(
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
        request_status=RequestStatus.ASSIGNED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/pickup-assignments/{assignment.id}/",
        {
            "status": AssignmentStatus.DECLINED,
            "instructions": (
                "Volunteer declined because transport was unavailable."
            ),
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.DECLINED
    assert (
        collection_request.status
        == RequestStatus.ASSIGNED
    )

    second_response = api_client.patch(
        f"/api/pickup-assignments/{assignment.id}/",
        {
            "status": AssignmentStatus.PROPOSED,
            "instructions": "Ready to reassign.",
        },
        format="json",
    )

    assert second_response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    assert assignment.status == AssignmentStatus.PROPOSED
    assert assignment.instructions == "Ready to reassign."


@pytest.mark.django_db
def test_cancelled_assignment_does_not_mark_request_collected(
    api_client,
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="cancelled-assignment-volunteer@example.com",
        full_name="Cancelled Assignment Volunteer",
    )
    collection_request = create_collection_request(
        requester=resident,
        request_status=RequestStatus.ASSIGNED,
    )
    assignment = create_assignment(
        request_obj=collection_request,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/pickup-assignments/{assignment.id}/",
        {
            "status": AssignmentStatus.CANCELLED,
            "instructions": "Resident requested a later pickup date.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.CANCELLED
    assert (
        collection_request.status
        == RequestStatus.ASSIGNED
    )


@pytest.mark.django_db
def test_completed_assignment_marks_request_collected(
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
        assignment_status=AssignmentStatus.ACCEPTED,
    )

    api_client.force_authenticate(operations_admin)

    response = api_client.patch(
        f"/api/pickup-assignments/{assignment.id}/",
        {
            "status": AssignmentStatus.COMPLETED,
            "instructions": "Pickup completed successfully.",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()
    collection_request.refresh_from_db()

    assert assignment.status == AssignmentStatus.COMPLETED
    assert (
        collection_request.status
        == RequestStatus.COLLECTED
    )

    transition = collection_request.status_history.get(
        to_status=RequestStatus.COLLECTED,
    )

    assert transition.actor == operations_admin
    assert (
        transition.from_status
        == RequestStatus.ASSIGNED
    )
    assert "Pickup completed by" in transition.note

    update_event = AuditEvent.objects.get(
        event_type="pickup.assignment_updated",
        object_type="PickupAssignment",
        object_id=str(assignment.id),
    )

    assert (
        update_event.metadata["changes"]["status"]["to"]
        == AssignmentStatus.COMPLETED
    )