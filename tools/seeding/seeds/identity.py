"""Non-production disabled identity placeholder seed."""

from sqlalchemy import select

from app.models import UserIdentity
from tools.seeding.context import (
    SeedContext,
    SeedMutation,
    SeedOwnership,
    SeedProfile,
    SeedScope,
    SeedStatus,
)
from tools.seeding.registry import SeedDefinition, SeedRegistry


PLACEHOLDER_EMAIL = "disabled-placeholder@example.invalid"


def seed_disabled_identity_placeholder(context: SeedContext) -> SeedMutation:
    existing = context.session.scalar(
        select(UserIdentity).where(UserIdentity.normalized_email == PLACEHOLDER_EMAIL)
    )
    if existing is not None:
        return SeedMutation(
            status=SeedStatus.UNCHANGED,
            unchanged=1,
            summary={"catalog": "disabled_identity_placeholder"},
        )
    context.session.add(
        UserIdentity(
            email=PLACEHOLDER_EMAIL,
            normalized_email=PLACEHOLDER_EMAIL,
            display_name="Disabled Development Placeholder",
            password_hash=None,
            status="disabled",
            is_service_account=False,
            email_verified=False,
        )
    )
    return SeedMutation(
        status=SeedStatus.CREATED,
        created=1,
        summary={"catalog": "disabled_identity_placeholder"},
    )


def register_identity_seeds(registry: SeedRegistry) -> None:
    registry.register(
        SeedDefinition(
            name="development.disabled_identity_placeholder",
            version="1",
            scope=SeedScope.GLOBAL,
            compatible_profiles=frozenset(
                {SeedProfile.DEVELOPMENT, SeedProfile.DEMO, SeedProfile.TEST}
            ),
            production_safe=False,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_disabled_identity_placeholder,
            order=60,
            description="Create a disabled, passwordless non-production placeholder.",
        )
    )
