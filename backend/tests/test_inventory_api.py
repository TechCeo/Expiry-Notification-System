from datetime import date, timedelta

from fastapi.testclient import TestClient

API = "/api/v1"


def create_organization(client: TestClient, suffix: str = "primary") -> dict:
    response = client.post(
        f"{API}/organizations",
        json={"name": f"Test Organization {suffix}", "slug": f"test-organization-{suffix}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_product(client: TestClient, organization_id: str, sku: str = "SKU-001") -> dict:
    response = client.post(
        f"{API}/products",
        json={
            "organization_id": organization_id,
            "sku": sku,
            "name": "Test Orange Juice",
            "description": "One litre carton",
            "category": "Beverages",
            "metadata": {"volume_ml": 1000, "refrigerated": True},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_location(client: TestClient, organization_id: str, code: str = "MAIN") -> dict:
    response = client.post(
        f"{API}/locations",
        json={
            "organization_id": organization_id,
            "name": "Main Warehouse",
            "code": code,
            "timezone": "America/New_York",
            "address": "100 Inventory Way",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_batch(
    client: TestClient,
    organization_id: str,
    product_id: str,
    location_id: str,
    batch_number: str = "LOT-001",
    expiry_date: date | None = None,
) -> dict:
    response = client.post(
        f"{API}/batches",
        json={
            "organization_id": organization_id,
            "product_id": product_id,
            "location_id": location_id,
            "batch_number": batch_number,
            "quantity_received": 100,
            "quantity_available": 90,
            "received_date": date.today().isoformat(),
            "expiry_date": (expiry_date or date.today() + timedelta(days=30)).isoformat(),
            "notes": "Integration test inventory",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_complete_inventory_crud_lifecycle(client: TestClient) -> None:
    organization = create_organization(client)
    organization_id = organization["id"]

    organization_page = client.get(
        f"{API}/organizations", params={"name": "test organization", "limit": 10, "offset": 0}
    )
    assert organization_page.status_code == 200
    assert organization_page.json()["total"] == 1

    product = create_product(client, organization_id)
    assert product["metadata"]["volume_ml"] == 1000
    product_id = product["id"]

    product_page = client.get(
        f"{API}/products",
        params={"organization_id": organization_id, "category": "Beverages", "search": "orange"},
    )
    assert product_page.status_code == 200
    assert product_page.json()["items"][0]["id"] == product_id

    location = create_location(client, organization_id)
    location_id = location["id"]
    location_page = client.get(
        f"{API}/locations",
        params={"organization_id": organization_id, "is_active": True, "name": "warehouse"},
    )
    assert location_page.status_code == 200
    assert location_page.json()["items"][0]["id"] == location_id

    expiry = date.today() + timedelta(days=30)
    batch = create_batch(client, organization_id, product_id, location_id, expiry_date=expiry)
    batch_id = batch["id"]

    for parameters in (
        {"product_id": product_id},
        {"location_id": location_id},
        {"expiry_date": expiry.isoformat()},
        {
            "organization_id": organization_id,
            "expires_from": (expiry - timedelta(days=1)).isoformat(),
            "expires_to": (expiry + timedelta(days=1)).isoformat(),
        },
    ):
        response = client.get(f"{API}/batches", params=parameters)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["id"] == batch_id

    assert client.get(f"{API}/organizations/{organization_id}").status_code == 200
    assert client.get(f"{API}/products/{product_id}").status_code == 200
    assert client.get(f"{API}/locations/{location_id}").status_code == 200
    assert client.get(f"{API}/batches/{batch_id}").status_code == 200

    updated_organization = client.patch(
        f"{API}/organizations/{organization_id}", json={"name": "Updated Organization"}
    )
    assert updated_organization.status_code == 200
    assert updated_organization.json()["name"] == "Updated Organization"

    updated_product = client.patch(
        f"{API}/products/{product_id}",
        json={"name": "Updated Orange Juice", "metadata": {"volume_ml": 750}},
    )
    assert updated_product.status_code == 200
    assert updated_product.json()["metadata"] == {"volume_ml": 750}

    updated_location = client.patch(
        f"{API}/locations/{location_id}", json={"address": "200 Updated Way"}
    )
    assert updated_location.status_code == 200
    assert updated_location.json()["address"] == "200 Updated Way"

    updated_batch = client.patch(
        f"{API}/batches/{batch_id}", json={"quantity_available": 25, "status": "quarantined"}
    )
    assert updated_batch.status_code == 200
    assert updated_batch.json()["quantity_available"] == 25
    assert updated_batch.json()["status"] == "quarantined"

    assert client.delete(f"{API}/products/{product_id}").status_code == 409
    assert client.delete(f"{API}/locations/{location_id}").status_code == 409
    assert client.delete(f"{API}/batches/{batch_id}").status_code == 204
    assert client.delete(f"{API}/products/{product_id}").status_code == 204
    assert client.delete(f"{API}/locations/{location_id}").status_code == 204
    assert client.delete(f"{API}/organizations/{organization_id}").status_code == 204

    assert client.get(f"{API}/organizations/{organization_id}").status_code == 404
    assert client.get(f"{API}/products/{product_id}").status_code == 404
    assert client.get(f"{API}/locations/{location_id}").status_code == 404
    assert client.get(f"{API}/batches/{batch_id}").status_code == 404


def test_pagination_and_uniqueness_conflicts(client: TestClient) -> None:
    organizations = [create_organization(client, str(index)) for index in range(3)]

    page = client.get(f"{API}/organizations", params={"limit": 2, "offset": 1})
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert page.json()["limit"] == 2
    assert page.json()["offset"] == 1
    assert len(page.json()["items"]) == 2

    duplicate = client.post(
        f"{API}/organizations",
        json={"name": "Duplicate", "slug": organizations[0]["slug"]},
    )
    assert duplicate.status_code == 409


def test_batch_enforces_tenant_and_quantity_boundaries(client: TestClient) -> None:
    first = create_organization(client, "tenant-a")
    second = create_organization(client, "tenant-b")
    product = create_product(client, first["id"], "TENANT-A-SKU")
    wrong_location = create_location(client, second["id"], "TENANT-B")

    cross_tenant = client.post(
        f"{API}/batches",
        json={
            "organization_id": first["id"],
            "product_id": product["id"],
            "location_id": wrong_location["id"],
            "batch_number": "INVALID-TENANT",
            "quantity_received": 10,
            "quantity_available": 5,
            "received_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    assert cross_tenant.status_code == 422
    assert "same organization" in cross_tenant.json()["detail"]

    invalid_quantity = client.post(
        f"{API}/batches",
        json={
            "organization_id": first["id"],
            "product_id": product["id"],
            "location_id": wrong_location["id"],
            "batch_number": "INVALID-QUANTITY",
            "quantity_received": 5,
            "quantity_available": 10,
            "received_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    assert invalid_quantity.status_code == 422


def test_openapi_documents_inventory_contracts(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    document = response.json()

    for path in ("/api/v1/organizations", "/api/v1/products", "/api/v1/locations", "/api/v1/batches"):
        assert path in document["paths"]
        assert "get" in document["paths"][path]
        assert "post" in document["paths"][path]

    batch_schema = document["components"]["schemas"]["BatchRead"]
    assert batch_schema["properties"]["expiry_date"]["description"]
    assert batch_schema["properties"]["quantity_available"]["description"]
