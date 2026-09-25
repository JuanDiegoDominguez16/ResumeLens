import re
from dataclasses import dataclass, asdict



# REGULAR EXPRESSIONS


# Boundaries use lookarounds instead of \b.
#
# This prevents matches such as:
#   JS      inside React.js
#   SQL     inside MySQL
#   Git     inside GitHub
#
# The dot is included in the left boundary because "." is
# commonly part of technical names such as React.js and Node.js.
#
# RIGHT only excludes word characters, so names ending in
# symbols such as C++ and C# are also supported.

LEFT = r"(?<![\w.])"
RIGHT = r"(?![\w])"


# Horizontal whitespace only.
#
# \s is NOT used inside multi-word patterns because it also
# matches line breaks, which allows a match to continue into
# the next line of the resume (for example, a degree absorbing
# the heading "Technical Skills" written on the following line).

HS = r"[ \t]"



# TECHNICAL QUALIFICATION VARIANTS

# Each item is:
#     (regular_expression, case_sensitive)
#
# Stage 1 only detects textual representations.
# It does NOT convert them into canonical qualifications.
#
# Example:
#     "React.js" -> "React.js"
#     "JS"       -> "JS"
#
# The conversion:
#     React.js -> REACT
#     JS       -> JAVASCRIPT
#
# belongs to Stage 2 (the FST).
#
# Ambiguous ordinary words (React, Vue, Spark, Java, Go...)
# are case-sensitive. Unambiguous technical terms are not.

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



# MASTER TECHNICAL PATTERN


def _build_master_pattern(variants_by_category):
    """
    Build one master regular expression containing all
    technical qualification variants.

    Each alternative receives its own named group so that,
    after a match, we can determine which category produced it.

    Longer expressions are placed before shorter expressions.
    For example:

        REST APIs
        REST API
        REST

    This ordering is necessary, not cosmetic: RIGHT accepts the
    space after "REST", so if "REST" were tried first it would
    win over "REST APIs".
    """

    entries = [
        (regex, case_sensitive, category)
        for category, variants in variants_by_category.items()
        for regex, case_sensitive in variants
    ]

    # Longest variants first.
    entries.sort(key=lambda entry: len(entry[0]), reverse=True)

    alternatives = []
    group_category = {}

    for index, (regex, case_sensitive, category) in enumerate(entries):

        group_name = f"t{index}"

        if case_sensitive:
            body = regex
        else:
            body = f"(?i:{regex})"

        alternatives.append(
            f"(?P<{group_name}>{body})"
        )

        group_category[group_name] = category

    master = (
        LEFT
        + "(?:"
        + "|".join(alternatives)
        + ")"
        + RIGHT
    )

    return re.compile(master), group_category


TECH_PATTERN, TECH_GROUP_CATEGORY = _build_master_pattern(
    TECH_VARIANTS
)



# CANDIDATE INFORMATION PATTERNS


# Candidate name.
#
# Expected in the first non-empty line that is not a resume
# heading such as "Curriculum Vitae" or "Hoja de Vida".
#
# Supports:
#   Wednesday Addams
#   **Wednesday Addams**
#   Ana María de la Torre      (lowercase particles)
#   José Rodríguez-López       (hyphenated surnames)
#
# The name must contain between 2 and 5 capitalized words.

_NAME_WORD = (
    r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    r"(?:-[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?"
)

_NAME_PARTICLE = r"(?:de|del|la|las|los|y|van|von|da|di)"

NAME_PATTERN = re.compile(
    rf"^[ \t]*"
    rf"(?:\*{{1,2}})?"
    rf"("
        rf"{_NAME_WORD}"
        rf"(?:"
            rf"{HS}+"
            rf"(?:{_NAME_PARTICLE}{HS}+)*"
            rf"{_NAME_WORD}"
        rf"){{1,4}}"
    rf")"
    rf"(?:\*{{1,2}})?"
    rf"[ \t]*$"
)


# Resume headings that may appear before the candidate name.

HEADER_PATTERN = re.compile(
    rf"^[ \t]*"
    rf"(?:\*{{1,2}})?"
    r"(?i:curriculum vitae|resume|résumé|hoja de vida|cv)"
    rf"(?:\*{{1,2}})?"
    rf"[ \t]*$"
)


# Email address.
EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])"
    r"[\w.+-]+"
    r"@"
    r"[\w-]+"
    r"(?:\.[\w-]+)*"
    r"\.[A-Za-z]{2,}"
    r"(?![\w-])"
)


# Phone number.
#
# Supports formats such as:
#   +57 300 123 4567
#   +57-300-123-4567
#   300 123 4567
#   (602) 1234567
#
# Separators are horizontal only, so a phone number cannot
# be split across two lines.

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


# Professional experience.
#
# Examples:
#   3 years of experience
#   3 years of professional experience
#   3+ years experience
#   5 yrs of experience

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


# Employment / experience date ranges.
#
# Examples:
#   2020-2024
#   2020–2024
#   2020 to 2024
#   2020-Present
#   2020 - Current

DATE_RANGE_PATTERN = re.compile(
    r"\b"
    r"(?:19|20)\d{2}"
    rf"{HS}*(?:-|–|to){HS}*"
    r"(?:(?:19|20)\d{2}|[Pp]resent|[Cc]urrent)"
    r"\b"
)


# Academic qualifications.
#
# A field word is a capitalized word that does NOT start an
# institution name. This stops the degree before
# "Universidad Icesi", "University of...", etc.

_FIELD_WORD = (
    r"(?!(?:Universi|Institut|College|School|Escuela)\w*)"
    r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ']*"
)

# A field of study: capitalized words, optionally joined
# by connectors such as "and", "y", "de", "of".
_FIELD = (
    rf"{_FIELD_WORD}"
    rf"(?:{HS}+(?:(?:and|y|de|of){HS}+)?{_FIELD_WORD})*"
)

# Examples:
#   Bachelor of Science
#   Bachelor of Science in Computer Science
#   Bachelor's degree in Computer Science
#   Master's in Data Science
#   Ph.D. Computer Science
#   B.Sc. in Computer Science
#   Ingeniería de Sistemas y Computación
#   Ingeniería Bioquímica
#   Licenciatura en Matemáticas
#
# "Bachelor" and "Master" require a connector (of / in) so that
# phrases such as "Master Chef" are not detected as degrees.

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



# FINDING DATA STRUCTURE


@dataclass
class Finding:
    """
    A piece of text recognized by a regular expression.

    text:
        Exact representation found in the resume.

    category:
        Category assigned during extraction.

    start:
        Starting character position in the original text.

    end:
        Ending character position in the original text.
    """

    text: str
    category: str
    start: int
    end: int



# GENERIC FINDING FUNCTIONS

def _findings(pattern, text, category):
    """
    Find all matches of a regular expression and convert
    them into Finding objects.
    """

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
    """
    Return True if two findings share at least one character.
    """

    return a.start < b.end and b.start < a.end



# NAME EXTRACTION

def extract_name(resume_text):
    """
    Extract the candidate name.

    The candidate name is expected in the first non-empty line,
    skipping resume headings such as "Curriculum Vitae".
    """

    for line in resume_text.splitlines():

        if not line.strip():
            continue

        if HEADER_PATTERN.match(line):
            continue

        match = NAME_PATTERN.match(line)

        if match:
            return match.group(1)

        return None

    return None



# PHONE EXTRACTION

def extract_phones(resume_text, date_ranges):
    """
    Detect phone numbers.

    Sequences such as "2015-2019 2020" have the shape of a
    phone number, so any phone candidate that overlaps a
    date range is discarded.
    """

    return [
        phone
        for phone in _findings(PHONE_PATTERN, resume_text, "Phone")
        if not any(_overlaps(phone, date) for date in date_ranges)
    ]



# TECHNICAL QUALIFICATION EXTRACTION

def extract_qualifications(resume_text):
    """
    Detect technical qualification representations.

    IMPORTANT:
    This function does NOT perform canonicalization.

    Example:

        "React.js" -> "React.js"
        "JS"       -> "JS"
        "NodeJS"   -> "NodeJS"

    The transformation into:

        REACT
        JAVASCRIPT
        NODE_JS

    belongs to Stage 2 (FST).
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



# COMPLETE EXTRACTION

def extract_resume(resume_text):
    """
    Run the complete Stage 1 extraction.

    The result is a structured representation of the
    information recognized in the resume.
    """

    qualifications = extract_qualifications(resume_text)

    # Create one list for every technical category.
    skills = {
        category: []
        for category in TECH_VARIANTS
    }

    # Place each technical finding in its category.
    for finding in qualifications:
        skills[finding.category].append(finding)

    date_ranges = _findings(
        DATE_RANGE_PATTERN,
        resume_text,
        "Experience"
    )

    return {
        "Candidate": {
            "name": extract_name(resume_text)
        },

        "Contact Information": {
            "email": _findings(
                EMAIL_PATTERN,
                resume_text,
                "Email"
            ),
            "phone": extract_phones(
                resume_text,
                date_ranges
            ),
        },

        "Academic Qualifications": _findings(
            DEGREE_PATTERN,
            resume_text,
            "Academic Qualifications"
        ),

        "Professional Experience": {
            "years": _findings(
                YEARS_EXPERIENCE_PATTERN,
                resume_text,
                "Experience"
            ),

            "date_ranges": date_ranges,
        },

        **skills,
    }



# STAGE 2 INPUT


def qualification_strings(resume_text):
    """
    Prepare the raw qualification representations for Stage 2.

    The strings are kept:
        - in their original representation;
        - in the order in which they appear;
        - without exact duplicates.

    Example:

        Resume:
            JS, React.js, JS, Git

        Output:
            ["JS", "React.js", "Git"]

    These strings are the input to the FST.
    """

    seen = set()
    ordered = []

    for finding in extract_qualifications(resume_text):

        if finding.text not in seen:

            seen.add(finding.text)
            ordered.append(finding.text)

    return ordered



# SERIALIZATION


def to_serializable(structure):
    """
    Convert Finding objects into dictionaries so the complete
    extraction result can be saved as JSON.
    """

    if isinstance(structure, Finding):
        return asdict(structure)

    if isinstance(structure, dict):
        return {
            key: to_serializable(value)
            for key, value in structure.items()
        }

    if isinstance(structure, list):
        return [
            to_serializable(value)
            for value in structure
        ]

    return structure