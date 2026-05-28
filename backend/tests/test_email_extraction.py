import unittest

from app.services.extraction_service import CandidateExtractionService


class EmailExtractionTests(unittest.TestCase):
    def test_labeled_email_with_colon(self):
        text = "Email: kajalguptavgs@gmail.com"
        email, confidence = CandidateExtractionService._extract_email(text)
        self.assertEqual(email, "kajalguptavgs@gmail.com")
        self.assertGreaterEqual(confidence, 0.9)

    def test_labeled_email_without_colon(self):
        text = "E-mail kajalguptavgs@gmail.com"
        email, confidence = CandidateExtractionService._extract_email(text)
        self.assertEqual(email, "kajalguptavgs@gmail.com")
        self.assertGreaterEqual(confidence, 0.9)

    def test_strips_pe_prefix_from_concatenated_local(self):
        text = "pekajalguptavgs@gmail.com"
        email, _ = CandidateExtractionService._extract_email(text)
        self.assertEqual(email, "kajalguptavgs@gmail.com")

    def test_normalize_email_strips_pe_prefix(self):
        cleaned = CandidateExtractionService.normalize_email(
            "pekajalguptavgs@gmail.com",
            "pekajalguptavgs@gmail.com",
        )
        self.assertEqual(cleaned, "kajalguptavgs@gmail.com")

    def test_does_not_break_peterson_email(self):
        text = "Contact peterson@example.com for info"
        email, _ = CandidateExtractionService._extract_email(text)
        self.assertEqual(email, "peterson@example.com")

    def test_rejects_invalid_multiple_at(self):
        self.assertIsNone(
            CandidateExtractionService.normalize_email("bad@@example.com", "")
        )

    def test_rejects_missing_domain_tld(self):
        self.assertIsNone(
            CandidateExtractionService.normalize_email("user@domain", "")
        )

    def test_prefers_cleanest_among_multiple(self):
        text = (
            "pekajalguptavgs@gmail.com\n"
            "Email: kajalguptavgs@gmail.com"
        )
        email, _ = CandidateExtractionService._extract_email(text)
        self.assertEqual(email, "kajalguptavgs@gmail.com")

    def test_strips_mail_prefix_from_local(self):
        cleaned = CandidateExtractionService.normalize_email(
            "mailjohn.doe@company.org",
            "E-mail mailjohn.doe@company.org",
        )
        self.assertEqual(cleaned, "john.doe@company.org")

    def test_full_extract_includes_cleaned_email(self):
        text = "Name: Kajal Gupta\nEmail: kajalguptavgs@gmail.com\n"
        result = CandidateExtractionService.extract(text)
        self.assertEqual(result.email, "kajalguptavgs@gmail.com")


if __name__ == "__main__":
    unittest.main()
