from functools import partial

from django.db import transaction

VOLUNTEER_APPLICATION_RECEIVED = "volunteer_application_received"
VOLUNTEER_APPLICATION_APPROVED = "volunteer_application_approved"
VOLUNTEER_APPLICATION_REJECTED = "volunteer_application_rejected"

PICKUP_ASSIGNMENT_PROPOSED = "pickup_assignment_proposed"
PICKUP_ASSIGNMENT_ACCEPTED = "pickup_assignment_accepted"
PICKUP_ASSIGNMENT_DECLINED = "pickup_assignment_declined"
PICKUP_ASSIGNMENT_RESCHEDULED = "pickup_assignment_rescheduled"
PICKUP_ASSIGNMENT_CANCELLED = "pickup_assignment_cancelled"


VOLUNTEER_EMAIL_EVENTS = frozenset(
    {
        VOLUNTEER_APPLICATION_APPROVED,
        VOLUNTEER_APPLICATION_REJECTED,
    }
)


def queue_volunteer_application_notification(
    profile_id,
    event_type: str,
) -> None:
    """Queue only approved and rejected volunteer-application emails."""

    if event_type not in VOLUNTEER_EMAIL_EVENTS:
        return

    from .volunteer_tasks import (
        send_volunteer_application_notification,
    )

    transaction.on_commit(
        partial(
            send_volunteer_application_notification.delay,
            str(profile_id),
            event_type,
        )
    )


def queue_pickup_assignment_notification(
    assignment_id,
    event_type: str,
    *,
    initial_assignment: bool = False,
    previous_scheduled_for: str = "",
    expected_scheduled_for: str = "",
    event_note: str = "",
) -> None:
    """Queue email only for the original creation of an assignment."""

    if (
        event_type != PICKUP_ASSIGNMENT_PROPOSED
        or not initial_assignment
    ):
        return

    from .assignment_tasks import (
        send_pickup_assignment_notification,
    )

    transaction.on_commit(
        partial(
            send_pickup_assignment_notification.delay,
            str(assignment_id),
            event_type,
            previous_scheduled_for,
            expected_scheduled_for,
            event_note,
        )
    )
