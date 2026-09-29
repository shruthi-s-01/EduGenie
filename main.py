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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    # Startup
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "⚠️  GEMINI_API_KEY is not set. AI features will not work. "
            "Set it in your .env file or environment variables."
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

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
async def health_check():
    """Health check endpoint."""
    has_api_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "ok",
        "service": "EduGenie",
        "version": "1.0.0",
        "ai_configured": has_api_key,
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
