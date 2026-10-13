import re
from dataclasses import dataclass, asdict


# ---------------------------------------------------------------------------
# REGULAR EXPRESSIONS
# ---------------------------------------------------------------------------

# Boundaries use lookarounds instead of \b.
# This prevents matches such as JS inside React.js, SQL inside MySQL,
# and Git inside GitHub.
LEFT = r"(?<![\w.])"
RIGHT = r"(?![\w])"

# Horizontal whitespace only. Using \s inside multi-word patterns would
# allow a match to continue across line breaks.
HS = r"[ \t]"


# ---------------------------------------------------------------------------
# TECHNICAL QUALIFICATION VARIANTS
# ---------------------------------------------------------------------------

# Each item is (regular_expression, case_sensitive).
# Stage 1 detects literal representations; Stage 2 performs canonicalization.
TECH_VARIANTS = {
    "Programming Languages": [
        (r"JavaScript", False),
        (r"JS", True),
        (r"TypeScript", False),
        (r"TS", True),
        (r"Python", False),
        (r"Java", True),
        (r"C\+\+", True),
        (r"C#", True),
        (r"Golang", False),
        (r"Go", True),
    ],
    "Frameworks and Libraries": [
        (r"React\.js", False),
        (r"ReactJS", False),
        (r"React", True),
        (r"Angular", True),
        (r"Vue\.js", False),
        (r"VueJS", False),
        (r"Vue", True),
        (r"Node\.js", False),
        (r"NodeJS", False),
        (r"Express\.js", False),
        (r"ExpressJS", False),
        (r"Django", False),
        (r"Flask", True),
        (r"FastAPI", False),
        (r"Spring Boot", False),
        (r"SpringBoot", False),
        (r"Pandas", False),
        (r"NumPy", False),
        (r"Matplotlib", False),
        (r"scikit[- ]learn", False),
        (r"sklearn", False),
        (r"Tensor Flow", False),
        (r"TensorFlow", False),
        (r"Py Torch", False),
        (r"PyTorch", False),
        (r"Keras", False),
    ],
    "Databases": [
        (r"NoSQL databases?", False),
        (r"NoSQL DB", False),
        (r"NoSQL", False),
        (r"PostgreSQL", False),
        (r"Postgres", False),
        (r"MySQL", False),
        (r"SQL", False),
        (r"MongoDB", False),
        (r"Mongo", True),
        (r"Redis", False),
    ],
    "Tools and Technologies": [
        (r"REST APIs", True),
        (r"REST API", True),
        (r"REST", True),
        (r"GitHub Actions", False),
        (r"GitLab CI/CD", False),
        (r"GitLab CI", False),
        (r"Git", False),
        (r"Docker", False),
        (r"Kubernetes", False),
        (r"K8s", False),
        (r"Amazon Web Services", False),
        (r"AWS", True),
        (r"Microsoft Azure", False),
        (r"Azure", True),
        (r"Google Cloud Platform", False),
        (r"Google Cloud", False),
        (r"GCP", True),
        (r"Jenkins", True),
        (r"Terraform", False),
        (r"Ansible", False),
        (r"Apache Airflow", False),
        (r"Airflow", True),
        (r"Apache Spark", False),
        (r"Spark", True),
        (r"Databricks", False),
    ],
    "Other Qualifications": [
        (r"Machine[- ]Learning Model Development", False),
        (r"Machine[- ]Learning", False),
        (r"ML", True),
        (r"Deep[- ]Learning", False),
    ],
}


def _build_master_pattern(variants_by_category):
    """Build one master regex and map each named group to its category."""
    entries = [
        (regex, case_sensitive, category)
        for category, variants in variants_by_category.items()
        for regex, case_sensitive in variants
    ]
    # Longest variants first, so REST APIs wins over REST.
    entries.sort(key=lambda entry: len(entry[0]), reverse=True)

    alternatives = []
    group_category = {}

    for index, (regex, case_sensitive, category) in enumerate(entries):
        group_name = f"t{index}"
        body = regex if case_sensitive else f"(?i:{regex})"
        alternatives.append(f"(?P<{group_name}>{body})")
        group_category[group_name] = category

    master = LEFT + "(?:" + "|".join(alternatives) + ")" + RIGHT
    return re.compile(master), group_category


TECH_PATTERN, TECH_GROUP_CATEGORY = _build_master_pattern(TECH_VARIANTS)


# ---------------------------------------------------------------------------
# CANDIDATE INFORMATION PATTERNS
# ---------------------------------------------------------------------------

# Plain-text names: 2–5 capitalized words, optional lowercase particles,
# and optional hyphenated surnames.
_NAME_WORD = (
    r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    r"(?:-[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?"
)
_NAME_PARTICLE = r"(?:de|del|la|las|los|y|van|von|da|di)"

NAME_PATTERN = re.compile(
    rf"^[ \t]*(?:\*\*?)?"
    rf"("
    rf"{_NAME_WORD}"
    rf"(?:{HS}+(?:(?:{_NAME_PARTICLE}){HS}+)?{_NAME_WORD})"
    rf"{{1,4}}"
    rf")"
    rf"(?:\*\*?)?[ \t]*$"
)

# Structured candidate profile, for example:
# personal {
#     name: "Victor von Doom"
# }
STRUCTURED_NAME_PATTERN = re.compile(
    r'^[ \t]*name[ \t]*:[ \t]*"([^"\n]+)"[ \t]*$',
    re.IGNORECASE,
)

HEADER_PATTERN = re.compile(
    r"^[ \t]*(?:\*\*?)?"
    r"(?i:curriculum vitae|resume|résumé|hoja de vida|cv)"
    r"(?:\*\*?)?[ \t]*$"
)

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])"
    r"[\w.+-]+"
    r"@"
    r"[\w-]+"
    r"(?:\.[\w-]+)*"
    r"\.[A-Za-z]{2,}"
    r"(?![\w-])"
)

PHONE_PATTERN = re.compile(
    r"(?<![\w+])"
    r"(?:\+\d{1,3}[ \t.-]?)?"
    r"(?:\(\d{2,4}\)|\d{2,4})"
    r"[ \t.-]?"
    r"\d{3,4}"
    r"[ \t.-]?"
    r"\d{3,4}"
    r"(?!\d)"
)

YEARS_EXPERIENCE_PATTERN = re.compile(
    r"\b"
    r"\d{1,2}\+?"
    rf"{HS}*"
    r"(?:years?|yrs?)"
    rf"(?:{HS}+of)?"
    rf"(?:{HS}+professional)?"
    rf"{HS}+experience"
    r"\b",
    re.IGNORECASE,
)

DATE_RANGE_PATTERN = re.compile(
    r"\b"
    r"(?:19|20)\d{2}"
    rf"{HS}*(?:-|–|to){HS}*"
    r"(?:(?:19|20)\d{2}|[Pp]resent|[Cc]urrent)"
    r"\b"
)


# ---------------------------------------------------------------------------
# STRUCTURED PROFESSIONAL EXPERIENCE
# ---------------------------------------------------------------------------

# Supports records such as:
# experience {
#     title: "Senior DevOps Engineer"
#     company: "Latveria Systems"
#     start_date: "2021-01"
#     end_date: "Present"
#     description: "Designed and maintained..."
# }
#
# Also supports the simplified format using position and years.
STRUCTURED_EXPERIENCE_PATTERN = re.compile(
    r"\bexperience\s*\{([^{}]*)\}",
    re.IGNORECASE,
)

EXPERIENCE_FIELD_PATTERNS = {
    "title": re.compile(
        r'^[ \t]*title[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "position": re.compile(
        r'^[ \t]*position[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "company": re.compile(
        r'^[ \t]*company[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "start_date": re.compile(
        r'^[ \t]*start_date[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "end_date": re.compile(
        r'^[ \t]*end_date[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "description": re.compile(
        r'^[ \t]*description[ \t]*:[ \t]*"([^"\n]*)"[ \t]*$',
        re.IGNORECASE | re.MULTILINE,
    ),
    "years": re.compile(
        r"^[ \t]*years[ \t]*:[ \t]*(\d+)[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}


def extract_structured_experiences(resume_text):
    """Extract structured experience blocks without affecting classification."""
    records = []

    for block in STRUCTURED_EXPERIENCE_PATTERN.finditer(resume_text):
        body = block.group(1)
        record = {}

        for field, pattern in EXPERIENCE_FIELD_PATTERNS.items():
            match = pattern.search(body)
            record[field] = match.group(1).strip() if match else ""

        # Normalize the two supported field names into one display field.
        record["title"] = record["title"] or record["position"]

        if record["title"] or record["company"]:
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# ACADEMIC QUALIFICATIONS
# ---------------------------------------------------------------------------

_FIELD_WORD = (
    r"(?!(?:Universi|Institut|College|School|Escuela)\w*)"
    r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ']*"
)

_FIELD = (
    rf"{_FIELD_WORD}"
    rf"(?:{HS}+(?:(?:and|y|de|of){HS}+)?{_FIELD_WORD})*"
)

DEGREE_PATTERN = re.compile(
    r"(?<![\w.])"
    r"(?:"
    r"(?:Bachelor|Master)(?:'s)?"
    rf"(?:{HS}+[Dd]egree)?"
    rf"(?:{HS}+of{HS}+{_FIELD_WORD}(?:{HS}+{_FIELD_WORD})*)?"
    rf"{HS}+(?:of|in){HS}+{_FIELD}"
    r"|(?:Ph\.D\.?|B\.Sc\.?|M\.Sc\.?)"
    rf"(?:{HS}+in)?"
    rf"{HS}+{_FIELD}"
    r"|(?:Licenciatura|Ingenier[ií]a)"
    rf"{HS}+(?:(?:en|de){HS}+)?{_FIELD}"
    r")"
)


# ---------------------------------------------------------------------------
# FINDING DATA STRUCTURE AND HELPERS
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A piece of text recognized by a regular expression."""

    text: str
    category: str
    start: int
    end: int


def _findings(pattern, text, category):
    """Find all matches and convert them into Finding objects."""
    return [
        Finding(
            text=match.group(0),
            category=category,
            start=match.start(),
            end=match.end(),
        )
        for match in pattern.finditer(text)
    ]


def _overlaps(a, b):
    """Return True if two findings share at least one character."""
    return a.start < b.end and b.start < a.end


# ---------------------------------------------------------------------------
# NAME EXTRACTION
# ---------------------------------------------------------------------------

def extract_name(resume_text):
    """
    Extract a candidate name from either:
    - a structured `name: "..."` field; or
    - the first non-empty line containing a plain-text name.
    """
    for line in resume_text.splitlines():
        match = STRUCTURED_NAME_PATTERN.match(line)
        if match:
            return match.group(1).strip()

    for line in resume_text.splitlines():
        if not line.strip():
            continue
        if HEADER_PATTERN.match(line):
            continue

        match = NAME_PATTERN.match(line)
        if match:
            return match.group(1).strip()

        # Preserve the original plain-text behavior: only the first
        # non-empty, non-heading line is considered a plain-text name.
        return None

    return None


# ---------------------------------------------------------------------------
# PHONE EXTRACTION
# ---------------------------------------------------------------------------

def extract_phones(resume_text, date_ranges):
    """
    Detect phone numbers. Discard candidates that overlap date ranges,
    since sequences such as 2015-2019 can resemble phone numbers.
    """
    return [
        phone
        for phone in _findings(PHONE_PATTERN, resume_text, "Phone")
        if not any(_overlaps(phone, date) for date in date_ranges)
    ]


# ---------------------------------------------------------------------------
# TECHNICAL QUALIFICATION EXTRACTION
# ---------------------------------------------------------------------------

def extract_qualifications(resume_text):
    """
    Detect literal technical qualification representations.
    Canonicalization belongs to Stage 2 (the FST).
    """
    findings = []

    for match in TECH_PATTERN.finditer(resume_text):
        category = TECH_GROUP_CATEGORY[match.lastgroup]
        findings.append(
            Finding(
                text=match.group(0),
                category=category,
                start=match.start(),
                end=match.end(),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# COMPLETE EXTRACTION
# ---------------------------------------------------------------------------

def extract_resume(resume_text):
    """
    Run Stage 1 extraction and return a structured representation.

    Existing extraction keys are preserved. The `records` list adds
    structured professional experience for the Streamlit presentation.
    """
    qualifications = extract_qualifications(resume_text)

    # Create one list for every technical category.
    skills = {category: [] for category in TECH_VARIANTS}

    # Place each technical finding in its category.
    for finding in qualifications:
        skills[finding.category].append(finding)

    date_ranges = _findings(
        DATE_RANGE_PATTERN,
        resume_text,
        "Experience",
    )

    structured_experiences = extract_structured_experiences(resume_text)

    return {
        "Candidate": {
            "name": extract_name(resume_text),
        },
        "Contact Information": {
            "email": _findings(
                EMAIL_PATTERN,
                resume_text,
                "Email",
            ),
            "phone": extract_phones(resume_text, date_ranges),
        },
        "Academic Qualifications": _findings(
            DEGREE_PATTERN,
            resume_text,
            "Academic Qualifications",
        ),
        "Professional Experience": {
            "years": _findings(
                YEARS_EXPERIENCE_PATTERN,
                resume_text,
                "Experience",
            ),
            "date_ranges": date_ranges,
            "records": structured_experiences,
        },
        **skills,
    }


# ---------------------------------------------------------------------------
# STAGE 2 INPUT
# ---------------------------------------------------------------------------

def qualification_strings(resume_text):
    """
    Prepare raw qualification representations for Stage 2.

    Keep original spelling and order, removing exact duplicates only.
    """
    seen = set()
    ordered = []

    for finding in extract_qualifications(resume_text):
        if finding.text not in seen:
            seen.add(finding.text)
            ordered.append(finding.text)

    return ordered


# ---------------------------------------------------------------------------
# SERIALIZATION
# ---------------------------------------------------------------------------

def to_serializable(structure):
    """Convert Finding objects and nested structures into JSON-safe values."""
    if isinstance(structure, Finding):
        return asdict(structure)

    if isinstance(structure, dict):
        return {
            key: to_serializable(value)
            for key, value in structure.items()
        }

    if isinstance(structure, list):
        return [to_serializable(value) for value in structure]

    return structure
