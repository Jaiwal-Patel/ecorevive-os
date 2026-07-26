from html import escape

from celery import shared_task
from django.utils import timezone

from operations.models import (
    VolunteerApprovalStatus,
    VolunteerProfile,
)

from .models import (
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
)
from .providers import send_email_message

VOLUNTEER_APPLICATION_RECEIVED = "volunteer_application_received"
VOLUNTEER_APPLICATION_APPROVED = "volunteer_application_approved"
VOLUNTEER_APPLICATION_REJECTED = "volunteer_application_rejected"

VOLUNTEER_EMAIL_EVENTS = {
    VOLUNTEER_APPLICATION_RECEIVED,
    VOLUNTEER_APPLICATION_APPROVED,
    VOLUNTEER_APPLICATION_REJECTED,
}


def _volunteer_email_content(
    *,
    profile: VolunteerProfile,
    event_type: str,
) -> tuple[str, str, str]:
    user = profile.user
    display_name = user.full_name or "EcoRevive volunteer"

    if event_type == VOLUNTEER_APPLICATION_RECEIVED:
        subject = "EcoRevive volunteer application received"
        heading = "Application received"
        message = (
            "We received your EcoRevive volunteer "
            "application. Our operations team will "
            "review it before your account can receive "
            "pickup assignments."
        )
        next_step = "No action is required right now. We will email you after the review."
    elif event_type == VOLUNTEER_APPLICATION_APPROVED:
        subject = "Your EcoRevive volunteer application has been approved"
        heading = "Application approved"
        message = (
            "Your EcoRevive volunteer application "
            "has been approved and your volunteer "
            "profile is now active."
        )
        next_step = (
            "You can sign in to EcoRevive OS. "
            "New pickup assignments will appear "
            "under My assignments."
        )
    elif event_type == VOLUNTEER_APPLICATION_REJECTED:
        subject = "Update on your EcoRevive volunteer application"
        heading = "Application decision"
        message = "Your EcoRevive volunteer application was not approved at this time."
        next_step = (
            "Review the decision note below. You may contact EcoRevive if you need clarification."
        )
    else:
        raise ValueError("Unsupported volunteer email event.")

    review_note = profile.review_note.strip() if profile.review_note else ""

    plain_review_note = ""

    if event_type == VOLUNTEER_APPLICATION_REJECTED:
        plain_review_note = f"\n\nDecision note:\n{review_note}"

    body = (
        f"Hello {display_name},\n\n"
        f"{message}\n\n"
        f"{next_step}"
        f"{plain_review_note}\n\n"
        "Thank you for supporting responsible "
        "recycling in Dubai.\n\n"
        "EcoRevive Dubai"
    )

    safe_name = escape(display_name)
    safe_heading = escape(heading)
    safe_message = escape(message)
    safe_next_step = escape(next_step)
    safe_review_note = escape(review_note)

    review_note_html = ""

    if event_type == VOLUNTEER_APPLICATION_REJECTED:
        review_note_html = f"""
          <div
            style="
              margin:22px 0;
              padding:16px;
              border:1px solid #dfe7e2;
              border-radius:12px;
              background:#f8faf9;
            "
          >
            <div
              style="
                margin-bottom:6px;
                font-size:13px;
                font-weight:bold;
                text-transform:uppercase;
                letter-spacing:.6px;
                color:#60736c;
              "
            >
              Decision note
            </div>
            <div
              style="
                font-size:15px;
                line-height:1.6;
                white-space:pre-wrap;
              "
            >
              {safe_review_note}
            </div>
          </div>
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
                    margin:0 0 18px;
                    font-size:16px;
                    line-height:1.6;
                  "
                >
                  {safe_message}
                </p>

                <p
                  style="
                    margin:0;
                    font-size:15px;
                    line-height:1.6;
                  "
                >
                  {safe_next_step}
                </p>

                {review_note_html}

                <p
                  style="
                    margin:22px 0 0;
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


@shared_task(
    bind=True,
    max_retries=2,
)
def send_volunteer_application_notification(
    self,
    profile_id: str,
    event_type: str,
):
    if event_type not in VOLUNTEER_EMAIL_EVENTS:
        raise ValueError("Unsupported volunteer email event.")

    profile = VolunteerProfile.objects.select_related(
        "user",
        "reviewed_by",
    ).get(
        id=profile_id,
    )
    user = profile.user

    if (
        event_type == VOLUNTEER_APPLICATION_APPROVED
        and profile.approval_status != VolunteerApprovalStatus.APPROVED
    ):
        return {
            "profile_id": str(profile.id),
            "status": "obsolete",
        }

    if (
        event_type == VOLUNTEER_APPLICATION_REJECTED
        and profile.approval_status != VolunteerApprovalStatus.REJECTED
    ):
        return {
            "profile_id": str(profile.id),
            "status": "obsolete",
        }

    subject, body, html_body = _volunteer_email_content(
        profile=profile,
        event_type=event_type,
    )

    task_id = self.request.id or ""
    object_id = str(profile.id)

    metadata = {
        "task_id": task_id,
        "event_type": event_type,
        "volunteer_profile_id": object_id,
        "volunteer_user_id": str(
            profile.user_id,
        ),
        "approval_status": (profile.approval_status),
    }

    notification_log, _created = NotificationLog.objects.get_or_create(
        channel=NotificationChannel.EMAIL,
        template_key=event_type,
        object_type="VolunteerProfile",
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
        notification_log.error = "The registered volunteer account does not have an email address."
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
            "profile_id": object_id,
            "status": notification_log.status,
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
        "profile_id": object_id,
        "event_type": event_type,
        "email_status": notification_log.status,
    }
