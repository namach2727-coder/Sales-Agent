"""Run the temporary Pinggy tunnel as a detached local helper.

This process exposes only the restricted Instagram webhook gateway on
127.0.0.1:8001. It writes the current public URLs and its PID to a small
runtime JSON file so the local setup can report the active callback URL.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
PINGGY_PACKAGE_DIR = TOOLS_DIR / "pinggy-python"
STATE_FILE = TOOLS_DIR / "pinggy-current.json"

sys.path.insert(0, str(PINGGY_PACKAGE_DIR))

import pinggy  # noqa: E402


def main() -> None:
    tunnel = pinggy.start_tunnel(
        forwardto="127.0.0.1:8001",
        httpsonly=True,
        # A reconnect creates a different free hostname. Keep one stable
        # hostname for the short Meta verification session instead.
        autoreconnect=False,
    )
    state = {"pid": os.getpid(), "urls": tunnel.urls}
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    tunnel.wait()


if __name__ == "__main__":
    main()
