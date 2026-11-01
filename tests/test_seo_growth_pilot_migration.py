from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import Store, Tenant


def test_revision_upgrade_preserves_existing_pilot_terms_and_blocks_evidence_loss(tmp_path):
    database = tmp_path / "pilot-migration.db"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database}"
    command.upgrade(config, "0028_seo_google_onboarding")
    engine = create_engine(config.attributes["database_url"])
    with Session(engine) as db:
        tenant = Tenant(name="Migration Fixture", slug="migration-fixture", status="active")
        db.add(tenant); db.flush()
        store = Store(tenant_id=tenant.id, name="Migration Workspace", slug="migration-workspace", status="active")
        db.add(store); db.flush()
        db.execute(text("""INSERT INTO seo_access_grants
            (tenant_id, store_id, status, max_sites, max_connections, expires_at, created_at)
            VALUES (:tenant, :store, 'active', 3, 2, :expires, :created)"""),
            {"tenant": tenant.id, "store": store.id, "expires": datetime.now(UTC) + timedelta(days=10), "created": datetime.now(UTC)})
        db.commit()
    columns = "tenant_id, store_id, status, max_sites, max_connections, expires_at, created_at"
    with engine.connect() as db:
        before = tuple(db.execute(text(f"SELECT {columns} FROM seo_access_grants")).one())
    command.upgrade(config, "head")
    with engine.connect() as db:
        assert tuple(db.execute(text(f"SELECT {columns} FROM seo_access_grants")).one()) == before
        assert db.scalar(text("SELECT revision FROM seo_access_grants")) == 1
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0029_seo_pilot_revision"
    with pytest.raises(RuntimeError, match="SEO pilot revision evidence"):
        command.downgrade(config, "0028_seo_google_onboarding")
    with engine.connect() as db:
        assert db.scalar(text("SELECT revision FROM seo_access_grants")) == 1
    engine.dispose()
