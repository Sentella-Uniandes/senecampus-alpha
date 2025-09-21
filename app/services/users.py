import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import select, func

from app.core.config import settings
from app.models.user import User
from app.models.vector import Vector

# -------- helpers --------

def username_from_email(email: str) -> str:
    return email.split("@", 1)[0].strip().lower()

def _ensure_vector_dim(data: list[float]) -> None:
    if len(data) != settings.VECTOR_DIM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Vector length {len(data)} != expected {settings.VECTOR_DIM}",
        )

def _pack_int8_normalized(vec_f32: list[float], *, renorm_tolerance: float = 1e-6) -> bytes:
    """
    Assumes the intent is L2-normalized input. We gently renormalize to be robust:
      - if norm == 0 -> 422
      - else vec := vec / norm
    Then quantize with fixed mapping: q = round(127 * vec), clamped to [-127, 127].
    """
    arr = np.asarray(vec_f32, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm == 0.0:
        raise HTTPException(status_code=422, detail="Zero-norm vector is not allowed")
    if abs(norm - 1.0) > renorm_tolerance:
        arr = arr / norm  # gentle renorm; keeps contract "normalized"
    q = np.clip(np.round(arr * 127.0), -127, 127).astype(np.int8)
    return q.tobytes()

def _create_vector(db: Session, vec_f32: list[float]) -> Vector:
    _ensure_vector_dim(vec_f32)
    blob = _pack_int8_normalized(vec_f32)
    vec = Vector(dim=len(vec_f32), data=blob)
    if len(blob) != vec.dim:
        # 1 byte per dim invariant
        raise HTTPException(status_code=500, detail="packed vector size mismatch")
    db.add(vec)
    db.flush()
    return vec

# -------- CRUD unchanged below (uses _create_vector) --------

def create_user(db: Session, email: str, first_name: str | None,
                vector_id: int | None, vector_data: list[float] | None) -> User:
    username = username_from_email(email)
    exists = db.scalar(select(func.count()).select_from(User).where(User.username == username))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

    vec_obj: Vector | None = None
    if vector_id is not None and vector_data is not None:
        raise HTTPException(status_code=400, detail="Provide either vector_id or vector, not both")

    if vector_id is not None:
        vec_obj = db.get(Vector, vector_id)
        if not vec_obj:
            raise HTTPException(status_code=404, detail="vector not found")
        if vec_obj.dim != settings.VECTOR_DIM:
            raise HTTPException(status_code=422, detail="vector dimension mismatch")

    if vector_data is not None:
        vec_obj = _create_vector(db, vector_data)

    user = User(username=username, first_name=first_name, vector=vec_obj)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_users(db: Session, offset: int, limit: int):
    total = db.scalar(select(func.count()).select_from(User)) or 0
    items = db.scalars(select(User).order_by(User.id).offset(offset).limit(limit)).all()
    return items, total

def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

def get_user_by_username(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

def update_user(db: Session, user_id: int, first_name: str | None) -> User:
    user = get_user(db, user_id)
    if first_name is not None:
        user.first_name = first_name
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()

def attach_vector(db: Session, user_id: int, vector_id: int | None, vector_data: list[float] | None) -> User:
    user = get_user(db, user_id)
    if (vector_id is None) == (vector_data is None):
        raise HTTPException(status_code=400, detail="Provide either vector_id or vector")

    if vector_id is not None:
        vec = db.get(Vector, vector_id)
        if not vec:
            raise HTTPException(status_code=404, detail="vector not found")
        if vec.dim != settings.VECTOR_DIM:
            raise HTTPException(status_code=422, detail="vector dimension mismatch")
        user.vector = vec
    else:
        vec = _create_vector(db, vector_data or [])
        user.vector = vec

    db.commit()
    db.refresh(user)
    return user

def unpack_int8_to_unit_float(blob: bytes) -> np.ndarray:
    q = np.frombuffer(blob, dtype=np.int8).astype(np.float32)
    return q / 127.0  # approximately unit-norm again