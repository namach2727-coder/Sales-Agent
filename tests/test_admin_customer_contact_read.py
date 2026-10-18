"""Read-only admin customer contact response contract (UAT feature gate)."""
from __future__ import annotations

import inspect

from app.commerce.schemas import AdminCustomerStoreRead
from app.commerce.router import admin_commerce_customers


def test_customer_contact_fields_nullable_for_legacy_tenants():
    response = AdminCustomerStoreRead(
        tenant_public_id="tenant-id", tenant_name="Business",
        store_public_id="store-id", store_name="Store",
        store_status="active", effective_capabilities=[],
    )
    assert response.customer_display_name is None
    assert response.customer_phone_number is None
    assert response.customer_email is None


def test_customer_contact_fields_may_be_populated_from_identity():
    response = AdminCustomerStoreRead(
        tenant_public_id="tenant-id", tenant_name="Business",
        store_public_id="store-id", store_name="Store",
        store_status="active", effective_capabilities=[],
        customer_display_name="Owner Example",
        customer_phone_number="+989123456789",
        customer_email="example@example.test",
    )
    assert response.customer_display_name == "Owner Example"
    assert response.customer_phone_number == "+989123456789"


def test_admin_contact_endpoint_remains_permission_guarded_read_only():
    source = inspect.getsource(admin_commerce_customers)
    assert "PermissionCode.COMMERCE_SUBSCRIPTION_READ" in source
    assert "created_by_identity_id" in source
    assert "UserIdentity" in source
    assert ".limit(page_size)" in source
    assert "session.add(" not in source
    assert "db.commit(" not in source
