"""ASGI entrypoint for DirectPilot FastAPI on Vercel.

The production API is a separate project from UAT; hosting secrets are set
through Vercel and never committed to this repository.
"""

from app.main import app
