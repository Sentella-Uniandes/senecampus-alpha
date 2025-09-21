import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.vector import Vector

def pack_int8(vec_f32: list[float]) -> bytes:
    arr = np.asarray(vec_f32, dtype=np.float32)
    q = np.clip(np.round(arr), -128, 127).astype(np.int8)
    return q.tobytes()

def unpack_int8(blob: bytes) -> np.ndarray:
    q = np.frombuffer(blob, dtype=np.int8)
    return q.astype(np.float32)

def create_vector_from_floats(db: Session, vec_f32: list[float]) -> Vector:
    if len(vec_f32) != settings.VECTOR_DIM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Vector length {len(vec_f32)} != expected {settings.VECTOR_DIM}",
        )
    blob = pack_int8(vec_f32)  # scale=1.0, zero_point=0.0 for MVP
    vec = Vector(dim=len(vec_f32), data=blob)
    # optional extra guard: assert len(blob) == vec.dim
    if len(blob) != vec.dim:
        raise HTTPException(status_code=500, detail="packed vector size mismatch")
    db.add(vec)
    db.flush()
    return vec
