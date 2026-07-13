from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    WHATSAPP = "whatsapp", "WhatsApp"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    SKIPPED = "skipped", "Skipped"
    FAILED = "failed", "Failed"


class NotificationLog(UUIDTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notification_logs",
    )
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    destination = models.CharField(max_length=255)
    template_key = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
