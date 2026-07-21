from html import escape

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from operations.models import CollectionRequest

from .models import (
    NotificationChannel,
    NotificationLog,
    NotificationStatus,
)
from .providers import (
    send_email_message,
    send_whatsapp_template,
)


def _status_label(value: str) -> str:
    return value.replace("_", " ").title()


def _request_status_email_content(
    *,
    request_obj: CollectionRequest,
    previous_status: str,
    new_status: str,
) -> tuple[str, str, str]:
    user = request_obj.requester
    reference = request_obj.public_reference
    previous_label = _status_label(previous_status)
    new_label = _status_label(new_status)

    subject = f"EcoRevive request {reference}: {new_label}"

    body = (
        f"Hello {user.full_name},\n\n"
        f"Your EcoRevive collection request {reference} "
        f"changed from {previous_label} to {new_label}.\n\n"
        "You can sign in to EcoRevive OS to review the "
        "latest request details.\n\n"
        "Thank you for supporting responsible recycling "
        "in Dubai.\n\n"
        "EcoRevive Dubai"
    )

    safe_name = escape(
        user.full_name or "EcoRevive member",
    )
    safe_reference = escape(reference)
    safe_previous = escape(previous_label)
    safe_new = escape(new_label)

    html_body = f"""
<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f4f7f5;">
    <table
      role="presentation"
      width="100%"
      cellspacing="0"
      cellpadding="0"
      style="background:#f4f7f5;padding:24px 12px;"
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
                  Request status updated
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
                  Your EcoRevive collection request
                  <strong>{safe_reference}</strong>
                  has been updated.
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
                  <tr>
                    <td
                      style="
                        padding:12px;
                        border:1px solid #dfe7e2;
                        background:#f8faf9;
                        font-size:14px;
                      "
                    >
                      Previous status
                    </td>
                    <td
                      style="
                        padding:12px;
                        border:1px solid #dfe7e2;
                        font-size:14px;
                      "
                    >
                      {safe_previous}
                    </td>
                  </tr>
                  <tr>
                    <td
                      style="
                        padding:12px;
                        border:1px solid #dfe7e2;
                        background:#f8faf9;
                        font-size:14px;
                      "
                    >
                      New status
                    </td>
                    <td
                      style="
                        padding:12px;
                        border:1px solid #dfe7e2;
                        font-size:14px;
                        font-weight:bold;
                      "
                    >
                      {safe_new}
                    </td>
                  </tr>
                </table>

                <p
                  style="
                    margin:0 0 18px;
                    font-size:15px;
                    line-height:1.6;
                  "
                >
                  Sign in to EcoRevive OS to review the
                  latest request details.
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
                This is an automated transactional message
                sent to the email registered with your
                EcoRevive OS account.
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
def send_request_status_notification(
    self,
    request_id: str,
    previous_status: str,
    new_status: str,
):
    request_obj = CollectionRequest.objects.select_related(
        "requester",
    ).get(
        id=request_id,
    )
    user = request_obj.requester

    subject, body, html_body = _request_status_email_content(
        request_obj=request_obj,
        previous_status=previous_status,
        new_status=new_status,
    )

    task_id = self.request.id or ""
    object_id = str(request_obj.id)
    metadata = {
        "request": request_obj.public_reference,
        "previous_status": previous_status,
        "status": new_status,
        "task_id": task_id,
    }

    email_log, _created = NotificationLog.objects.get_or_create(
        channel=NotificationChannel.EMAIL,
        template_key="request_status_updated",
        object_type="CollectionRequest",
        object_id=object_id,
        metadata__task_id=task_id,
        defaults={
            "user": user,
            "destination": user.email,
            "subject": subject,
            "metadata": metadata,
        },
    )

    email_log.user = user
    email_log.destination = user.email
    email_log.subject = subject
    email_log.metadata = metadata
    email_log.attempt_count += 1
    email_log.last_attempt_at = timezone.now()
    email_log.error = ""

    if not user.email:
        email_log.status = NotificationStatus.SKIPPED
        email_log.error = "The registered account does not have an email address."
        email_log.save(
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
        try:
            send_email_message(
                to=user.email,
                subject=subject,
                body=body,
                html_body=html_body,
            )
        except Exception as exc:
            email_log.error = str(exc)

            if self.request.retries < self.max_retries:
                email_log.status = NotificationStatus.PENDING
                email_log.save(
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

            email_log.status = NotificationStatus.FAILED
            email_log.save(
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
            email_log.status = NotificationStatus.SENT
            email_log.sent_at = timezone.now()
            email_log.save(
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

    if user.phone_number:
        whatsapp_log, _created = NotificationLog.objects.get_or_create(
            channel=NotificationChannel.WHATSAPP,
            template_key=(settings.WHATSAPP_TEMPLATE_STATUS_UPDATED),
            object_type="CollectionRequest",
            object_id=object_id,
            metadata__task_id=task_id,
            defaults={
                "user": user,
                "destination": user.phone_number,
                "metadata": metadata,
            },
        )

        whatsapp_log.user = user
        whatsapp_log.destination = user.phone_number
        whatsapp_log.metadata = metadata
        whatsapp_log.attempt_count += 1
        whatsapp_log.last_attempt_at = timezone.now()
        whatsapp_log.error = ""

        try:
            result = send_whatsapp_template(
                to=user.phone_number,
                template_name=(settings.WHATSAPP_TEMPLATE_STATUS_UPDATED),
                body_parameters=[
                    request_obj.public_reference,
                    new_status.replace(
                        "_",
                        " ",
                    ),
                ],
            )

            if result.get("skipped"):
                whatsapp_log.status = NotificationStatus.SKIPPED
                whatsapp_log.error = result.get(
                    "reason",
                    "",
                )
            else:
                whatsapp_log.status = NotificationStatus.SENT
                whatsapp_log.sent_at = timezone.now()

                messages = result.get(
                    "messages",
                    [],
                )

                if messages:
                    whatsapp_log.provider_message_id = messages[0].get(
                        "id",
                        "",
                    )
        except Exception as exc:
            whatsapp_log.status = NotificationStatus.FAILED
            whatsapp_log.error = str(exc)

        whatsapp_log.save(
            update_fields=[
                "user",
                "destination",
                "metadata",
                "attempt_count",
                "last_attempt_at",
                "sent_at",
                "status",
                "error",
                "provider_message_id",
                "updated_at",
            ],
        )

    return {
        "request_id": object_id,
        "request_reference": (request_obj.public_reference),
        "email_status": email_log.status,
    }
