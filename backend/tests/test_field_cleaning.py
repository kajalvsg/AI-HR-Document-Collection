import unittest

from app.services.field_cleaning import (
    clean_company,
    clean_designation,
    company_for_message,
    designation_for_message,
    is_usable_company,
    is_usable_designation,
    strip_trailing_location_from_title,
)


class FieldCleaningTests(unittest.TestCase):
    def test_clean_company_semicolon_and_previously(self):
        raw = "Coinbase; previously at D.E. Shaw on firm-wide quant data"
        self.assertEqual(clean_company(raw), "Coinbase")
        self.assertTrue(is_usable_company("Coinbase", raw))
        self.assertEqual(company_for_message(raw), "Coinbase")

    def test_clean_company_project_fragment(self):
        raw = "Hungerbox Created A Unified Generic Notification Module"
        self.assertEqual(clean_company(raw), "Hungerbox")
        self.assertFalse(is_usable_company("Hungerbox", raw))
        self.assertIsNone(company_for_message(raw))

    def test_clean_company_max_four_words(self):
        raw = "International Business Machines Corporation Global Services"
        self.assertEqual(
            clean_company(raw),
            "International Business Machines Corporation",
        )

    def test_clean_designation_strips_project_text(self):
        raw = "Software Engineer Created A Unified Generic Notification Module"
        self.assertEqual(clean_designation(raw), "Software Engineer")
        self.assertTrue(is_usable_designation("Software Engineer"))

    def test_clean_designation_title_pipe_company(self):
        raw = "Software Engineer | Coinbase"
        self.assertEqual(clean_designation(raw), "Software Engineer")

    def test_strip_location_keeps_intern_suffix(self):
        raw = "Software Engineer Intern Bangalore, India"
        self.assertEqual(
            strip_trailing_location_from_title(raw),
            "Software Engineer Intern",
        )
        self.assertEqual(clean_designation(raw), "Software Engineer Intern")

    def test_designation_noise_not_usable(self):
        raw = "Hungerbox Created A Unified Generic Notification Module"
        self.assertEqual(clean_designation(raw), "Hungerbox")
        self.assertIsNone(designation_for_message(raw))


if __name__ == "__main__":
    unittest.main()
