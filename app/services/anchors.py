from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List
import json
import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

# ---- In-memory caches ----
_ANCHORS: Dict[str, "Anchor"] = {}   # normal anchors
_GHOSTS: Dict[str, "Anchor"] = {}    # ghost templates


# ---- File schema ----
class AnchorDoc(BaseModel):
    version: int = 1
    slug: str
    title: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)

    # Normal vs Ghost
    is_ghost: bool = False
    min_size: Optional[int] = None    # required for normal
    max_size: Optional[int] = None    # required for normal
    join_window_min: Optional[int] = None     # ghosts only (defaulted)
    notify_template: Optional[str] = None     # ghosts only

    # Vectors
    raw_dim: int = 384
    raw_vec_file: Optional[str] = None

    reduced_dim: int = Field(default_factory=lambda: settings.VECTOR_DIM)
    reduced_vec_file: Optional[str] = None
    reducer_id: Optional[str] = None

    # Instructions
    instructions_url: Optional[str] = None       # external URL (preferred if set)
    instructions_html: Optional[str] = None      # local file path like "static/anchors/foo.html"


class Anchor(BaseModel):
    slug: str
    title: str
    description: str
    tags: List[str]
    reduced: List[float]          # len == settings.VECTOR_DIM (may be empty if not provided)
    meta: dict                    # includes sizes, ghost flags, instructions, etc.


# ---- Loader helpers ----
def _read_json_floats(path: Path) -> List[float]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return [float(x) for x in data]


def load_anchors(dir_path: str = "data/anchors") -> dict[str, Anchor]:
    base = Path(dir_path)
    if not base.exists():
        # No anchors dir yet; clear caches and return empty
        _publish({}, {})
        return {}

    normals: Dict[str, Anchor] = {}
    ghosts: Dict[str, Anchor] = {}

    for yml in sorted(base.glob("*.yaml")):
        raw = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        try:
            doc = AnchorDoc.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(f"Invalid anchor doc {yml}: {e}") from e

        # Reduced vector (optional but validated if present)
        reduced: List[float] = []
        if doc.reduced_vec_file:
            vec_path = Path(doc.reduced_vec_file)
            if not vec_path.exists():
                raise RuntimeError(f"{doc.slug}: missing reduced_vec_file: {vec_path}")
            reduced = _read_json_floats(vec_path)
            if len(reduced) != doc.reduced_dim:
                raise RuntimeError(f"{doc.slug}: reduced_vec length {len(reduced)} != {doc.reduced_dim}")
            if doc.reduced_dim != settings.VECTOR_DIM:
                raise RuntimeError(
                    f"{doc.slug}: reduced_dim {doc.reduced_dim} != settings.VECTOR_DIM {settings.VECTOR_DIM}"
                )

        # Sizes
        if doc.is_ghost:
            mn = doc.min_size or 2
            mx = doc.max_size or 4
            join_window = doc.join_window_min or 15
        else:
            if doc.min_size is None or doc.max_size is None:
                raise RuntimeError(f"{doc.slug}: normal anchors require min_size and max_size")
            mn, mx = doc.min_size, doc.max_size
            join_window = None

        if mn < 1 or mx < mn:
            raise RuntimeError(f"{doc.slug}: invalid size range (min={mn}, max={mx})")

        meta = {
            "is_ghost": doc.is_ghost,
            "min_size": mn,
            "max_size": mx,
            "join_window_min": join_window,
            "notify_template": doc.notify_template or (
                "{initiator_username} wants '{anchor_title}' ({min_size}-{max_size}). Join?"
                if doc.is_ghost else None
            ),
            "reducer_id": doc.reducer_id,
            "raw_vec_file": doc.raw_vec_file,
            "raw_dim": doc.raw_dim,
            "reduced_vec_file": doc.reduced_vec_file,
            "reduced_dim": doc.reduced_dim,
            "instructions_url": doc.instructions_url,
            "instructions_html": doc.instructions_html,
            "source": str(yml),
        }

        anchor = Anchor(
            slug=doc.slug,
            title=doc.title,
            description=doc.description,
            tags=doc.tags,
            reduced=reduced,
            meta=meta,
        )

        if doc.is_ghost:
            ghosts[doc.slug] = anchor
        else:
            normals[doc.slug] = anchor

    _publish(normals, ghosts)
    return normals


def _publish(normals: Dict[str, Anchor], ghosts: Dict[str, Anchor]) -> None:
    global _ANCHORS, _GHOSTS
    _ANCHORS, _GHOSTS = normals, ghosts


# ---- Read API for the rest of the app ----
def list_anchors() -> List[Anchor]:
    return list(_ANCHORS.values())


def get_anchor(slug: str) -> Optional[Anchor]:
    return _ANCHORS.get(slug)


def list_ghosts() -> List[Anchor]:
    return list(_GHOSTS.values())


def get_ghost(slug: str) -> Optional[Anchor]:
    return _GHOSTS.get(slug)
