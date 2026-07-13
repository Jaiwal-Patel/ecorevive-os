from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.services import record_event

from .models import ALLOWED_TRANSITIONS, CollectionRequest, RequestStatus, StatusTransition


@transaction.atomic
def transition_request(*, request_obj: CollectionRequest, to_status: str, actor, note: str = ""):
    current = request_obj.status
    if to_status not in ALLOWED_TRANSITIONS[current]:
        raise ValidationError(f"Invalid transition from {current} to {to_status}.")

    request_obj.status = to_status
    if to_status == RequestStatus.SUBMITTED:
        request_obj.submitted_at = timezone.now()
    if to_status == RequestStatus.COMPLETED:
        request_obj.completed_at = timezone.now()
    request_obj.save(update_fields=["status", "submitted_at", "completed_at", "updated_at"])

    StatusTransition.objects.create(
        request=request_obj,
        from_status=current,
        to_status=to_status,
        actor=actor,
        note=note,
    )
    record_event(
        actor=actor,
        event_type="collection.status_transition",
        summary=f"{request_obj.public_reference}: {current} → {to_status}",
        object_type="CollectionRequest",
        object_id=request_obj.id,
        metadata={"from": current, "to": to_status, "note": note},
    )

    transaction.on_commit(
        lambda: _queue_notification_safely(str(request_obj.id), current, to_status)
    )
    return request_obj


def _queue_notification_safely(request_id, previous_status, new_status):
    try:
        from notifications.tasks import send_request_status_notification
        send_request_status_notification.delay(request_id, previous_status, new_status)
    except Exception:
        return
