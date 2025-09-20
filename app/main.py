from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)

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
