"""
EduGenie Summary Module - Text summarization endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ai_service import generate_response, parse_json_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Summary"])


class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000, description="The text to summarize")


class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Concise summary of the text")
    key_points: list[str] = Field(default_factory=list, description="Key points extracted from the text")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_text(request: SummaryRequest):
    """Summarize a long text passage and extract key points."""
    try:
        prompt = (
            "Summarize the following text concisely while preserving the most important information.\n\n"
            "IMPORTANT: Respond with ONLY a valid JSON object with these keys:\n"
            '- "summary": a clear, concise summary paragraph\n'
            '- "key_points": an array of 3-6 key bullet point strings\n\n'
            "Do not include any markdown formatting or extra text outside the JSON.\n\n"
            f"Text to summarize:\n{request.text}\n\n"
            "JSON response:"
        )
        raw_response = await generate_response(prompt, max_tokens=1500)

        try:
            parsed = parse_json_response(raw_response)
            summary = parsed.get("summary", "")
            key_points = parsed.get("key_points", [])

            if not summary:
                raise ValueError("Missing summary in response")

            if not isinstance(key_points, list):
                key_points = []

            key_points = [str(kp) for kp in key_points if kp]

            return SummaryResponse(summary=summary, key_points=key_points)

        except (ValueError, AttributeError):
            # Graceful degradation: use raw text as summary
            logger.warning("Failed to parse structured summary, using raw text")
            return SummaryResponse(summary=raw_response.strip(), key_points=[])

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
