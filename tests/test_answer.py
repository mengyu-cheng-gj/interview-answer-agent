import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

class AnswerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = {"candidate": {"name": "Demo", "target_role": "Engineer", "experiences": []}, "question": "Introduce yourself", "language": "both"}

    @patch("app.config.MODEL_MODE", "mock")
    def test_bilingual_missing_evidence(self):
        response = self.client.post("/api/answer/generate", json=self.payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data["answers"]), {"zh", "en"})
        self.assertTrue(data["missing_information"])
        self.assertTrue(data["requires_review"])
        self.assertEqual(data["evidence"], [])

    def test_invalid_language(self):
        self.payload["language"] = "fr"
        self.assertEqual(self.client.post("/api/answer/generate", json=self.payload).status_code, 422)

    @patch("app.config.MODEL_MODE", "live")
    @patch("app.config.LLM_API_KEY", "")
    def test_live_missing_credentials(self):
        self.assertEqual(self.client.post("/api/answer/generate", json=self.payload).status_code, 502)

    @patch("app.config.MODEL_MODE", "mock")
    def test_revision(self):
        response = self.client.post("/api/interaction/revise", json={"original": self.payload, "previous_answer": "Draft", "feedback": "Shorter"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("requires live mode", response.json()["answers"]["en"])
