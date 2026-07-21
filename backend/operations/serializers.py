from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import UserRole
from audit.services import record_event

from .models import (
    AssignmentStatus,
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
        previous_active = instance.active
        decision = validated_data["decision"]
        review_note = validated_data.get(
            "review_note",
            "",
        )

        instance.approval_status = decision
        instance.reviewed_by = actor
        instance.reviewed_at = timezone.now()
        instance.review_note = review_note
        instance.active = (
            decision == VolunteerApprovalStatus.APPROVED
        )

        instance.save(
            update_fields=[
                "approval_status",
                "reviewed_by",
                "reviewed_at",
                "review_note",
                "active",
                "updated_at",
            ],
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
                "previous_active": previous_active,
                "decision": decision,
                "active": instance.active,
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
    request_status = serializers.CharField(
        source="request.status",
        read_only=True,
    )
    request_area = serializers.CharField(
        source="request.area",
        read_only=True,
    )
    request_city = serializers.CharField(
        source="request.city",
        read_only=True,
    )
    request_address = serializers.CharField(
        source="request.address_line",
        read_only=True,
    )
    request_access_instructions = serializers.CharField(
        source="request.access_instructions",
        read_only=True,
    )
    volunteer_name = serializers.CharField(
        source="volunteer.user.full_name",
        read_only=True,
    )
    volunteer_email = serializers.EmailField(
        source="volunteer.user.email",
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    is_awaiting_response = serializers.BooleanField(
        read_only=True,
    )
    can_be_accepted = serializers.BooleanField(
        read_only=True,
    )
    can_be_declined = serializers.BooleanField(
        read_only=True,
    )
    can_be_completed = serializers.BooleanField(
        read_only=True,
    )

    class Meta:
        model = PickupAssignment
        fields = [
            "id",
            "request",
            "request_reference",
            "request_status",
            "request_area",
            "request_city",
            "request_address",
            "request_access_instructions",
            "volunteer",
            "volunteer_name",
            "volunteer_email",
            "scheduled_for",
            "status",
            "status_label",
            "instructions",
            "assigned_by",
            "accepted_at",
            "declined_at",
            "decline_reason",
            "is_awaiting_response",
            "can_be_accepted",
            "can_be_declined",
            "can_be_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "request_reference",
            "request_status",
            "request_area",
            "request_city",
            "request_address",
            "request_access_instructions",
            "volunteer_name",
            "volunteer_email",
            "status",
            "status_label",
            "assigned_by",
            "accepted_at",
            "declined_at",
            "decline_reason",
            "is_awaiting_response",
            "can_be_accepted",
            "can_be_declined",
            "can_be_completed",
            "created_at",
            "updated_at",
        ]

    def validate_volunteer(self, volunteer):
        if not volunteer.can_receive_assignments:
            raise serializers.ValidationError(
                "This volunteer is not eligible for assignments. "
                "The volunteer must be approved and active."
            )

        return volunteer

    def validate(self, attrs):
        instance = self.instance
        request_obj = attrs.get(
            "request",
            getattr(
                instance,
                "request",
                None,
            ),
        )

        if request_obj is None:
            return attrs

        if instance is None:
            if request_obj.status not in {
                RequestStatus.SCHEDULED,
                RequestStatus.ASSIGNED,
            }:
                raise serializers.ValidationError(
                    {
                        "request": (
                            "Only a scheduled request can be assigned "
                            "to a volunteer."
                        )
                    }
                )

            if PickupAssignment.objects.filter(
                request=request_obj,
            ).exists():
                raise serializers.ValidationError(
                    {
                        "request": (
                            "This collection request already has a "
                            "pickup assignment."
                        )
                    }
                )

        if (
            instance is not None
            and instance.status
            in {
                AssignmentStatus.ACCEPTED,
                AssignmentStatus.COMPLETED,
            }
        ):
            volunteer_changed = (
                "volunteer" in attrs
                and attrs["volunteer"].id
                != instance.volunteer_id
            )

            if volunteer_changed:
                raise serializers.ValidationError(
                    {
                        "volunteer": (
                            "An accepted or completed assignment cannot "
                            "be reassigned. Cancel it first."
                        )
                    }
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        assignment = PickupAssignment.objects.create(
            assigned_by=self.context["request"].user,
            status=AssignmentStatus.PROPOSED,
            **validated_data,
        )

        record_event(
            actor=self.context["request"].user,
            event_type="pickup.assignment_proposed",
            summary=(
                f"Pickup {assignment.request.public_reference} "
                f"was proposed to "
                f"{assignment.volunteer.user.email}"
            ),
            object_type="PickupAssignment",
            object_id=assignment.id,
            metadata={
                "request_id": str(assignment.request_id),
                "request_reference": (
                    assignment.request.public_reference
                ),
                "volunteer_profile_id": str(
                    assignment.volunteer_id
                ),
                "volunteer_user_id": str(
                    assignment.volunteer.user_id
                ),
                "scheduled_for": (
                    assignment.scheduled_for.isoformat()
                ),
                "status": assignment.status,
            },
        )

        return assignment

    @transaction.atomic
    def update(self, instance, validated_data):
        actor = self.context["request"].user
        previous_volunteer_id = instance.volunteer_id
        previous_scheduled_for = instance.scheduled_for
        previous_status = instance.status

        volunteer_changed = (
            "volunteer" in validated_data
            and validated_data["volunteer"].id
            != instance.volunteer_id
        )
        schedule_changed = (
            "scheduled_for" in validated_data
            and validated_data["scheduled_for"]
            != instance.scheduled_for
        )

        reset_for_response = (
            instance.status
            in {
                AssignmentStatus.DECLINED,
                AssignmentStatus.CANCELLED,
            }
            and (
                volunteer_changed
                or schedule_changed
            )
        )

        if reset_for_response:
            validated_data["status"] = AssignmentStatus.PROPOSED
            validated_data["accepted_at"] = None
            validated_data["declined_at"] = None
            validated_data["decline_reason"] = ""

        instance = super().update(
            instance,
            validated_data,
        )

        record_event(
            actor=actor,
            event_type="pickup.assignment_updated",
            summary=(
                f"Pickup assignment for "
                f"{instance.request.public_reference} was updated"
            ),
            object_type="PickupAssignment",
            object_id=instance.id,
            metadata={
                "request_id": str(instance.request_id),
                "request_reference": (
                    instance.request.public_reference
                ),
                "previous_volunteer_id": str(
                    previous_volunteer_id
                ),
                "volunteer_profile_id": str(
                    instance.volunteer_id
                ),
                "previous_scheduled_for": (
                    previous_scheduled_for.isoformat()
                ),
                "scheduled_for": (
                    instance.scheduled_for.isoformat()
                ),
                "previous_status": previous_status,
                "status": instance.status,
                "reset_for_response": reset_for_response,
            },
        )

        return instance


class PickupAssignmentDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            (
                AssignmentStatus.ACCEPTED,
                "Accept",
            ),
            (
                AssignmentStatus.DECLINED,
                "Decline",
            ),
        ],
    )
    decline_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=2000,
    )

    def validate(self, attrs):
        assignment = self.instance
        decision = attrs["decision"]
        decline_reason = attrs.get(
            "decline_reason",
            "",
        ).strip()

        if assignment is None:
            raise serializers.ValidationError(
                "An assignment is required."
            )

        if assignment.status != AssignmentStatus.PROPOSED:
            raise serializers.ValidationError(
                {
                    "decision": (
                        "This assignment is no longer awaiting a "
                        "volunteer response."
                    )
                }
            )

        if (
            decision == AssignmentStatus.ACCEPTED
            and not assignment.volunteer.can_receive_assignments
        ):
            raise serializers.ValidationError(
                {
                    "decision": (
                        "This volunteer is no longer eligible to "
                        "accept assignments."
                    )
                }
            )

        if (
            decision == AssignmentStatus.DECLINED
            and not decline_reason
        ):
            raise serializers.ValidationError(
                {
                    "decline_reason": (
                        "A reason is required when declining an "
                        "assignment."
                    )
                }
            )

        attrs["decline_reason"] = decline_reason

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        actor = self.context["request"].user
        decision = validated_data["decision"]
        decline_reason = validated_data.get(
            "decline_reason",
            "",
        )
        now = timezone.now()

        if decision == AssignmentStatus.ACCEPTED:
            instance.status = AssignmentStatus.ACCEPTED
            instance.accepted_at = now
            instance.declined_at = None
            instance.decline_reason = ""

            event_type = "pickup.assignment_accepted"
            event_summary = (
                f"{actor.full_name or actor.email} accepted pickup "
                f"{instance.request.public_reference}"
            )
        else:
            instance.status = AssignmentStatus.DECLINED
            instance.accepted_at = None
            instance.declined_at = now
            instance.decline_reason = decline_reason

            event_type = "pickup.assignment_declined"
            event_summary = (
                f"{actor.full_name or actor.email} declined pickup "
                f"{instance.request.public_reference}"
            )

        instance.save(
            update_fields=[
                "status",
                "accepted_at",
                "declined_at",
                "decline_reason",
                "updated_at",
            ],
        )

        record_event(
            actor=actor,
            event_type=event_type,
            summary=event_summary,
            object_type="PickupAssignment",
            object_id=instance.id,
            metadata={
                "request_id": str(instance.request_id),
                "request_reference": (
                    instance.request.public_reference
                ),
                "volunteer_profile_id": str(
                    instance.volunteer_id
                ),
                "volunteer_user_id": str(
                    instance.volunteer.user_id
                ),
                "decision": decision,
                "decline_reason": decline_reason,
            },
        )

        return instance

    def create(self, validated_data):
        raise NotImplementedError(
            "Assignment decisions update an existing assignment."
        )


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