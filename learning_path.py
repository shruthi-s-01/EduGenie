"""
EduGenie Learning Path Module - Personalized learning path generation.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ai_service import generate_response, parse_json_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Learning Path"])


class LearningPathRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="The subject to create a learning path for")


class LearningStage(BaseModel):
    stage: str = Field(..., description="Stage level (e.g., Beginner, Foundation)")
    title: str = Field(..., description="Stage title")
    description: str = Field(..., description="What this stage covers")
    topics: list[str] = Field(default_factory=list, description="Topics to study")
    resources: list[str] = Field(default_factory=list, description="Suggested resources")
    duration: str = Field(default="", description="Estimated time for this stage")


class LearningPathResponse(BaseModel):
    stages: list[LearningStage] = Field(..., description="Ordered learning stages")


def validate_learning_path(data) -> list[dict]:
    """Validate and sanitize parsed learning path data."""
    if not isinstance(data, list):
        raise ValueError("Learning path must be a list of stages")

    if len(data) < 1:
        raise ValueError("Learning path must contain at least one stage")

    validated = []
    for i, item in enumerate(data[:6]):  # Max 6 stages
        if not isinstance(item, dict):
            continue

        stage = str(item.get("stage", f"Stage {i + 1}")).strip()
        title = str(item.get("title", "")).strip()
        description = str(item.get("description", "")).strip()

        if not title and not description:
            continue

        topics = item.get("topics", [])
        if not isinstance(topics, list):
            topics = [str(topics)] if topics else []
        topics = [str(t).strip() for t in topics if t]

        resources = item.get("resources", [])
        if not isinstance(resources, list):
            resources = [str(resources)] if resources else []
        resources = [str(r).strip() for r in resources if r]

        duration = str(item.get("duration", "")).strip()

        validated.append({
            "stage": stage,
            "title": title or stage,
            "description": description or "Continue your learning journey.",
            "topics": topics,
            "resources": resources,
            "duration": duration or "Self-paced",
        })

    if not validated:
        raise ValueError("No valid learning stages found in response")

    return validated


@router.post("/learn/recommendations", response_model=LearningPathResponse)
async def create_learning_path(request: LearningPathRequest):
    """Generate a structured learning path for a given topic."""
    try:
        prompt = (
            "Create a structured learning path for mastering the following subject.\n\n"
            f"Subject: {request.topic}\n\n"
            "IMPORTANT: Respond with ONLY a valid JSON array. No markdown, no extra text.\n"
            "Create exactly 4 stages in this order: Beginner, Foundation, Intermediate, Advanced.\n\n"
            "Each object must have these keys:\n"
            '- "stage": the level name (e.g., "Beginner")\n'
            '- "title": a descriptive title for this stage\n'
            '- "description": what the learner will achieve in this stage (2-3 sentences)\n'
            '- "topics": array of 3-5 specific topics/skills to study\n'
            '- "resources": array of 2-3 recommended resource types or specific resources\n'
            '- "duration": estimated time (e.g., "2-3 weeks")\n\n'
            "Make the path practical and actionable. Respond with ONLY the JSON array:"
        )
        raw_response = await generate_response(prompt, max_tokens=2048)
        parsed = parse_json_response(raw_response)
        validated = validate_learning_path(parsed)
        return LearningPathResponse(stages=[LearningStage(**s) for s in validated])

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Learning path error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate learning path. Please try again.")
