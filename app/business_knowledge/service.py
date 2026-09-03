"""Tenant- and Store-bound application service for business knowledge."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.business_knowledge.domain import (
    READABLE_STORE_STATUSES,
    WRITABLE_STORE_STATUSES,
    BusinessKnowledgeConflictError,
    BusinessKnowledgeError,
    BusinessKnowledgeInvalidTransitionError,
    BusinessKnowledgeNotFoundError,
    BusinessKnowledgeStaleWriteError,
    BusinessKnowledgeStoreStateError,
    BusinessKnowledgeValidationError,
    normalize_code,
    normalize_content,
    normalize_display_text,
    normalize_email,
    normalize_entry_type,
    normalize_keywords,
    normalize_optional_content,
    normalize_optional_display_text,
    normalize_phone,
    normalize_policy_type,
    normalize_priority,
    normalize_question,
    normalize_slug,
    normalize_url,
    validate_transition,
)
from app.business_knowledge.industry import (
    CUSTOMER_PROVENANCE,
    INDUSTRY_PROFILE_SLUG,
    serialize_industry_profile,
)
from app.business_knowledge.models import (
    BusinessFAQ,
    BusinessKnowledgeEntry,
    BusinessPolicy,
    BusinessProfile,
)
from app.models import TenantAuditLog, utc_now


KnowledgeModel = TypeVar(
    "KnowledgeModel",
    BusinessProfile,
    BusinessPolicy,
    BusinessFAQ,
    BusinessKnowledgeEntry,
)


class BusinessKnowledgePermissionError(BusinessKnowledgeError):
    code = "permission_denied"


class BusinessKnowledgeService:
    """Owns store knowledge invariants and one transaction per mutation."""

    def __init__(
        self,
        session: Session,
        *,
        tenant_id: int,
        store_id: int,
        tenant_status: str,
        store_status: str,
        actor_identity_id: int | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.store_id = store_id
        self.tenant_status = tenant_status
        self.store_status = store_status
        self.actor_identity_id = actor_identity_id

    def _ensure_readable(self) -> None:
        if self.tenant_status != "active":
            raise BusinessKnowledgeStoreStateError("tenant is not active")
        if self.store_status in {"archived", "deleted"}:
            raise BusinessKnowledgeNotFoundError("resource not found")
        if self.store_status not in READABLE_STORE_STATUSES:
            raise BusinessKnowledgeStoreStateError("store is not readable")

    def _ensure_writable(self) -> None:
        self._ensure_readable()
        if self.store_status not in WRITABLE_STORE_STATUSES:
            raise BusinessKnowledgeStoreStateError("store is not writable")

    def _audit(
        self,
        *,
        action: str,
        target_type: str,
        target_public_id: str,
        details: dict[str, object],
    ) -> None:
        self.session.add(
            TenantAuditLog(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                actor_identity_id=self.actor_identity_id,
                action=action,
                target_type=target_type,
                target_public_id=target_public_id,
                details_json=details,
            )
        )

    def _flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise BusinessKnowledgeConflictError(
                "business knowledge identifier already exists"
            ) from exc
        except StaleDataError as exc:
            self.session.rollback()
            raise BusinessKnowledgeStaleWriteError(
                "resource was changed by another request"
            ) from exc

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise BusinessKnowledgeConflictError(
                "business knowledge identifier already exists"
            ) from exc
        except StaleDataError as exc:
            self.session.rollback()
            raise BusinessKnowledgeStaleWriteError(
                "resource was changed by another request"
            ) from exc

    def _resource(
        self,
        model: type[KnowledgeModel],
        public_id: str,
    ) -> KnowledgeModel:
        self._ensure_readable()
        item = self.session.scalar(
            select(model).where(
                model.public_id == public_id,
                model.tenant_id == self.tenant_id,
                model.store_id == self.store_id,
            )
        )
        if item is None:
            raise BusinessKnowledgeNotFoundError("resource not found")
        return item

    @staticmethod
    def _check_create_revision(expected_revision: int) -> None:
        if expected_revision != 0:
            raise BusinessKnowledgeStaleWriteError(
                "new resources require expected_revision 0"
            )

    @staticmethod
    def _check_revision(item: KnowledgeModel, expected_revision: int) -> None:
        if item.revision != expected_revision:
            raise BusinessKnowledgeStaleWriteError(
                "resource revision does not match"
            )

    @staticmethod
    def _require_draft(item: KnowledgeModel) -> None:
        if item.status != "draft":
            raise BusinessKnowledgeConflictError(
                "only draft resources may be edited"
            )

    @staticmethod
    def _required_string(value: object, *, field: str) -> str:
        if not isinstance(value, str):
            raise BusinessKnowledgeValidationError(f"{field} cannot be null")
        return value

    @staticmethod
    def _required_integer(value: object, *, field: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise BusinessKnowledgeValidationError(f"{field} cannot be null")
        return value

    @staticmethod
    def _page(
        session: Session,
        query: Select[tuple[KnowledgeModel]],
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[KnowledgeModel], int]:
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            session.scalars(
                query.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )
        return items, total

    def create_profile(
        self,
        *,
        expected_revision: int,
        display_name: str,
        business_category: str | None = None,
        description: str | None = None,
        support_phone: str | None = None,
        support_email: str | None = None,
        website_url: str | None = None,
        address_text: str | None = None,
        working_hours_text: str | None = None,
    ) -> BusinessProfile:
        self._ensure_writable()
        self._check_create_revision(expected_revision)
        if self.session.scalar(
            select(BusinessProfile.id).where(
                BusinessProfile.tenant_id == self.tenant_id,
                BusinessProfile.store_id == self.store_id,
            )
        ) is not None:
            raise BusinessKnowledgeConflictError(
                "the Store already has a business profile"
            )
        item = BusinessProfile(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            display_name=normalize_display_text(
                display_name, field="display name", maximum=200
            ),
            business_category=normalize_optional_display_text(
                business_category, field="business category", maximum=100
            ),
            description=normalize_optional_content(
                description, field="description"
            ),
            support_phone=normalize_phone(support_phone),
            support_email=normalize_email(support_email),
            website_url=normalize_url(website_url),
            address_text=normalize_optional_content(
                address_text, field="address", maximum=4_000
            ),
            working_hours_text=normalize_optional_content(
                working_hours_text, field="working hours", maximum=4_000
            ),
        )
        self.session.add(item)
        self._flush()
        self._audit(
            action="business_profile.created",
            target_type="business_profile",
            target_public_id=item.public_id,
            details={"changed_fields": ["display_name"], "revision": item.revision},
        )
        self._commit()
        self.session.refresh(item)
        return item

    def get_profile(self) -> BusinessProfile:
        self._ensure_readable()
        item = self.session.scalar(
            select(BusinessProfile).where(
                BusinessProfile.tenant_id == self.tenant_id,
                BusinessProfile.store_id == self.store_id,
            )
        )
        if item is None:
            raise BusinessKnowledgeNotFoundError("resource not found")
        return item

    def update_profile(
        self,
        *,
        expected_revision: int,
        changes: dict[str, object],
    ) -> BusinessProfile:
        self._ensure_writable()
        item = self.get_profile()
        self._check_revision(item, expected_revision)
        self._require_draft(item)
        normalized: dict[str, object | None] = {}
        for field, value in changes.items():
            if field == "display_name":
                normalized[field] = normalize_display_text(
                    self._required_string(value, field="display name"),
                    field="display name",
                    maximum=200,
                )
            elif field == "business_category":
                normalized[field] = normalize_optional_display_text(
                    value if isinstance(value, str) else None,
                    field="business category",
                    maximum=100,
                )
            elif field == "description":
                normalized[field] = normalize_optional_content(
                    value if isinstance(value, str) else None,
                    field="description",
                )
            elif field == "support_phone":
                normalized[field] = normalize_phone(
                    value if isinstance(value, str) else None
                )
            elif field == "support_email":
                normalized[field] = normalize_email(
                    value if isinstance(value, str) else None
                )
            elif field == "website_url":
                normalized[field] = normalize_url(
                    value if isinstance(value, str) else None
                )
            elif field == "address_text":
                normalized[field] = normalize_optional_content(
                    value if isinstance(value, str) else None,
                    field="address",
                    maximum=4_000,
                )
            elif field == "working_hours_text":
                normalized[field] = normalize_optional_content(
                    value if isinstance(value, str) else None,
                    field="working hours",
                    maximum=4_000,
                )
        self._apply_update(
            item,
            normalized,
            action="business_profile.updated",
            target_type="business_profile",
        )
        return item

    def create_policy(
        self,
        *,
        expected_revision: int,
        code: str,
        policy_type: str,
        title: str,
        content: str,
        priority: int = 100,
    ) -> BusinessPolicy:
        self._ensure_writable()
        self._check_create_revision(expected_revision)
        item = BusinessPolicy(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            code=normalize_code(code),
            policy_type=normalize_policy_type(policy_type),
            title=normalize_display_text(title, field="title", maximum=200),
            content=normalize_content(content, field="content"),
            priority=normalize_priority(priority),
        )
        return self._create(
            item,
            action="business_policy.created",
            target_type="business_policy",
            changed_fields=["code", "policy_type", "title", "content", "priority"],
        )

    def get_policy(self, public_id: str) -> BusinessPolicy:
        return self._resource(BusinessPolicy, public_id)

    def update_policy(
        self,
        public_id: str,
        *,
        expected_revision: int,
        changes: dict[str, object],
    ) -> BusinessPolicy:
        self._ensure_writable()
        item = self.get_policy(public_id)
        self._check_revision(item, expected_revision)
        self._require_draft(item)
        normalized: dict[str, object] = {}
        for field, value in changes.items():
            if field == "code":
                normalized[field] = normalize_code(
                    self._required_string(value, field="code")
                )
            elif field == "policy_type":
                normalized[field] = normalize_policy_type(
                    self._required_string(value, field="policy type")
                )
            elif field == "title":
                normalized[field] = normalize_display_text(
                    self._required_string(value, field="title"),
                    field="title",
                    maximum=200,
                )
            elif field == "content":
                normalized[field] = normalize_content(
                    self._required_string(value, field="content"),
                    field="content",
                )
            elif field == "priority":
                normalized[field] = normalize_priority(
                    self._required_integer(value, field="priority")
                )
        self._apply_update(
            item,
            normalized,
            action="business_policy.updated",
            target_type="business_policy",
        )
        return item

    def list_policies(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        search: str | None = None,
        policy_type: str | None = None,
    ) -> tuple[list[BusinessPolicy], int]:
        self._ensure_readable()
        query = select(BusinessPolicy).where(
            BusinessPolicy.tenant_id == self.tenant_id,
            BusinessPolicy.store_id == self.store_id,
        )
        if status:
            query = query.where(BusinessPolicy.status == status)
        else:
            query = query.where(BusinessPolicy.status != "archived")
        if policy_type:
            query = query.where(
                BusinessPolicy.policy_type == normalize_policy_type(policy_type)
            )
        if search:
            pattern = f"%{normalize_display_text(search, field='search', maximum=200).lower()}%"
            query = query.where(
                or_(
                    func.lower(BusinessPolicy.title).like(pattern),
                    func.lower(BusinessPolicy.code).like(pattern),
                )
            )
        query = query.order_by(BusinessPolicy.priority, BusinessPolicy.id)
        return self._page(self.session, query, page=page, page_size=page_size)

    def create_faq(
        self,
        *,
        expected_revision: int,
        question: str,
        answer: str,
        keywords: list[str] | None = None,
        priority: int = 100,
    ) -> BusinessFAQ:
        self._ensure_writable()
        self._check_create_revision(expected_revision)
        display_question, normalized_question = normalize_question(question)
        item = BusinessFAQ(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            question=display_question,
            normalized_question=normalized_question,
            answer=normalize_content(answer, field="answer"),
            keywords=normalize_keywords(keywords or []),
            priority=normalize_priority(priority),
        )
        return self._create(
            item,
            action="business_faq.created",
            target_type="business_faq",
            changed_fields=["question", "answer", "keywords", "priority"],
        )

    def get_faq(self, public_id: str) -> BusinessFAQ:
        return self._resource(BusinessFAQ, public_id)

    def update_faq(
        self,
        public_id: str,
        *,
        expected_revision: int,
        changes: dict[str, object],
    ) -> BusinessFAQ:
        self._ensure_writable()
        item = self.get_faq(public_id)
        self._check_revision(item, expected_revision)
        self._require_draft(item)
        normalized: dict[str, object] = {}
        for field, value in changes.items():
            if field == "question":
                question, normalized_question = normalize_question(
                    self._required_string(value, field="question")
                )
                normalized["question"] = question
                normalized["normalized_question"] = normalized_question
            elif field == "answer":
                normalized[field] = normalize_content(
                    self._required_string(value, field="answer"),
                    field="answer",
                )
            elif field == "keywords":
                if not isinstance(value, list):
                    raise BusinessKnowledgeValidationError(
                        "keywords cannot be null"
                    )
                normalized[field] = normalize_keywords(value)
            elif field == "priority":
                normalized[field] = normalize_priority(
                    self._required_integer(value, field="priority")
                )
        self._apply_update(
            item,
            normalized,
            action="business_faq.updated",
            target_type="business_faq",
        )
        return item

    def list_faqs(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[BusinessFAQ], int]:
        self._ensure_readable()
        query = select(BusinessFAQ).where(
            BusinessFAQ.tenant_id == self.tenant_id,
            BusinessFAQ.store_id == self.store_id,
        )
        if status:
            query = query.where(BusinessFAQ.status == status)
        else:
            query = query.where(BusinessFAQ.status != "archived")
        if search:
            pattern = f"%{normalize_display_text(search, field='search', maximum=200).casefold()}%"
            query = query.where(BusinessFAQ.normalized_question.like(pattern))
        query = query.order_by(BusinessFAQ.priority, BusinessFAQ.id)
        return self._page(self.session, query, page=page, page_size=page_size)

    def create_entry(
        self,
        *,
        expected_revision: int,
        slug: str,
        entry_type: str,
        title: str,
        content: str,
        keywords: list[str] | None = None,
        priority: int = 100,
    ) -> BusinessKnowledgeEntry:
        self._ensure_writable()
        self._check_create_revision(expected_revision)
        normalized_slug = normalize_slug(slug)
        if normalized_slug == INDUSTRY_PROFILE_SLUG:
            raise BusinessKnowledgeValidationError("slug is reserved")
        item = BusinessKnowledgeEntry(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            slug=normalized_slug,
            entry_type=normalize_entry_type(entry_type),
            title=normalize_display_text(title, field="title", maximum=200),
            content=normalize_content(content, field="content"),
            keywords=normalize_keywords(keywords or []),
            priority=normalize_priority(priority),
        )
        return self._create(
            item,
            action="business_knowledge_entry.created",
            target_type="business_knowledge_entry",
            changed_fields=[
                "slug",
                "entry_type",
                "title",
                "content",
                "keywords",
                "priority",
            ],
        )

    def get_entry(self, public_id: str) -> BusinessKnowledgeEntry:
        return self._resource(BusinessKnowledgeEntry, public_id)

    def get_industry_profile(self) -> BusinessKnowledgeEntry:
        """Return the reserved industry profile entry for this store."""
        self._ensure_readable()
        item = self.session.scalar(
            select(BusinessKnowledgeEntry).where(
                BusinessKnowledgeEntry.tenant_id == self.tenant_id,
                BusinessKnowledgeEntry.store_id == self.store_id,
                BusinessKnowledgeEntry.slug == INDUSTRY_PROFILE_SLUG,
                BusinessKnowledgeEntry.status != "archived",
            )
        )
        if item is None:
            raise BusinessKnowledgeNotFoundError("industry profile not found")
        return item

    def save_industry_profile(
        self,
        *,
        expected_revision: int,
        industry_code: str,
        subcategory: str | None,
        attributes: dict[str, object],
        business_type: str | None = None,
    ) -> BusinessKnowledgeEntry:
        """Persist schema-validated industry answers without a new table."""
        self._ensure_writable()
        try:
            payload = serialize_industry_profile(
                industry_code=industry_code,
                subcategory=subcategory,
                attributes=attributes,
                business_type=business_type,
            )
        except ValueError as exc:
            raise BusinessKnowledgeValidationError(str(exc)) from exc
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        item = self.session.scalar(
            select(BusinessKnowledgeEntry).where(
                BusinessKnowledgeEntry.tenant_id == self.tenant_id,
                BusinessKnowledgeEntry.store_id == self.store_id,
                BusinessKnowledgeEntry.slug == INDUSTRY_PROFILE_SLUG,
            )
        )
        if item is None:
            if expected_revision != 0:
                raise BusinessKnowledgeStaleWriteError(
                    "new industry profiles require expected_revision 0"
                )
            item = BusinessKnowledgeEntry(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                slug=INDUSTRY_PROFILE_SLUG,
                entry_type="fact",
                title="Industry profile",
                content=content,
                keywords=[payload["industry_code"]],
                priority=0,
            )
            return self._create(
                item,
                action="business_industry_profile.created",
                target_type="business_industry_profile",
                changed_fields=["industry_code", "subcategory", "attributes"],
            )
        self._check_revision(item, expected_revision)
        self._require_draft(item)
        item.title = "Industry profile"
        item.content = content
        item.keywords = [str(payload["industry_code"])]
        item.revision += 1
        item.updated_at = utc_now()
        self._audit(
            action="business_industry_profile.updated",
            target_type="business_industry_profile",
            target_public_id=item.public_id,
            details={
                "changed_fields": ["industry_code", "subcategory", "attributes"],
                "provenance": CUSTOMER_PROVENANCE,
                "revision": item.revision,
            },
        )
        self._commit()
        self.session.refresh(item)
        return item

    def update_entry(
        self,
        public_id: str,
        *,
        expected_revision: int,
        changes: dict[str, object],
    ) -> BusinessKnowledgeEntry:
        self._ensure_writable()
        item = self.get_entry(public_id)
        self._check_revision(item, expected_revision)
        self._require_draft(item)
        normalized: dict[str, object] = {}
        for field, value in changes.items():
            if field == "slug":
                normalized_slug = normalize_slug(
                    self._required_string(value, field="slug")
                )
                if normalized_slug == INDUSTRY_PROFILE_SLUG:
                    raise BusinessKnowledgeValidationError("slug is reserved")
                normalized[field] = normalized_slug
            elif field == "entry_type":
                normalized[field] = normalize_entry_type(
                    self._required_string(value, field="entry type")
                )
            elif field == "title":
                normalized[field] = normalize_display_text(
                    self._required_string(value, field="title"),
                    field="title",
                    maximum=200,
                )
            elif field == "content":
                normalized[field] = normalize_content(
                    self._required_string(value, field="content"),
                    field="content",
                )
            elif field == "keywords":
                if not isinstance(value, list):
                    raise BusinessKnowledgeValidationError(
                        "keywords cannot be null"
                    )
                normalized[field] = normalize_keywords(value)
            elif field == "priority":
                normalized[field] = normalize_priority(
                    self._required_integer(value, field="priority")
                )
        self._apply_update(
            item,
            normalized,
            action="business_knowledge_entry.updated",
            target_type="business_knowledge_entry",
        )
        return item

    def list_entries(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        search: str | None = None,
        entry_type: str | None = None,
    ) -> tuple[list[BusinessKnowledgeEntry], int]:
        self._ensure_readable()
        query = select(BusinessKnowledgeEntry).where(
            BusinessKnowledgeEntry.tenant_id == self.tenant_id,
            BusinessKnowledgeEntry.store_id == self.store_id,
        )
        if status:
            query = query.where(BusinessKnowledgeEntry.status == status)
        else:
            query = query.where(BusinessKnowledgeEntry.status != "archived")
        if entry_type:
            query = query.where(
                BusinessKnowledgeEntry.entry_type == normalize_entry_type(entry_type)
            )
        if search:
            pattern = f"%{normalize_display_text(search, field='search', maximum=200).lower()}%"
            query = query.where(
                or_(
                    func.lower(BusinessKnowledgeEntry.title).like(pattern),
                    func.lower(BusinessKnowledgeEntry.slug).like(pattern),
                )
            )
        query = query.order_by(
            BusinessKnowledgeEntry.priority,
            BusinessKnowledgeEntry.id,
        )
        return self._page(self.session, query, page=page, page_size=page_size)

    def _create(
        self,
        item: KnowledgeModel,
        *,
        action: str,
        target_type: str,
        changed_fields: list[str],
    ) -> KnowledgeModel:
        self.session.add(item)
        self._flush()
        self._audit(
            action=action,
            target_type=target_type,
            target_public_id=item.public_id,
            details={
                "changed_fields": sorted(changed_fields),
                "revision": item.revision,
            },
        )
        self._commit()
        self.session.refresh(item)
        return item

    def _apply_update(
        self,
        item: KnowledgeModel,
        changes: dict[str, object | None],
        *,
        action: str,
        target_type: str,
    ) -> None:
        if not changes:
            raise BusinessKnowledgeValidationError(
                "at least one mutable field is required"
            )
        for field, value in changes.items():
            setattr(item, field, value)
        item.revision += 1
        item.updated_at = utc_now()
        self._audit(
            action=action,
            target_type=target_type,
            target_public_id=item.public_id,
            details={
                "changed_fields": sorted(changes),
                "status": item.status,
                "revision": item.revision,
            },
        )
        self._commit()
        self.session.refresh(item)

    @staticmethod
    def _publishable(item: KnowledgeModel) -> None:
        if isinstance(item, BusinessProfile):
            if not item.display_name.strip() or not any(
                (
                    item.business_category,
                    item.description,
                    item.support_phone,
                    item.support_email,
                    item.website_url,
                    item.address_text,
                    item.working_hours_text,
                )
            ):
                raise BusinessKnowledgeValidationError(
                    "business profile requires descriptive or contact information"
                )
        elif isinstance(item, BusinessPolicy):
            if not item.title.strip() or not item.content.strip():
                raise BusinessKnowledgeValidationError("policy is incomplete")
        elif isinstance(item, BusinessFAQ):
            if not item.question.strip() or not item.answer.strip():
                raise BusinessKnowledgeValidationError("FAQ is incomplete")
        elif isinstance(item, BusinessKnowledgeEntry):
            if not item.title.strip() or not item.content.strip():
                raise BusinessKnowledgeValidationError(
                    "knowledge entry is incomplete"
                )

    def transition(
        self,
        model: type[KnowledgeModel],
        public_id: str | None,
        *,
        expected_revision: int,
        target_status: str,
        publish_authorized: bool,
    ) -> KnowledgeModel:
        self._ensure_writable()
        if model is BusinessProfile:
            item = self.get_profile()
        else:
            assert public_id is not None
            item = self._resource(model, public_id)
        self._check_revision(item, expected_revision)
        target = validate_transition(item.status, target_status)
        if (
            item.status == "published" or target == "published"
        ) and not publish_authorized:
            raise BusinessKnowledgePermissionError(
                "knowledge.publish permission is required"
            )
        if target == "published":
            self._publishable(item)
        old_status = item.status
        now = datetime.now(UTC)
        item.status = target
        item.published_at = now if target == "published" else None
        item.archived_at = now if target == "archived" else None
        item.updated_at = now
        item.revision += 1
        target_type = {
            BusinessProfile: "business_profile",
            BusinessPolicy: "business_policy",
            BusinessFAQ: "business_faq",
            BusinessKnowledgeEntry: "business_knowledge_entry",
        }[model]
        self._audit(
            action=f"{target_type}.transitioned",
            target_type=target_type,
            target_public_id=item.public_id,
            details={
                "old_status": old_status,
                "new_status": target,
                "revision": item.revision,
            },
        )
        self._commit()
        self.session.refresh(item)
        return item
