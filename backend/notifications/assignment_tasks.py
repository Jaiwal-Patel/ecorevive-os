from datetime import datetime
from html import escape

from celery import shared_task
from django.utils import timezone

from operations.models import (
    AssignmentStatus,
    PickupAssignment,
)

from .models import (
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
)
from .providers import send_email_message

PICKUP_ASSIGNMENT_PROPOSED = "pickup_assignment_proposed"
PICKUP_ASSIGNMENT_ACCEPTED = "pickup_assignment_accepted"
PICKUP_ASSIGNMENT_DECLINED = "pickup_assignment_declined"
PICKUP_ASSIGNMENT_RESCHEDULED = "pickup_assignment_rescheduled"
PICKUP_ASSIGNMENT_CANCELLED = "pickup_assignment_cancelled"

PICKUP_ASSIGNMENT_EMAIL_EVENTS = {
    PICKUP_ASSIGNMENT_PROPOSED,
    PICKUP_ASSIGNMENT_ACCEPTED,
    PICKUP_ASSIGNMENT_DECLINED,
    PICKUP_ASSIGNMENT_RESCHEDULED,
    PICKUP_ASSIGNMENT_CANCELLED,
}


def _format_datetime(value) -> str:
    if value is None:
        return "Not specified"

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    return value.strftime(
        "%A, %B %d, %Y at %I:%M %p %Z",
    ).replace(
        " 0",
        " ",
    )


def _format_iso_datetime(value: str) -> str:
    if not value:
        return "Not specified"

    try:
        parsed_value = datetime.fromisoformat(value)
    except ValueError:
        return value

    if timezone.is_naive(parsed_value):
        parsed_value = timezone.make_aware(
            parsed_value,
            timezone.get_current_timezone(),
        )

    return _format_datetime(parsed_value)


def _assignment_email_content(
    *,
    assignment: PickupAssignment,
    event_type: str,
    previous_scheduled_for: str = "",
    event_note: str = "",
) -> tuple[str, str, str]:
    volunteer_user = assignment.volunteer.user
    request_obj = assignment.request

    display_name = volunteer_user.full_name or "EcoRevive volunteer"
    reference = request_obj.public_reference
    scheduled_for = _format_datetime(
        assignment.scheduled_for,
    )
    previous_schedule = _format_iso_datetime(
        previous_scheduled_for,
    )

    location_parts = [
        request_obj.address_line,
        request_obj.area,
        request_obj.city,
    ]
    location = ", ".join(part.strip() for part in location_parts if part and part.strip())

    if not location:
        location = "Location available in EcoRevive OS"

    instructions = assignment.instructions.strip() if assignment.instructions else ""
    access_instructions = (
        request_obj.access_instructions.strip() if request_obj.access_instructions else ""
    )
    decline_reason = assignment.decline_reason.strip() if assignment.decline_reason else ""
    event_note = event_note.strip()

    if event_type == PICKUP_ASSIGNMENT_PROPOSED:
        subject = f"New EcoRevive pickup assignment: {reference}"
        heading = "New pickup assignment"
        message = "A pickup assignment is awaiting your response."
        next_step = "Sign in to EcoRevive OS to review the request and accept or decline it."
    elif event_type == PICKUP_ASSIGNMENT_ACCEPTED:
        subject = f"EcoRevive pickup accepted: {reference}"
        heading = "Assignment accepted"
        message = "Your acceptance of this pickup assignment has been recorded."
        next_step = (
            "Please complete the collection at the "
            "scheduled time and follow the instructions "
            "shown below."
        )
    elif event_type == PICKUP_ASSIGNMENT_DECLINED:
        subject = f"EcoRevive pickup declined: {reference}"
        heading = "Assignment declined"
        message = "Your decision to decline this pickup assignment has been recorded."
        next_step = "The EcoRevive operations team can now arrange another volunteer."
    elif event_type == PICKUP_ASSIGNMENT_RESCHEDULED:
        subject = f"EcoRevive pickup rescheduled: {reference}"
        heading = "Pickup rescheduled"
        message = "The scheduled time for your pickup assignment has changed."
        next_step = (
            "Review the updated schedule below and "
            "sign in to EcoRevive OS for the latest "
            "assignment details."
        )
    elif event_type == PICKUP_ASSIGNMENT_CANCELLED:
        subject = f"EcoRevive pickup cancelled: {reference}"
        heading = "Assignment cancelled"
        message = "This pickup assignment has been cancelled."
        next_step = "No further action is required for this assignment."
    else:
        raise ValueError("Unsupported pickup assignment email event.")

    detail_lines = [
        f"Request reference: {reference}",
        f"Scheduled for: {scheduled_for}",
        f"Location: {location}",
    ]

    if event_type == PICKUP_ASSIGNMENT_RESCHEDULED:
        detail_lines.insert(
            1,
            f"Previous schedule: {previous_schedule}",
        )

    if instructions:
        detail_lines.append(
            f"Assignment instructions: {instructions}",
        )

    if access_instructions:
        detail_lines.append(
            f"Access instructions: {access_instructions}",
        )

    if event_type == PICKUP_ASSIGNMENT_DECLINED and decline_reason:
        detail_lines.append(
            f"Decline reason: {decline_reason}",
        )

    if event_type == PICKUP_ASSIGNMENT_CANCELLED and event_note:
        detail_lines.append(
            f"Cancellation note: {event_note}",
        )

    plain_details = "\n".join(detail_lines)

    body = (
        f"Hello {display_name},\n\n"
        f"{message}\n\n"
        f"{plain_details}\n\n"
        f"{next_step}\n\n"
        "Thank you for supporting responsible "
        "recycling in Dubai.\n\n"
        "EcoRevive Dubai"
    )

    safe_name = escape(display_name)
    safe_heading = escape(heading)
    safe_message = escape(message)
    safe_next_step = escape(next_step)
    safe_reference = escape(reference)
    safe_scheduled_for = escape(scheduled_for)
    safe_previous_schedule = escape(
        previous_schedule,
    )
    safe_location = escape(location)
    safe_instructions = escape(instructions)
    safe_access_instructions = escape(
        access_instructions,
    )
    safe_decline_reason = escape(decline_reason)
    safe_event_note = escape(event_note)

    detail_rows = f"""
      <tr>
        <td style="{_label_cell_style()}">
          Request
        </td>
        <td style="{_value_cell_style()}">
          {safe_reference}
        </td>
      </tr>
    """

    if event_type == PICKUP_ASSIGNMENT_RESCHEDULED:
        detail_rows += f"""
          <tr>
            <td style="{_label_cell_style()}">
              Previous schedule
            </td>
            <td style="{_value_cell_style()}">
              {safe_previous_schedule}
            </td>
          </tr>
        """

    detail_rows += f"""
      <tr>
        <td style="{_label_cell_style()}">
          Scheduled for
        </td>
        <td style="{_value_cell_style()}">
          {safe_scheduled_for}
        </td>
      </tr>
      <tr>
        <td style="{_label_cell_style()}">
          Location
        </td>
        <td style="{_value_cell_style()}">
          {safe_location}
        </td>
      </tr>
    """

    if instructions:
        detail_rows += f"""
          <tr>
            <td style="{_label_cell_style()}">
              Assignment instructions
            </td>
            <td style="{_value_cell_style()}">
              {safe_instructions}
            </td>
          </tr>
        """

    if access_instructions:
        detail_rows += f"""
          <tr>
            <td style="{_label_cell_style()}">
              Access instructions
            </td>
            <td style="{_value_cell_style()}">
              {safe_access_instructions}
            </td>
          </tr>
        """

    if event_type == PICKUP_ASSIGNMENT_DECLINED and decline_reason:
        detail_rows += f"""
          <tr>
            <td style="{_label_cell_style()}">
              Decline reason
            </td>
            <td style="{_value_cell_style()}">
              {safe_decline_reason}
            </td>
          </tr>
        """

    if event_type == PICKUP_ASSIGNMENT_CANCELLED and event_note:
        detail_rows += f"""
          <tr>
            <td style="{_label_cell_style()}">
              Cancellation note
            </td>
            <td style="{_value_cell_style()}">
              {safe_event_note}
            </td>
          </tr>
        """

    html_body = f"""
<!doctype html>
<html lang="en">
  <body
    style="
      margin:0;
      padding:0;
      background:#f4f7f5;
    "
  >
    <table
      role="presentation"
      width="100%"
      cellspacing="0"
      cellpadding="0"
      style="
        background:#f4f7f5;
        padding:24px 12px;
      "
    >
      <tr>
        <td align="center">
          <table
            role="presentation"
            width="100%"
            cellspacing="0"
            cellpadding="0"
            style="
              max-width:600px;
              background:#ffffff;
              border:1px solid #dfe7e2;
              border-radius:16px;
              overflow:hidden;
              font-family:Arial,sans-serif;
              color:#18332a;
            "
          >
            <tr>
              <td
                style="
                  padding:24px 28px;
                  background:#173f35;
                  color:#ffffff;
                "
              >
                <div
                  style="
                    font-size:13px;
                    letter-spacing:1.2px;
                    text-transform:uppercase;
                    opacity:.8;
                  "
                >
                  EcoRevive Dubai
                </div>

                <h1
                  style="
                    margin:8px 0 0;
                    font-size:24px;
                    line-height:1.3;
                  "
                >
                  {safe_heading}
                </h1>
              </td>
            </tr>

            <tr>
              <td style="padding:28px;">
                <p
                  style="
                    margin:0 0 18px;
                    font-size:16px;
                    line-height:1.6;
                  "
                >
                  Hello {safe_name},
                </p>

                <p
                  style="
                    margin:0 0 20px;
                    font-size:16px;
                    line-height:1.6;
                  "
                >
                  {safe_message}
                </p>

                <table
                  role="presentation"
                  width="100%"
                  cellspacing="0"
                  cellpadding="0"
                  style="
                    margin:0 0 22px;
                    border-collapse:collapse;
                  "
                >
                  {detail_rows}
                </table>

                <p
                  style="
                    margin:0 0 18px;
                    font-size:15px;
                    line-height:1.6;
                  "
                >
                  {safe_next_step}
                </p>

                <p
                  style="
                    margin:0;
                    font-size:15px;
                    line-height:1.6;
                  "
                >
                  Thank you for supporting responsible
                  recycling in Dubai.
                </p>
              </td>
            </tr>

            <tr>
              <td
                style="
                  padding:18px 28px;
                  border-top:1px solid #dfe7e2;
                  color:#60736c;
                  font-size:12px;
                  line-height:1.5;
                "
              >
                This automated transactional message
                was sent to the email registered with
                your EcoRevive OS account.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()

    return subject, body, html_body


def _label_cell_style() -> str:
    return (
        "padding:12px;"
        "border:1px solid #dfe7e2;"
        "background:#f8faf9;"
        "font-size:14px;"
        "vertical-align:top;"
        "width:38%;"
    )


def _value_cell_style() -> str:
    return (
        "padding:12px;border:1px solid #dfe7e2;font-size:14px;line-height:1.5;vertical-align:top;"
    )


def _event_is_obsolete(
    *,
    assignment: PickupAssignment,
    event_type: str,
    expected_scheduled_for: str,
) -> bool:
    if event_type == PICKUP_ASSIGNMENT_PROPOSED:
        return assignment.status != AssignmentStatus.PROPOSED

    if event_type == PICKUP_ASSIGNMENT_ACCEPTED:
        return assignment.status not in {
            AssignmentStatus.ACCEPTED,
            AssignmentStatus.COMPLETED,
        }

    if event_type == PICKUP_ASSIGNMENT_DECLINED:
        return assignment.status != AssignmentStatus.DECLINED

    if event_type == PICKUP_ASSIGNMENT_CANCELLED:
        return assignment.status != AssignmentStatus.CANCELLED

    if event_type == PICKUP_ASSIGNMENT_RESCHEDULED and expected_scheduled_for:
        try:
            expected_value = datetime.fromisoformat(
                expected_scheduled_for,
            )
        except ValueError:
            return True

        if timezone.is_naive(expected_value):
            expected_value = timezone.make_aware(
                expected_value,
                timezone.get_current_timezone(),
            )

        actual_value = assignment.scheduled_for

        if timezone.is_naive(actual_value):
            actual_value = timezone.make_aware(
                actual_value,
                timezone.get_current_timezone(),
            )

        return actual_value != expected_value

    return False


@shared_task(
    bind=True,
    max_retries=2,
)
def send_pickup_assignment_notification(
    self,
    assignment_id: str,
    event_type: str,
    previous_scheduled_for: str = "",
    expected_scheduled_for: str = "",
    event_note: str = "",
):
    if event_type not in PICKUP_ASSIGNMENT_EMAIL_EVENTS:
        raise ValueError("Unsupported pickup assignment email event.")

    assignment = PickupAssignment.objects.select_related(
        "request",
        "request__requester",
        "volunteer",
        "volunteer__user",
        "assigned_by",
    ).get(
        id=assignment_id,
    )

    if _event_is_obsolete(
        assignment=assignment,
        event_type=event_type,
        expected_scheduled_for=(expected_scheduled_for),
    ):
        return {
            "assignment_id": str(assignment.id),
            "event_type": event_type,
            "status": "obsolete",
        }

    user = assignment.volunteer.user

    subject, body, html_body = _assignment_email_content(
        assignment=assignment,
        event_type=event_type,
        previous_scheduled_for=(previous_scheduled_for),
        event_note=event_note,
    )

    task_id = self.request.id or ""
    object_id = str(assignment.id)

    metadata = {
        "task_id": task_id,
        "event_type": event_type,
        "pickup_assignment_id": object_id,
        "request_id": str(
            assignment.request_id,
        ),
        "request_reference": (assignment.request.public_reference),
        "volunteer_profile_id": str(
            assignment.volunteer_id,
        ),
        "volunteer_user_id": str(
            assignment.volunteer.user_id,
        ),
        "assignment_status": assignment.status,
        "scheduled_for": (assignment.scheduled_for.isoformat()),
        "previous_scheduled_for": (previous_scheduled_for),
        "event_note": event_note,
    }

    notification_log, _created = NotificationLog.objects.get_or_create(
        channel=NotificationChannel.EMAIL,
        template_key=event_type,
        object_type="PickupAssignment",
        object_id=object_id,
        metadata__task_id=task_id,
        defaults={
            "user": user,
            "destination": user.email,
            "subject": subject,
            "metadata": metadata,
        },
    )

    notification_log.user = user
    notification_log.destination = user.email
    notification_log.subject = subject
    notification_log.metadata = metadata
    notification_log.attempt_count += 1
    notification_log.last_attempt_at = timezone.now()
    notification_log.error = ""

    if not user.email:
        notification_log.status = NotificationStatus.SKIPPED
        notification_log.error = "The assigned volunteer account does not have an email address."
        notification_log.save(
            update_fields=[
                "user",
                "destination",
                "subject",
                "metadata",
                "attempt_count",
                "last_attempt_at",
                "status",
                "error",
                "updated_at",
            ],
        )

        return {
            "assignment_id": object_id,
            "event_type": event_type,
            "email_status": (notification_log.status),
        }

    try:
        send_email_message(
            to=user.email,
            subject=subject,
            body=body,
            html_body=html_body,
        )
    except Exception as exc:
        notification_log.error = str(exc)

        if self.request.retries < self.max_retries:
            notification_log.status = NotificationStatus.PENDING
            notification_log.save(
                update_fields=[
                    "user",
                    "destination",
                    "subject",
                    "metadata",
                    "attempt_count",
                    "last_attempt_at",
                    "status",
                    "error",
                    "updated_at",
                ],
            )

            retry_delay = 60 * (2**self.request.retries)

            raise self.retry(
                exc=exc,
                countdown=retry_delay,
            ) from exc

        notification_log.status = NotificationStatus.FAILED
        notification_log.save(
            update_fields=[
                "user",
                "destination",
                "subject",
                "metadata",
                "attempt_count",
                "last_attempt_at",
                "status",
                "error",
                "updated_at",
            ],
        )
    else:
        notification_log.status = NotificationStatus.SENT
        notification_log.sent_at = timezone.now()
        notification_log.save(
            update_fields=[
                "user",
                "destination",
                "subject",
                "metadata",
                "attempt_count",
                "last_attempt_at",
                "sent_at",
                "status",
                "error",
                "updated_at",
            ],
        )

    return {
        "assignment_id": object_id,
        "event_type": event_type,
        "email_status": notification_log.status,
    }
