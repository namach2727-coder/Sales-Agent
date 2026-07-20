"""Transactional seed execution with tenant resolution and safe audit history."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models import SeedHistory
from app.tenancy import TenantContext, TenantResolutionError, resolve_explicit_internal_tenant
from tools.seeding.context import (
    SeedContext,
    SeedExecutionError,
    SeedMutation,
    SeedProfile,
    SeedReport,
    SeedResult,
    SeedStatus,
    SeedValidationError,
)
from tools.seeding.registry import SeedDefinition, SeedRegistry


class SeedRunner:
    """Execute each seed in its own transaction for clear retry boundaries."""

    def __init__(self, engine: Engine, registry: SeedRegistry):
        self.engine = engine
        self.registry = registry
        self._sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def run(
        self,
        profile: str | SeedProfile,
        *,
        tenant_slug: str | None = None,
        seed_names: tuple[str, ...] | None = None,
        dry_run: bool = False,
    ) -> SeedReport:
        resolved_profile = SeedProfile.parse(profile)
        tenant = self._resolve_tenant(tenant_slug) if tenant_slug else None
        definitions = self.registry.select(
            resolved_profile,
            names=seed_names,
            tenant_supplied=tenant is not None,
        )
        if dry_run:
            results = self._run_dry_run(definitions, resolved_profile, tenant)
        else:
            completed: list[SeedResult] = []
            try:
                for definition in definitions:
                    completed.append(self._run_one(definition, resolved_profile, tenant))
            except SeedExecutionError as exc:
                report = SeedReport(
                    profile=resolved_profile,
                    dry_run=False,
                    results=(*completed, exc.result),
                )
                raise SeedExecutionError(exc.seed_name, exc.result, report) from exc
            results = tuple(completed)
        return SeedReport(profile=resolved_profile, dry_run=dry_run, results=results)

    def run_in_session(
        self,
        session: Session,
        profile: str | SeedProfile,
        *,
        tenant: TenantContext,
        seed_names: tuple[str, ...],
        dry_run: bool = False,
    ) -> SeedReport:
        """Run selected seeds inside a caller-owned transaction.

        This entry point never begins, commits, rolls back, retries, or closes the
        supplied session. It is intended for larger atomic workflows such as
        tenant provisioning, where seed mutations and their history must share
        the same transaction as tenant creation.
        """

        resolved_profile = SeedProfile.parse(profile)
        definitions = self.registry.select(
            resolved_profile,
            names=seed_names,
            tenant_supplied=True,
        )
        results: list[SeedResult] = []
        current: SeedDefinition | None = None
        started_at = datetime.now(UTC)
        try:
            for current in definitions:
                started_at = datetime.now(UTC)
                mutation = current.handler(
                    SeedContext(
                        session=session,
                        profile=resolved_profile,
                        tenant=tenant,
                        dry_run=dry_run,
                    )
                )
                session.flush()
                result = self._result(current, mutation, tenant, dry_run=dry_run)
                results.append(result)
                session.add(
                    SeedHistory(
                        seed_name=current.name,
                        seed_version=current.version,
                        profile=resolved_profile.value,
                        scope=current.scope.value,
                        tenant_id=(
                            tenant.store_id
                            if current.scope.value == "tenant"
                            else None
                        ),
                        status=result.status.value,
                        summary=self._history_summary(result),
                        started_at=started_at,
                        completed_at=datetime.now(UTC),
                    )
                )
                session.flush()
        except Exception as exc:
            if current is None:
                raise
            failed = SeedResult(
                seed_name=current.name,
                seed_version=current.version,
                status=SeedStatus.FAILED,
                scope=current.scope,
                tenant_slug=tenant.store_slug,
                dry_run=dry_run,
                summary={"error_type": type(exc).__name__},
            )
            report = SeedReport(
                profile=resolved_profile,
                dry_run=dry_run,
                results=(*results, failed),
            )
            raise SeedExecutionError(current.name, failed, report) from exc
        return SeedReport(
            profile=resolved_profile,
            dry_run=dry_run,
            results=tuple(results),
        )

    def _run_dry_run(
        self,
        definitions: tuple[SeedDefinition, ...],
        profile: SeedProfile,
        tenant: TenantContext | None,
    ) -> tuple[SeedResult, ...]:
        """Run the selected dependency chain in one transaction, then roll it back."""

        session = self._sessions()
        transaction = session.begin()
        results: list[SeedResult] = []
        current: SeedDefinition | None = None
        try:
            for current in definitions:
                mutation = current.handler(
                    SeedContext(session=session, profile=profile, tenant=tenant, dry_run=True)
                )
                session.flush()
                results.append(self._result(current, mutation, tenant, dry_run=True))
            transaction.rollback()
            return tuple(results)
        except Exception as exc:
            transaction.rollback()
            if current is None:
                raise
            failed = SeedResult(
                seed_name=current.name,
                seed_version=current.version,
                status=SeedStatus.FAILED,
                scope=current.scope,
                tenant_slug=tenant.store_slug if tenant else None,
                dry_run=True,
                summary={"error_type": type(exc).__name__},
            )
            report = SeedReport(
                profile=profile,
                dry_run=True,
                results=(*results, failed),
            )
            raise SeedExecutionError(current.name, failed, report) from exc
        finally:
            session.close()

    def _resolve_tenant(self, tenant_slug: str) -> TenantContext:
        with self._sessions() as session:
            try:
                return resolve_explicit_internal_tenant(
                    session,
                    tenant_slug,
                    trusted=True,
                    actor_id="seed-runner",
                )
            except TenantResolutionError as exc:
                raise SeedValidationError(
                    f"tenant {tenant_slug!r} does not exist or is not active"
                ) from exc

    def _run_one(
        self,
        definition: SeedDefinition,
        profile: SeedProfile,
        tenant: TenantContext | None,
    ) -> SeedResult:
        started_at = datetime.now(UTC)
        for attempt in range(2):
            session = self._sessions()
            try:
                transaction = session.begin()
                mutation = definition.handler(
                    SeedContext(
                        session=session,
                        profile=profile,
                        tenant=tenant,
                        dry_run=False,
                    )
                )
                session.flush()
                completed_at = datetime.now(UTC)
                result = self._result(definition, mutation, tenant, dry_run=False)
                session.add(
                    SeedHistory(
                        seed_name=definition.name,
                        seed_version=definition.version,
                        profile=profile.value,
                        scope=definition.scope.value,
                        tenant_id=tenant.store_id if tenant else None,
                        status=result.status.value,
                        summary=self._history_summary(result),
                        started_at=started_at,
                        completed_at=completed_at,
                    )
                )
                transaction.commit()
                return result
            except IntegrityError as exc:
                session.rollback()
                if attempt == 0:
                    continue
                return self._fail(definition, profile, tenant, started_at, exc)
            except Exception as exc:
                session.rollback()
                return self._fail(definition, profile, tenant, started_at, exc)
            finally:
                session.close()
        raise AssertionError("unreachable seed retry state")

    def _fail(
        self,
        definition: SeedDefinition,
        profile: SeedProfile,
        tenant: TenantContext | None,
        started_at: datetime,
        error: Exception,
    ) -> SeedResult:
        result = SeedResult(
            seed_name=definition.name,
            seed_version=definition.version,
            status=SeedStatus.FAILED,
            scope=definition.scope,
            tenant_slug=tenant.store_slug if tenant else None,
            dry_run=False,
            summary={"error_type": type(error).__name__},
        )
        with self._sessions.begin() as session:
            session.add(
                SeedHistory(
                    seed_name=definition.name,
                    seed_version=definition.version,
                    profile=profile.value,
                    scope=definition.scope.value,
                    tenant_id=tenant.store_id if tenant else None,
                    status=SeedStatus.FAILED.value,
                    summary={"error_type": type(error).__name__},
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                )
            )
        raise SeedExecutionError(definition.name, result) from error

    @staticmethod
    def _result(
        definition: SeedDefinition,
        mutation: SeedMutation,
        tenant: TenantContext | None,
        *,
        dry_run: bool,
    ) -> SeedResult:
        return SeedResult(
            seed_name=definition.name,
            seed_version=definition.version,
            status=mutation.status,
            scope=definition.scope,
            tenant_slug=tenant.store_slug if tenant else None,
            dry_run=dry_run,
            created=mutation.created,
            updated=mutation.updated,
            unchanged=mutation.unchanged,
            skipped=mutation.skipped,
            summary=SeedRunner._safe_summary(mutation.summary),
        )

    @staticmethod
    def _history_summary(result: SeedResult) -> dict[str, object]:
        return {
            "created": result.created,
            "updated": result.updated,
            "unchanged": result.unchanged,
            "skipped": result.skipped,
            **result.summary,
        }

    @staticmethod
    def _safe_summary(summary: dict[str, object]) -> dict[str, object]:
        safe: dict[str, object] = {}
        sensitive_markers = ("secret", "password", "token", "credential", "database_url")
        for key, value in summary.items():
            normalized = str(key).lower()
            if any(marker in normalized for marker in sensitive_markers):
                safe[str(key)] = "[redacted]"
            elif isinstance(value, (bool, int, float)) or value is None:
                safe[str(key)] = value
            elif isinstance(value, str):
                safe[str(key)] = value[:200]
            else:
                safe[str(key)] = str(value)[:200]
        return safe
