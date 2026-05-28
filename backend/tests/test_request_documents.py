import unittest

from app import create_app
from app.extensions import db
from app.models import Candidate, RequestLog


class RequestDocumentsTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app.config["OPENROUTER_API_KEY"] = ""
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _add_candidate(self, email: str) -> Candidate:
        candidate = Candidate(
            name="Test User",
            email=email,
            extraction_status="Parsed",
        )
        db.session.add(candidate)
        db.session.commit()
        return candidate

    def test_missing_email_returns_error(self):
        candidate = self._add_candidate("pending.abc123@extract.pending")
        response = self.client.post(
            f"/api/candidates/{candidate.id}/request-documents"
        )
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error"], "missing_email")

    def test_simulated_email_request_success(self):
        candidate = self._add_candidate("kajal@example.com")
        response = self.client.post(
            f"/api/candidates/{candidate.id}/request-documents"
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(
            body["message"],
            "Document request generated and email simulated successfully",
        )
        data = body["data"]
        self.assertEqual(data["channel"], "email")
        self.assertEqual(data["recipient"], "kajal@example.com")
        self.assertEqual(data["delivery_status"], "sent_simulated")

        log = db.session.get(RequestLog, data["request_log"]["id"])
        self.assertIsNotNone(log)
        self.assertEqual(log.channel, "email")
        self.assertEqual(log.recipient, "kajal@example.com")
        self.assertEqual(log.delivery_status, "sent_simulated")
        self.assertIn(log.message_source, ("ai", "template"))


if __name__ == "__main__":
    unittest.main()
