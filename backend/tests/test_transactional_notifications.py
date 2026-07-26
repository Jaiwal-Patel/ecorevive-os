from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from accounts.models import User, UserRole
from notifications.assignment_tasks import (
    PICKUP_ASSIGNMENT_ACCEPTED,
    PICKUP_ASSIGNMENT_CANCELLED,
    PICKUP_ASSIGNMENT_DECLINED,
    PICKUP_ASSIGNMENT_PROPOSED,
    PICKUP_ASSIGNMENT_RESCHEDULED,
    send_pickup_assignment_notification,
)
from notifications.dispatch import (
    queue_pickup_assignment_notification,
    queue_volunteer_application_notification,
)
from notifications.models import (
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
)
from notifications.volunteer_tasks import (
    VOLUNTEER_APPLICATION_APPROVED,
    VOLUNTEER_APPLICATION_RECEIVED,
    VOLUNTEER_APPLICATION_REJECTED,
    send_volunteer_application_notification,
)
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
        email="notification-admin@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Notification Administrator",
        role=UserRole.OPERATIONS_ADMIN,
    )


@pytest.fixture
def volunteer_user(db):
    return User.objects.create_user(
        email="notification-volunteer@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Notification Volunteer",
        role=UserRole.VOLUNTEER,
    )


@pytest.fixture
def pending_volunteer(volunteer_user):
    return VolunteerProfile.objects.create(
        user=volunteer_user,
        approval_status=VolunteerApprovalStatus.PENDING,
        active=False,
        service_areas="Dubai",
    )


def create_volunteer_profile(
    *,
    email: str,
    approval_status=VolunteerApprovalStatus.APPROVED,
    active=True,
    review_note="",
):
    user = User.objects.create_user(
        email=email,
        password="Strong-Test-Pass-123!",
        full_name="Transactional Volunteer",
        role=UserRole.VOLUNTEER,
    )

    return VolunteerProfile.objects.create(
        user=user,
        approval_status=approval_status,
        active=active,
        review_note=review_note,
        service_areas="Dubai",
    )


def create_collection_request(
    *,
    requester,
    request_status=RequestStatus.SCHEDULED,
):
    return CollectionRequest.objects.create(
        requester=requester,
        status=request_status,
        address_line="Al Ghozlan",
        area="The Greens",
        city="Dubai",
        access_instructions="Call the resident at the gate.",
        consent_to_contact=True,
        consent_to_data_processing=True,
    )


def create_assignment(
    *,
    requester,
    volunteer,
    assigned_by,
    assignment_status=AssignmentStatus.PROPOSED,
    scheduled_for=None,
    decline_reason="",
):
    request_obj = create_collection_request(
        requester=requester,
    )

    assignment = PickupAssignment.objects.create(
        request=request_obj,
        volunteer=volunteer,
        assigned_by=assigned_by,
        scheduled_for=(scheduled_for or timezone.now() + timedelta(hours=4)),
        status=assignment_status,
        instructions="Collect two laptops.",
        decline_reason=decline_reason,
    )

    return assignment


@pytest.mark.django_db
def test_volunteer_profile_creation_queues_received_email(
    api_client,
    volunteer_user,
    django_capture_on_commit_callbacks,
):
    api_client.force_authenticate(
        volunteer_user,
    )

    with patch(
        "notifications.volunteer_tasks.send_volunteer_application_notification.delay",
    ) as task_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                "/api/volunteer-profiles/",
                {
                    "user": str(volunteer_user.id),
                    "service_areas": "The Greens",
                    "availability_notes": "Available weekends.",
                    "safety_acknowledged": True,
                },
                format="json",
            )

    assert response.status_code == status.HTTP_201_CREATED

    profile = VolunteerProfile.objects.get(
        user=volunteer_user,
    )

    task_delay.assert_called_once_with(
        str(profile.id),
        VOLUNTEER_APPLICATION_RECEIVED,
    )


@pytest.mark.django_db
def test_volunteer_approval_queues_approved_email(
    api_client,
    operations_admin,
    pending_volunteer,
    django_capture_on_commit_callbacks,
):
    api_client.force_authenticate(
        operations_admin,
    )

    with patch(
        "notifications.volunteer_tasks.send_volunteer_application_notification.delay",
    ) as task_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                (f"/api/volunteer-profiles/{pending_volunteer.id}/review/"),
                {
                    "decision": (VolunteerApprovalStatus.APPROVED),
                    "review_note": "Approved after review.",
                },
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    task_delay.assert_called_once_with(
        str(pending_volunteer.id),
        VOLUNTEER_APPLICATION_APPROVED,
    )


@pytest.mark.django_db
def test_volunteer_rejection_queues_rejected_email(
    api_client,
    operations_admin,
    pending_volunteer,
    django_capture_on_commit_callbacks,
):
    api_client.force_authenticate(
        operations_admin,
    )

    with patch(
        "notifications.volunteer_tasks.send_volunteer_application_notification.delay",
    ) as task_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                (f"/api/volunteer-profiles/{pending_volunteer.id}/review/"),
                {
                    "decision": (VolunteerApprovalStatus.REJECTED),
                    "review_note": ("Application information was incomplete."),
                },
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    task_delay.assert_called_once_with(
        str(pending_volunteer.id),
        VOLUNTEER_APPLICATION_REJECTED,
    )


@pytest.mark.django_db
def test_assignment_creation_queues_proposed_email(
    api_client,
    operations_admin,
    resident,
    django_capture_on_commit_callbacks,
):
    volunteer = create_volunteer_profile(
        email="proposed-email@example.com",
    )
    request_obj = create_collection_request(
        requester=resident,
        request_status=RequestStatus.APPROVED,
    )
    scheduled_for = timezone.now() + timedelta(
        days=1,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    with (
        patch(
            "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
        ) as assignment_delay,
        patch(
            "notifications.tasks.send_request_status_notification.delay",
        ),
    ):
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                "/api/pickup-assignments/",
                {
                    "request": str(request_obj.id),
                    "volunteer": str(volunteer.id),
                    "scheduled_for": (scheduled_for.isoformat()),
                    "instructions": "Collect two laptops.",
                },
                format="json",
            )

    assert response.status_code == status.HTTP_201_CREATED

    assignment = PickupAssignment.objects.get(
        request=request_obj,
    )

    assignment_delay.assert_called_once_with(
        str(assignment.id),
        PICKUP_ASSIGNMENT_PROPOSED,
        "",
        "",
        "",
    )


@pytest.mark.django_db
def test_assignment_acceptance_queues_accepted_email(
    api_client,
    operations_admin,
    resident,
    django_capture_on_commit_callbacks,
):
    volunteer = create_volunteer_profile(
        email="accepted-email@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        volunteer.user,
    )

    with (
        patch(
            "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
        ) as assignment_delay,
        patch(
            "notifications.tasks.send_request_status_notification.delay",
        ),
    ):
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                (f"/api/pickup-assignments/{assignment.id}/accept/"),
                {},
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    assignment_delay.assert_called_once_with(
        str(assignment.id),
        PICKUP_ASSIGNMENT_ACCEPTED,
        "",
        "",
        "",
    )


@pytest.mark.django_db
def test_assignment_decline_queues_declined_email(
    api_client,
    operations_admin,
    resident,
    django_capture_on_commit_callbacks,
):
    volunteer = create_volunteer_profile(
        email="declined-email@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        volunteer.user,
    )

    with patch(
        "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
    ) as assignment_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                (f"/api/pickup-assignments/{assignment.id}/decline/"),
                {
                    "decline_reason": ("Transport is unavailable."),
                },
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    assignment_delay.assert_called_once_with(
        str(assignment.id),
        PICKUP_ASSIGNMENT_DECLINED,
        "",
        "",
        "",
    )


@pytest.mark.django_db
def test_assignment_reschedule_queues_rescheduled_email(
    api_client,
    operations_admin,
    resident,
    django_capture_on_commit_callbacks,
):
    volunteer = create_volunteer_profile(
        email="rescheduled-email@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )
    previous_scheduled_for = assignment.scheduled_for
    new_scheduled_for = previous_scheduled_for + timedelta(days=2)

    api_client.force_authenticate(
        operations_admin,
    )

    with patch(
        "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
    ) as assignment_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.patch(
                (f"/api/pickup-assignments/{assignment.id}/"),
                {
                    "scheduled_for": (new_scheduled_for.isoformat()),
                },
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    args = assignment_delay.call_args.args

    assert args[0] == str(assignment.id)
    assert args[1] == PICKUP_ASSIGNMENT_RESCHEDULED
    assert args[2] == previous_scheduled_for.isoformat()
    assert (
        datetime.fromisoformat(
            args[3],
        )
        == assignment.scheduled_for
    )
    assert args[4] == ""


@pytest.mark.django_db
def test_assignment_cancellation_queues_cancelled_email(
    api_client,
    operations_admin,
    resident,
    django_capture_on_commit_callbacks,
):
    volunteer = create_volunteer_profile(
        email="cancelled-email@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    api_client.force_authenticate(
        operations_admin,
    )

    with patch(
        "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
    ) as assignment_delay:
        with django_capture_on_commit_callbacks(
            execute=True,
        ):
            response = api_client.post(
                (f"/api/pickup-assignments/{assignment.id}/cancel/"),
                {
                    "note": "Resident requested cancellation.",
                },
                format="json",
            )

    assert response.status_code == status.HTTP_200_OK

    assignment.refresh_from_db()

    assert assignment.status == AssignmentStatus.CANCELLED

    assignment_delay.assert_called_once_with(
        str(assignment.id),
        PICKUP_ASSIGNMENT_CANCELLED,
        "",
        "",
        "Resident requested cancellation.",
    )


@pytest.mark.django_db
def test_rolled_back_transaction_queues_no_notifications(
    django_capture_on_commit_callbacks,
):
    with (
        patch(
            "notifications.volunteer_tasks.send_volunteer_application_notification.delay",
        ) as volunteer_delay,
        patch(
            "notifications.assignment_tasks.send_pickup_assignment_notification.delay",
        ) as assignment_delay,
    ):
        with django_capture_on_commit_callbacks(
            execute=True,
        ) as callbacks:
            with pytest.raises(
                RuntimeError,
                match="Force rollback",
            ):
                with transaction.atomic():
                    queue_volunteer_application_notification(
                        "volunteer-profile-id",
                        VOLUNTEER_APPLICATION_RECEIVED,
                    )
                    queue_pickup_assignment_notification(
                        "pickup-assignment-id",
                        PICKUP_ASSIGNMENT_PROPOSED,
                    )

                    raise RuntimeError(
                        "Force rollback",
                    )

    assert callbacks == []
    volunteer_delay.assert_not_called()
    assignment_delay.assert_not_called()


@pytest.mark.django_db
def test_rejected_volunteer_email_contains_review_note():
    review_note = "Please provide complete availability information."
    profile = create_volunteer_profile(
        email="rejected-content@example.com",
        approval_status=VolunteerApprovalStatus.REJECTED,
        active=False,
        review_note=review_note,
    )

    with patch(
        "notifications.volunteer_tasks.send_email_message",
        return_value={
            "sent": True,
        },
    ) as send_email:
        result = send_volunteer_application_notification.apply(
            args=[
                str(profile.id),
                VOLUNTEER_APPLICATION_REJECTED,
            ],
            task_id="rejected-volunteer-email",
            throw=True,
        ).get()

    assert result["email_status"] == NotificationStatus.SENT

    email_kwargs = send_email.call_args.kwargs

    assert email_kwargs["to"] == profile.user.email
    assert review_note in email_kwargs["body"]
    assert review_note in email_kwargs["html_body"]

    log = NotificationLog.objects.get(
        template_key=VOLUNTEER_APPLICATION_REJECTED,
        object_id=str(profile.id),
    )

    assert log.channel == NotificationChannel.EMAIL
    assert log.user == profile.user
    assert log.destination == profile.user.email
    assert log.status == NotificationStatus.SENT
    assert log.attempt_count == 1
    assert log.sent_at is not None
    assert log.error == ""


@pytest.mark.django_db
def test_declined_assignment_email_contains_decline_reason(
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="declined-content@example.com",
    )
    decline_reason = "Vehicle maintenance is required."
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
        assignment_status=AssignmentStatus.DECLINED,
        decline_reason=decline_reason,
    )

    with patch(
        "notifications.assignment_tasks.send_email_message",
        return_value={
            "sent": True,
        },
    ) as send_email:
        result = send_pickup_assignment_notification.apply(
            args=[
                str(assignment.id),
                PICKUP_ASSIGNMENT_DECLINED,
            ],
            task_id="declined-assignment-email",
            throw=True,
        ).get()

    assert result["email_status"] == NotificationStatus.SENT

    email_kwargs = send_email.call_args.kwargs

    assert email_kwargs["to"] == volunteer.user.email
    assert decline_reason in email_kwargs["body"]
    assert decline_reason in email_kwargs["html_body"]

    log = NotificationLog.objects.get(
        template_key=PICKUP_ASSIGNMENT_DECLINED,
        object_id=str(assignment.id),
    )

    assert log.user == volunteer.user
    assert log.destination == volunteer.user.email
    assert log.status == NotificationStatus.SENT
    assert log.attempt_count == 1
    assert log.sent_at is not None


@pytest.mark.django_db
def test_outdated_volunteer_decision_task_is_obsolete(
    pending_volunteer,
):
    with patch(
        "notifications.volunteer_tasks.send_email_message",
    ) as send_email:
        result = send_volunteer_application_notification.apply(
            args=[
                str(pending_volunteer.id),
                VOLUNTEER_APPLICATION_APPROVED,
            ],
            task_id="obsolete-volunteer-task",
            throw=True,
        ).get()

    assert result["status"] == "obsolete"
    send_email.assert_not_called()

    assert not NotificationLog.objects.filter(
        object_type="VolunteerProfile",
        object_id=str(pending_volunteer.id),
    ).exists()


@pytest.mark.django_db
def test_outdated_assignment_task_is_obsolete(
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="obsolete-assignment@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
        assignment_status=AssignmentStatus.ACCEPTED,
    )

    with patch(
        "notifications.assignment_tasks.send_email_message",
    ) as send_email:
        result = send_pickup_assignment_notification.apply(
            args=[
                str(assignment.id),
                PICKUP_ASSIGNMENT_PROPOSED,
            ],
            task_id="obsolete-assignment-task",
            throw=True,
        ).get()

    assert result["status"] == "obsolete"
    send_email.assert_not_called()

    assert not NotificationLog.objects.filter(
        object_type="PickupAssignment",
        object_id=str(assignment.id),
    ).exists()


@pytest.mark.django_db
def test_volunteer_email_without_destination_is_skipped(
    pending_volunteer,
):
    User.objects.filter(
        id=pending_volunteer.user_id,
    ).update(
        email="",
    )

    with patch(
        "notifications.volunteer_tasks.send_email_message",
    ) as send_email:
        result = send_volunteer_application_notification.apply(
            args=[
                str(pending_volunteer.id),
                VOLUNTEER_APPLICATION_RECEIVED,
            ],
            task_id="missing-volunteer-email",
            throw=True,
        ).get()

    assert result["status"] == NotificationStatus.SKIPPED
    send_email.assert_not_called()

    log = NotificationLog.objects.get(
        template_key=VOLUNTEER_APPLICATION_RECEIVED,
        object_id=str(pending_volunteer.id),
    )

    assert log.destination == ""
    assert log.status == NotificationStatus.SKIPPED
    assert log.sent_at is None
    assert "does not have an email address" in log.error


@pytest.mark.django_db
def test_assignment_email_without_destination_is_skipped(
    operations_admin,
    resident,
):
    volunteer = create_volunteer_profile(
        email="missing-assignment-email@example.com",
    )
    assignment = create_assignment(
        requester=resident,
        volunteer=volunteer,
        assigned_by=operations_admin,
    )

    User.objects.filter(
        id=volunteer.user_id,
    ).update(
        email="",
    )

    with patch(
        "notifications.assignment_tasks.send_email_message",
    ) as send_email:
        result = send_pickup_assignment_notification.apply(
            args=[
                str(assignment.id),
                PICKUP_ASSIGNMENT_PROPOSED,
            ],
            task_id="missing-assignment-email",
            throw=True,
        ).get()

    assert result["email_status"] == NotificationStatus.SKIPPED
    send_email.assert_not_called()

    log = NotificationLog.objects.get(
        template_key=PICKUP_ASSIGNMENT_PROPOSED,
        object_id=str(assignment.id),
    )

    assert log.destination == ""
    assert log.status == NotificationStatus.SKIPPED
    assert log.sent_at is None
    assert "does not have an email address" in log.error


@pytest.mark.django_db
def test_failed_email_is_recorded_after_final_attempt(
    pending_volunteer,
):
    with patch(
        "notifications.volunteer_tasks.send_email_message",
        side_effect=RuntimeError(
            "SMTP service unavailable",
        ),
    ):
        result = send_volunteer_application_notification.apply(
            args=[
                str(pending_volunteer.id),
                VOLUNTEER_APPLICATION_RECEIVED,
            ],
            task_id="final-volunteer-failure",
            retries=2,
            throw=True,
        ).get()

    assert result["email_status"] == NotificationStatus.FAILED

    log = NotificationLog.objects.get(
        template_key=VOLUNTEER_APPLICATION_RECEIVED,
        object_id=str(pending_volunteer.id),
    )

    assert log.status == NotificationStatus.FAILED
    assert log.attempt_count == 1
    assert log.sent_at is None
    assert "SMTP service unavailable" in log.error


@pytest.mark.django_db
def test_temporary_email_failure_is_left_pending_for_retry(
    pending_volunteer,
):
    with patch(
        "notifications.volunteer_tasks.send_email_message",
        side_effect=RuntimeError(
            "Temporary SMTP failure",
        ),
    ):
        with pytest.raises(Retry):
            send_volunteer_application_notification.apply(
                args=[
                    str(pending_volunteer.id),
                    VOLUNTEER_APPLICATION_RECEIVED,
                ],
                task_id="retry-volunteer-email",
                retries=0,
                throw=True,
            )

    log = NotificationLog.objects.get(
        template_key=VOLUNTEER_APPLICATION_RECEIVED,
        object_id=str(pending_volunteer.id),
    )

    assert log.status == NotificationStatus.PENDING
    assert log.attempt_count == 1
    assert log.sent_at is None
    assert "Temporary SMTP failure" in log.error
