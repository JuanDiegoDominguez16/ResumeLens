import pytest

from src.classification.classifier import classify
from src.extraction.extractor import extract_resume, qualification_strings
from src.grammar.generator import (
    IncompleteProfile,
    quote,
    render,
    split_degree,
    years_in,
)
from src.grammar.validator import validate


# The sample résumés the interface offers, which are also the end to end
# scenarios of docs/test-cases.md section 8.4. The first two are the
# assignment's reference fragments, with the contact details the language
# requires added.

WEDNESDAY_ADDAMS = """Wednesday Addams
wednesday.addams@example.com
+57 300 123 4567
3 years of experience developing web applications.

Education:
B.Sc. in Computer Science
Universidad Icesi

Technical Skills:
JS, React.js, NodeJS, Postgres, Git."""

MARY_JANE_WATSON = """Mary Jane Watson
mj.watson@example.com
2 years of experience developing predictive models and data-processing pipelines.

Education:
Master's degree in Data Science

Technical Skills:
Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git."""

ANA_TORRES = """Ana Torres
ana.torres@example.com
+57 315 987 6543
5 years of experience building web platforms.
2019 - Present

Education:
Ingeniería de Sistemas
Universidad Icesi

Technical Skills:
TypeScript, Angular, Spring Boot, NoSQL databases, REST APIs, Git, Docker."""

SOFIA_RAMIREZ = """Sofía Ramírez
sofia.ramirez@example.com
6 years of experience in data platforms and predictive modelling.

Technical Skills:
Python, Pandas, Scikit-learn, PyTorch, Machine Learning Model Development,
SQL, Git, Apache Airflow, Apache Spark, PostgreSQL, Databricks."""

CARLOS_MENA = """Carlos Mena
carlos.mena@example.com
1 year of experience.

Technical Skills:
Java, C++, Redis."""

SAMPLES = {
    "Wednesday Addams": WEDNESDAY_ADDAMS,
    "Mary Jane Watson": MARY_JANE_WATSON,
    "Ana Torres": ANA_TORRES,
    "Sofía Ramírez": SOFIA_RAMIREZ,
    "Carlos Mena": CARLOS_MENA,
}


def profile_of(resume_text):
    """Run the three stages and render the result, which is what Stage 4 does."""

    extraction = extract_resume(resume_text)
    normalization = normalize_of(resume_text)
    classification = classify(normalization.qualification_set)

    return render(extraction, normalization, classification)


def normalize_of(resume_text):
    from src.normalization.normalizer import normalize

    return normalize(qualification_strings(resume_text))


def model_of(resume_text):
    return validate(profile_of(resume_text))


# THE ROUND TRIP, SECTION 8.3


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_every_sample_resume_renders_a_profile_the_grammar_accepts(name):
    """
    The failure this guards against is the whole point of the stage: the
    generator and the grammar drifting apart, so that the system produces
    profiles its own language rejects.
    """

    assert validate(profile_of(SAMPLES[name])) is not None


def test_rendering_is_deterministic():
    assert profile_of(ANA_TORRES) == profile_of(ANA_TORRES)


# WHAT THE PROFILE CARRIES


def test_the_candidate_name_and_contact_details_come_from_stage_1():
    model = model_of(WEDNESDAY_ADDAMS)

    assert model.personal.name == "Wednesday Addams"
    assert model.personal.email == "wednesday.addams@example.com"
    assert model.personal.phone == "+57 300 123 4567"


def test_the_skills_come_from_stage_2():
    model = model_of(WEDNESDAY_ADDAMS)

    assert [skill.symbol for skill in model.skills.skills] == [
        "GIT", "JAVASCRIPT", "NODE_JS", "POSTGRESQL", "REACT",
    ]


def test_the_classification_matches_what_stage_3_reported():
    """Section 8.4: the profile must not disagree with the stage that produced it."""

    normalization = normalize_of(SOFIA_RAMIREZ)
    classification = classify(normalization.qualification_set)

    model = model_of(SOFIA_RAMIREZ)

    assert sorted(entry.profile for entry in model.classifications) == sorted(
        classification.accepted_keys
    )


def test_a_candidate_accepted_by_two_profiles_carries_two_classifications():
    model = model_of(SOFIA_RAMIREZ)

    assert [entry.profile for entry in model.classifications] == [
        "DATA_ENGINEER", "MACHINE_LEARNING_ENGINEER",
    ]


def test_an_unclassified_candidate_carries_none():
    model = model_of(CARLOS_MENA)

    assert model.classifications == []


def test_a_resume_with_no_canonical_qualification_renders_an_empty_skills_block():
    """Carlos Mena lists Java, C++ and Redis, none of which Stage 2 normalizes."""

    model = model_of(CARLOS_MENA)

    assert model.skills.skills == []


# OPTIONAL VALUES


def test_a_resume_without_a_phone_renders_no_phone_line():
    assert "phone:" not in profile_of(MARY_JANE_WATSON)


def test_the_profile_without_a_phone_still_validates():
    assert validate(profile_of(MARY_JANE_WATSON)) is not None


# WHAT THE GENERATOR REFUSES TO INVENT


def test_a_resume_without_an_email_cannot_be_represented():
    """
    The Email rule has no empty form, so there is no way to write "no email"
    in the language. The generator says so instead of inventing an address.
    """

    with pytest.raises(IncompleteProfile) as raised:
        profile_of("Wednesday Addams\nTechnical Skills: Git.")

    assert raised.value.missing == "email address"


def test_an_empty_resume_cannot_be_represented_either():
    with pytest.raises(IncompleteProfile):
        profile_of("")


def test_a_resume_whose_first_line_is_not_a_name_renders_an_empty_name():
    """
    An empty string is a value of the language, so "not stated" is
    representable for every required field except the email address.
    """

    model = validate(profile_of("CURRICULUM\nfoo@example.com\nSkills: Git."))

    assert model.personal.name == ""


# QUOTING


def test_a_quotation_mark_in_a_value_is_escaped():
    assert quote('Ana "Tita" Torres') == '"Ana \\"Tita\\" Torres"'


def test_an_escaped_value_survives_the_round_trip():
    source = ('candidate { personal { name: ' + quote('Ana "Tita" Torres')
              + ' email: a@b.co } skills { } }')

    assert validate(source).personal.name == 'Ana "Tita" Torres'


def test_a_missing_value_is_written_as_an_empty_string():
    assert quote(None) == '""'


# DEGREES


@pytest.mark.parametrize("text, degree, field", [
    ("B.Sc. in Computer Science", "B.Sc.", "Computer Science"),
    ("Bachelor's degree in Computer Science",
     "Bachelor's degree", "Computer Science"),
    ("Master's in Data Science", "Master's", "Data Science"),
    ("Licenciatura en Matemáticas", "Licenciatura", "Matemáticas"),
])
def test_a_degree_is_split_at_the_connector(text, degree, field):
    assert split_degree(text) == (degree, field)


@pytest.mark.parametrize("text", [
    "Ingeniería de Sistemas",
    "Bachelor of Science",
])
def test_a_degree_that_names_no_field_keeps_the_whole_text(text):
    """
    "of" and "de" are part of the degree's name, not connectors to a field,
    so splitting on them would invent a field of study.
    """

    assert split_degree(text) == (text, "")


def test_a_degree_without_a_field_still_validates():
    model = model_of(ANA_TORRES)

    assert model.educations[0].degree == "Ingeniería de Sistemas"
    assert model.educations[0].field == ""


# EXPERIENCE


@pytest.mark.parametrize("text, years", [
    ("3 years of experience", 3),
    ("3 years of professional experience", 3),
    ("12 yrs experience", 12),
])
def test_the_years_are_read_from_the_phrase(text, years):
    assert years_in(text) == years


def test_the_position_is_left_empty_because_stage_1_does_not_extract_titles():
    model = model_of(WEDNESDAY_ADDAMS)

    assert model.experiences[0].position == ""
    assert model.experiences[0].years == 3


def test_a_resume_with_no_experience_statement_renders_no_experience_block():
    source = profile_of("Ana Torres\nana@example.com\nSkills: Git.")

    assert "experience {" not in source
    assert validate(source) is not None