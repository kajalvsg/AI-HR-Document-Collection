import re
from dataclasses import dataclass, field

KEY_FIELDS = ("name", "email", "phone", "company", "designation", "skills")

# Local: must start/end with alphanumeric; domain with valid TLD (word boundaries).
EMAIL_BOUNDARY_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})"
    r"@"
    r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)"
    r"(\.[A-Za-z]{2,63})"
    r"(?![A-Za-z0-9._%+-])",
    re.IGNORECASE,
)

# Strict full-string validation after cleaning.
EMAIL_STRICT_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"\.[A-Za-z]{2,63}$",
    re.IGNORECASE,
)

# Longer prefixes first; "pe" handled with extra corroboration rules.
EMAIL_LOCAL_PREFIXES = (
    "email",
    "e-mail",
    "e_mail",
    "contact",
    "mail",
    "pe",
)

LABEL_EMAIL_PATTERNS = (
    re.compile(
        r"(?:^|\n)\s*e[-\s]?mail\s*[:\-]\s*"
        r"([A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:^|\n)\s*e[-\s]?mail\s+"
        r"([A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        re.IGNORECASE,
    ),
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?"
)
LABEL_PATTERNS = {
    "name": re.compile(r"(?:^|\n)\s*(?:name|full\s*name)\s*[:\-]\s*(.+)", re.I),
    "email": LABEL_EMAIL_PATTERNS[0],
    "phone": re.compile(
        r"(?:^|\n)\s*(?:phone|mobile|contact|tel)\s*[:\-]\s*([+\d()\s\-]{8,20})",
        re.I,
    ),
    "company": re.compile(
        r"(?:^|\n)\s*(?:company|organization|employer|current\s+company)\s*[:\-]\s*(.+)",
        re.I,
    ),
    "designation": re.compile(
        r"(?:^|\n)\s*(?:designation|title|role|position|job\s*title)\s*[:\-]\s*(.+)",
        re.I,
    ),
    "skills": re.compile(
        r"(?:^|\n)\s*(?:skills|technical\s+skills|core\s+skills)\s*[:\-]\s*(.+)",
        re.I | re.S,
    ),
}

EXPERIENCE_AT_PATTERN = re.compile(
    r"(?:at|@)\s+([A-Z][A-Za-z0-9&\s.,'-]{2,60})(?:\s*[|,|\n]|$)"
)
TITLE_LINE_PATTERN = re.compile(
    r"(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})\s*(?:\||-)\s*([A-Za-z0-9&\s.'-]{2,80})"
)

COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "node", "nodejs",
    "flask", "django", "sql", "mysql", "postgresql", "mongodb", "aws", "azure",
    "docker", "kubernetes", "git", "html", "css", "tailwind", "rest", "api",
    "machine learning", "data analysis", "excel", "communication", "leadership",
    "c++", "c#", ".net", "spring", "hibernate", "redis", "kafka", "spark",
    "pandas", "numpy", "tensorflow", "pytorch", "agile", "scrum", "jira",
}


@dataclass
class ExtractionResult:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    designation: str | None = None
    skills: list[str] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    overall_confidence: float = 0.0
    extraction_status: str = "Failed"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "designation": self.designation,
            "skills": self.skills,
            "confidence_scores": self.confidence_scores,
            "overall_confidence": self.overall_confidence,
            "extraction_status": self.extraction_status,
        }


class CandidateExtractionService:
    @staticmethod
    def extract(text: str) -> ExtractionResult:
        if not text or not text.strip():
            result = ExtractionResult(extraction_status="Failed")
            result.confidence_scores = {f: 0.0 for f in KEY_FIELDS}
            return result

        normalized = text.strip()
        lines = [ln.strip() for ln in normalized.split("\n") if ln.strip()]

        result = ExtractionResult()
        result.email, result.confidence_scores["email"] = (
            CandidateExtractionService._extract_email(normalized)
        )
        result.phone, result.confidence_scores["phone"] = (
            CandidateExtractionService._extract_phone(normalized)
        )
        result.name, result.confidence_scores["name"] = (
            CandidateExtractionService._extract_name(normalized, lines, result.email)
        )
        result.company, result.confidence_scores["company"] = (
            CandidateExtractionService._extract_company(normalized, lines)
        )
        result.designation, result.confidence_scores["designation"] = (
            CandidateExtractionService._extract_designation(normalized, lines)
        )
        result.skills, result.confidence_scores["skills"] = (
            CandidateExtractionService._extract_skills(normalized)
        )

        result.overall_confidence = CandidateExtractionService._overall_confidence(
            result.confidence_scores
        )
        result.extraction_status = CandidateExtractionService._resolve_status(
            result, result.confidence_scores
        )
        return result

    @staticmethod
    def _extract_email(text: str) -> tuple[str | None, float]:
        candidates: list[tuple[str, float, int]] = []

        for pattern in LABEL_EMAIL_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(1).strip().rstrip(".,;)>]")
                cleaned = CandidateExtractionService.normalize_email(raw, text)
                if cleaned:
                    candidates.append((cleaned, 0.95, match.start()))

        for match in EMAIL_BOUNDARY_PATTERN.finditer(text):
            raw = f"{match.group(1)}@{match.group(2)}{match.group(3)}"
            cleaned = CandidateExtractionService.normalize_email(raw, text)
            if cleaned:
                score = 0.8 if match.start() < 500 else 0.65
                candidates.append((cleaned, score, match.start()))

        if not candidates:
            return None, 0.0

        best = CandidateExtractionService._select_best_email(candidates)
        return best[0], best[1]

    @staticmethod
    def normalize_email(raw: str, context: str = "") -> str | None:
        """Validate and clean a single email string. Used by upload flow."""
        if not raw:
            return None

        candidate = raw.strip().lower().rstrip(".,;)>]")
        if candidate.count("@") != 1:
            return None

        local, domain = candidate.split("@", 1)
        local = CandidateExtractionService._clean_local_part(local, context)
        if not local:
            return None

        email = f"{local}@{domain}"
        if not CandidateExtractionService.is_valid_email(email):
            return None
        return email

    @staticmethod
    def is_valid_email(email: str) -> bool:
        if not email or email.count("@") != 1:
            return False
        local, domain = email.rsplit("@", 1)
        if not local or not domain or "." not in domain:
            return False
        tld = domain.rsplit(".", 1)[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False
        if domain.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            return False
        return bool(EMAIL_STRICT_PATTERN.fullmatch(email))

    @staticmethod
    def _clean_local_part(local: str, context: str) -> str | None:
        local = local.lower().strip("._-")
        if not local:
            return None

        raw_locals = [
            m.group(1).lower()
            for m in EMAIL_BOUNDARY_PATTERN.finditer(context or local)
        ]
        changed = True
        while changed:
            changed = False
            for prefix in EMAIL_LOCAL_PREFIXES:
                if not local.startswith(prefix) or len(local) <= len(prefix) + 2:
                    continue
                stripped = local[len(prefix) :]
                if not CandidateExtractionService._is_plausible_local(stripped):
                    continue
                if not CandidateExtractionService._should_strip_prefix(
                    prefix, local, stripped, context, raw_locals
                ):
                    continue
                local = stripped
                changed = True
                break

        return local if CandidateExtractionService._is_plausible_local(local) else None

    @staticmethod
    def _is_plausible_local(local: str) -> bool:
        if not local or len(local) > 64:
            return False
        if local.startswith(".") or local.endswith("."):
            return False
        return bool(re.fullmatch(r"[a-z0-9][a-z0-9._%+-]*", local))

    @staticmethod
    def _should_strip_prefix(
        prefix: str,
        original_local: str,
        stripped_local: str,
        context: str,
        raw_locals: list[str],
    ) -> bool:
        # Longer semantic prefixes (email, mail, contact) can be stripped when plausible.
        if len(prefix) > 2:
            return True

        # Short prefix "pe" — corroboration or safe heuristic (avoids peterson@ → terson@).
        if prefix == "pe":
            if CandidateExtractionService._corroborates_clean_local(
                stripped_local, context
            ):
                return True
            if CandidateExtractionService._has_email_label_near(context, stripped_local):
                return True
            for other in raw_locals:
                if (
                    other != original_local
                    and other.endswith(stripped_local)
                    and other[: -len(stripped_local)].lower() in EMAIL_LOCAL_PREFIXES
                ):
                    return True
            # Concatenated "e-mail" residue: pe + long local embedded in same token.
            if (
                original_local.startswith("pe")
                and len(stripped_local) >= 8
                and stripped_local in original_local
            ):
                return True
            return False

        return True

    @staticmethod
    def _corroborates_clean_local(local: str, context: str) -> bool:
        if not context:
            return False
        ctx = context.lower()
        if re.search(
            rf"(?:^|[\s:(\[]){re.escape(local)}@",
            ctx,
            re.MULTILINE,
        ):
            return True
        if re.search(
            rf"e[-\s]?mail\s*[:\-]?\s*{re.escape(local)}@",
            ctx,
        ):
            return True
        return False

    @staticmethod
    def _has_email_label_near(context: str, local: str) -> bool:
        return bool(
            re.search(
                rf"e[-\s]?mail\s*[:\-\s]+{re.escape(local)}@",
                context,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _select_best_email(
        candidates: list[tuple[str, float, int]],
    ) -> tuple[str, float, int]:
        """Pick highest score, then earliest position, then shortest local part."""
        unique: dict[str, tuple[float, int]] = {}
        for email, score, pos in candidates:
            if email not in unique or score > unique[email][0]:
                unique[email] = (score, pos)

        ranked = sorted(
            unique.items(),
            key=lambda item: (
                -item[1][0],
                item[1][1],
                len(item[0].split("@", 1)[0]),
            ),
        )
        email, (score, pos) = ranked[0]
        return email, score, pos

    @staticmethod
    def _extract_phone(text: str) -> tuple[str | None, float]:
        label_match = LABEL_PATTERNS["phone"].search(text)
        if label_match:
            raw = re.sub(r"\s+", " ", label_match.group(1).strip())
            digits = re.sub(r"\D", "", raw)
            if 10 <= len(digits) <= 15:
                return raw, 0.9

        for match in PHONE_PATTERN.finditer(text):
            raw = match.group(0).strip()
            digits = re.sub(r"\D", "", raw)
            if 10 <= len(digits) <= 15:
                confidence = 0.75 if match.start() < 800 else 0.55
                return raw, confidence
        return None, 0.0

    @staticmethod
    def _extract_name(
        text: str, lines: list[str], email: str | None
    ) -> tuple[str | None, float]:
        label_match = LABEL_PATTERNS["name"].search(text)
        if label_match:
            name = label_match.group(1).strip().split("\n")[0][:120]
            if CandidateExtractionService._looks_like_name(name):
                return name.title(), 0.92

        if lines:
            first = lines[0]
            if CandidateExtractionService._looks_like_name(first) and "@" not in first:
                if email and email.split("@")[0].lower() in first.lower():
                    return first.title(), 0.8
                if len(first.split()) <= 5:
                    return first.title(), 0.65

        if email:
            local = email.split("@")[0].replace(".", " ").replace("_", " ")
            if 1 < len(local.split()) <= 4:
                return local.title(), 0.45

        return None, 0.0

    @staticmethod
    def _extract_company(text: str, lines: list[str]) -> tuple[str | None, float]:
        label_match = LABEL_PATTERNS["company"].search(text)
        if label_match:
            company = label_match.group(1).strip().split("\n")[0][:120]
            return company, 0.88

        exp_match = EXPERIENCE_AT_PATTERN.search(text)
        if exp_match:
            return exp_match.group(1).strip(), 0.6

        for line in lines:
            lower = line.lower()
            if "experience" in lower or "employment" in lower:
                continue
            if " at " in lower:
                parts = re.split(r"\s+at\s+", line, maxsplit=1, flags=re.I)
                if len(parts) == 2 and len(parts[1]) > 2:
                    return parts[1].strip()[:120], 0.55

        title_match = TITLE_LINE_PATTERN.search(text)
        if title_match:
            return title_match.group(2).strip()[:120], 0.5

        return None, 0.0

    @staticmethod
    def _extract_designation(text: str, lines: list[str]) -> tuple[str | None, float]:
        label_match = LABEL_PATTERNS["designation"].search(text)
        if label_match:
            role = label_match.group(1).strip().split("\n")[0][:120]
            return role, 0.9

        title_match = TITLE_LINE_PATTERN.search(text)
        if title_match:
            return title_match.group(1).strip()[:120], 0.65

        role_keywords = (
            "engineer",
            "developer",
            "manager",
            "analyst",
            "consultant",
            "lead",
            "architect",
            "intern",
            "director",
            "specialist",
        )
        for line in lines[:12]:
            lower = line.lower()
            if any(kw in lower for kw in role_keywords) and len(line) < 80:
                return line.strip()[:120], 0.5

        return None, 0.0

    @staticmethod
    def _extract_skills(text: str) -> tuple[list[str], float]:
        label_match = LABEL_PATTERNS["skills"].search(text)
        skills: list[str] = []

        if label_match:
            block = label_match.group(1).strip()
            skills = CandidateExtractionService._parse_skill_tokens(block)
            if skills:
                return skills[:30], 0.88

        lower_text = text.lower()
        found = []
        for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
            if skill in lower_text and skill not in {s.lower() for s in found}:
                found.append(skill.title() if skill.islower() else skill)

        section_match = re.search(
            r"(?:skills|technologies|tech\s*stack)\s*[:\-]?\s*([\s\S]{10,400})",
            text,
            re.I,
        )
        if section_match and len(found) < 3:
            extra = CandidateExtractionService._parse_skill_tokens(
                section_match.group(1)
            )
            for item in extra:
                if item.lower() not in {s.lower() for s in found}:
                    found.append(item)

        if found:
            confidence = min(0.85, 0.45 + 0.05 * len(found))
            return found[:30], confidence
        return [], 0.0

    @staticmethod
    def _parse_skill_tokens(block: str) -> list[str]:
        block = re.split(r"\n\s*\n", block)[0]
        tokens = re.split(r"[,;|•\n/]", block)
        skills = []
        for token in tokens:
            cleaned = token.strip(" -•\t")
            if 2 <= len(cleaned) <= 40 and not cleaned.isdigit():
                skills.append(cleaned)
        return skills

    @staticmethod
    def _looks_like_name(value: str) -> bool:
        if not value or "@" in value or any(c.isdigit() for c in value):
            return False
        words = value.split()
        if not 1 <= len(words) <= 5:
            return False
        return all(re.match(r"^[A-Za-z][A-Za-z.'-]*$", w) for w in words)

    @staticmethod
    def _overall_confidence(scores: dict[str, float]) -> float:
        values = [scores.get(f, 0.0) for f in KEY_FIELDS]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    @staticmethod
    def _resolve_status(result: ExtractionResult, scores: dict[str, float]) -> str:
        core_present = sum(
            1
            for field in ("name", "email", "phone", "company", "designation")
            if getattr(result, field)
        )
        if core_present == 0 and not result.skills:
            return "Failed"

        strong_fields = sum(1 for f in KEY_FIELDS if scores.get(f, 0) >= 0.6)
        if strong_fields >= 4 and result.email:
            return "Parsed"
        if core_present >= 2 or result.skills:
            return "Partial"
        return "Failed"
