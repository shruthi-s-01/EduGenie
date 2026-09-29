"""
EduGenie Quiz Module - Interactive quiz generation endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ai_service import generate_response, parse_json_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Quiz"])


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="The topic for quiz generation")


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]


def validate_quiz_data(data) -> list[dict]:
    """Validate and sanitize parsed quiz data from AI response."""
    if not isinstance(data, list):
        raise ValueError("Quiz data must be a list of questions")

    if len(data) < 1:
        raise ValueError("Quiz must contain at least one question")

    validated = []
    for i, item in enumerate(data[:3]):  # Take at most 3 questions
        if not isinstance(item, dict):
            raise ValueError(f"Question {i + 1} is not a valid object")

        question = item.get("question")
        options = item.get("options")
        correct_answer = item.get("correct_answer")

        if not question or not isinstance(question, str):
            raise ValueError(f"Question {i + 1} is missing valid question text")

        if not options or not isinstance(options, list):
            raise ValueError(f"Question {i + 1} is missing valid options")

        # Ensure exactly 4 options, pad or trim if needed
        str_options = [str(o) for o in options if o]
        if len(str_options) < 2:
            raise ValueError(f"Question {i + 1} has too few options")
        str_options = str_options[:4]  # Trim to max 4
        while len(str_options) < 4:
            str_options.append(f"Option {len(str_options) + 1}")

        if not correct_answer or not isinstance(correct_answer, str):
            raise ValueError(f"Question {i + 1} is missing a correct answer")

        # Ensure correct_answer matches one of the options
        correct_answer = str(correct_answer)
        if correct_answer not in str_options:
            # Try to find a close match
            matches = [o for o in str_options if correct_answer.lower().strip() in o.lower().strip() or o.lower().strip() in correct_answer.lower().strip()]
            if matches:
                correct_answer = matches[0]
            else:
                # Default to first option as fallback
                correct_answer = str_options[0]
                logger.warning(f"Question {i + 1}: correct_answer didn't match any option, defaulting to first option")

        validated.append({
            "question": str(question).strip(),
            "options": str_options,
            "correct_answer": correct_answer,
        })

    if len(validated) == 0:
        raise ValueError("No valid questions could be extracted")

    return validated


@router.post("/quiz", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """Generate an interactive quiz on a given topic."""
    try:
        prompt = (
            "Generate exactly 3 multiple-choice quiz questions about the following topic.\n\n"
            f"Topic: {request.topic}\n\n"
            "IMPORTANT: Respond with ONLY a valid JSON array. No markdown, no explanation, no extra text.\n"
            "Each object in the array must have exactly these keys:\n"
            '- "question": a clear question string\n'
            '- "options": an array of exactly 4 distinct answer strings\n'
            '- "correct_answer": a string that exactly matches one of the 4 options\n\n'
            "Requirements:\n"
            "- Questions should test understanding, not just recall\n"
            "- Distractors (wrong options) should be plausible\n"
            "- Cover different aspects of the topic\n\n"
            "Respond with ONLY the JSON array:"
        )
        raw_response = await generate_response(prompt, max_tokens=1500)
        parsed = parse_json_response(raw_response)
        validated = validate_quiz_data(parsed)
        return QuizResponse(questions=[QuizQuestion(**q) for q in validated])

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz. Please try again.")
