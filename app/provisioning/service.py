"""Atomic, reusable tenant provisioning orchestration."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AdminAuditLog, ModuleDefinition, Store, StoreModule
from app.module_catalog import DEFAULT_PROVISIONING_MODULES
from app.provisioning.context import TenantProvisioningContext
from app.provisioning.exceptions import (
    ProvisioningConflictError,
    ProvisioningError,
    ProvisioningExecutionError,
    ProvisioningTransactionError,
    ProvisioningValidationError,
)
from app.provisioning.models import (
    ProvisioningStatus,
    TenantProvisioningRequest,
    TenantProvisioningResult,
)
from app.provisioning.steps import TenantProvisioningStep
from app.provisioning.validation import normalize_request
from app.tenancy import (
    TenantActor,
    TenantActorType,
    TenantConnector,
    TenantContext,
    TenantResolutionSource,
    normalize_correlation_id,
)
from tools.seeding import SeedRunner, default_registry


LOGGER = logging.getLogger("sales_agent.provisioning")
PROVISIONING_SEEDS = ("tenant.module_entitlements",)


class TenantProvisioningService:
    """Provision one tenant and own exactly one database transaction.

    The supplied session must be clean (no active transaction). On success the
    service commits. On dry-run or any failure it rolls back. Callers must not
    wrap this method in another transaction.
    """

    def __init__(
        self,
        session: Session,
        *,
        seed_runner: SeedRunner | None = None,
        step_overrides: dict[
            str, Callable[[TenantProvisioningContext], None]
        ] | None = None,
    ) -> None:
        self.session = session
        self.seed_runner = seed_runner or SeedRunner(
            session.get_bind(), default_registry()  # type: ignore[arg-type]
        )
        self.step_overrides = dict(step_overrides or {})

    def plan(
        self, request: TenantProvisioningRequest
    ) -> tuple[TenantProvisioningRequest, tuple[str, ...]]:
        normalized, _ = normalize_request(request)
        return normalized, tuple(step.name for step in self._steps())

    def provision(
        self,
        request: TenantProvisioningRequest,
        *,
        dry_run: bool = False,
    ) -> TenantProvisioningResult:
        if self.session.in_transaction():
            raise ProvisioningTransactionError(
                "provisioning requires a session without an active transaction"
            )
        normalized, profile = normalize_request(request)
        context = TenantProvisioningContext(
            session=self.session,
            request=normalized,
            profile=profile,
            operation_id=str(uuid.uuid4()),
            dry_run=dry_run,
        )
        transaction = self.session.begin()
        current_step = "transaction"
        started = time.monotonic()
        LOGGER.info(
            "tenant provisioning started operation_id=%s tenant_slug=%s",
            context.operation_id,
            normalized.slug,
        )
        try:
            for step in self._steps():
                current_step = step.name
                handler = self.step_overrides.get(step.name, step.handler)
                handler(context)
                context.completed_steps.append(step.name)
            assert context.tenant is not None
            result = TenantProvisioningResult(
                operation_id=context.operation_id,
                tenant_id=context.tenant.id,
                tenant_name=context.tenant.name,
                tenant_slug=context.tenant.slug,
                tenant_status=context.tenant.status,
                profile=profile.value,
                status=(
                    ProvisioningStatus.PLANNED
                    if dry_run
                    else ProvisioningStatus.SUCCEEDED
                ),
                completed_steps=tuple(context.completed_steps),
                seed_names=tuple(item.seed_name for item in context.seed_results),
                module_codes=context.selected_module_codes,
                dry_run=dry_run,
            )
            if dry_run:
                transaction.rollback()
            else:
                transaction.commit()
            LOGGER.info(
                "tenant provisioning completed operation_id=%s tenant_slug=%s "
                "status=%s duration_ms=%d",
                context.operation_id,
                normalized.slug,
                result.status.value,
                int((time.monotonic() - started) * 1000),
            )
            return result
        except IntegrityError as exc:
            transaction.rollback()
            LOGGER.warning(
                "tenant provisioning conflict operation_id=%s tenant_slug=%s step=%s",
                context.operation_id,
                normalized.slug,
                current_step,
            )
            raise ProvisioningConflictError("tenant slug already exists") from exc
        except ProvisioningError:
            transaction.rollback()
            LOGGER.warning(
                "tenant provisioning rejected operation_id=%s tenant_slug=%s step=%s",
                context.operation_id,
                normalized.slug,
                current_step,
            )
            raise
        except Exception as exc:
            transaction.rollback()
            LOGGER.error(
                "tenant provisioning failed operation_id=%s tenant_slug=%s "
                "step=%s error_type=%s",
                context.operation_id,
                normalized.slug,
                current_step,
                type(exc).__name__,
            )
            raise ProvisioningExecutionError(current_step, cause=exc) from exc

    def _steps(self) -> tuple[TenantProvisioningStep, ...]:
        return (
            TenantProvisioningStep("validate_identity", 10, self._validate_identity),
            TenantProvisioningStep("create_tenant", 20, self._create_tenant),
            TenantProvisioningStep("establish_tenant_context", 30, self._establish_context),
            TenantProvisioningStep("run_tenant_seeds", 40, self._run_tenant_seeds),
            TenantProvisioningStep("configure_modules", 50, self._configure_modules),
            TenantProvisioningStep("verify_tenant", 60, self._verify_tenant),
            TenantProvisioningStep("finalize_tenant", 70, self._finalize_tenant),
            TenantProvisioningStep("record_audit", 80, self._record_audit),
        )

    @staticmethod
    def _validate_identity(context: TenantProvisioningContext) -> None:
        existing = context.session.scalar(
            select(Store.id).where(func.lower(Store.slug) == context.request.slug)
        )
        if existing is not None:
            raise ProvisioningConflictError("tenant slug already exists")

    @staticmethod
    def _create_tenant(context: TenantProvisioningContext) -> None:
        tenant = Store(
            name=context.request.name,
            slug=context.request.slug,
            status="provisioning",
        )
        context.session.add(tenant)
        context.session.flush()
        context.tenant = tenant

    @staticmethod
    def _establish_context(context: TenantProvisioningContext) -> None:
        assert context.tenant is not None
        context.tenant_context = TenantContext(
            store_id=context.tenant.id,
            store_slug=context.tenant.slug,
            store_status=context.tenant.status,
            resolution_source=TenantResolutionSource.EXPLICIT_INTERNAL,
            actor=TenantActor(
                id="tenant-provisioning-service",
                type=TenantActorType.SYSTEM,
                role="tenant_provisioner",
            ),
            membership_id=None,
            connector=TenantConnector(),
            correlation_id=normalize_correlation_id(context.operation_id),
        )

    def _run_tenant_seeds(self, context: TenantProvisioningContext) -> None:
        assert context.tenant_context is not None
        report = self.seed_runner.run_in_session(
            context.session,
            context.profile,
            tenant=context.tenant_context,
            seed_names=PROVISIONING_SEEDS,
            dry_run=context.dry_run,
        )
        context.seed_results.extend(report.results)

    @staticmethod
    def _configure_modules(context: TenantProvisioningContext) -> None:
        definitions = {
            item.code: item
            for item in context.session.scalars(select(ModuleDefinition)).all()
        }
        requested = set(DEFAULT_PROVISIONING_MODULES)
        requested.update(context.request.requested_module_codes)
        unknown = sorted(requested - definitions.keys())
        if unknown:
            raise ProvisioningValidationError(
                f"unknown module code(s): {', '.join(unknown)}"
            )

        selected: set[str] = set()
        visiting: set[str] = set()

        def include(code: str) -> None:
            if code in selected:
                return
            if code in visiting:
                raise ProvisioningValidationError("module dependency cycle detected")
            definition = definitions[code]
            if not definition.is_sellable or definition.availability == "planned":
                raise ProvisioningValidationError(
                    f"module {code!r} is not available for provisioning"
                )
            visiting.add(code)
            for dependency in definition.dependencies or []:
                dependency_code = str(dependency)
                if dependency_code not in definitions:
                    raise ProvisioningValidationError(
                        f"module {code!r} has unknown dependency {dependency_code!r}"
                    )
                include(dependency_code)
            visiting.remove(code)
            selected.add(code)

        for code in sorted(requested):
            include(code)

        assert context.tenant is not None
        entitlements = {
            item.module_code: item
            for item in context.session.scalars(
                select(StoreModule).where(StoreModule.store_id == context.tenant.id)
            ).all()
        }
        missing = sorted(definitions.keys() - entitlements.keys())
        if missing:
            raise ProvisioningExecutionError("configure_modules")
        for code in selected:
            entitlement = entitlements[code]
            entitlement.status = "active"
            entitlement.source = "provisioning"
        context.selected_module_codes = tuple(sorted(selected))
        context.session.flush()

    @staticmethod
    def _verify_tenant(context: TenantProvisioningContext) -> None:
        assert context.tenant is not None
        persisted = context.session.scalar(
            select(Store).where(
                Store.id == context.tenant.id,
                Store.slug == context.request.slug,
                Store.status == "provisioning",
            )
        )
        if persisted is None:
            raise ProvisioningExecutionError("verify_tenant")
        definitions = set(context.session.scalars(select(ModuleDefinition.code)).all())
        entitlements = list(
            context.session.scalars(
                select(StoreModule).where(StoreModule.store_id == context.tenant.id)
            ).all()
        )
        if {item.module_code for item in entitlements} != definitions:
            raise ProvisioningExecutionError("verify_tenant")
        active = {
            item.module_code for item in entitlements if item.status == "active"
        }
        if not set(context.selected_module_codes).issubset(active):
            raise ProvisioningExecutionError("verify_tenant")
        if not any(
            item.seed_name == "tenant.module_entitlements"
            for item in context.seed_results
        ):
            raise ProvisioningExecutionError("verify_tenant")

    @staticmethod
    def _finalize_tenant(context: TenantProvisioningContext) -> None:
        assert context.tenant is not None
        context.tenant.status = "active"
        context.session.flush()

    @staticmethod
    def _record_audit(context: TenantProvisioningContext) -> None:
        assert context.tenant is not None
        context.session.add(
            AdminAuditLog(
                store_id=context.tenant.id,
                action="tenant_provisioned",
                entity_type="store",
                entity_id=str(context.tenant.id),
                details_json={
                    "operation_id": context.operation_id,
                    "profile": context.profile.value,
                    "module_codes": list(context.selected_module_codes),
                    "completed_steps": list(context.completed_steps),
                },
            )
        )
        context.session.flush()
