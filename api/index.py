"""ASGI entrypoint for isolated DirectPilot Vercel UAT evaluation.

Importing the existing FastAPI instance avoids diverging route definitions.
The UAT deployment must provide environment settings and database credentials
through its hosting configuration; no credentials belong in this file.
"""

from app.main import app
