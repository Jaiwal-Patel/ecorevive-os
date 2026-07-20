import random
import string
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from common.models import UUIDTimeStampedModel
from organizations.models import Organization


class RequestStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under review"
    APPROVED = "approved", "Approved"
    SCHEDULED = "scheduled", "Scheduled"
    ASSIGNED = "assigned", "Assigned"
    COLLECTED = "collected", "Collected"
    HANDED_TO_RECYCLER = (
        "handed_to_recycler",
        "Handed to recycler",
    )
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


ALLOWED_TRANSITIONS = {
    RequestStatus.DRAFT: {
        RequestStatus.SUBMITTED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.SUBMITTED: {
        RequestStatus.UNDER_REVIEW,
        RequestStatus.CANCELLED,
    },
    RequestStatus.UNDER_REVIEW: {
        RequestStatus.APPROVED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.APPROVED: {
        RequestStatus.SCHEDULED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.SCHEDULED: {
        RequestStatus.ASSIGNED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.ASSIGNED: {
        RequestStatus.COLLECTED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.COLLECTED: {
        RequestStatus.HANDED_TO_RECYCLER,
    },
    RequestStatus.HANDED_TO_RECYCLER: {
        RequestStatus.COMPLETED,
    },
    RequestStatus.COMPLETED: set(),
    RequestStatus.CANCELLED: set(),
}


class ItemCategory(UUIDTimeStampedModel):
    name = models.CharField(
        max_length=120,
        unique=True,
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
    )
    description = models.TextField(
        blank=True,
    )
    active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "item categories"


class CollectionRequest(UUIDTimeStampedModel):
    public_reference = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="collection_requests",
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="collection_requests",
    )
    status = models.CharField(
        max_length=30,
        choices=RequestStatus.choices,
        default=RequestStatus.DRAFT,
        db_index=True,
    )
    address_line = models.TextField()
    area = models.CharField(
        max_length=120,
    )
    city = models.CharField(
        max_length=80,
        default="Dubai",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    preferred_date = models.DateField(
        null=True,
        blank=True,
    )
    preferred_time_window = models.CharField(
        max_length=120,
        blank=True,
    )
    access_instructions = models.TextField(
        blank=True,
    )
    resident_notes = models.TextField(
        blank=True,
    )
    estimated_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0"),
            )
        ],
    )
    actual_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0"),
            )
        ],
    )
    consent_to_contact = models.BooleanField(
        default=False,
    )
    consent_to_data_processing = models.BooleanField(
        default=False,
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=[
                    "status",
                    "preferred_date",
                ],
            )
        ]

    def save(self, *args, **kwargs):
        if not self.public_reference:
            suffix = "".join(
                random.choices(
                    string.ascii_uppercase
                    + string.digits,
                    k=6,
                )
            )
            self.public_reference = (
                f"ER-{suffix}"
            )

        super().save(
            *args,
            **kwargs,
        )


class CollectionItem(UUIDTimeStampedModel):
    request = models.ForeignKey(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        max_length=255,
    )
    quantity = models.PositiveIntegerField(
        default=1,
    )
    condition = models.CharField(
        max_length=120,
        blank=True,
    )
    approximate_weight_kg = (
        models.DecimalField(
            max_digits=8,
            decimal_places=2,
            null=True,
            blank=True,
            validators=[
                MinValueValidator(
                    Decimal("0"),
                )
            ],
        )
    )
    photo = models.ImageField(
        upload_to=(
            "collection-items/%Y/%m/"
        ),
        null=True,
        blank=True,
    )


class VolunteerApprovalStatus(
    models.TextChoices,
):
    PENDING = (
        "pending",
        "Pending review",
    )
    APPROVED = (
        "approved",
        "Approved",
    )
    REJECTED = (
        "rejected",
        "Rejected",
    )


class VolunteerProfile(
    UUIDTimeStampedModel,
):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    approval_status = models.CharField(
        max_length=20,
        choices=(
            VolunteerApprovalStatus.choices
        ),
        default=(
            VolunteerApprovalStatus.PENDING
        ),
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name=(
            "volunteer_profiles_reviewed"
        ),
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    review_note = models.TextField(
        blank=True,
    )
    service_areas = models.CharField(
        max_length=255,
        blank=True,
    )
    has_vehicle = models.BooleanField(
        default=False,
    )
    vehicle_description = (
        models.CharField(
            max_length=160,
            blank=True,
        )
    )
    capacity_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(
                Decimal("0"),
            )
        ],
    )
    availability_notes = (
        models.TextField(
            blank=True,
        )
    )
    active = models.BooleanField(
        default=False,
    )
    safety_acknowledged = (
        models.BooleanField(
            default=False,
        )
    )

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_approved(self):
        return (
            self.approval_status
            == VolunteerApprovalStatus.APPROVED
        )

    @property
    def can_receive_assignments(self):
        return (
            self.is_approved
            and self.active
        )


class AssignmentStatus(
    models.TextChoices,
):
    PROPOSED = (
        "proposed",
        "Awaiting volunteer response",
    )
    ACCEPTED = (
        "accepted",
        "Accepted",
    )
    DECLINED = (
        "declined",
        "Declined",
    )
    COMPLETED = (
        "completed",
        "Completed",
    )
    CANCELLED = (
        "cancelled",
        "Cancelled",
    )


class PickupAssignment(
    UUIDTimeStampedModel,
):
    request = models.OneToOneField(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="assignment",
    )
    volunteer = models.ForeignKey(
        VolunteerProfile,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name=(
            "pickup_assignments_created"
        ),
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.PROPOSED,
        db_index=True,
    )
    instructions = models.TextField(
        blank=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    declined_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    decline_reason = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(
                fields=[
                    "volunteer",
                    "status",
                    "scheduled_for",
                ],
            ),
        ]

    @property
    def is_awaiting_response(self):
        return (
            self.status
            == AssignmentStatus.PROPOSED
        )

    @property
    def can_be_accepted(self):
        return (
            self.status
            == AssignmentStatus.PROPOSED
            and self.volunteer.can_receive_assignments
        )

    @property
    def can_be_declined(self):
        return (
            self.status
            == AssignmentStatus.PROPOSED
        )

    @property
    def can_be_completed(self):
        return (
            self.status
            == AssignmentStatus.ACCEPTED
        )


class StatusTransition(
    UUIDTimeStampedModel,
):
    request = models.ForeignKey(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(
        max_length=30,
        choices=RequestStatus.choices,
    )
    to_status = models.CharField(
        max_length=30,
        choices=RequestStatus.choices,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    note = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["created_at"]


class HandoverBatch(
    UUIDTimeStampedModel,
):
    reference = models.CharField(
        max_length=60,
        unique=True,
    )
    recycler_name = models.CharField(
        max_length=160,
        default="Enviroserve UAE",
    )
    handover_date = models.DateField()
    receipt_number = models.CharField(
        max_length=120,
        blank=True,
    )
    total_weight_kg = (
        models.DecimalField(
            max_digits=12,
            decimal_places=2,
            validators=[
                MinValueValidator(
                    Decimal("0"),
                )
            ],
        )
    )
    receipt_document = (
        models.FileField(
            upload_to=(
                "handover-receipts/%Y/%m/"
            ),
            null=True,
            blank=True,
        )
    )
    requests = models.ManyToManyField(
        CollectionRequest,
        through="HandoverRequest",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="handover_batches",
    )

    class Meta:
        ordering = ["-handover_date"]


class HandoverRequest(
    UUIDTimeStampedModel,
):
    batch = models.ForeignKey(
        HandoverBatch,
        on_delete=models.CASCADE,
    )
    request = models.OneToOneField(
        CollectionRequest,
        on_delete=models.PROTECT,
    )
    verified_weight_kg = (
        models.DecimalField(
            max_digits=10,
            decimal_places=2,
            validators=[
                MinValueValidator(
                    Decimal("0"),
                )
            ],
        )
    )