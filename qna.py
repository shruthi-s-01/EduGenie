"""
EduGenie Q&A Module - Question and Answer endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ai_service import generate_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Q&A"])


class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="The educational question to answer")


class QAResponse(BaseModel):
    answer: str = Field(..., description="The AI-generated answer")


@router.post("/qa", response_model=QAResponse)
async def answer_question(request: QARequest):
    """Answer an educational question using AI."""
    try:
        prompt = (
            "You are EduGenie, a helpful educational assistant. "
            "Answer the following question clearly, accurately, and in a way that helps a student learn. "
            "Use examples where helpful. Structure your response with headings and bullet points when appropriate.\n\n"
            f"Question: {request.question}\n\n"
            "Provide a thorough yet concise answer:"
        )
        answer = await generate_response(prompt)
        return QAResponse(answer=answer)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
