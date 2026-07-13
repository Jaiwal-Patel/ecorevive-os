from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from common.models import UUIDTimeStampedModel


class ImpactMetric(UUIDTimeStampedModel):
    key = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=180)
    value = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    unit = models.CharField(max_length=50)
    public = models.BooleanField(default=True)
    source_note = models.TextField(blank=True)

    class Meta:
        ordering = ["key"]
