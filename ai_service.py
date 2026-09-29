"""
EduGenie AI Service - Centralized Gemini API integration.
"""

import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "gemini-2.0-flash"


def get_gemini_model():
    """Configure and return a Gemini generative model instance."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


async def generate_response(prompt: str, max_tokens: int = 2048) -> str:
    """
    Generate a response from the Gemini API.

    Args:
        prompt: The prompt to send to the model.
        max_tokens: Maximum tokens in the response.

    Returns:
        The generated text response.

    Raises:
        ValueError: If the API key is missing or response is empty.
        RuntimeError: If the API call fails.
    """
    try:
        model = get_gemini_model()
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        if not response or not response.text:
            raise ValueError("Empty response from AI model")
        return response.text
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"AI service unavailable: {e}")


def parse_json_response(text: str):
    """
    Parse JSON from an AI response, handling markdown code fences.

    Args:
        text: Raw text response that may contain JSON.

    Returns:
        Parsed JSON as dict or list.

    Raises:
        ValueError: If the text cannot be parsed as valid JSON.
    """
    cleaned = text.strip()

    # Remove markdown code fences (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing fence
        cleaned = "\n".join(lines).strip()

    # Also handle case where ``` appears at end without newline
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}\nText: {cleaned[:500]}")
        raise ValueError("Failed to parse AI response as structured data")
