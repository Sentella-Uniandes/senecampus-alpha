from fastapi import APIRouter
from .users import router as users

api = APIRouter()
api.include_router(users)
