from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import UserRole
from audit.services import record_event

from .models import (
    CollectionItem,
    CollectionRequest,
    HandoverBatch,
    HandoverRequest,
    ItemCategory,
    PickupAssignment,
    RequestStatus,
    StatusTransition,
    VolunteerApprovalStatus,
    VolunteerProfile,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "active",
        ]


class CollectionItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "category",
            "category_name",
            "description",
            "quantity",
            "condition",
            "approximate_weight_kg",
            "photo",
        ]
        read_only_fields = [
            "id",
            "category_name",
        ]


class StatusTransitionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(
        source="actor.full_name",
        read_only=True,
    )

    class Meta:
        model = StatusTransition
        fields = [
            "id",
            "from_status",
            "to_status",
            "actor_name",
            "note",
            "created_at",
        ]
        read_only_fields = fields


class CollectionRequestSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(
        many=True,
    )
    requester_name = serializers.CharField(
        source="requester.full_name",
        read_only=True,
    )
    requester_email = serializers.EmailField(
        source="requester.email",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    status_history = StatusTransitionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = CollectionRequest
        fields = [
            "id",
            "public_reference",
            "requester_name",
            "requester_email",
            "organization",
            "status",
            "status_label",
            "address_line",
            "area",
            "city",
            "latitude",
            "longitude",
            "preferred_date",
            "preferred_time_window",
            "access_instructions",
            "resident_notes",
            "estimated_weight_kg",
            "actual_weight_kg",
            "consent_to_contact",
            "consent_to_data_processing",
            "submitted_at",
            "completed_at",
            "items",
            "status_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "public_reference",
            "requester_name",
            "requester_email",
            "status",
            "submitted_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        consent = attrs.get(
            "consent_to_data_processing",
            getattr(
                self.instance,
                "consent_to_data_processing",
                False,
            ),
        )

        if not consent:
            raise serializers.ValidationError(
                {
                    "consent_to_data_processing": (
                        "Consent is required to coordinate a collection."
                    )
                }
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")

        request_obj = CollectionRequest.objects.create(
            requester=self.context["request"].user,
            status=RequestStatus.DRAFT,
            **validated_data,
        )

        for item in items_data:
            CollectionItem.objects.create(
                request=request_obj,
                **item,
            )

        return request_obj

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop(
            "items",
            None,
        )

        instance = super().update(
            instance,
            validated_data,
        )

        if (
            items_data is not None
            and instance.status == RequestStatus.DRAFT
        ):
            instance.items.all().delete()

            for item in items_data:
                CollectionItem.objects.create(
                    request=instance,
                    **item,
                )

        return instance


class VolunteerProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )
    user_name = serializers.CharField(
        source="user.full_name",
        read_only=True,
    )
    approval_status_label = serializers.CharField(
        source="get_approval_status_display",
        read_only=True,
    )
    reviewed_by_name = serializers.CharField(
        source="reviewed_by.full_name",
        read_only=True,
        allow_null=True,
    )
    is_approved = serializers.BooleanField(
        read_only=True,
    )
    can_receive_assignments = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = VolunteerProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "approval_status",
            "approval_status_label",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_note",
            "service_areas",
            "has_vehicle",
            "vehicle_description",
            "capacity_kg",
            "availability_notes",
            "active",
            "safety_acknowledged",
            "is_approved",
            "can_receive_assignments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "user_name",
            "approval_status",
            "approval_status_label",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_note",
            "is_approved",
            "can_receive_assignments",
            "created_at",
            "updated_at",
        ]

    def validate_user(self, user):
        if user.role != UserRole.VOLUNTEER:
            raise serializers.ValidationError(
                "Selected user must have the Volunteer role."
            )

        return user

    def validate(self, attrs):
        instance = self.instance

        approval_status = (
            instance.approval_status
            if instance
            else VolunteerApprovalStatus.PENDING
        )

        active = attrs.get(
            "active",
            getattr(
                instance,
                "active",
                False,
            ),
        )

        safety_acknowledged = attrs.get(
            "safety_acknowledged",
            getattr(
                instance,
                "safety_acknowledged",
                False,
            ),
        )

        if (
            active
            and approval_status
            != VolunteerApprovalStatus.APPROVED
        ):
            raise serializers.ValidationError(
                {
                    "active": (
                        "A volunteer cannot be activated until the "
                        "application has been approved."
                    )
                }
            )

        if active and not safety_acknowledged:
            raise serializers.ValidationError(
                {
                    "active": (
                        "A volunteer cannot be activated until the "
                        "safety acknowledgement is complete."
                    )
                }
            )

        return attrs


class VolunteerReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (
                VolunteerApprovalStatus.APPROVED,
                "Approve",
            ),
            (
                VolunteerApprovalStatus.REJECTED,
                "Reject",
            ),
        ]
    )
    review_note = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=2000,
    )

    def validate(self, attrs):
        instance = self.instance
        decision = attrs["decision"]
        review_note = attrs.get(
            "review_note",
            "",
        ).strip()

        if (
            decision == VolunteerApprovalStatus.REJECTED
            and not review_note
        ):
            raise serializers.ValidationError(
                {
                    "review_note": (
                        "A reason is required when rejecting a "
                        "volunteer application."
                    )
                }
            )

        if (
            instance
            and instance.approval_status == decision
        ):
            raise serializers.ValidationError(
                {
                    "decision": (
                        "This volunteer already has the selected "
                        "approval status."
                    )
                }
            )

        attrs["review_note"] = review_note

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        actor = self.context["request"].user
        previous_status = instance.approval_status
        decision = validated_data["decision"]
        review_note = validated_data.get(
            "review_note",
            "",
        )

        instance.approval_status = decision
        instance.reviewed_by = actor
        instance.reviewed_at = timezone.now()
        instance.review_note = review_note

        update_fields = [
            "approval_status",
            "reviewed_by",
            "reviewed_at",
            "review_note",
            "updated_at",
        ]

        if decision == VolunteerApprovalStatus.REJECTED:
            instance.active = False
            update_fields.append("active")

        instance.save(
            update_fields=update_fields,
        )

        record_event(
            actor=actor,
            event_type="volunteer.application_reviewed",
            summary=(
                f"{actor.full_name or actor.email} changed "
                f"{instance.user.email} volunteer application "
                f"from {previous_status} to {decision}"
            ),
            object_type="VolunteerProfile",
            object_id=instance.id,
            metadata={
                "previous_status": previous_status,
                "decision": decision,
                "review_note": review_note,
                "volunteer_user_id": str(instance.user_id),
            },
        )

        return instance

    def create(self, validated_data):
        raise NotImplementedError(
            "Volunteer reviews update an existing volunteer profile."
        )


class PickupAssignmentSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(
        source="request.public_reference",
        read_only=True,
    )
    volunteer_name = serializers.CharField(
        source="volunteer.user.full_name",
        read_only=True,
    )

    class Meta:
        model = PickupAssignment
        fields = [
            "id",
            "request",
            "request_reference",
            "volunteer",
            "volunteer_name",
            "scheduled_for",
            "status",
            "instructions",
            "assigned_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "request_reference",
            "volunteer_name",
            "assigned_by",
            "created_at",
        ]

    def validate_volunteer(self, volunteer):
        if not volunteer.can_receive_assignments:
            raise serializers.ValidationError(
                
                    "This volunteer is not eligible for assignments. "
                    "The volunteer must be approved, active, and have "
                    "completed the safety acknowledgement."
                
            )

        return volunteer


class HandoverRequestSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(
        source="request.public_reference",
        read_only=True,
    )

    class Meta:
        model = HandoverRequest
        fields = [
            "request",
            "request_reference",
            "verified_weight_kg",
        ]


class HandoverBatchSerializer(serializers.ModelSerializer):
    handover_requests = HandoverRequestSerializer(
        source="handoverrequest_set",
        many=True,
        write_only=True,
    )
    included_requests = HandoverRequestSerializer(
        source="handoverrequest_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = HandoverBatch
        fields = [
            "id",
            "reference",
            "recycler_name",
            "handover_date",
            "receipt_number",
            "total_weight_kg",
            "receipt_document",
            "handover_requests",
            "included_requests",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recorded_by",
            "created_at",
            "included_requests",
        ]

    @transaction.atomic
    def create(self, validated_data):
        links = validated_data.pop(
            "handoverrequest_set",
        )

        batch = HandoverBatch.objects.create(
            recorded_by=self.context["request"].user,
            **validated_data,
        )

        for link in links:
            HandoverRequest.objects.create(
                batch=batch,
                **link,
            )

        return batch