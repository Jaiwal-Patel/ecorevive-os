from celery import shared_task
from django.conf import settings

from operations.models import CollectionRequest

from .models import NotificationChannel, NotificationLog, NotificationStatus
from .providers import send_email_message, send_whatsapp_template


@shared_task
def send_request_status_notification(request_id: str, previous_status: str, new_status: str):
    request_obj = CollectionRequest.objects.select_related("requester").get(id=request_id)
    user = request_obj.requester
    subject = (
        f"EcoRevive request {request_obj.public_reference}: "
        f"{new_status.replace('_', ' ').title()}"
    )
    body = (
        f"Hello {user.full_name},\n\n"
        f"Your EcoRevive collection request {request_obj.public_reference} changed "
        f"from {previous_status.replace('_', ' ')} to {new_status.replace('_', ' ')}.\n\n"
        "Thank you for supporting responsible recycling in Dubai."
    )

    email_log = NotificationLog.objects.create(
        user=user,
        channel=NotificationChannel.EMAIL,
        destination=user.email,
        template_key="request_status_updated",
        metadata={"request": request_obj.public_reference, "status": new_status},
    )
    try:
        send_email_message(to=user.email, subject=subject, body=body)
        email_log.status = NotificationStatus.SENT
    except Exception as exc:
        email_log.status = NotificationStatus.FAILED
        email_log.error = str(exc)
    email_log.save(update_fields=["status", "error", "updated_at"])

    if user.phone_number:
        whatsapp_log = NotificationLog.objects.create(
            user=user,
            channel=NotificationChannel.WHATSAPP,
            destination=user.phone_number,
            template_key=settings.WHATSAPP_TEMPLATE_STATUS_UPDATED,
            metadata={"request": request_obj.public_reference, "status": new_status},
        )
        try:
            result = send_whatsapp_template(
                to=user.phone_number,
                template_name=settings.WHATSAPP_TEMPLATE_STATUS_UPDATED,
                body_parameters=[
                    request_obj.public_reference,
                    new_status.replace("_", " "),
                ],
            )
            if result.get("skipped"):
                whatsapp_log.status = NotificationStatus.SKIPPED
                whatsapp_log.error = result.get("reason", "")
            else:
                whatsapp_log.status = NotificationStatus.SENT
                messages = result.get("messages", [])
                if messages:
                    whatsapp_log.provider_message_id = messages[0].get("id", "")
        except Exception as exc:
            whatsapp_log.status = NotificationStatus.FAILED
            whatsapp_log.error = str(exc)
        whatsapp_log.save(
            update_fields=["status", "error", "provider_message_id", "updated_at"]
        )
