"""
EduGenie - AI-Powered Educational Assistant
Main application entry point.
"""

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Base directory for reliable path resolution in Vercel / serverless environments
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Load environment variables (do not override system env vars)
load_dotenv(override=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from ai_service import get_gemini_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    # Startup
    api_key = get_gemini_api_key()
    if not api_key:
        logger.warning(
            "⚠️  GEMINI_API_KEY is not set. AI features will not work. "
            "Set it in your environment variables or Vercel project settings."
        )
    else:
        logger.info("✅ GEMINI_API_KEY is configured")
    logger.info("🎓 EduGenie is starting up...")
    yield
    # Shutdown
    logger.info("👋 EduGenie is shutting down...")


# Create FastAPI application
app = FastAPI(
    title="EduGenie",
    description="AI-Powered Educational Assistant - Learn smarter, understand faster.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files safely
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Import and include routers
from qna import router as qa_router
from explanation_module import router as explain_router
from quiz_module import router as quiz_router
from summary_module import router as summary_router
from learning_path import router as learn_router

app.include_router(qa_router)
app.include_router(explain_router)
app.include_router(quiz_router)
app.include_router(summary_router)
app.include_router(learn_router)


@app.get("/")
async def home(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
@app.get("/api/diagnostic")
async def health_check():
    """
    Safe health and diagnostic check endpoint.
    Reports whether the Gemini API key is configured without exposing secret values.
    """
    has_api_key = bool(get_gemini_api_key())
    return {
        "status": "ok",
        "service": "EduGenie",
        "version": "1.0.0",
        "gemini_api_key_configured": has_api_key,
        "ai_configured": has_api_key,
        "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        "platform": "vercel" if os.getenv("VERCEL") else "serverless/standard",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent leaking stack traces."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "The requested resource was not found."},
    )
