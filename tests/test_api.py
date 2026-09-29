"""
EduGenie Test Suite
Tests all API endpoints with mocked Gemini responses.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Patch the AI service before importing main
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


# ─── Health Check ────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "EduGenie"
        assert "gemini_api_key_configured" in data

    def test_diagnostic_endpoint(self):
        response = client.get("/api/diagnostic")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "EduGenie"
        assert "gemini_api_key_configured" in data
        assert "model" in data
        # Ensure secret API key is never exposed in response
        assert "AIza" not in response.text
        assert "AQ." not in response.text

    def test_homepage_loads(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "EduGenie" in response.text


# ─── Q&A Tests ───────────────────────────────────────────────────

class TestQA:
    @patch("qna.generate_response", new_callable=AsyncMock)
    def test_qa_success(self, mock_gen):
        mock_gen.return_value = "Photosynthesis is the process by which plants convert light energy into chemical energy."
        response = client.post("/qa", json={"question": "What is photosynthesis?"})
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "Photosynthesis" in data["answer"]

    def test_qa_empty_question(self):
        response = client.post("/qa", json={"question": ""})
        assert response.status_code == 422

    def test_qa_missing_field(self):
        response = client.post("/qa", json={})
        assert response.status_code == 422

    @patch("qna.generate_response", new_callable=AsyncMock)
    def test_qa_api_error(self, mock_gen):
        mock_gen.side_effect = RuntimeError("AI service unavailable")
        response = client.post("/qa", json={"question": "Test question"})
        assert response.status_code == 503

    @patch("qna.generate_response", new_callable=AsyncMock)
    def test_qa_missing_api_key(self, mock_gen):
        mock_gen.side_effect = ValueError("GEMINI_API_KEY not set")
        response = client.post("/qa", json={"question": "Test"})
        assert response.status_code == 422


# ─── Explanation Tests ───────────────────────────────────────────

class TestExplanation:
    @patch("explanation_module.generate_response", new_callable=AsyncMock)
    def test_explain_success(self, mock_gen):
        mock_gen.return_value = "## Quantum Entanglement\n\nQuantum entanglement is a phenomenon..."
        response = client.post("/explain", json={"concept": "Quantum Entanglement"})
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0

    def test_explain_empty_concept(self):
        response = client.post("/explain", json={"concept": ""})
        assert response.status_code == 422

    @patch("explanation_module.generate_response", new_callable=AsyncMock)
    def test_explain_api_error(self, mock_gen):
        mock_gen.side_effect = RuntimeError("AI service unavailable")
        response = client.post("/explain", json={"concept": "Test"})
        assert response.status_code == 503


# ─── Quiz Tests ──────────────────────────────────────────────────

class TestQuiz:
    VALID_QUIZ_JSON = json.dumps([
        {
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "correct_answer": "Paris"
        },
        {
            "question": "Which planet is largest?",
            "options": ["Earth", "Jupiter", "Saturn", "Mars"],
            "correct_answer": "Jupiter"
        },
        {
            "question": "What is H2O?",
            "options": ["Hydrogen", "Oxygen", "Water", "Helium"],
            "correct_answer": "Water"
        }
    ])

    @patch("quiz_module.generate_response", new_callable=AsyncMock)
    def test_quiz_success(self, mock_gen):
        mock_gen.return_value = self.VALID_QUIZ_JSON
        response = client.post("/quiz", json={"topic": "General Knowledge"})
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 3
        for q in data["questions"]:
            assert "question" in q
            assert "options" in q
            assert len(q["options"]) == 4
            assert "correct_answer" in q
            assert q["correct_answer"] in q["options"]

    @patch("quiz_module.generate_response", new_callable=AsyncMock)
    def test_quiz_with_markdown_fences(self, mock_gen):
        mock_gen.return_value = f"```json\n{self.VALID_QUIZ_JSON}\n```"
        response = client.post("/quiz", json={"topic": "Science"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 3

    @patch("quiz_module.generate_response", new_callable=AsyncMock)
    def test_quiz_malformed_json(self, mock_gen):
        mock_gen.return_value = "This is not valid JSON at all"
        response = client.post("/quiz", json={"topic": "Test"})
        assert response.status_code == 422

    def test_quiz_empty_topic(self):
        response = client.post("/quiz", json={"topic": ""})
        assert response.status_code == 422

    @patch("quiz_module.generate_response", new_callable=AsyncMock)
    def test_quiz_api_error(self, mock_gen):
        mock_gen.side_effect = RuntimeError("AI service unavailable")
        response = client.post("/quiz", json={"topic": "Test"})
        assert response.status_code == 503


# ─── Summary Tests ───────────────────────────────────────────────

class TestSummary:
    @patch("summary_module.generate_response", new_callable=AsyncMock)
    def test_summary_success(self, mock_gen):
        mock_gen.return_value = json.dumps({
            "summary": "This is a concise summary of the text.",
            "key_points": ["Point 1", "Point 2", "Point 3"]
        })
        response = client.post("/summarize", json={
            "text": "This is a long text that needs to be summarized. " * 10
        })
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "key_points" in data
        assert len(data["key_points"]) > 0

    @patch("summary_module.generate_response", new_callable=AsyncMock)
    def test_summary_graceful_degradation(self, mock_gen):
        mock_gen.return_value = "Just a plain text summary without JSON structure."
        response = client.post("/summarize", json={
            "text": "This is a long text that needs to be summarized. " * 10
        })
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        # Should gracefully fall back to raw text
        assert len(data["summary"]) > 0

    def test_summary_too_short(self):
        response = client.post("/summarize", json={"text": "Short"})
        assert response.status_code == 422

    def test_summary_empty(self):
        response = client.post("/summarize", json={"text": ""})
        assert response.status_code == 422


# ─── Learning Path Tests ────────────────────────────────────────

class TestLearningPath:
    VALID_PATH_JSON = json.dumps([
        {
            "stage": "Beginner",
            "title": "Getting Started",
            "description": "Learn the basics of the subject.",
            "topics": ["Intro", "Fundamentals", "Key concepts"],
            "resources": ["Online tutorials", "Beginner textbook"],
            "duration": "2-3 weeks"
        },
        {
            "stage": "Foundation",
            "title": "Building Strong Foundations",
            "description": "Deepen your understanding.",
            "topics": ["Core theory", "Practice problems"],
            "resources": ["Intermediate course", "Practice platform"],
            "duration": "3-4 weeks"
        },
        {
            "stage": "Intermediate",
            "title": "Expanding Knowledge",
            "description": "Apply concepts to real problems.",
            "topics": ["Applications", "Case studies"],
            "resources": ["Advanced tutorials", "Projects"],
            "duration": "4-6 weeks"
        },
        {
            "stage": "Advanced",
            "title": "Mastery",
            "description": "Achieve deep expertise.",
            "topics": ["Research papers", "Cutting edge"],
            "resources": ["Research journals", "Community"],
            "duration": "Ongoing"
        }
    ])

    @patch("learning_path.generate_response", new_callable=AsyncMock)
    def test_learning_path_success(self, mock_gen):
        mock_gen.return_value = self.VALID_PATH_JSON
        response = client.post("/learn/recommendations", json={"topic": "Machine Learning"})
        assert response.status_code == 200
        data = response.json()
        assert "stages" in data
        assert len(data["stages"]) == 4
        for stage in data["stages"]:
            assert "stage" in stage
            assert "title" in stage
            assert "description" in stage
            assert "topics" in stage
            assert "resources" in stage
            assert "duration" in stage

    def test_learning_path_empty_topic(self):
        response = client.post("/learn/recommendations", json={"topic": ""})
        assert response.status_code == 422

    @patch("learning_path.generate_response", new_callable=AsyncMock)
    def test_learning_path_api_error(self, mock_gen):
        mock_gen.side_effect = RuntimeError("AI service unavailable")
        response = client.post("/learn/recommendations", json={"topic": "Test"})
        assert response.status_code == 503

    @patch("learning_path.generate_response", new_callable=AsyncMock)
    def test_learning_path_malformed_json(self, mock_gen):
        mock_gen.return_value = "Not valid JSON"
        response = client.post("/learn/recommendations", json={"topic": "Test"})
        assert response.status_code == 422


# ─── Utility Tests ───────────────────────────────────────────────

class TestParseJson:
    def test_parse_clean_json(self):
        from ai_service import parse_json_response
        result = parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_with_code_fences(self):
        from ai_service import parse_json_response
        result = parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_with_plain_fences(self):
        from ai_service import parse_json_response
        result = parse_json_response('```\n[1, 2, 3]\n```')
        assert result == [1, 2, 3]

    def test_parse_invalid_json(self):
        from ai_service import parse_json_response
        with pytest.raises(ValueError):
            parse_json_response("not json at all")


class TestQuizValidation:
    def test_valid_quiz(self):
        from quiz_module import validate_quiz_data
        data = [
            {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_answer": "A"},
            {"question": "Q2?", "options": ["A", "B", "C", "D"], "correct_answer": "B"},
            {"question": "Q3?", "options": ["A", "B", "C", "D"], "correct_answer": "C"},
        ]
        result = validate_quiz_data(data)
        assert len(result) == 3

    def test_quiz_not_list(self):
        from quiz_module import validate_quiz_data
        with pytest.raises(ValueError):
            validate_quiz_data({"not": "a list"})

    def test_quiz_empty_list(self):
        from quiz_module import validate_quiz_data
        with pytest.raises(ValueError):
            validate_quiz_data([])

    def test_quiz_missing_fields(self):
        from quiz_module import validate_quiz_data
        with pytest.raises(ValueError):
            validate_quiz_data([{"question": "Q1?"}])
