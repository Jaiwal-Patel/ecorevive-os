from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id", "name", "organization_type", "contact_email", "contact_phone",
            "address", "approved", "created_by_email", "created_at",
        ]
        read_only_fields = ["id", "approved", "created_by_email", "created_at"]
