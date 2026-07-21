from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "channel",
        "destination",
        "template_key",
        "status",
        "attempt_count",
        "sent_at",
    ]
    list_filter = [
        "channel",
        "status",
        "template_key",
        "created_at",
        "sent_at",
    ]
    search_fields = [
        "destination",
        "subject",
        "template_key",
        "object_type",
        "object_id",
        "provider_message_id",
        "error",
    ]
    ordering = [
        "-created_at",
    ]
    date_hierarchy = "created_at"
    readonly_fields = [field.name for field in NotificationLog._meta.fields]
    fieldsets = [
        (
            "Recipient",
            {
                "fields": [
                    "user",
                    "channel",
                    "destination",
                ],
            },
        ),
        (
            "Notification",
            {
                "fields": [
                    "template_key",
                    "subject",
                    "object_type",
                    "object_id",
                    "metadata",
                ],
            },
        ),
        (
            "Delivery",
            {
                "fields": [
                    "status",
                    "attempt_count",
                    "last_attempt_at",
                    "sent_at",
                    "provider_message_id",
                    "error",
                ],
            },
        ),
        (
            "Record",
            {
                "fields": [
                    "id",
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False
