from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api import api
from app.services.anchors import load_anchors

from app.core.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # mappings already imported
    load_anchors()
    yield
    engine.dispose()

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
app.include_router(api)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

def main():
    print("Hello from senecampus-backend!")
    print("""
          You are meant to execute this server with:
          `uv run uvicorn app.main:app --reload`
          """)


if __name__ == "__main__":
    main()
