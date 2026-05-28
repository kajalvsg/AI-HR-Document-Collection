import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.models import Candidate
from app.services.ai_service import AIService


class AIServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config["OPENROUTER_API_KEY"] = ""
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def _candidate(self, documents=None, **kwargs):
        candidate = MagicMock(spec=Candidate)
        candidate.id = 1
        candidate.name = kwargs.get("name", "Aakash Mahadevan")
        candidate.email = kwargs.get("email", "aakash@example.com")
        candidate.designation = kwargs.get("designation", "Engineering Intern")
        candidate.company = kwargs.get("company", "Hungerbox")
        candidate.documents.all.return_value = documents or []
        return candidate

    def _mock_response(self, status_code=200, json_data=None, text=""):
        response = MagicMock()
        response.ok = 200 <= status_code < 300
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = text
        return response

    def test_template_when_api_key_missing(self):
        message, status, source = AIService.generate_document_request_message(
            self._candidate()
        )
        self.assertEqual(source, "template")
        self.assertEqual(status, "success")
        self.assertIn("Dear Aakash Mahadevan", message)

    def test_template_format_matches_expected_style(self):
        message = AIService._template_message(self._candidate())
        self.assertIn("Regards,\nHR Team", message)
        self.assertIn("Engineering Intern", message)

    @patch("app.services.ai_service.requests.post")
    def test_ai_source_on_success(self, mock_post):
        self.app.config["OPENROUTER_API_KEY"] = "test-key"
        mock_post.return_value = self._mock_response(
            json_data={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Dear Aakash,\n\n"
                                "Congratulations on moving forward.\n\n"
                                "Please upload your PAN and Aadhaar documents for verification.\n"
                                "Accepted formats: PDF or clear image.\n\n"
                                "Regards,\nHR Team"
                            )
                        }
                    }
                ]
            }
        )

        message, status, source = AIService.generate_document_request_message(
            self._candidate()
        )
        self.assertEqual(source, "ai")
        self.assertEqual(status, "success")
        self.assertIn("Dear", message)
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["json"]["temperature"], 0.2)
        self.assertEqual(call_kwargs["json"]["max_tokens"], 180)

    @patch("app.services.ai_service.requests.post")
    def test_template_on_api_http_error(self, mock_post):
        self.app.config["OPENROUTER_API_KEY"] = "test-key"
        mock_post.return_value = self._mock_response(
            status_code=401,
            json_data={"error": {"message": "Invalid API key"}},
        )

        message, status, source = AIService.generate_document_request_message(
            self._candidate()
        )
        self.assertEqual(source, "template")
        self.assertNotIn("Invalid API key", message)
        self.assertIn("Dear", message)

    @patch("app.services.ai_service.requests.post")
    def test_template_when_ai_response_missing_required_sentence(self, mock_post):
        self.app.config["OPENROUTER_API_KEY"] = "test-key"
        mock_post.return_value = self._mock_response(
            json_data={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Dear Aakash,\n\nCongratulations on moving forward.\n\nRegards,\nHR Team"
                            )
                        }
                    }
                ]
            }
        )

        message, status, source = AIService.generate_document_request_message(
            self._candidate()
        )
        self.assertEqual(source, "template")
        self.assertEqual(status, "success")
        self.assertIn("Please upload your PAN and Aadhaar documents for verification.", message)


if __name__ == "__main__":
    unittest.main()
