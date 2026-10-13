"""
The candidate profile generator, Stage 4.

This module writes the result of the first three stages as a sentence of the
Candidate Profile Language. It is the only place in the system that knows how
that language is spelled, and it knows nothing about how the information was
obtained.

    extraction, normalization, classification
                    |
                    v
            render(...)  ->  candidate profile source
                    |
                    v
            validator.validate(source)


WHAT IT WRITES, AND WHAT IT REFUSES TO INVENT

Every value in the profile comes from a stage: the name and the contact
details from Stage 1, the skills from Stage 2, the classifications from
Stage 3. Nothing is derived here, and nothing is filled in with a plausible
default, because a candidate profile is a statement about a person and an
invented value in it would be indistinguishable from an extracted one.

Where the résumé said nothing and the grammar requires a value, the generator
therefore writes an empty string rather than a guess:

    name: ""        the résumé's first line was not a name
    field: ""       the degree names no field of study
    position: ""    the résumé states years of experience but no job title

An empty string is a value of the language, so these profiles still validate,
and a reader can tell "not stated" from "stated as such" at a glance.

The one value that has no empty form is the email address: the Email rule of
section 5.2 requires an `@` and a dot, so there is no way to write "no email"
in the language. A résumé without one therefore cannot be represented, and
render() raises IncompleteProfile rather than inventing an address. Section
8.4 of docs/test-cases.md originally expected an empty résumé to produce a
valid profile; implementing this stage showed that it cannot, and that row was
corrected rather than satisfied with a fabricated value.


FORMATTING

The output is indented the way the examples in docs/formalization.md section 5
are written. None of it is meaningful: the language is not layout sensitive,
and test/grammar/validator_test.py checks that a profile flattened onto one
line still validates. The formatting exists because the interface shows this
text to a person.
"""

import re


class IncompleteProfile(Exception):
    """
    The stage results do not contain what the language requires.

    In practice this means the résumé stated no email address. The attribute
    `missing` names the field, so a caller can say which one rather than
    repeating the message.
    """

    def __init__(self, missing):
        super().__init__(
            f"the resume states no {missing}, which the Candidate Profile "
            f"Language requires"
        )

        self.missing = missing


INDENT = "    "


# The connectors that introduce a field of study inside a degree, in the two
# languages the extraction patterns of section 2 accept. "Bachelor of Science"
# is a degree name rather than a degree and a field, so "of" and "de" are
# deliberately not in this list: "Ingeniería de Sistemas" is one degree.

_FIELD_CONNECTOR = re.compile(r"\s+(?:in|en)\s+", re.IGNORECASE)

_LEADING_NUMBER = re.compile(r"\d+")


def quote(value):
    """
    Write a value as a String of the language.

    Only the quotation mark needs escaping: section 5.1 defines String as any
    run of characters between quotes, and textX returns a `\\"` as a plain
    quotation mark, so the round trip is exact. A backslash is not an escape
    character in this language and is written through unchanged.
    """

    return '"' + (value or "").replace('"', '\\"') + '"'


def first_text(findings):
    """The text of the first Finding, or None when there is none."""

    return findings[0].text if findings else None


def split_degree(text):
    """
    Split an academic qualification into the degree and the field of study.

        >>> split_degree("B.Sc. in Computer Science")
        ('B.Sc.', 'Computer Science')
        >>> split_degree("Ingeniería de Sistemas")
        ('Ingeniería de Sistemas', '')

    The split happens at the first "in" or "en", which is what introduces a
    field in the degree patterns of section 2. A qualification that names no
    field keeps the whole text as the degree and leaves the field empty, since
    inventing one would be inventing information.
    """

    parts = _FIELD_CONNECTOR.split(text, maxsplit=1)

    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return text.strip(), ""


def years_in(text):
    """
    The number of years stated by an experience phrase.

        >>> years_in("3 years of professional experience")
        3

    Returns None when the phrase carries no number, which the extraction
    pattern makes impossible in practice but which is not this module's
    assumption to make.
    """

    match = _LEADING_NUMBER.search(text)

    return int(match.group(0)) if match else None


def render(extraction, normalization, classification):
    """
    Write the stage results as a candidate profile.

    The arguments are exactly what the three stages produce: the dictionary
    from extractor.extract_resume, the NormalizationResult from
    normalizer.normalize, and the ClassificationResult from
    classifier.classify.

        >>> source = render(extraction, normalization, classification)
        >>> validator.validate(source) is not None
        True

    Raises IncompleteProfile when the résumé states no email address.
    """

    email = first_text(extraction["Contact Information"]["email"])

    if email is None:
        raise IncompleteProfile("email address")

    blocks = [_personal(extraction, email)]

    blocks += [
        _education(finding.text)
        for finding in extraction["Academic Qualifications"]
    ]

    blocks += [
        block
        for block in (
            _experience(finding.text)
            for finding in extraction["Professional Experience"]["years"]
        )
        if block is not None
    ]

    blocks.append(_skills(normalization.qualifications))

    body = "\n\n".join(blocks)

    for key in sorted(classification.accepted_keys):
        body += f"\n\n{INDENT}classification: {key}"

    return f"candidate {{\n{body}\n}}"


def _block(keyword, lines):
    """One indented block of the profile, with its keyword and braces."""

    inner = "".join(f"{INDENT}{INDENT}{line}\n" for line in lines)

    return f"{INDENT}{keyword} {{\n{inner}{INDENT}}}"


def _personal(extraction, email):
    lines = [
        f"name: {quote(extraction['Candidate']['name'])}",
        f"email: {email}",
    ]

    phone = first_text(extraction["Contact Information"]["phone"])

    if phone is not None:
        lines.append(f"phone: {quote(phone)}")

    return _block("personal", lines)


def _education(text):
    degree, field = split_degree(text)

    return _block("education", [
        f"degree: {quote(degree)}",
        f"field: {quote(field)}",
    ])


def _experience(text):
    """
    One experience record per years-of-experience statement.

    The position is left empty because a phrase such as "3 years of experience
    developing web applications" states a duration, not a job title, and
    Stage 1 does not extract titles. The date ranges Stage 1 also finds are not
    written at all: they say when, which the language has no field for.

    Returns None when the phrase carries no number, since an experience record
    without its years would not be a sentence of the language.
    """

    years = years_in(text)

    if years is None:
        return None

    return _block("experience", [
        'position: ""',
        f"years: {years}",
    ])


def _skills(qualifications):
    return _block("skills", [
        f"skill: {symbol}" for symbol in qualifications
    ])