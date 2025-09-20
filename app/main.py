from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

def main():
    print("Hello from senecampus-backend!")
    print("""
          You are meant to execute this server with:
          `uv run uvicorn app.main:app --reload`
          """)


if __name__ == "__main__":
    main()
