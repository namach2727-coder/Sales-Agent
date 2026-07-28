"""Immutable permission and system-role catalog."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.authz.context import PermissionScope


PERMISSION_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$"
)
ROLE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class PermissionCode:
    TENANT_CREATE = "tenant.create"
    TENANT_READ = "tenant.read"
    TENANT_UPDATE = "tenant.update"
    TENANT_DISABLE = "tenant.disable"
    TENANT_SUSPEND = "tenant.suspend"
    TENANT_ARCHIVE = "tenant.archive"
    TENANT_PROVISION = "tenant.provision"
    TENANT_ACCESS_MANAGE = "tenant.access_manage"
    PLATFORM_AUDIT_READ = "platform.audit_read"
    PLATFORM_ACCESS_MANAGE = "platform.access_manage"
    MODULE_CATALOG_MANAGE = "module.catalog_manage"
    PLATFORM_SETTINGS_MANAGE = "platform.settings_manage"

    TENANT_SETTINGS_READ = "tenant.settings_read"
    TENANT_SETTINGS_UPDATE = "tenant.settings_update"
    TENANT_MEMBERS_READ = "tenant.members_read"
    TENANT_MEMBERS_MANAGE = "tenant.members_manage"
    TENANT_MEMBERS_MANAGE_V2 = "tenant.members.manage"
    STORE_CREATE = "store.create"
    STORE_READ = "store.read"
    STORE_UPDATE = "store.update"
    STORE_SUSPEND = "store.suspend"
    STORE_ARCHIVE = "store.archive"
    STORE_MEMBERS_MANAGE = "store.members.manage"
    MODULE_ENTITLEMENT_READ = "module.entitlement_read"
    MODULE_ENTITLEMENT_MANAGE = "module.entitlement_manage"
    PRODUCT_READ = "product.read"
    PRODUCT_MANAGE = "product.manage"
    CATALOG_READ = "catalog.read"
    CATALOG_MANAGE = "catalog.manage"
    PRICING_READ = "pricing.read"
    PRICING_MANAGE = "pricing.manage"
    AVAILABILITY_READ = "availability.read"
    AVAILABILITY_MANAGE = "availability.manage"
    MEDIA_READ = "media.read"
    MEDIA_MANAGE = "media.manage"
    BUSINESS_PROFILE_READ = "business_profile.read"
    BUSINESS_PROFILE_MANAGE = "business_profile.manage"
    KNOWLEDGE_READ = "knowledge.read"
    KNOWLEDGE_MANAGE = "knowledge.manage"
    KNOWLEDGE_PUBLISH = "knowledge.publish"
    CONTENT_READ = "content.read"
    CONTENT_MANAGE = "content.manage"
    CONNECTOR_READ = "connector.read"
    CONNECTOR_MANAGE = "connector.manage"
    CONVERSATION_READ = "conversation.read"
    CONVERSATION_MANAGE = "conversation.manage"
    ORDER_READ = "order.read"
    ORDER_MANAGE = "order.manage"
    ANALYTICS_READ = "analytics.read"
    AUDIT_READ = "audit.read"


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    code: str
    scope: PermissionScope
    description: str

    def __post_init__(self) -> None:
        if PERMISSION_CODE_PATTERN.fullmatch(self.code) is None:
            raise ValueError(f"invalid permission code {self.code!r}")


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    code: str
    display_name: str
    scope: PermissionScope
    description: str
    permission_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if ROLE_CODE_PATTERN.fullmatch(self.code) is None:
            raise ValueError(f"invalid role code {self.code!r}")
        if len(set(self.permission_codes)) != len(self.permission_codes):
            raise ValueError(f"role {self.code!r} contains duplicate permissions")


def _permission(code: str, scope: PermissionScope, description: str) -> PermissionDefinition:
    return PermissionDefinition(code, scope, description)


PLATFORM_PERMISSIONS = (
    _permission(PermissionCode.TENANT_CREATE, PermissionScope.PLATFORM, "Create tenant records."),
    _permission(PermissionCode.TENANT_READ, PermissionScope.PLATFORM, "Read provider tenant inventory."),
    _permission(PermissionCode.TENANT_UPDATE, PermissionScope.PLATFORM, "Update tenant configuration and entitlements."),
    _permission(PermissionCode.TENANT_DISABLE, PermissionScope.PLATFORM, "Disable a tenant."),
    _permission(PermissionCode.TENANT_SUSPEND, PermissionScope.PLATFORM, "Suspend and reactivate tenants."),
    _permission(PermissionCode.TENANT_ARCHIVE, PermissionScope.PLATFORM, "Archive tenants."),
    _permission(PermissionCode.TENANT_PROVISION, PermissionScope.PLATFORM, "Run tenant provisioning."),
    _permission(PermissionCode.TENANT_ACCESS_MANAGE, PermissionScope.PLATFORM, "Manage access across explicit tenants."),
    _permission(PermissionCode.PLATFORM_AUDIT_READ, PermissionScope.PLATFORM, "Read platform audit records."),
    _permission(PermissionCode.PLATFORM_ACCESS_MANAGE, PermissionScope.PLATFORM, "Manage platform role assignments."),
    _permission(PermissionCode.MODULE_CATALOG_MANAGE, PermissionScope.PLATFORM, "Manage provider module catalog."),
    _permission(PermissionCode.PLATFORM_SETTINGS_MANAGE, PermissionScope.PLATFORM, "Manage platform settings."),
)

TENANT_PERMISSIONS = (
    _permission(PermissionCode.TENANT_SETTINGS_READ, PermissionScope.TENANT, "Read tenant settings."),
    _permission(PermissionCode.TENANT_SETTINGS_UPDATE, PermissionScope.TENANT, "Update tenant settings."),
    _permission(PermissionCode.TENANT_MEMBERS_READ, PermissionScope.TENANT, "Read tenant membership."),
    _permission(PermissionCode.TENANT_MEMBERS_MANAGE, PermissionScope.TENANT, "Manage tenant membership and roles."),
    _permission(PermissionCode.TENANT_MEMBERS_MANAGE_V2, PermissionScope.TENANT, "Manage tenant membership lifecycle."),
    _permission(PermissionCode.STORE_CREATE, PermissionScope.TENANT, "Create stores in the active tenant."),
    _permission(PermissionCode.STORE_READ, PermissionScope.TENANT, "Read explicitly authorized stores."),
    _permission(PermissionCode.STORE_UPDATE, PermissionScope.TENANT, "Update explicitly authorized stores."),
    _permission(PermissionCode.STORE_SUSPEND, PermissionScope.TENANT, "Suspend and reactivate stores."),
    _permission(PermissionCode.STORE_ARCHIVE, PermissionScope.TENANT, "Archive stores."),
    _permission(PermissionCode.STORE_MEMBERS_MANAGE, PermissionScope.TENANT, "Manage explicit store access assignments."),
    _permission(PermissionCode.MODULE_ENTITLEMENT_READ, PermissionScope.TENANT, "Read tenant module entitlements."),
    _permission(PermissionCode.MODULE_ENTITLEMENT_MANAGE, PermissionScope.TENANT, "Manage tenant module entitlements."),
    _permission(PermissionCode.PRODUCT_READ, PermissionScope.TENANT, "Read tenant products."),
    _permission(PermissionCode.PRODUCT_MANAGE, PermissionScope.TENANT, "Manage tenant products."),
    _permission(PermissionCode.CATALOG_READ, PermissionScope.TENANT, "Read the tenant business catalog."),
    _permission(PermissionCode.CATALOG_MANAGE, PermissionScope.TENANT, "Manage the tenant business catalog."),
    _permission(PermissionCode.PRICING_READ, PermissionScope.TENANT, "Read store-specific SKU prices."),
    _permission(PermissionCode.PRICING_MANAGE, PermissionScope.TENANT, "Manage store-specific SKU prices."),
    _permission(PermissionCode.AVAILABILITY_READ, PermissionScope.TENANT, "Read store-specific SKU availability."),
    _permission(PermissionCode.AVAILABILITY_MANAGE, PermissionScope.TENANT, "Manage store-specific SKU availability."),
    _permission(PermissionCode.MEDIA_READ, PermissionScope.TENANT, "Read catalog media metadata and associations."),
    _permission(PermissionCode.MEDIA_MANAGE, PermissionScope.TENANT, "Manage catalog media metadata and associations."),
    _permission(PermissionCode.BUSINESS_PROFILE_READ, PermissionScope.TENANT, "Read assigned-store business profiles."),
    _permission(PermissionCode.BUSINESS_PROFILE_MANAGE, PermissionScope.TENANT, "Manage assigned-store business profiles."),
    _permission(PermissionCode.KNOWLEDGE_READ, PermissionScope.TENANT, "Read assigned-store policies, FAQs, and knowledge entries."),
    _permission(PermissionCode.KNOWLEDGE_MANAGE, PermissionScope.TENANT, "Manage draft assigned-store policies, FAQs, and knowledge entries."),
    _permission(PermissionCode.KNOWLEDGE_PUBLISH, PermissionScope.TENANT, "Publish or withdraw assigned-store business knowledge."),
    _permission(PermissionCode.CONTENT_READ, PermissionScope.TENANT, "Read tenant content."),
    _permission(PermissionCode.CONTENT_MANAGE, PermissionScope.TENANT, "Manage tenant content."),
    _permission(PermissionCode.CONNECTOR_READ, PermissionScope.TENANT, "Read tenant connector status."),
    _permission(PermissionCode.CONNECTOR_MANAGE, PermissionScope.TENANT, "Manage tenant connectors."),
    _permission(PermissionCode.CONVERSATION_READ, PermissionScope.TENANT, "Read tenant conversations."),
    _permission(PermissionCode.CONVERSATION_MANAGE, PermissionScope.TENANT, "Manage tenant conversations."),
    _permission(PermissionCode.ORDER_READ, PermissionScope.TENANT, "Read tenant orders."),
    _permission(PermissionCode.ORDER_MANAGE, PermissionScope.TENANT, "Manage tenant orders."),
    _permission(PermissionCode.ANALYTICS_READ, PermissionScope.TENANT, "Read tenant analytics."),
    _permission(PermissionCode.AUDIT_READ, PermissionScope.TENANT, "Read tenant audit records."),
)

def validate_permission_catalog(
    definitions: tuple[PermissionDefinition, ...],
) -> dict[str, PermissionDefinition]:
    catalog: dict[str, PermissionDefinition] = {}
    for item in definitions:
        if item.code in catalog:
            raise ValueError(f"duplicate permission code {item.code!r}")
        catalog[item.code] = item
    return catalog


def validate_role_catalog(
    definitions: tuple[RoleDefinition, ...],
    permissions: dict[str, PermissionDefinition],
) -> dict[str, RoleDefinition]:
    catalog: dict[str, RoleDefinition] = {}
    for role in definitions:
        if role.code in catalog:
            raise ValueError(f"duplicate role code {role.code!r}")
        for code in role.permission_codes:
            permission = permissions.get(code)
            if permission is None or permission.scope is not role.scope:
                raise ValueError(
                    f"role {role.code!r} has incompatible permission {code!r}"
                )
        catalog[role.code] = role
    return catalog


PERMISSION_DEFINITIONS = (*PLATFORM_PERMISSIONS, *TENANT_PERMISSIONS)
PERMISSION_BY_CODE = validate_permission_catalog(PERMISSION_DEFINITIONS)

ALL_PLATFORM_CODES = tuple(item.code for item in PLATFORM_PERMISSIONS)
ALL_TENANT_CODES = tuple(item.code for item in TENANT_PERMISSIONS)


ROLE_DEFINITIONS = (
    RoleDefinition("platform_super_admin", "Platform Super Admin", PermissionScope.PLATFORM, "Explicit full platform administration.", ALL_PLATFORM_CODES),
    RoleDefinition("platform_operator", "Platform Operator", PermissionScope.PLATFORM, "Tenant and module operations without access-policy administration.", (
        PermissionCode.TENANT_CREATE, PermissionCode.TENANT_READ, PermissionCode.TENANT_UPDATE,
        PermissionCode.TENANT_DISABLE, PermissionCode.TENANT_PROVISION,
        PermissionCode.TENANT_ACCESS_MANAGE, PermissionCode.MODULE_CATALOG_MANAGE,
    )),
    RoleDefinition("platform_auditor", "Platform Auditor", PermissionScope.PLATFORM, "Read-only platform inventory and audit.", (
        PermissionCode.TENANT_READ, PermissionCode.PLATFORM_AUDIT_READ,
    )),
    RoleDefinition("tenant_owner", "Tenant Owner", PermissionScope.TENANT, "Full explicit tenant administration.", ALL_TENANT_CODES),
    RoleDefinition("tenant_admin", "Tenant Admin", PermissionScope.TENANT, "Tenant administration except audit ownership.", tuple(code for code in ALL_TENANT_CODES if code != PermissionCode.AUDIT_READ)),
    RoleDefinition("tenant_operator", "Tenant Operator", PermissionScope.TENANT, "Sales and operational management.", (
        PermissionCode.TENANT_SETTINGS_READ, PermissionCode.MODULE_ENTITLEMENT_READ,
        PermissionCode.PRODUCT_READ, PermissionCode.PRODUCT_MANAGE,
        PermissionCode.CATALOG_READ, PermissionCode.CATALOG_MANAGE,
        PermissionCode.PRICING_READ, PermissionCode.PRICING_MANAGE,
        PermissionCode.AVAILABILITY_READ, PermissionCode.AVAILABILITY_MANAGE,
        PermissionCode.MEDIA_READ, PermissionCode.MEDIA_MANAGE,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.BUSINESS_PROFILE_MANAGE,
        PermissionCode.KNOWLEDGE_READ, PermissionCode.KNOWLEDGE_MANAGE,
        PermissionCode.CONNECTOR_READ, PermissionCode.CONVERSATION_READ,
        PermissionCode.CONVERSATION_MANAGE, PermissionCode.ORDER_READ, PermissionCode.ORDER_MANAGE,
    )),
    RoleDefinition("tenant_content_manager", "Tenant Content Manager", PermissionScope.TENANT, "Product and content management.", (
        PermissionCode.PRODUCT_READ, PermissionCode.CATALOG_READ, PermissionCode.CATALOG_MANAGE,
        PermissionCode.MEDIA_READ, PermissionCode.MEDIA_MANAGE,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.BUSINESS_PROFILE_MANAGE,
        PermissionCode.KNOWLEDGE_READ, PermissionCode.KNOWLEDGE_MANAGE,
        PermissionCode.KNOWLEDGE_PUBLISH,
        PermissionCode.CONTENT_READ, PermissionCode.CONTENT_MANAGE,
    )),
    RoleDefinition("tenant_analyst", "Tenant Analyst", PermissionScope.TENANT, "Analytics and supporting read access.", (
        PermissionCode.PRODUCT_READ, PermissionCode.CATALOG_READ, PermissionCode.PRICING_READ,
        PermissionCode.AVAILABILITY_READ, PermissionCode.MEDIA_READ,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.KNOWLEDGE_READ,
        PermissionCode.CONTENT_READ, PermissionCode.CONVERSATION_READ,
        PermissionCode.ORDER_READ, PermissionCode.ANALYTICS_READ,
    )),
    RoleDefinition("tenant_viewer", "Tenant Viewer", PermissionScope.TENANT, "Read-only tenant access.", (
        PermissionCode.TENANT_SETTINGS_READ, PermissionCode.TENANT_MEMBERS_READ,
        PermissionCode.MODULE_ENTITLEMENT_READ, PermissionCode.PRODUCT_READ,
        PermissionCode.CATALOG_READ, PermissionCode.PRICING_READ,
        PermissionCode.AVAILABILITY_READ, PermissionCode.MEDIA_READ,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.KNOWLEDGE_READ,
        PermissionCode.CONTENT_READ, PermissionCode.CONNECTOR_READ,
        PermissionCode.CONVERSATION_READ, PermissionCode.ORDER_READ,
        PermissionCode.ANALYTICS_READ, PermissionCode.AUDIT_READ,
    )),
    RoleDefinition("store_manager", "Store Manager", PermissionScope.TENANT, "Manage explicitly assigned stores.", (
        PermissionCode.STORE_READ, PermissionCode.STORE_UPDATE,
        PermissionCode.STORE_SUSPEND, PermissionCode.STORE_MEMBERS_MANAGE,
        PermissionCode.PRODUCT_READ, PermissionCode.PRODUCT_MANAGE,
        PermissionCode.CATALOG_READ, PermissionCode.CATALOG_MANAGE,
        PermissionCode.PRICING_READ, PermissionCode.PRICING_MANAGE,
        PermissionCode.AVAILABILITY_READ, PermissionCode.AVAILABILITY_MANAGE,
        PermissionCode.MEDIA_READ, PermissionCode.MEDIA_MANAGE,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.BUSINESS_PROFILE_MANAGE,
        PermissionCode.KNOWLEDGE_READ, PermissionCode.KNOWLEDGE_MANAGE,
        PermissionCode.KNOWLEDGE_PUBLISH,
        PermissionCode.CONTENT_READ, PermissionCode.CONTENT_MANAGE,
        PermissionCode.ORDER_READ, PermissionCode.ORDER_MANAGE,
    )),
    RoleDefinition("operator", "Operator", PermissionScope.TENANT, "Operate assigned stores without access administration.", (
        PermissionCode.STORE_READ, PermissionCode.PRODUCT_READ,
        PermissionCode.CATALOG_READ, PermissionCode.PRICING_READ,
        PermissionCode.AVAILABILITY_READ, PermissionCode.MEDIA_READ,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.KNOWLEDGE_READ,
        PermissionCode.CONVERSATION_READ, PermissionCode.CONVERSATION_MANAGE,
        PermissionCode.ORDER_READ, PermissionCode.ORDER_MANAGE,
    )),
    RoleDefinition("read_only", "Read Only", PermissionScope.TENANT, "Read assigned store data.", (
        PermissionCode.STORE_READ, PermissionCode.PRODUCT_READ,
        PermissionCode.CATALOG_READ, PermissionCode.PRICING_READ,
        PermissionCode.AVAILABILITY_READ, PermissionCode.MEDIA_READ,
        PermissionCode.BUSINESS_PROFILE_READ, PermissionCode.KNOWLEDGE_READ,
        PermissionCode.CONTENT_READ, PermissionCode.CONVERSATION_READ,
        PermissionCode.ORDER_READ, PermissionCode.ANALYTICS_READ,
    )),
)

ROLE_BY_CODE = validate_role_catalog(ROLE_DEFINITIONS, PERMISSION_BY_CODE)
