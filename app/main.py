from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api import api

from app.core.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # mappings already imported
    yield
    engine.dispose()

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG, lifespan=lifespan)
app.include_router(api)

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
