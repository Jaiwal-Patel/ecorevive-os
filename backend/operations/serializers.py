from django.db import transaction
from rest_framework import serializers

from accounts.models import UserRole

from .models import (
    CollectionItem,
    CollectionRequest,
    HandoverBatch,
    HandoverRequest,
    ItemCategory,
    PickupAssignment,
    RequestStatus,
    StatusTransition,
    VolunteerProfile,
)


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ["id", "name", "slug", "description", "active"]


class CollectionItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CollectionItem
        fields = [
            "id", "category", "category_name", "description",
            "quantity", "condition", "approximate_weight_kg", "photo",
        ]
        read_only_fields = ["id", "category_name"]


class StatusTransitionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)

    class Meta:
        model = StatusTransition
        fields = ["id", "from_status", "to_status", "actor_name", "note", "created_at"]
        read_only_fields = fields


class CollectionRequestSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(many=True)
    requester_name = serializers.CharField(source="requester.full_name", read_only=True)
    requester_email = serializers.EmailField(source="requester.email", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    status_history = StatusTransitionSerializer(many=True, read_only=True)

    class Meta:
        model = CollectionRequest
        fields = [
            "id", "public_reference", "requester_name", "requester_email",
            "organization", "status", "status_label", "address_line", "area",
            "city", "latitude", "longitude", "preferred_date",
            "preferred_time_window", "access_instructions", "resident_notes",
            "estimated_weight_kg", "actual_weight_kg", "consent_to_contact",
            "consent_to_data_processing", "submitted_at", "completed_at",
            "items", "status_history", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "public_reference", "requester_name", "requester_email",
            "status", "submitted_at", "completed_at", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        consent = attrs.get(
            "consent_to_data_processing",
            getattr(self.instance, "consent_to_data_processing", False),
        )
        if not consent:
            raise serializers.ValidationError({
                "consent_to_data_processing": "Consent is required to coordinate a collection."
            })
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
            CollectionItem.objects.create(request=request_obj, **item)
        return request_obj

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        instance = super().update(instance, validated_data)
        if items_data is not None and instance.status == RequestStatus.DRAFT:
            instance.items.all().delete()
            for item in items_data:
                CollectionItem.objects.create(request=instance, **item)
        return instance


class VolunteerProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = VolunteerProfile
        fields = [
            "id", "user", "user_email", "user_name", "service_areas",
            "has_vehicle", "vehicle_description", "capacity_kg",
            "availability_notes", "active", "safety_acknowledged",
        ]
        read_only_fields = ["id", "user_email", "user_name"]

    def validate_user(self, user):
        if user.role != UserRole.VOLUNTEER:
            raise serializers.ValidationError("Selected user must have the Volunteer role.")
        return user


class PickupAssignmentSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(source="request.public_reference", read_only=True)
    volunteer_name = serializers.CharField(source="volunteer.user.full_name", read_only=True)

    class Meta:
        model = PickupAssignment
        fields = [
            "id", "request", "request_reference", "volunteer", "volunteer_name",
            "scheduled_for", "status", "instructions", "assigned_by", "created_at",
        ]
        read_only_fields = [
            "id", "request_reference", "volunteer_name", "assigned_by", "created_at",
        ]


class HandoverRequestSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(source="request.public_reference", read_only=True)

    class Meta:
        model = HandoverRequest
        fields = ["request", "request_reference", "verified_weight_kg"]


class HandoverBatchSerializer(serializers.ModelSerializer):
    handover_requests = HandoverRequestSerializer(
        source="handoverrequest_set", many=True, write_only=True
    )
    included_requests = HandoverRequestSerializer(
        source="handoverrequest_set", many=True, read_only=True
    )

    class Meta:
        model = HandoverBatch
        fields = [
            "id", "reference", "recycler_name", "handover_date",
            "receipt_number", "total_weight_kg", "receipt_document",
            "handover_requests", "included_requests", "recorded_by", "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "created_at", "included_requests"]

    @transaction.atomic
    def create(self, validated_data):
        links = validated_data.pop("handoverrequest_set")
        batch = HandoverBatch.objects.create(
            recorded_by=self.context["request"].user, **validated_data
        )
        for link in links:
            HandoverRequest.objects.create(batch=batch, **link)
        return batch
