"""
FastAPI application entry point for the Driver Assessment System.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import connect_to_mongo, close_mongo_connection
from routes.mcqs import router as mcqs_router
from routes.evaluation import router as evaluation_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    await connect_to_mongo()
    # Ensure static folders are created on startup
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)
    yield
    await close_mongo_connection()


app = FastAPI(
    title="🚗 Intelligent Driver Assessment System",
    description="AntiGravity Engine — AI-based driver evaluation using multimedia MCQs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for deployment ease. In strict production, set this to the exact Vercel URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static media files (audio, images)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register routers
app.include_router(mcqs_router)
app.include_router(evaluation_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {
        "message": "🚗 AntiGravity Driver Assessment API is running",
        "docs": "/docs",
        "endpoints": {
            "text_mcqs": "/api/mcqs/text",
            "audio_mcqs": "/api/mcqs/audio",
            "image_mcqs": "/api/mcqs/image",
            "all_mcqs": "/api/mcqs/all",
            "submit_answers": "/api/submit-answers",
        },
    }
