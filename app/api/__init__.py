from fastapi import APIRouter
from .users import router as users
from .anchors import router as anchors

api = APIRouter()
api.include_router(users)
api.include_router(anchors)
