import re
from dataclasses import dataclass, asdict


# Regular expressions defined in formalization.md.
#
# Design decisions
# 1. Stage 1 only DETECTS textual variants. It does not decide which
#    variants are equivalent, so patterns are grouped by category and
#    never by canonical qualification. Equivalence belongs to Stage 2 (FST).
# 2. Boundaries use lookarounds instead of \b, because \b treats "." as a
#    boundary and "JS" would be found inside "React.js" or "Node.js".
# 3. Terms that are also ordinary English words (react, rest, spark...)
#    are case sensitive. Unambiguous terms are case insensitive.
# 4. All variants are merged into one master expression ordered from the
#    longest to the shortest, so each piece of text is consumed only once.

LEFT = r"(?<![\w.])"
RIGHT = r"(?![\w])"

# category -> list of (regex, case_sensitive)
TECH_VARIANTS = {
    "Programming Languages": [
        (r"JavaScript", False),
        (r"JS", True),
        (r"TypeScript", False),
        (r"TS", True),
        (r"Python", False),
    ],
    "Frameworks and Libraries": [
        (r"React\.js", False), (r"ReactJS", False), (r"React", True),
        (r"Angular", True),
        (r"Vue\.js", False), (r"VueJS", False), (r"Vue", True),
        (r"Node\.js", False), (r"NodeJS", False),
        (r"Django", False),
        (r"Spring Boot", False), (r"SpringBoot", False),
        (r"Pandas", False),
        (r"NumPy", False),
        (r"scikit[- ]learn", False), (r"sklearn", False),
        (r"Tensor Flow", False), (r"TensorFlow", False),
        (r"Py Torch", False), (r"PyTorch", False),
    ],
    "Databases": [
        (r"NoSQL database", False), (r"NoSQL DB", False), (r"NoSQL", False),
        (r"PostgreSQL", False), (r"Postgres", False),
        (r"MySQL", False),
        (r"SQL", False),
    ],
    "Tools and Technologies": [
        (r"REST APIs", True), (r"REST API", True), (r"REST", True),
        (r"GitHub Actions", False),
        (r"GitLab CI/CD", False), (r"GitLab CI", False),
        (r"Git", False),
        (r"Docker", False),
        (r"Amazon Web Services", False), (r"AWS", True),
        (r"Microsoft Azure", False), (r"Azure", True),
        (r"Google Cloud Platform", False), (r"Google Cloud", False), (r"GCP", True),
        (r"Jenkins", True),
        (r"Terraform", False),
        (r"Ansible", False),
        (r"Apache Airflow", False), (r"Airflow", True),
        (r"Apache Spark", False), (r"Spark", True),
        (r"Databricks", False),
    ],
    "Other Qualifications": [
        (r"Machine[- ]Learning Model Development", False),
    ],
}


def _build_master_pattern(variants_by_category):
    """
    Build a single alternation with one named group per variant.
    Returns the compiled pattern and a map group_name -> category.
    """
    entries = [
        (regex, sensitive, category)
        for category, variants in variants_by_category.items()
        for regex, sensitive in variants
    ]
    # Longest variants first: "REST APIs" must be tried before "REST".
    entries.sort(key=lambda e: len(e[0]), reverse=True)

    alternatives = []
    group_category = {}
    for index, (regex, sensitive, category) in enumerate(entries):
        name = f"t{index}"
        body = regex if sensitive else f"(?i:{regex})"
        alternatives.append(f"(?P<{name}>{body})")
        group_category[name] = category

    master = LEFT + "(?:" + "|".join(alternatives) + ")" + RIGHT
    return re.compile(master), group_category


TECH_PATTERN, TECH_GROUP_CATEGORY = _build_master_pattern(TECH_VARIANTS)


# Candidate data patterns.
NAME_PATTERN = re.compile(
    r"^[ \t]*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})[ \t]*$"
)

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}(?![\w-])"
)

PHONE_PATTERN = re.compile(
    r"(?<![\w+])\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?![\d])"
)

YEARS_EXPERIENCE_PATTERN = re.compile(
    r"\b\d{1,2}\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+professional)?\s+experience\b",
    re.IGNORECASE,
)

DATE_RANGE_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:(?:19|20)\d{2}|[Pp]resent|[Cc]urrent)\b"
)

_CAP_WORD = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ']*"
DEGREE_PATTERN = re.compile(
    r"(?<![\w.])"
    r"(?:Bachelor(?:'s)?|Master(?:'s)?|Ph\.?D\.?|B\.Sc\.|M\.Sc\.|Licenciatura|Ingenier[ií]a)"
    rf"(?:\s+{_CAP_WORD})*"
    rf"(?:\s+(?:of|in|en|de|and|y)\s+{_CAP_WORD}(?:\s+{_CAP_WORD})*)*"
)


@dataclass
class Finding:
    """A piece of text recognized by a regular expression."""
    text: str
    category: str
    start: int
    end: int


def _findings(pattern, text, category):
    return [Finding(m.group(0), category, m.start(), m.end())
            for m in pattern.finditer(text)]


def extract_name(resume_text):
    """The candidate name is expected in the first non-empty line."""
    for line in resume_text.splitlines():
        if line.strip():
            match = NAME_PATTERN.match(line)
            return match.group(1) if match else None
    return None


def extract_qualifications(resume_text):
    """
    Detect technical qualifications keeping the original representation.
    No canonicalization is performed.
    """
    return [
        Finding(m.group(0), TECH_GROUP_CATEGORY[m.lastgroup], m.start(), m.end())
        for m in TECH_PATTERN.finditer(resume_text)
    ]


def extract_resume(resume_text):
    """Run the whole extraction stage and return a structured result."""
    qualifications = extract_qualifications(resume_text)

    skills = {category: [] for category in TECH_VARIANTS}
    for finding in qualifications:
        skills[finding.category].append(finding)

    return {
        "Candidate": {"name": extract_name(resume_text)},
        "Contact Information": {
            "email": _findings(EMAIL_PATTERN, resume_text, "Email"),
            "phone": _findings(PHONE_PATTERN, resume_text, "Phone"),
        },
        "Academic Qualifications": _findings(DEGREE_PATTERN, resume_text,
                                             "Academic Qualifications"),
        "Professional Experience": {
            "years": _findings(YEARS_EXPERIENCE_PATTERN, resume_text, "Experience"),
            "date_ranges": _findings(DATE_RANGE_PATTERN, resume_text, "Experience"),
        },
        **skills,
    }


def qualification_strings(resume_text):
    """
    Input for Stage 2 (normalization): the raw strings in the order they
    appear, without exact duplicates.
    """
    seen = set()
    ordered = []
    for finding in extract_qualifications(resume_text):
        if finding.text not in seen:
            seen.add(finding.text)
            ordered.append(finding.text)
    return ordered


def to_serializable(structure):
    """Convert Findings to dicts so the result can be saved as JSON."""
    if isinstance(structure, Finding):
        return asdict(structure)
    if isinstance(structure, dict):
        return {k: to_serializable(v) for k, v in structure.items()}
    if isinstance(structure, list):
        return [to_serializable(v) for v in structure]
    return structure