from unittest.mock import patch

import pytest

from accounts.models import User, UserRole
from operations.models import (
    CollectionRequest,
    RequestStatus,
)
from operations.services import (
    transition_request,
)

PASSWORD = (
    "Strong-Optional-Email-Pass-123!"
)


@pytest.mark.django_db
def test_resident_can_register_without_email(
    api_client,
):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "",
            "full_name": (
                "No Email Resident"
            ),
            "phone_number": (
                "+971500001001"
            ),
            "password": PASSWORD,
            "account_type": (
                UserRole.RESIDENT
            ),
        },
        format="json",
    )

    assert response.status_code == 201

    user = User.objects.get(
        phone_number="+971500001001",
    )

    assert user.email is None
    assert (
        user.role
        == UserRole.RESIDENT
    )


@pytest.mark.django_db
def test_email_less_resident_can_login_by_phone(
    api_client,
):
    User.objects.create_user(
        email=None,
        full_name="Phone Login Resident",
        phone_number="+971500001002",
        password=PASSWORD,
        role=UserRole.RESIDENT,
    )

    response = api_client.post(
        "/api/auth/token/",
        {
            "login": "+971500001002",
            "password": PASSWORD,
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]


@pytest.mark.django_db
def test_existing_email_login_still_works(
    api_client,
):
    User.objects.create_user(
        email=(
            "existing-login@example.com"
        ),
        full_name="Existing Login",
        phone_number="+971500001003",
        password=PASSWORD,
        role=UserRole.RESIDENT,
    )

    response = api_client.post(
        "/api/auth/token/",
        {
            "login": (
                "existing-login@example.com"
            ),
            "password": PASSWORD,
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]


@pytest.mark.django_db
def test_resident_without_email_requires_phone(
    api_client,
):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "",
            "full_name": (
                "Missing Contact Resident"
            ),
            "phone_number": "",
            "password": PASSWORD,
            "account_type": (
                UserRole.RESIDENT
            ),
        },
        format="json",
    )

    assert response.status_code == 400
    assert (
        "phone_number"
        in response.data
    )


@pytest.mark.django_db
def test_volunteer_still_requires_email(
    api_client,
):
    response = api_client.post(
        "/api/auth/register/",
        {
            "email": "",
            "full_name": (
                "Email Less Volunteer"
            ),
            "phone_number": (
                "+971500001004"
            ),
            "password": PASSWORD,
            "account_type": (
                UserRole.VOLUNTEER
            ),
        },
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_email_less_resident_submission_does_not_queue_email(
    django_capture_on_commit_callbacks,
):
    resident = User.objects.create_user(
        email=None,
        full_name=(
            "No Notification Resident"
        ),
        phone_number="+971500001005",
        password=PASSWORD,
        role=UserRole.RESIDENT,
    )

    request_obj = (
        CollectionRequest.objects.create(
            requester=resident,
            status=RequestStatus.DRAFT,
            address_line=(
                "Test address"
            ),
            area="Dubai",
            city="Dubai",
            consent_to_contact=True,
            consent_to_data_processing=True,
        )
    )

    with patch(
        "notifications.tasks."
        "send_request_status_notification.delay",
    ) as email_task:
        with (
            django_capture_on_commit_callbacks(
                execute=True,
            )
        ):
            transition_request(
                request_obj=request_obj,
                to_status=(
                    RequestStatus.SUBMITTED
                ),
                actor=resident,
            )

    request_obj.refresh_from_db()

    assert (
        request_obj.status
        == RequestStatus.SUBMITTED
    )
    email_task.assert_not_called()