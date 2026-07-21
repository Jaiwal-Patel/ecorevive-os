from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.db import transaction
from django.utils import timezone
from rest_framework import (
    mixins,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from accounts.models import UserRole
from audit.services import record_event
from common.permissions import IsOperationalAdmin

from .models import (
    AssignmentStatus,
    CollectionRequest,
    HandoverBatch,
    ItemCategory,
    PickupAssignment,
    RequestStatus,
    VolunteerApprovalStatus,
    VolunteerProfile,
)
from .serializers import (
    CollectionRequestSerializer,
    HandoverBatchSerializer,
    ItemCategorySerializer,
    PickupAssignmentDecisionSerializer,
    PickupAssignmentSerializer,
    VolunteerProfileSerializer,
    VolunteerReviewSerializer,
)
from .services import transition_request

ADMIN_ROLES = {
    UserRole.FOUNDER_GUARDIAN,
    UserRole.PRINCIPAL_ADMIN,
    UserRole.OPERATIONS_ADMIN,
}


class ItemCategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ItemCategory.objects.filter(
        active=True,
    )
    serializer_class = ItemCategorySerializer
    permission_classes = [AllowAny]
    http_method_names = [
        "get",
        "head",
        "options",
    ]
    pagination_class = None


class CollectionRequestViewSet(viewsets.ModelViewSet):
    queryset = CollectionRequest.objects.all()
    serializer_class = CollectionRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            CollectionRequest.objects.select_related(
                "requester",
                "organization",
            )
            .prefetch_related(
                "items__category",
                "status_history__actor",
            )
            .all()
        )

        if user.role in ADMIN_ROLES:
            return queryset

        if user.role == UserRole.VOLUNTEER:
            return queryset.filter(
                assignment__volunteer__user=user,
            )

        return queryset.filter(
            requester=user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance

        if self.request.user.role not in ADMIN_ROLES and instance.status != RequestStatus.DRAFT:
            raise ValidationError("Only draft requests can be edited by the requester.")

        serializer.save()

    @action(
        detail=True,
        methods=["post"],
    )
    def submit(self, request, pk=None):
        request_obj = self.get_object()

        if request_obj.requester != request.user and request.user.role not in ADMIN_ROLES:
            raise PermissionDenied("You cannot submit this collection request.")

        try:
            transition_request(
                request_obj=request_obj,
                to_status=RequestStatus.SUBMITTED,
                actor=request.user,
                note=request.data.get(
                    "note",
                    "Submitted by requester",
                ),
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.messages,
            ) from exc

        request_obj.refresh_from_db()

        return Response(
            self.get_serializer(request_obj).data,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOperationalAdmin],
    )
    def transition(self, request, pk=None):
        request_obj = self.get_object()
        to_status = request.data.get("to_status")

        if not to_status:
            raise ValidationError(
                {
                    "to_status": "This field is required.",
                }
            )

        try:
            transition_request(
                request_obj=request_obj,
                to_status=to_status,
                actor=request.user,
                note=request.data.get(
                    "note",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.messages,
            ) from exc

        request_obj.refresh_from_db()

        return Response(
            self.get_serializer(request_obj).data,
        )


class VolunteerProfileViewSet(viewsets.ModelViewSet):
    queryset = VolunteerProfile.objects.all()
    serializer_class = VolunteerProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = VolunteerProfile.objects.select_related(
            "user",
            "reviewed_by",
        ).exclude(
            user__email=("deleted-volunteer@ecorevive.invalid"),
        )

        if self.request.user.role in ADMIN_ROLES:
            approval_status = self.request.query_params.get(
                "approval_status",
            )

            if approval_status:
                valid_statuses = {choice for choice, _label in VolunteerApprovalStatus.choices}

                if approval_status not in valid_statuses:
                    raise ValidationError(
                        {
                            "approval_status": (
                                "Invalid approval status. Use pending, approved, or rejected."
                            )
                        }
                    )

                queryset = queryset.filter(
                    approval_status=approval_status,
                )

            return queryset

        return queryset.filter(
            user=self.request.user,
        )

    def perform_create(self, serializer):
        if self.request.user.role in ADMIN_ROLES:
            serializer.save()
            return

        if self.request.user.role != UserRole.VOLUNTEER:
            raise PermissionDenied("Only volunteer accounts can create a volunteer profile.")

        if VolunteerProfile.objects.filter(
            user=self.request.user,
        ).exists():
            raise ValidationError(
                {"user": ("A volunteer profile already exists for this account.")}
            )

        serializer.save(
            user=self.request.user,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOperationalAdmin],
        url_path="review",
    )
    def review(self, request, pk=None):
        volunteer_profile = self.get_object()

        serializer = VolunteerReviewSerializer(
            instance=volunteer_profile,
            data=request.data,
            context={
                "request": request,
            },
        )
        serializer.is_valid(
            raise_exception=True,
        )
        reviewed_profile = serializer.save()

        response_serializer = VolunteerProfileSerializer(
            reviewed_profile,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsOperationalAdmin],
        url_path="pending",
    )
    def pending(self, request):
        queryset = self.get_queryset().filter(
            approval_status=VolunteerApprovalStatus.PENDING,
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = VolunteerProfileSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = VolunteerProfileSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(
            serializer.data,
        )


class PickupAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = PickupAssignmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        queryset = PickupAssignment.objects.select_related(
            "request",
            "request__requester",
            "volunteer",
            "volunteer__user",
            "assigned_by",
        )

        user = self.request.user

        if user.role in ADMIN_ROLES:
            return queryset

        if user.role == UserRole.VOLUNTEER:
            return queryset.filter(
                volunteer__user=user,
            )

        return queryset.none()

    def get_serializer_class(self):
        if self.action in {
            "accept",
            "decline",
        }:
            return PickupAssignmentDecisionSerializer

        return PickupAssignmentSerializer

    def _require_admin(self):
        if self.request.user.role not in ADMIN_ROLES:
            raise PermissionDenied("Only an operational administrator may manage assignments.")

    def _require_assignment_owner(
        self,
        assignment,
    ):
        user = self.request.user

        if user.role != UserRole.VOLUNTEER:
            raise PermissionDenied("Only volunteer accounts can respond to assignments.")

        if assignment.volunteer.user_id != user.id:
            raise PermissionDenied("You cannot respond to another volunteer's assignment.")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._require_admin()

        request_id = request.data.get("request")

        if not request_id:
            raise ValidationError(
                {
                    "request": "This field is required.",
                }
            )

        try:
            collection_request = CollectionRequest.objects.select_for_update().get(
                id=request_id,
            )
        except CollectionRequest.DoesNotExist as exc:
            raise ValidationError(
                {"request": ("The selected collection request does not exist.")}
            ) from exc

        if collection_request.status == RequestStatus.APPROVED:
            try:
                transition_request(
                    request_obj=collection_request,
                    to_status=RequestStatus.SCHEDULED,
                    actor=request.user,
                    note=("Request prepared for volunteer assignment."),
                )
            except DjangoValidationError as exc:
                raise ValidationError(
                    exc.messages,
                ) from exc

        return super().create(
            request,
            *args,
            **kwargs,
        )

    def perform_create(self, serializer):
        self._require_admin()

        serializer.save()

    def perform_update(self, serializer):
        self._require_admin()

        serializer.save()

    @action(
        detail=False,
        methods=["get"],
        url_path="mine",
    )
    def mine(self, request):
        if request.user.role != UserRole.VOLUNTEER:
            raise PermissionDenied("Only volunteers have a personal assignment list.")

        queryset = self.get_queryset()

        assignment_status = request.query_params.get(
            "status",
        )

        if assignment_status:
            valid_statuses = {value for value, _label in AssignmentStatus.choices}

            if assignment_status not in valid_statuses:
                raise ValidationError({"status": ("Invalid assignment status.")})

            queryset = queryset.filter(
                status=assignment_status,
            )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = PickupAssignmentSerializer(
                page,
                many=True,
                context=self.get_serializer_context(),
            )

            return self.get_paginated_response(
                serializer.data,
            )

        serializer = PickupAssignmentSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(
            serializer.data,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="accept",
    )
    @transaction.atomic
    def accept(self, request, pk=None):
        assignment = self.get_object()

        self._require_assignment_owner(
            assignment,
        )

        serializer = PickupAssignmentDecisionSerializer(
            instance=assignment,
            data={
                "decision": AssignmentStatus.ACCEPTED,
            },
            context={
                "request": request,
            },
        )
        serializer.is_valid(
            raise_exception=True,
        )
        assignment = serializer.save()

        request_obj = assignment.request

        if request_obj.status == RequestStatus.APPROVED:
            try:
                transition_request(
                    request_obj=request_obj,
                    to_status=RequestStatus.SCHEDULED,
                    actor=request.user,
                    note=("Request scheduled before volunteer acceptance."),
                )
            except DjangoValidationError as exc:
                raise ValidationError(
                    exc.messages,
                ) from exc

        request_obj.refresh_from_db()

        if request_obj.status == RequestStatus.SCHEDULED:
            try:
                transition_request(
                    request_obj=request_obj,
                    to_status=RequestStatus.ASSIGNED,
                    actor=request.user,
                    note=("Volunteer accepted the pickup assignment."),
                )
            except DjangoValidationError as exc:
                raise ValidationError(
                    exc.messages,
                ) from exc

        assignment.refresh_from_db()

        return Response(
            PickupAssignmentSerializer(
                assignment,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="decline",
    )
    @transaction.atomic
    def decline(self, request, pk=None):
        assignment = self.get_object()

        self._require_assignment_owner(
            assignment,
        )

        serializer = PickupAssignmentDecisionSerializer(
            instance=assignment,
            data={
                "decision": AssignmentStatus.DECLINED,
                "decline_reason": request.data.get(
                    "decline_reason",
                    "",
                ),
            },
            context={
                "request": request,
            },
        )
        serializer.is_valid(
            raise_exception=True,
        )
        assignment = serializer.save()

        return Response(
            PickupAssignmentSerializer(
                assignment,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOperationalAdmin],
        url_path="complete",
    )
    @transaction.atomic
    def complete(self, request, pk=None):
        assignment = self.get_object()

        if assignment.status != AssignmentStatus.ACCEPTED:
            raise ValidationError({"status": ("Only an accepted assignment can be completed.")})

        request_obj = assignment.request

        if request_obj.status != RequestStatus.ASSIGNED:
            raise ValidationError(
                {
                    "request": (
                        "The collection request must be assigned "
                        "before the pickup can be completed."
                    )
                }
            )

        completion_note = request.data.get(
            "note",
            "",
        ).strip()

        assignment.status = AssignmentStatus.COMPLETED
        assignment.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        try:
            transition_request(
                request_obj=request_obj,
                to_status=RequestStatus.COLLECTED,
                actor=request.user,
                note=(
                    completion_note
                    or (f"Pickup completed by {assignment.volunteer.user.full_name}")
                ),
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.messages,
            ) from exc

        record_event(
            actor=request.user,
            event_type="pickup.assignment_completed",
            summary=(f"Completed pickup {request_obj.public_reference}"),
            object_type="PickupAssignment",
            object_id=assignment.id,
            metadata={
                "request_id": str(
                    request_obj.id,
                ),
                "request_reference": (request_obj.public_reference),
                "volunteer_profile_id": str(
                    assignment.volunteer_id,
                ),
                "volunteer_user_id": str(
                    assignment.volunteer.user_id,
                ),
                "completion_note": completion_note,
                "completed_at": timezone.now().isoformat(),
            },
        )

        assignment.refresh_from_db()

        return Response(
            PickupAssignmentSerializer(
                assignment,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )


class HandoverBatchViewSet(viewsets.ModelViewSet):
    queryset = HandoverBatch.objects.prefetch_related(
        "handoverrequest_set__request",
    ).select_related(
        "recorded_by",
    )
    serializer_class = HandoverBatchSerializer
    permission_classes = [IsOperationalAdmin]
    http_method_names = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    @transaction.atomic
    def perform_create(self, serializer):
        batch = serializer.save()

        for link in batch.handoverrequest_set.select_related(
            "request",
        ):
            request_obj = link.request
            request_obj.actual_weight_kg = link.verified_weight_kg
            request_obj.save(
                update_fields=[
                    "actual_weight_kg",
                    "updated_at",
                ]
            )

            if request_obj.status == RequestStatus.COLLECTED:
                transition_request(
                    request_obj=request_obj,
                    to_status=RequestStatus.HANDED_TO_RECYCLER,
                    actor=self.request.user,
                    note=(f"Included in handover batch {batch.reference}"),
                )

        record_event(
            actor=self.request.user,
            event_type="handover.batch_created",
            summary=(f"Recorded handover batch {batch.reference}"),
            object_type="HandoverBatch",
            object_id=batch.id,
            metadata={
                "total_weight_kg": str(
                    batch.total_weight_kg,
                ),
            },
        )
