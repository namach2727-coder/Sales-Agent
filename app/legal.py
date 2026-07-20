from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(include_in_schema=False)
STATIC_DIR = Path(__file__).parent / "static"


@router.get("/privacy", response_class=FileResponse)
def privacy_policy() -> FileResponse:
    return FileResponse(STATIC_DIR / "privacy.html")


@router.get("/data-deletion", response_class=FileResponse)
def data_deletion() -> FileResponse:
    return FileResponse(STATIC_DIR / "data_deletion.html")
