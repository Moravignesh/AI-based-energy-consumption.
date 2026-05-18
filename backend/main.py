# Root entry-point — allows running from the backend/ directory with:
#   uvicorn main:app --reload --port 8000
# The real application lives in app/main.py
from app.main import app  # noqa: F401 — re-export for uvicorn

__all__ = ["app"]
