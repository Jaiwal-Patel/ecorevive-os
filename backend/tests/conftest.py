import pytest
from rest_framework.test import APIClient

from accounts.models import User, UserRole
from operations.models import ItemCategory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def resident(db):
    return User.objects.create_user(
        email="resident@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Test Resident",
        role=UserRole.RESIDENT,
    )


@pytest.fixture
def category(db):
    return ItemCategory.objects.create(name="Laptops", slug="laptops")
