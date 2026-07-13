import pytest
from rest_framework import status

from operations.models import CollectionRequest, RequestStatus


@pytest.mark.django_db
def test_resident_creates_and_submits_request(api_client, resident, category):
    api_client.force_authenticate(resident)
    response = api_client.post(
        "/api/collection-requests/",
        {
            "address_line": "Building 1, The Greens",
            "area": "The Greens",
            "city": "Dubai",
            "preferred_time_window": "After 5 PM",
            "consent_to_contact": True,
            "consent_to_data_processing": True,
            "items": [{
                "category": str(category.id),
                "description": "Old laptop",
                "quantity": 1,
                "condition": "Not working",
            }],
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    request_obj = CollectionRequest.objects.get(id=response.data["id"])
    submit = api_client.post(
        f"/api/collection-requests/{request_obj.id}/submit/", {}, format="json"
    )
    assert submit.status_code == status.HTTP_200_OK
    request_obj.refresh_from_db()
    assert request_obj.status == RequestStatus.SUBMITTED
    assert request_obj.status_history.count() == 1


@pytest.mark.django_db
def test_resident_cannot_see_other_request(api_client, resident):
    other = resident.__class__.objects.create_user(
        email="other@example.com",
        password="Strong-Test-Pass-123!",
        full_name="Other Resident",
    )
    request_obj = CollectionRequest.objects.create(
        requester=other,
        address_line="Other address",
        area="Marina",
        consent_to_data_processing=True,
    )
    api_client.force_authenticate(resident)
    response = api_client.get(f"/api/collection-requests/{request_obj.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_item_categories_are_an_unpaginated_public_list(api_client, category):
    response = api_client.get("/api/item-categories/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert response.data[0]["name"] == category.name
