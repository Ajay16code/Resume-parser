from __future__ import annotations

import re

COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "react",
    "fastapi",
    "docker",
    "kubernetes",
    "aws",
    "machine learning",
    "deep learning",
    "sql",
    "pandas",
    "numpy",
}


def extract_skills(text: str) -> list[str]:
    """Simple keyword-based skill extraction."""
    normalized = re.sub(r"\s+", " ", text.lower())
    found = [skill for skill in COMMON_SKILLS if skill in normalized]
    return sorted(found)


def infer_title(text: str) -> str:
    """Heuristic inference of candidate's title/profession from resume text.

    This is a lightweight fallback for quick HR-level displays. For higher
    accuracy consider calling an LLM or using an NLP NER model.
    """
    if not text or not text.strip():
        return ""

    normalized = text.lower()
    # Common role keywords to search for
    roles = [
        "machine learning engineer",
        "data scientist",
        "machine learning",
        "ml engineer",
        "data engineer",
        "software engineer",
        "senior software engineer",
        "backend engineer",
        "frontend engineer",
        "full[- ]stack",
        "devops",
        "qa",
        "designer",
        "product manager",
        "architect",
        "cloud",
        "security",
        "researcher",
    ]

    # Look for the most specific role first
    for role in roles:
        if re.search(rf"\b{role}\b", normalized):
            return role.title()

    # Fallback: use the first short line that looks like a title (<=6 words)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:10]:
        words = line.split()
        if 1 < len(words) <= 6:
            # avoid picking contact lines with emails or phones
            if re.search(r"@|\d{3}[-\.\s]\d{3}", line):
                continue
            # avoid lines that are obviously addresses
            if re.search(r"address|www\.|http", line.lower()):
                continue
            return line.strip()

    return ""


def summarize_text(text: str, max_chars: int = 300) -> str:
    """Return a short summary (first N characters) as a quick preview."""
    if not text:
        return ""
    s = " ".join(text.strip().split())
    return s[:max_chars].rsplit(' ', 1)[0] + ("..." if len(s) > max_chars else "")
