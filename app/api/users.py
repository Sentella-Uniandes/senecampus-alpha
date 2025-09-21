from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import users as svc  # uses the service layer you have

# ----- Schemas (Pydantic v2) -----

class VectorCreate(BaseModel):
    data: Annotated[list[float], Field(min_length=1)]

class UserCreate(BaseModel):
    email: str  # EmailStr -> str
    first_name: str | None = None
    vector_id: int | None = None
    vector: VectorCreate | None = None


class UserRead(BaseModel):
    id: int
    username: str
    first_name: str | None = None
    vector_id: int | None = None

class UserList(BaseModel):
    items: list[UserRead]
    total: int

class UserPatch(BaseModel):
    first_name: str | None = None

class DisplayNameCreate(BaseModel):
    value: str

class DisplayNameRead(BaseModel):
    id: int
    value: str

class AttachVectorRequest(BaseModel):
    vector_id: int | None = None
    vector: VectorCreate | None = None

# ----- Router -----

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    vec_data = payload.vector.data if payload.vector else None
    if not payload.email.lower().endswith("@uniandes.edu.co"):
        raise HTTPException(status_code=422, detail="email must be @uniandes.edu.co")
    u = svc.create_user(
        db,
        email=payload.email,
        first_name=payload.first_name,
        vector_id=payload.vector_id,
        vector_data=vec_data,
    )
    return UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id)

@router.get("", response_model=UserList)
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = svc.list_users(db, offset=offset, limit=limit)
    return UserList(
        items=[UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id) for u in items],
        total=total,
    )

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = svc.get_user(db, user_id)
    return UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id)

@router.get("/by-username/{username}", response_model=UserRead)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    u = svc.get_user_by_username(db, username)
    return UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id)

@router.patch("/{user_id}", response_model=UserRead)
def patch_user(user_id: int, payload: UserPatch, db: Session = Depends(get_db)):
    u = svc.update_user(db, user_id, first_name=payload.first_name)
    return UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id)

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    svc.delete_user(db, user_id)
    return None

@router.put("/{user_id}/vector", response_model=UserRead)
def attach_vector(user_id: int, payload: AttachVectorRequest, db: Session = Depends(get_db)):
    vec_id = payload.vector_id
    vec_data = payload.vector.data if payload.vector else None
    u = svc.attach_vector(db, user_id, vector_id=vec_id, vector_data=vec_data)
    return UserRead(id=u.id, username=u.username, first_name=u.first_name, vector_id=u.vector_id)
