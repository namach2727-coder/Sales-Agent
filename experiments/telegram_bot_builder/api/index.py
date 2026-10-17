"""Vercel UAT entrypoint: loads only the isolated TelBot FastAPI module."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_spec = importlib.util.spec_from_file_location("telbot_qa_runtime", _ROOT / "api.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("TelBot UAT backend module missing")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
app = _module.app
