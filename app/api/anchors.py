from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query
from app.services.anchors import list_anchors, get_anchor, list_ghosts, get_ghost

router = APIRouter(tags=["anchors"])

def _build_instructions_url(meta: dict, request: Request) -> Optional[str]:
    if meta.get("instructions_url"):
        return meta["instructions_url"]
    html_path = meta.get("instructions_html")
    if not html_path:
        return None
    rel = html_path.split("static/", 1)[-1] if "static/" in html_path else html_path
    return str(request.url_for("static", path=rel))

def _anchor_summary(a, request: Request):
    return {
        "slug": a.slug,
        "title": a.title,
        "tags": a.tags,
        "min_size": a.meta.get("min_size"),
        "max_size": a.meta.get("max_size"),
        "instructions_url": _build_instructions_url(a.meta, request),
        "is_ghost": bool(a.meta.get("is_ghost")),
    }

# ---------- Normal anchors ----------
@router.get("/anchors")
def anchors_index(request: Request):
    return [_anchor_summary(a, request) for a in list_anchors()]

@router.get("/anchor/{slug}")
def anchor_detail(
    slug: str,
    request: Request,
    include_reduced: bool = Query(False, description="Include reduced vector floats"),
    include_html: bool = Query(False, description="Inline instructions HTML if available"),
):
    a = get_anchor(slug)
    if not a:
        raise HTTPException(status_code=404, detail="anchor not found")
    resp = {
        "slug": a.slug,
        "title": a.title,
        "description": a.description,
        "tags": a.tags,
        "min_size": a.meta.get("min_size"),
        "max_size": a.meta.get("max_size"),
        "instructions_url": _build_instructions_url(a.meta, request),
        "is_ghost": False,
        "meta": {
            "reducer_id": a.meta.get("reducer_id"),
            "source": a.meta.get("source"),
        },
    }
    if include_reduced:
        resp["reduced"] = a.reduced
    if include_html and a.meta.get("instructions_html"):
        try:
            from pathlib import Path
            resp["instructions_html"] = Path(a.meta["instructions_html"]).read_text(encoding="utf-8")
        except FileNotFoundError:
            resp["instructions_html"] = None
    return resp

# ---------- Ghost anchors (templates) ----------
@router.get("/ghost-anchors")
def ghosts_index(request: Request):
    out = []
    for a in list_ghosts():
        row = _anchor_summary(a, request)
        row["join_window_min"] = a.meta.get("join_window_min")
        out.append(row)
    return out

@router.get("/ghost-anchors/{slug}")
def ghost_detail(
    slug: str,
    request: Request,
    include_reduced: bool = Query(False),
    include_html: bool = Query(False),
):
    a = get_ghost(slug)
    if not a:
        raise HTTPException(status_code=404, detail="ghost anchor not found")
    resp = {
        "slug": a.slug,
        "title": a.title,
        "description": a.description,
        "tags": a.tags,
        "min_size": a.meta.get("min_size"),
        "max_size": a.meta.get("max_size"),
        "join_window_min": a.meta.get("join_window_min"),
        "notify_template": a.meta.get("notify_template"),
        "instructions_url": _build_instructions_url(a.meta, request),
        "is_ghost": True,
        "meta": {
            "reducer_id": a.meta.get("reducer_id"),
            "source": a.meta.get("source"),
        },
    }
    if include_reduced:
        resp["reduced"] = a.reduced
    if include_html and a.meta.get("instructions_html"):
        try:
            from pathlib import Path
            resp["instructions_html"] = Path(a.meta["instructions_html"]).read_text(encoding="utf-8")
        except FileNotFoundError:
            resp["instructions_html"] = None
    return resp
