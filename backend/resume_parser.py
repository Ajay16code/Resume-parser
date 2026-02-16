from __future__ import annotations

import re
from typing import Dict, List


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+\d{1,3}[\s-])?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})")


def _find_section_lines(lines: List[str], heading: str) -> List[str]:
    heading_low = heading.lower()
    out: List[str] = []
    capture = False
    for line in lines:
        if not line:
            if capture and out:
                break
            continue
        l = line.strip()
        if l.lower().startswith(heading_low):
            capture = True
            # skip the heading itself
            continue
        if capture:
            # stop if next heading
            if re.match(r"^[A-Z][A-Za-z ]{1,30}:?$", l):
                break
            out.append(l)
    return out


def parse_resume_text(text: str) -> Dict[str, object]:
    """Return structured fields extracted from resume text.

    Fields: name, email, phone, title, skills, summary, education (list), experience (list)
    """
    if not text:
        return {}

    # Normalize lines
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l]

    # Name heuristic: first non-empty line (if it looks like a name)
    name = ""
    if lines:
        first = lines[0]
        # avoid picking headings like 'resume' etc
        if len(first.split()) <= 6 and not re.search(r"\d|@|www\.|http", first):
            name = first

    # Email
    email_m = EMAIL_RE.search(text)
    email = email_m.group(0) if email_m else ""

    # Phone
    phone_m = PHONE_RE.search(text)
    phone = phone_m.group(0) if phone_m else ""

    # Title: try line after name if short
    title = ""
    if len(lines) > 1:
        cand = lines[1]
        if 1 < len(cand.split()) <= 6 and not re.search(r"\d|@", cand):
            title = cand

    # Summary: first 300 chars
    summary = " ".join(text.split())[:300]

    # Sections
    education = _find_section_lines(lines, "education")
    experience = _find_section_lines(lines, "experience")
    skills = _find_section_lines(lines, "skills")

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "title": title,
        "summary": summary,
        "education": education,
        "experience": experience,
        "skills_block": skills,
    }


def ats_check(text: str, job_description: str = "") -> Dict[str, object]:
    """Basic ATS (Applicant Tracking System) style checks.

    Returns a small report with an `ats_score` in [0,1] and a list of `issues`.
    This is a lightweight heuristic useful for indicating obvious problems
    (missing contact info, too-short resumes, low keyword overlap with the job).
    """
    issues: List[str] = []
    normalized = (text or "").lower()

    # Contact information
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    if not email:
        issues.append("Missing email address.")
    if not phone:
        issues.append("Missing phone number.")

    # Name check
    name_present = False
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        first = lines[0]
        if len(first.split()) <= 6 and not re.search(r"\d|@|www\.|http", first):
            name_present = True
    if not name_present:
        issues.append("Name not clearly identified at top of resume.")

    # Length check
    char_count = len(text or "")
    if char_count < 200:
        issues.append("Resume appears very short; consider adding more detail.")

    # Keyword overlap with job description
    jd = (job_description or "").lower()
    jd_tokens = [t.strip() for t in re.split(r"[,;\n]", jd) if t.strip()]
    jd_tokens = jd_tokens or [t for t in jd.split() if len(t) > 2]
    if jd_tokens:
        matches = 0
        for tok in jd_tokens:
            if tok and tok in normalized:
                matches += 1
        overlap = matches / len(jd_tokens)
    else:
        overlap = 0.0

    if overlap < 0.3:
        issues.append("Low keyword overlap with job description (may fail simple ATS filters).")

    # Compose a score: weighted heuristics (contact 30%, name 10%, length 10%, keyword 50%)
    contact_score = 1.0 if (email and phone) else 0.0
    name_score = 1.0 if name_present else 0.0
    length_score = 1.0 if char_count >= 400 else (0.5 if char_count >= 200 else 0.0)
    keyword_score = overlap

    ats_score = (0.3 * contact_score) + (0.1 * name_score) + (0.1 * length_score) + (0.5 * keyword_score)

    return {
        "ats_score": round(float(ats_score), 3),
        "overlap": round(float(overlap), 3),
        "issues": issues,
    }
