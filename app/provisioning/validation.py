"""Normalization and validation that precede provisioning writes."""

from __future__ import annotations

from app.provisioning.exceptions import ProvisioningValidationError
from app.provisioning.models import TenantProvisioningRequest
from app.tenancy import normalize_store_slug
from tools.seeding import SeedProfile, SeedValidationError


MAX_TENANT_NAME_LENGTH = 200


def normalize_request(
    request: TenantProvisioningRequest,
) -> tuple[TenantProvisioningRequest, SeedProfile]:
    name = request.name.strip()
    if not name:
        raise ProvisioningValidationError("tenant name is required")
    if len(name) > MAX_TENANT_NAME_LENGTH:
        raise ProvisioningValidationError("tenant name is too long")
    try:
        slug = normalize_store_slug(request.slug)
    except ValueError as exc:
        raise ProvisioningValidationError("tenant slug is invalid or reserved") from exc
    try:
        profile = SeedProfile.parse(request.profile)
    except SeedValidationError as exc:
        raise ProvisioningValidationError(str(exc)) from exc
    modules = tuple(code.strip().lower() for code in request.requested_module_codes)
    if any(not code for code in modules):
        raise ProvisioningValidationError("module codes cannot be empty")
    if len(set(modules)) != len(modules):
        raise ProvisioningValidationError("duplicate requested module codes are not allowed")
    return (
        TenantProvisioningRequest(
            name=name,
            slug=slug,
            profile=profile.value,
            requested_module_codes=modules,
        ),
        profile,
    )
