from fastapi import FastAPI
from app.core.cors import setup_cors
from app.api.router import api_router

app = FastAPI()
setup_cors(app)

app.include_router(api_router, prefix="/api")

@app.get("/ping")
def ping():
    return {"ok": True}
