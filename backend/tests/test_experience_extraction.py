import unittest

from app.services.extraction_service import CandidateExtractionService

KAJAL_STYLE_RESUME = """
Kajal Gupta
Email: kajalguptavgs@gmail.com
Phone: +91 9876543210

SKILLS
Python, React, Flask

WORK EXPERIENCE
WeWork India July 2025 - Dec 2025
Software Engineer Intern Bangalore, India
- Built a unified notification module for internal teams
- Collaborated with backend engineers on API design

PROJECTS
Personal Portfolio Website

AWARDS AND RECOGNITION
Technical Team Member - Smart India Hackathon 2024
Winner - College Coding Championship

EDUCATION
B.Tech Computer Science, 2022 - 2026
"""

AWARDS_ONLY_RESUME = """
Jane Doe
jane@example.com

AWARDS AND RECOGNITION
Technical Team Member - National Hackathon 2024
"""


class ExperienceExtractionTests(unittest.TestCase):
    def test_kajal_resume_prefers_work_experience_over_awards(self):
        result = CandidateExtractionService.extract(KAJAL_STYLE_RESUME)
        self.assertEqual(result.company, "WeWork India")
        self.assertEqual(result.designation, "Software Engineer Intern")
        self.assertGreaterEqual(result.confidence_scores.get("company", 0), 0.9)
        self.assertGreaterEqual(
            result.confidence_scores.get("designation", 0), 0.9
        )

    def test_awards_used_only_when_no_work_experience(self):
        result = CandidateExtractionService.extract(AWARDS_ONLY_RESUME)
        self.assertIsNone(result.company)
        self.assertIn("Technical Team Member", result.designation or "")

    def test_work_experience_title_at_company_format(self):
        text = """
WORK EXPERIENCE
Software Engineer Intern at WeWork India
Jan 2025 - Present
- Shipped features
"""
        result = CandidateExtractionService.extract(text)
        self.assertEqual(result.company, "WeWork India")
        self.assertEqual(result.designation, "Software Engineer Intern")

    def test_work_experience_pipe_format(self):
        text = """
WORK EXPERIENCE
Software Engineer Intern | WeWork India
- Did work
PROJECTS
Side project
"""
        result = CandidateExtractionService.extract(text)
        self.assertEqual(result.company, "WeWork India")
        self.assertEqual(result.designation, "Software Engineer Intern")


if __name__ == "__main__":
    unittest.main()
