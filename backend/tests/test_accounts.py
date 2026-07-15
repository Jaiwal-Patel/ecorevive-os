import pytest
from django.core.exceptions import ValidationError

from accounts.models import User, UserRole
from operations.models import VolunteerProfile


@pytest.mark.django_db
def test_founder_guardian_cannot_be_deactivated():
    founder = User.objects.create_user(
        email="founder@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Founder",
        role=UserRole.FOUNDER_GUARDIAN,
        is_staff=True,
    )

    founder.is_active = False

    with pytest.raises(ValidationError):
        founder.save()


@pytest.mark.django_db
def test_founder_recovery_cannot_be_deleted():
    recovery = User.objects.create_user(
        email="recovery@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Recovery",
        role=UserRole.FOUNDER_RECOVERY,
    )

    with pytest.raises(ValidationError):
        recovery.delete()


@pytest.mark.django_db
def test_user_can_change_temporary_password(api_client, resident):
    resident.must_change_password = True
    resident.save(
        update_fields=[
            "must_change_password",
            "updated_at",
        ]
    )

    api_client.force_authenticate(resident)

    response = api_client.post(
        "/api/auth/change-password/",
        {
            "current_password": "Strong-Test-Pass-123!",
            "new_password": "A-New-Unique-Test-Pass-456!",
        },
        format="json",
    )

    assert response.status_code == 200

    resident.refresh_from_db()

    assert resident.check_password("A-New-Unique-Test-Pass-456!")
    assert resident.must_change_password is False


@pytest.mark.django_db
def test_recovery_identity_cannot_access_collection_operations(api_client):
    recovery = User.objects.create_user(
        email="recovery-ops@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Recovery",
        role=UserRole.FOUNDER_RECOVERY,
    )

    api_client.force_authenticate(recovery)

    response = api_client.get("/api/collection-requests/")

    assert response.status_code == 200
    assert response.data["results"] == []

    handovers = api_client.get("/api/handover-batches/")

    assert handovers.status_code == 403


@pytest.mark.django_db
def test_operations_admin_cannot_appoint_principal_admin(api_client):
    operator = User.objects.create_user(
        email="operator@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Operator",
        role=UserRole.OPERATIONS_ADMIN,
    )

    api_client.force_authenticate(operator)

    response = api_client.post(
        "/api/users/",
        {
            "email": "principal@example.com",
            "full_name": "Principal",
            "role": UserRole.PRINCIPAL_ADMIN,
            "password": "Another-Strong-Test-Pass-123!",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_resident_can_register(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new-resident@example.com",
            "full_name": "New Resident",
            "phone_number": "+971500000001",
            "password": "Strong-Resident-Pass-123!",
            "account_type": UserRole.RESIDENT,
        },
        format="json",
    )

    assert response.status_code == 201

    user = User.objects.get(
        email="new-resident@example.com",
    )

    assert user.role == UserRole.RESIDENT
    assert not VolunteerProfile.objects.filter(
        user=user,
    ).exists()


@pytest.mark.django_db
def test_registration_defaults_to_resident(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "default-resident@example.com",
            "full_name": "Default Resident",
            "phone_number": "+971500000002",
            "password": "Strong-Default-Resident-Pass-123!",
        },
        format="json",
    )

    assert response.status_code == 201

    user = User.objects.get(
        email="default-resident@example.com",
    )

    assert user.role == UserRole.RESIDENT
    assert not VolunteerProfile.objects.filter(
        user=user,
    ).exists()


@pytest.mark.django_db
def test_volunteer_can_register_with_pending_profile(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "new-volunteer@example.com",
            "full_name": "New Volunteer",
            "phone_number": "+971500000003",
            "password": "Strong-Volunteer-Pass-123!",
            "account_type": UserRole.VOLUNTEER,
        },
        format="json",
    )

    assert response.status_code == 201

    user = User.objects.get(
        email="new-volunteer@example.com",
    )
    profile = VolunteerProfile.objects.get(
        user=user,
    )

    assert user.role == UserRole.VOLUNTEER
    assert user.is_active is True
    assert profile.active is False
    assert profile.safety_acknowledged is False


@pytest.mark.django_db
def test_public_registration_rejects_admin_role(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "fake-admin@example.com",
            "full_name": "Fake Admin",
            "phone_number": "+971500000004",
            "password": "Strong-Fake-Admin-Pass-123!",
            "account_type": UserRole.OPERATIONS_ADMIN,
        },
        format="json",
    )

    assert response.status_code == 400
    assert not User.objects.filter(
        email="fake-admin@example.com",
    ).exists()