from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from accounts.models import UserRole
from audit.services import record_event
from common.permissions import IsOperationalAdmin

from .models import (
    CollectionRequest,
    HandoverBatch,
    ItemCategory,
    PickupAssignment,
    RequestStatus,
    VolunteerProfile,
)
from .serializers import (
    CollectionRequestSerializer,
    HandoverBatchSerializer,
    ItemCategorySerializer,
    PickupAssignmentSerializer,
    VolunteerProfileSerializer,
)
from .services import transition_request

ADMIN_ROLES = {
    UserRole.FOUNDER_GUARDIAN,
    UserRole.PRINCIPAL_ADMIN,
    UserRole.OPERATIONS_ADMIN,
}


class ItemCategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ItemCategory.objects.filter(active=True)
    serializer_class = ItemCategorySerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
    pagination_class = None


class CollectionRequestViewSet(viewsets.ModelViewSet):
    queryset = CollectionRequest.objects.all()
    serializer_class = CollectionRequestSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = (
            CollectionRequest.objects.select_related("requester", "organization")
            .prefetch_related("items__category", "status_history__actor")
            .all()
        )
        if user.role in ADMIN_ROLES:
            return queryset
        if user.role == UserRole.VOLUNTEER:
            return queryset.filter(assignment__volunteer__user=user)
        return queryset.filter(requester=user)

    def perform_update(self, serializer):
        instance = serializer.instance
        if self.request.user.role not in ADMIN_ROLES and instance.status != RequestStatus.DRAFT:
            raise ValidationError("Only draft requests can be edited by the requester.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        request_obj = self.get_object()
        if request_obj.requester != request.user and request.user.role not in ADMIN_ROLES:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            transition_request(
                request_obj=request_obj,
                to_status=RequestStatus.SUBMITTED,
                actor=request.user,
                note=request.data.get("note", "Submitted by requester"),
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(self.get_serializer(request_obj).data)

    @action(detail=True, methods=["post"], permission_classes=[IsOperationalAdmin])
    def transition(self, request, pk=None):
        request_obj = self.get_object()
        to_status = request.data.get("to_status")
        if not to_status:
            raise ValidationError({"to_status": "This field is required."})
        try:
            transition_request(
                request_obj=request_obj,
                to_status=to_status,
                actor=request.user,
                note=request.data.get("note", ""),
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(self.get_serializer(request_obj).data)


class VolunteerProfileViewSet(viewsets.ModelViewSet):
    queryset = VolunteerProfile.objects.all()
    serializer_class = VolunteerProfileSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if self.request.user.role in ADMIN_ROLES:
            return VolunteerProfile.objects.select_related("user").all()
        return VolunteerProfile.objects.select_related("user").filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role in ADMIN_ROLES:
            serializer.save()
        else:
            serializer.save(user=self.request.user)


class PickupAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = PickupAssignmentSerializer
    permission_classes = [IsOperationalAdmin]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return PickupAssignment.objects.select_related(
            "request", "volunteer__user", "assigned_by"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        request_obj = serializer.validated_data["request"]
        assignment = serializer.save(assigned_by=self.request.user)
        if request_obj.status == RequestStatus.APPROVED:
            transition_request(
                request_obj=request_obj,
                to_status=RequestStatus.SCHEDULED,
                actor=self.request.user,
                note=f"Pickup scheduled for {assignment.scheduled_for.isoformat()}",
            )
        if request_obj.status == RequestStatus.SCHEDULED:
            transition_request(
                request_obj=request_obj,
                to_status=RequestStatus.ASSIGNED,
                actor=self.request.user,
                note=f"Assigned to {assignment.volunteer.user.full_name}",
            )


class HandoverBatchViewSet(viewsets.ModelViewSet):
    queryset = HandoverBatch.objects.prefetch_related(
        "handoverrequest_set__request"
    ).select_related("recorded_by")
    serializer_class = HandoverBatchSerializer
    permission_classes = [IsOperationalAdmin]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @transaction.atomic
    def perform_create(self, serializer):
        batch = serializer.save()
        for link in batch.handoverrequest_set.select_related("request"):
            request_obj = link.request
            request_obj.actual_weight_kg = link.verified_weight_kg
            request_obj.save(update_fields=["actual_weight_kg", "updated_at"])
            if request_obj.status == RequestStatus.COLLECTED:
                transition_request(
                    request_obj=request_obj,
                    to_status=RequestStatus.HANDED_TO_RECYCLER,
                    actor=self.request.user,
                    note=f"Included in handover batch {batch.reference}",
                )
        record_event(
            actor=self.request.user,
            event_type="handover.batch_created",
            summary=f"Recorded handover batch {batch.reference}",
            object_type="HandoverBatch",
            object_id=batch.id,
            metadata={"total_weight_kg": str(batch.total_weight_kg)},
        )
