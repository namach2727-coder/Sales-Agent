from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.catalog_text import normalize_catalog_text, phrase_is_present
from app.models import (
    CatalogProduct,
    KnowledgeItem,
    KnowledgeVersion,
    Product,
    Store,
)


@dataclass(frozen=True)
class ProductResolution:
    managed: bool
    product: Product | None = None
    ambiguous: bool = False
    candidates: tuple[Product, ...] = ()
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class _TermHit:
    catalog_product: CatalogProduct
    term: str
    priority: int


def _active_version_id(
    db: Session, store_slug: str
) -> tuple[bool, int | None]:
    store = db.scalar(select(Store).where(Store.slug == store_slug))
    if store is None:
        return store_slug != "default", None
    if store.active_version_id is None:
        # Only the historical default demo has a global legacy catalog.
        # A future tenant without a publication must not see another catalog.
        if store_slug != "default":
            return True, None
        return False, None

    # active_version_id intentionally remains a simple pointer. Verify ownership
    # on every read so a corrupt or stale pointer cannot expose another store.
    version_id = db.scalar(
        select(KnowledgeVersion.id).where(
            KnowledgeVersion.id == store.active_version_id,
            KnowledgeVersion.store_id == store.id,
        )
    )
    if version_id is None:
        return True, None
    return True, version_id


def _load_catalog_products(db: Session, version_id: int) -> list[CatalogProduct]:
    return list(
        db.scalars(
            select(CatalogProduct)
            .options(
                joinedload(CatalogProduct.product),
                joinedload(CatalogProduct.category),
                selectinload(CatalogProduct.aliases),
            )
            .where(CatalogProduct.knowledge_version_id == version_id)
            .order_by(CatalogProduct.sort_order, CatalogProduct.id)
        ).all()
    )


def _term_in_message(message: str, term: str) -> bool:
    if not message or not term:
        return False
    return phrase_is_present(message, term)


def _unique_products(
    catalog_products: list[CatalogProduct], product_ids: set[int]
) -> tuple[Product, ...]:
    products: list[Product] = []
    seen: set[int] = set()
    for catalog_product in catalog_products:
        product = catalog_product.product
        if product.id in product_ids and product.id not in seen:
            products.append(product)
            seen.add(product.id)
    return tuple(products)


def _dominant_alias_product(hits: list[_TermHit]) -> int | None:
    """Resolve an explicit full alias that contains every competing alias."""
    dominant_product_ids: set[int] = set()
    for hit in hits:
        if all(_term_in_message(hit.term, other.term) for other in hits):
            dominant_product_ids.add(hit.catalog_product.product_id)
    if len(dominant_product_ids) == 1:
        return next(iter(dominant_product_ids))
    return None


def resolve_product(
    db: Session, message: str, store_slug: str = "default"
) -> ProductResolution:
    managed, version_id = _active_version_id(db, store_slug)
    if not managed:
        return ProductResolution(managed=False)
    if version_id is None:
        return ProductResolution(managed=True)

    normalized_message = normalize_catalog_text(message)
    catalog_products = _load_catalog_products(db, version_id)
    alias_hits: list[_TermHit] = []
    category_product_ids: set[int] = set()
    category_terms: set[str] = set()

    for catalog_product in catalog_products:
        # A canonical name remains matchable even if a malformed publication
        # omitted its canonical ProductAlias row.
        terms: dict[str, int] = {normalize_catalog_text(catalog_product.name): 10}
        for alias in catalog_product.aliases:
            term = normalize_catalog_text(alias.value)
            if term:
                terms[term] = min(terms.get(term, alias.priority), alias.priority)

        for term, priority in terms.items():
            if term and _term_in_message(normalized_message, term):
                alias_hits.append(
                    _TermHit(
                        catalog_product=catalog_product,
                        term=term,
                        priority=priority,
                    )
                )

        if catalog_product.category is not None:
            category_values = [catalog_product.category.name]
            category_values.extend(catalog_product.category.name.split("/"))
            for category_value in category_values:
                category_term = normalize_catalog_text(category_value)
                if category_term and _term_in_message(normalized_message, category_term):
                    category_product_ids.add(catalog_product.product_id)
                    category_terms.add(category_term)

    if alias_hits:
        highest_priority = min(hit.priority for hit in alias_hits)
        strongest_hits = [
            hit for hit in alias_hits if hit.priority == highest_priority
        ]
        product_ids = {
            hit.catalog_product.product_id for hit in strongest_hits
        }

        if len(product_ids) > 1 and category_product_ids:
            narrowed = product_ids & category_product_ids
            if narrowed:
                product_ids = narrowed

        if len(product_ids) > 1:
            dominant_product_id = _dominant_alias_product(strongest_hits)
            if dominant_product_id in product_ids:
                product_ids = {dominant_product_id}

        candidates = _unique_products(catalog_products, product_ids)
        matched_terms = tuple(
            sorted({hit.term for hit in strongest_hits}, key=lambda item: (-len(item), item))
        )
        if len(candidates) == 1:
            return ProductResolution(
                managed=True,
                product=candidates[0],
                candidates=candidates,
                matched_terms=matched_terms,
            )
        return ProductResolution(
            managed=True,
            ambiguous=bool(candidates),
            candidates=candidates,
            matched_terms=matched_terms,
        )

    if category_product_ids:
        candidates = _unique_products(catalog_products, category_product_ids)
        if len(candidates) == 1:
            return ProductResolution(
                managed=True,
                product=candidates[0],
                candidates=candidates,
                matched_terms=tuple(sorted(category_terms)),
            )
        return ProductResolution(
            managed=True,
            ambiguous=bool(candidates),
            candidates=candidates,
            matched_terms=tuple(sorted(category_terms)),
        )

    return ProductResolution(managed=True)


def list_products(
    db: Session, store_slug: str = "default"
) -> tuple[bool, list[Product]]:
    managed, version_id = _active_version_id(db, store_slug)
    if not managed:
        return False, list(db.scalars(select(Product).order_by(Product.id)).all())
    if version_id is None:
        return True, []

    catalog_products = _load_catalog_products(db, version_id)
    return True, list(
        _unique_products(
            catalog_products,
            {catalog_product.product_id for catalog_product in catalog_products},
        )
    )


def find_knowledge_answer(
    db: Session, message: str, store_slug: str = "default"
) -> tuple[bool, str | None]:
    managed, version_id = _active_version_id(db, store_slug)
    if not managed:
        return False, None
    if version_id is None:
        return True, None

    normalized_message = normalize_catalog_text(message)
    items = db.scalars(
        select(KnowledgeItem)
        .where(
            KnowledgeItem.knowledge_version_id == version_id,
            KnowledgeItem.kind.in_(("faq", "rule")),
        )
        .order_by(KnowledgeItem.priority, KnowledgeItem.id)
    ).all()

    matches: list[tuple[int, int, int, int, str]] = []
    for item in items:
        terms = {normalize_catalog_text(item.title)}
        if isinstance(item.keywords, list):
            terms.update(
                normalize_catalog_text(keyword)
                for keyword in item.keywords
                if isinstance(keyword, str)
            )
        matched = [
            term for term in terms if term and _term_in_message(normalized_message, term)
        ]
        if not matched:
            continue
        most_specific = max(matched, key=lambda term: (len(term.split()), len(term)))
        matches.append(
            (
                item.priority,
                -len(most_specific.split()),
                -len(most_specific),
                item.id,
                item.answer,
            )
        )

    if not matches:
        return True, None
    return True, min(matches)[-1]
