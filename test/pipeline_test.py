import json

import pytest

from src.grammar.validator import validate
from src.pipeline import PipelineResult, run


# The five sample resumes the interface offers. Section 8.4 of
# docs/test-cases.md asks that each one traverse all four stages.

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


# THE FOUR STAGES RUN IN ORDER, SECTION 8.4


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_every_sample_resume_traverses_the_four_stages(name):
    result = run(SAMPLES[name])

    assert result.extraction
    assert result.normalization is not None
    assert result.classification is not None
    assert result.has_profile


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_the_profile_of_every_sample_validates(name):
    """
    The generated profile is parsed by the pipeline itself, so this repeats
    the check deliberately: if the pipeline ever stopped validating, every
    other assertion about the profile would still pass.
    """

    result = run(SAMPLES[name])

    assert validate(result.profile_source) is not None


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_every_sample_produces_a_visualization(name):
    result = run(SAMPLES[name])

    assert result.visualization.startswith("<!DOCTYPE html>")


# THE STAGES AGREE WITH ONE ANOTHER


def test_the_profile_carries_the_qualifications_stage_2_produced():
    result = run(WEDNESDAY_ADDAMS)

    assert [skill.symbol for skill in result.candidate_profile.skills.skills] \
        == list(result.qualifications)


def test_the_profile_carries_the_classification_stage_3_reported():
    """Section 8.4: the profile must not disagree with the stage that produced it."""

    result = run(SOFIA_RAMIREZ)

    assert sorted(
        entry.profile for entry in result.candidate_profile.classifications
    ) == sorted(result.accepted_keys)


def test_the_candidate_name_reaches_the_profile_and_the_document():
    result = run(ANA_TORRES)

    assert result.candidate_name == "Ana Torres"
    assert result.candidate_profile.personal.name == "Ana Torres"
    assert "Ana Torres" in result.visualization


def test_an_accepted_candidate_is_accepted_end_to_end():
    result = run(ANA_TORRES)

    assert result.accepted_keys == ("FULL_STACK_DEVELOPER",)
    assert not result.is_unclassified


def test_a_candidate_may_be_accepted_by_two_profiles():
    result = run(SOFIA_RAMIREZ)

    assert sorted(result.accepted_keys) == [
        "DATA_ENGINEER", "MACHINE_LEARNING_ENGINEER",
    ]


def test_an_unclassified_candidate_still_reaches_stage_4():
    """
    Carlos Mena satisfies no pattern. That is a result, not a failure, and the
    profile that represents it is an ordinary sentence of the language with
    zero classification elements.
    """

    result = run(CARLOS_MENA)

    assert result.is_unclassified
    assert result.has_profile
    assert result.candidate_profile.classifications == []


# THE RESUMES STAGE 4 CANNOT REPRESENT


def test_an_empty_resume_runs_the_first_three_stages():
    result = run("")

    assert result.qualifications == ()
    assert result.is_unclassified
    assert result.candidate_name is None


def test_an_empty_resume_produces_no_profile_and_says_why():
    result = run("")

    assert not result.has_profile
    assert result.profile_source is None
    assert result.visualization is None
    assert "email" in result.profile_error


def test_a_resume_without_an_email_is_not_an_error():
    """
    The run still returns a result. Stages 1 to 3 did their work and that work
    is what the interface shows; only the profile is missing.
    """

    result = run(WEDNESDAY_ADDAMS.replace(
        "wednesday.addams@example.com\n", ""))

    assert isinstance(result, PipelineResult)
    assert result.accepted_keys == ()
    assert result.qualifications == (
        "GIT", "JAVASCRIPT", "NODE_JS", "POSTGRESQL", "REACT",
    )
    assert not result.has_profile


# THE SERIALIZED VIEW


def test_the_result_can_be_written_as_json():
    payload = run(ANA_TORRES).as_dict()

    assert json.loads(json.dumps(payload))["candidate"] == "Ana Torres"


def test_the_json_view_carries_the_profile_source():
    payload = run(ANA_TORRES).as_dict()

    assert payload["candidate_profile"].startswith("candidate {")
    assert payload["profile_error"] is None


def test_the_json_view_of_a_resume_without_a_profile():
    payload = run("").as_dict()

    assert payload["candidate_profile"] is None
    assert "email" in payload["profile_error"]


# THE DOCUMENTED EXAMPLE OF THE ASSIGNMENT


def test_the_wednesday_addams_fragment_end_to_end():
    """
    The reference fragment of the assignment, through all four stages. It does
    not satisfy the Full Stack pattern, which docs/test-cases.md section 7
    records as a property of the patterns the team defined, not a defect.
    """

    result = run(WEDNESDAY_ADDAMS)

    assert result.qualifications == (
        "GIT", "JAVASCRIPT", "NODE_JS", "POSTGRESQL", "REACT",
    )
    assert result.is_unclassified
    assert result.has_profile