import logging
import re

import requests
from flask import current_app

from app.config import load_environment
from app.models import Candidate
from app.services.field_cleaning import (
    company_for_message,
    designation_for_message,
)

logger = logging.getLogger(__name__)

REQUIRED_DOCUMENTS = ("pan", "aadhaar")
MAX_DESIGNATION_LEN = 60
MAX_COMPANY_LEN = 60
MAX_NAME_LEN = 80
MAX_MESSAGE_LEN = 900
REQUIRED_REQUEST_SENTENCE = "Please upload your PAN and Aadhaar documents for verification."

RESUME_NOISE_PATTERN = re.compile(
    r"(?i)(skills?\s*[:|]|experience|education|curriculum vitae|resume|"
    r"@\w+\.\w+|https?://|\+?\d{10,})"
)


class OpenRouterAPIError(Exception):
    def __init__(self, status_code: int | None, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class AIService:
    @staticmethod
    def generate_document_request_message(
        candidate: Candidate,
    ) -> tuple[str, str, str]:
        """
        Returns (message, status, message_source).
        message_source is "ai" or "template". Internal errors are logged only.
        """
        settings = AIService._openrouter_settings()
        api_key = settings["api_key"]
        AIService._debug_log_config(api_key, settings["model"])

        if not api_key:
            logger.warning(
                "OpenRouter API key not configured; using template for candidate id=%s",
                candidate.id,
            )
            message = AIService._template_message(candidate)
            return message, "success", "template"

        try:
            raw = AIService._generate_with_openrouter(candidate, settings)
            message = AIService._clean_generated_message(raw)
            if not message:
                raise ValueError("Empty response from AI after cleaning")
            if not AIService._is_valid_request_message(message):
                raise ValueError("AI response did not include required PAN/Aadhaar sentence")
            return message, "success", "ai"
        except Exception:
            logger.exception(
                "OpenRouter request failed for candidate id=%s; using template",
                candidate.id,
            )
            message = AIService._template_message(candidate)
            return message, "success", "template"

    @staticmethod
    def _openrouter_settings() -> dict:
        # App config is refreshed from backend/.env during Config.init_app().
        # Keep AI reads consistent with Flask app config (and test overrides).
        return {
            "api_key": (current_app.config.get("OPENROUTER_API_KEY") or "").strip(),
            "base_url": (current_app.config.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1")
            .strip()
            .rstrip("/"),
            "model": (current_app.config.get("OPENROUTER_MODEL") or "google/gemini-2.0-flash-001").strip(),
            "timeout": float(current_app.config.get("OPENROUTER_TIMEOUT") or 30),
        }

    @staticmethod
    def _generate_with_openrouter(candidate: Candidate, settings: dict) -> str:
        fields = AIService._structured_fields(candidate)
        prompt = AIService._build_prompt(fields)

        url = f"{settings['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings["model"],
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You write concise, professional HR emails. "
                        "Output ONLY the email body plain text. "
                        "Do not include resume content, bullet lists of skills, "
                        "or candidate background beyond the provided fields. "
                        "Keep the email under 120 words. "
                        "You MUST include the exact sentence: "
                        "\"Please upload your PAN and Aadhaar documents for verification.\" "
                        "You MUST mention accepted formats: \"PDF\" or \"clear image\"."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 180,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings["timeout"],
            )
        except requests.RequestException as exc:
            AIService._debug_log_http_failure(None, str(exc))
            raise OpenRouterAPIError(None, str(exc)) from exc

        AIService._debug_log_http_status(response.status_code)

        if not response.ok:
            error_message = AIService._parse_error_response(response)
            AIService._debug_log_http_failure(response.status_code, error_message)
            raise OpenRouterAPIError(response.status_code, error_message)

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices in OpenRouter response")

        content = choices[0].get("message", {}).get("content")
        if not content or not str(content).strip():
            raise ValueError("Empty message content in OpenRouter response")

        return str(content).strip()

    @staticmethod
    def _parse_error_response(response: requests.Response) -> str:
        try:
            body = response.json()
            err = body.get("error")
            if isinstance(err, dict):
                return err.get("message") or str(err)
            if isinstance(err, str):
                return err
        except ValueError:
            pass
        return response.text[:500] if response.text else f"HTTP {response.status_code}"

    @staticmethod
    def _debug_log_config(api_key: str, model: str) -> None:
        loaded = "yes" if api_key else "no"
        print(f"[OpenRouter debug] OpenRouter key loaded: {loaded}")
        print(f"[OpenRouter debug] selected model: {model}")

    @staticmethod
    def _debug_log_http_status(status_code: int) -> None:
        print(f"[OpenRouter debug] OpenRouter status code: {status_code}")

    @staticmethod
    def _debug_log_http_failure(status_code: int | None, error_message: str) -> None:
        if status_code is not None:
            print(f"[OpenRouter debug] OpenRouter status code: {status_code}")
        else:
            print("[OpenRouter debug] OpenRouter status code: unavailable")
        print(f"[OpenRouter debug] OpenRouter error message: {error_message}")

    @staticmethod
    def _structured_fields(candidate: Candidate) -> dict[str, str]:
        missing = AIService._missing_documents(candidate)
        if not missing:
            docs = "PAN and Aadhaar"
        elif len(missing) == 2:
            docs = "PAN and Aadhaar"
        else:
            docs = missing[0].replace(" card", "")

        name = AIService._clean_field(candidate.name, MAX_NAME_LEN) or "Candidate"
        designation = designation_for_message(candidate.designation) or (
            "the role you applied for"
        )
        company = company_for_message(candidate.company)
        email = AIService._clean_email(candidate.email)

        return {
            "name": name,
            "designation": designation,
            "company": company,
            "email": email,
            "documents_needed": docs,
        }

    @staticmethod
    def _build_prompt(fields: dict[str, str]) -> str:
        return (
            "Write a professional HR email requesting identity document uploads.\n\n"
            "Use ONLY these facts (do not invent or add anything else):\n"
            f"- Candidate name: {fields['name']}\n"
            f"- Designation: {fields['designation']}\n"
            f"- Company: {fields['company'] or '(omit from message)'}\n"
            f"- Registered email: {fields['email']}\n"
            f"- Documents needed: PAN and Aadhaar\n\n"
            "Format requirements:\n"
            "- Start with 'Dear {name},'\n"
            "- One short congratulatory sentence mentioning the designation"
            + (" and company" if fields["company"] else "")
            + "\n"
            f"- Include this EXACT sentence on its own line:\n  {REQUIRED_REQUEST_SENTENCE}\n"
            "- Mention accepted formats: PDF or clear image\n"
            "- End with 'Regards,\\nHR Team'\n"
            "- No numbered lists, no resume excerpts, no phone numbers, no URLs"
        )

    @staticmethod
    def _clean_field(value: str | None, max_len: int) -> str | None:
        if not value:
            return None

        text = re.sub(r"\s+", " ", str(value).strip())
        text = text.split("\n")[0].split("|")[0].split("•")[0].strip()
        text = re.sub(r"^[:\-\s]+", "", text)
        text = re.sub(r"[:\-\s]+$", "", text)

        if RESUME_NOISE_PATTERN.search(text) and len(text) > 40:
            return None

        if len(text) > max_len:
            text = text[:max_len].rsplit(" ", 1)[0].strip()

        return text or None

    @staticmethod
    def _clean_email(email: str | None) -> str:
        if not email or "@extract.pending" in email.lower():
            return "on file"
        cleaned = email.strip().lower()
        if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", cleaned):
            return "on file"
        return cleaned

    @staticmethod
    def _clean_generated_message(raw: str) -> str:
        text = raw.strip()
        text = re.sub(r"^```(?:\w+)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                if lines:
                    lines.append("")
                continue
            if RESUME_NOISE_PATTERN.search(stripped) and "dear" not in stripped.lower():
                continue
            if re.match(r"^[\-\*•]\s+", stripped):
                continue
            lines.append(stripped)

        text = "\n".join(lines).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)

        if len(text) > MAX_MESSAGE_LEN:
            text = text[:MAX_MESSAGE_LEN].rsplit("\n", 1)[0].strip()

        if not text.lower().startswith("dear"):
            name_match = re.search(r"dear\s+[^,\n]+", text, re.I)
            if name_match:
                text = text[name_match.start() :]
            else:
                text = f"Dear Candidate,\n\n{text}"

        if "regards" not in text.lower():
            text = f"{text}\n\nRegards,\nHR Team"

        return text.strip()

    @staticmethod
    def _missing_documents(candidate: Candidate) -> list[str]:
        uploaded = {doc.document_type.lower() for doc in candidate.documents.all()}
        labels = {"pan": "PAN card", "aadhaar": "Aadhaar card"}
        return [
            labels[doc_type]
            for doc_type in REQUIRED_DOCUMENTS
            if doc_type not in uploaded
        ]

    @staticmethod
    def _template_message(candidate: Candidate) -> str:
        fields = AIService._structured_fields(candidate)
        name = fields["name"]
        congrats = AIService._congratulations_line(fields["designation"], fields["company"])

        return (
            f"Dear {name},\n\n"
            f"{congrats}\n\n"
            f"{REQUIRED_REQUEST_SENTENCE}\n"
            f"Accepted formats: PDF or clear image.\n\n"
            f"Regards,\nHR Team"
        )

    @staticmethod
    def _congratulations_line(designation: str, company: str | None) -> str:
        role = designation or "the role you applied for"
        line = (
            "Congratulations on moving forward in the hiring process "
            f"for the {role} role"
        )
        if company:
            line += f" at {company}"
        line += "."
        return line

    # Backward-compatible alias for tests
    _fallback_message = _template_message

    @staticmethod
    def _is_valid_request_message(message: str) -> bool:
        m = message.lower()
        if "pan" not in m or "aadhaar" not in m:
            return False
        if REQUIRED_REQUEST_SENTENCE.lower() not in m:
            return False
        # Ensure formats are mentioned
        if "pdf" not in m:
            return False
        if "clear image" not in m and "image" not in m:
            return False
        return True
