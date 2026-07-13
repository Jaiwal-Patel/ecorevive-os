from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class OrganizationType(models.TextChoices):
    CORPORATE = "corporate", "Corporate office"
    SCHOOL = "school", "School"
    COMMUNITY = "community", "Residential community"
    NONPROFIT = "nonprofit", "Community organization"


class Organization(UUIDTimeStampedModel):
    name = models.CharField(max_length=200)
    organization_type = models.CharField(max_length=30, choices=OrganizationType.choices)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organizations_created",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="OrganizationMembership",
        related_name="organizations",
    )

    class Meta:
        ordering = ["name"]


class OrganizationMembership(UUIDTimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120, blank=True)
    is_coordinator = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_organization_membership"
            )
        ]
