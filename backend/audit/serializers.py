from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id", "actor_email", "event_type", "object_type", "object_id",
            "summary", "metadata", "created_at",
        ]
        read_only_fields = fields
