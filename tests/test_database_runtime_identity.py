from app.config import Settings
from app.database import build_engine, database_runtime_identity


def test_database_runtime_identity_excludes_credentials() -> None:
    engine = build_engine(
        Settings(database_url="postgresql+psycopg://user:password@example.neon.tech:5432/directpilot")
    )
    try:
        identity = database_runtime_identity(engine)
    finally:
        engine.dispose()

    assert identity == {
        "driver": "postgresql+psycopg",
        "host": "example.neon.tech",
        "port": "5432",
        "database": "directpilot",
    }
    assert "password" not in str(identity)
