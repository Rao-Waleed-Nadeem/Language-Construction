"""Documentation API routes.

Safely serves docs/*.md specification files to the frontend Reference and Documentation views.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import DocDetail

router = APIRouter(prefix="/api/docs", tags=["docs"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DOCS_DIR = ROOT_DIR / "docs"


@router.get("", response_model=list[dict[str, str]])
def list_docs() -> list[dict[str, str]]:
    """List all available documentation specification markdown files."""
    items: list[dict[str, str]] = []
    if DOCS_DIR.exists():
        for p in sorted(DOCS_DIR.glob("*.md")):
            items.append(
                {"name": p.stem, "filename": p.name, "title": p.stem.replace("_", " ").title()}
            )
    return items


@router.get("/{name}", response_model=DocDetail)
def get_doc(name: str) -> DocDetail:
    """Serve markdown text of a specific documentation file."""
    # Prevent directory traversal attacks
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid document name")

    path = DOCS_DIR / f"{name}.md"
    if not path.exists():
        path = DOCS_DIR / name
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Document '{name}' not found")

    content = path.read_text(encoding="utf-8")
    title = name.replace("_", " ").title()
    # Extract first header if present
    for line in content.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    return DocDetail(name=name, title=title, content=content)
