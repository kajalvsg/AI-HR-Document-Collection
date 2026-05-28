"""Clean company and designation strings for storage and HR messages."""

import re

MAX_COMPANY_WORDS = 4
MAX_DESIGNATION_WORDS = 5

# Cut remainder from this word onward (case-insensitive).
_TRUNCATE_MARKERS = re.compile(
    r"\b(?:previously\s+at|formerly\s+at|created|built|developed|worked\s+on)\b",
    re.IGNORECASE,
)

_COMPANY_NOISE_WORDS = frozenset(
    {
        "created",
        "built",
        "developed",
        "worked",
        "previously",
        "formerly",
        "module",
        "modules",
        "unified",
        "generic",
        "notification",
        "notifications",
        "experience",
        "skills",
        "resume",
        "project",
        "projects",
        "responsible",
        "implemented",
        "designed",
        "maintained",
        "using",
        "firm-wide",
        "quant",
    }
)

_DESIGNATION_NOISE_WORDS = _COMPANY_NOISE_WORDS | frozenset(
    {"hungerbox", "unified", "module"}
)

_ROLE_KEYWORDS = (
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
    "associate",
    "executive",
    "officer",
    "scientist",
    "designer",
    "administrator",
    "coordinator",
    "recruiter",
    "tester",
    "qa",
)

# Longest phrases first so "Software Engineer Intern" is not cut at "Engineer".
_ROLE_TITLE_PHRASES = tuple(
    sorted(
        (
            "software engineer intern",
            "software development engineer intern",
            "software development engineer",
            "software engineer",
            "data engineer intern",
            "data scientist intern",
            "product manager intern",
            "business analyst intern",
            "technical team member",
            "team member",
            "engineer intern",
            "developer intern",
            "engineering intern",
            "intern",
            "engineer",
            "developer",
            "manager",
            "analyst",
            "consultant",
            "architect",
            "director",
            "specialist",
            "associate",
            "coordinator",
            "administrator",
            "scientist",
            "designer",
            "tester",
            "trainee",
            "fellow",
            "member",
        ),
        key=len,
        reverse=True,
    )
)

_LOCATION_TAIL = re.compile(
    r",|\b(?:india|usa|uk|uae|remote|bangalore|bengaluru|mumbai|delhi|hyderabad|"
    r"pune|chennai|kolkata|gurgaon|gurugram|noida)\b",
    re.IGNORECASE,
)


def clean_company(value: str | None) -> str | None:
    """Return a short organization name (max 4 words) or None."""
    text = _normalize_and_truncate(value)
    if not text:
        return None
    text = _limit_words(text, MAX_COMPANY_WORDS)
    return text or None


def clean_designation(value: str | None) -> str | None:
    """Return a short job title (max 5 words) or None."""
    text = _normalize_and_truncate(value)
    if not text:
        return None
    text = _take_title_segment(text)
    text = strip_trailing_location_from_title(text)
    text = _limit_words(text, MAX_DESIGNATION_WORDS)
    return text or None


def strip_trailing_location_from_title(text: str) -> str:
    """Remove trailing city/country from a role line (keeps full titles like Intern)."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    lower = cleaned.lower()
    title_end = -1
    for phrase in _ROLE_TITLE_PHRASES:
        index = lower.find(phrase)
        if index == -1:
            continue
        end = index + len(phrase)
        if end > title_end:
            title_end = end

    if title_end == -1:
        return cleaned

    title = cleaned[:title_end].strip()
    remainder = cleaned[title_end:].strip()
    if remainder and _LOCATION_TAIL.search(remainder):
        return title
    return cleaned


def is_usable_company(cleaned: str | None, original: str | None = None) -> bool:
    """True if cleaned company is safe to mention in an HR message."""
    if not cleaned:
        return False
    if _looks_noisy(cleaned, _COMPANY_NOISE_WORDS):
        return False
    if len(cleaned.split()) > MAX_COMPANY_WORDS:
        return False
    if original and _original_suggests_noisy_company(original, cleaned):
        return False
    return True


def is_usable_designation(cleaned: str | None) -> bool:
    """True if cleaned string looks like a job title."""
    if not cleaned:
        return False
    if len(cleaned.split()) > MAX_DESIGNATION_WORDS:
        return False
    if _looks_noisy(cleaned, _DESIGNATION_NOISE_WORDS):
        return False
    lower = cleaned.lower()
    if any(kw in lower for kw in _ROLE_KEYWORDS):
        return True
    words = cleaned.split()
    if 1 <= len(words) <= 3 and words[0][0].isupper():
        return True
    return False


def company_for_message(
    value: str | None, *, already_cleaned: bool = False
) -> str | None:
    cleaned = value if already_cleaned else clean_company(value)
    original = None if already_cleaned else value
    if is_usable_company(cleaned, original):
        return cleaned
    return None


def designation_for_message(
    value: str | None, *, already_cleaned: bool = False
) -> str | None:
    cleaned = value if already_cleaned else clean_designation(value)
    if is_usable_designation(cleaned):
        return cleaned
    return None


def _normalize_and_truncate(value: str | None) -> str | None:
    if not value:
        return None

    text = re.sub(r"\s+", " ", str(value).strip())
    text = text.split("\n")[0].strip()
    if not text:
        return None

    for sep in (";", "|"):
        if sep in text:
            text = text.split(sep, 1)[0].strip()

    if "," in text:
        head, tail = text.split(",", 1)
        if re.search(
            r"\b(?:previously|formerly|created|built|developed|worked)\b",
            tail,
            re.I,
        ):
            text = head.strip()

    text = re.split(r"\s+[-–—]\s+", text, maxsplit=1)[0].strip()

    marker = _TRUNCATE_MARKERS.search(text)
    if marker:
        text = text[: marker.start()].strip()

    text = re.sub(r"^[:\-\s]+", "", text)
    text = re.sub(r"[:\-\s.,;]+$", "", text)
    return text or None


def _take_title_segment(text: str) -> str:
    """Prefer segment before '|' or ' - ' when it looks like a title."""
    if "|" in text:
        left, right = text.split("|", 1)
        if _segment_has_role_keyword(left):
            return left.strip()
        if _segment_has_role_keyword(right):
            return right.strip()

    if re.search(r"\s+[-–—]\s+", text):
        parts = re.split(r"\s+[-–—]\s+", text)
        for part in parts:
            if _segment_has_role_keyword(part):
                return part.strip()

    return text


def _segment_has_role_keyword(segment: str) -> bool:
    lower = segment.lower()
    return any(kw in lower for kw in _ROLE_KEYWORDS)


def _limit_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _looks_noisy(text: str, noise_words: frozenset[str]) -> bool:
    lower = text.lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9'-]*", lower)
    if any(token in noise_words for token in tokens):
        return True
    if re.search(r"\b(on|at|for|with|and)\s+(?:firm|the|a)\b", lower):
        return True
    if len(text) > 50 and sum(1 for c in text if c.islower()) > len(text) * 0.6:
        return True
    return False


def _original_suggests_noisy_company(original: str, cleaned: str) -> bool:
    orig = original.strip()
    head = orig.split(";")[0].split("|")[0].strip()
    if head != orig:
        return _looks_noisy(head, _COMPANY_NOISE_WORDS) or len(
            head.split()
        ) > MAX_COMPANY_WORDS
    if _TRUNCATE_MARKERS.search(orig):
        return True
    if len(orig.split()) > MAX_COMPANY_WORDS + 2:
        return True
    return _looks_noisy(orig, _COMPANY_NOISE_WORDS)
