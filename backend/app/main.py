from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.rfp import router as rfp_router
from app.api.routes.chat import router as chat_router

app = FastAPI(
    title="RFP Intelligence Agent"
)

import os

ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex="https?://.*",  # Allow all domains in production since users will deploy to various netlify/vercel URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rfp_router)
app.include_router(chat_router)

@app.get("/")
def home():
    return {
        "message": "Backend Running Successfully"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }