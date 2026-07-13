from typing import Any

from .models import AuditEvent


def record_event(
    *,
    event_type: str,
    summary: str,
    actor=None,
    object_type: str = "",
    object_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        actor=actor,
        event_type=event_type,
        summary=summary,
        object_type=object_type,
        object_id=str(object_id),
        metadata=metadata or {},
    )
