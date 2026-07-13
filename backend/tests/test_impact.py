import pytest
from rest_framework.test import APIClient

from impact.models import ImpactMetric


@pytest.mark.django_db
def test_public_impact_excludes_private():
    ImpactMetric.objects.create(key="public", label="Public", value=1, unit="kg", public=True)
    ImpactMetric.objects.create(key="private", label="Private", value=2, unit="kg", public=False)
    response = APIClient().get("/api/public/impact/")
    assert response.status_code == 200
    assert {item["key"] for item in response.data} == {"public"}
