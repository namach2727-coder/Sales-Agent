from __future__ import annotations

import argparse
import os

import httpx


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run non-destructive deployment smoke tests")
    result.add_argument("--base-url", default=os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000"))
    result.add_argument("--email", default=os.getenv("SMOKE_ADMIN_EMAIL"))
    result.add_argument("--password-env", default="SMOKE_ADMIN_PASSWORD")
    result.add_argument("--expect-empty-catalog", action="store_true")
    result.add_argument(
        "--forwarded-proto",
        default=os.getenv("SMOKE_FORWARDED_PROTO"),
        choices=("http", "https"),
        help="Optional X-Forwarded-Proto header for local smoke testing.",
    )
    return result


def _require(response: httpx.Response, status: int, label: str) -> None:
    if response.status_code != status:
        raise RuntimeError(f"{label} failed with HTTP {response.status_code}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    password = os.getenv(args.password_env)
    if not args.email or not password:
        print("ERROR smoke identity email/password environment is required")
        return 2
    try:
        headers = (
            {"X-Forwarded-Proto": args.forwarded_proto}
            if args.forwarded_proto
            else None
        )
        with httpx.Client(
            base_url=args.base_url,
            timeout=15.0,
            follow_redirects=False,
            headers=headers,
        ) as client:
            _require(client.get("/live"), 200, "liveness")
            _require(client.get("/ready"), 200, "readiness")
            _require(client.get("/version"), 200, "version")
            _require(client.get("/admin/api/provider/stores"), 401, "anonymous RBAC rejection")
            login = client.post("/auth/login", json={"email": args.email, "password": password})
            _require(login, 200, "login")
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            _require(client.get("/auth/me", headers=headers), 200, "principal resolution")
            _require(client.get("/admin/api/provider/stores", headers=headers), 200, "platform RBAC")
            if args.expect_empty_catalog:
                products = client.get("/products").json()
                if products:
                    raise RuntimeError("isolated deployment unexpectedly contains demo products")
            _require(client.post("/auth/logout", headers=headers), 200, "logout")
            _require(client.get("/auth/me", headers=headers), 401, "session revocation")
        print("Deployment smoke tests passed.")
        return 0
    except Exception as exc:
        print(f"ERROR deployment smoke tests failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
