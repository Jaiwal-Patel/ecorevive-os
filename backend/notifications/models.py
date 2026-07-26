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
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        db_index=True,
    )
    destination = models.CharField(
        max_length=255,
        db_index=True,
    )
    template_key = models.CharField(
        max_length=120,
        db_index=True,
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
    )
    object_type = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    object_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
    )
    attempt_count = models.PositiveSmallIntegerField(
        default=0,
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
    )
    error = models.TextField(
        blank=True,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "channel",
                    "status",
                    "created_at",
                ],
                name="notif_channel_status_idx",
            ),
            models.Index(
                fields=[
                    "object_type",
                    "object_id",
                ],
                name="notif_object_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.channel}: {self.template_key} "
            f"to {self.destination} ({self.status})"
        )