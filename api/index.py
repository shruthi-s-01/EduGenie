"""
Vercel serverless entrypoint for EduGenie FastAPI application.
"""

import sys
import os

# Ensure the root directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Export app for Vercel ASGI handler
__all__ = ["app"]
