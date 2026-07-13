from rest_framework import serializers

from .models import ImpactMetric


class ImpactMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpactMetric
        fields = [
            "id", "key", "label", "value", "unit",
            "public", "source_note", "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
