from rest_framework import mixins, viewsets

from common.permissions import IsGovernanceLeader

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = AuditEvent.objects.select_related("actor").all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsGovernanceLeader]
    http_method_names = ["get", "head", "options"]
