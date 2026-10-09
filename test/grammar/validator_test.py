import os

import pytest

from src.grammar.validator import (
    InvalidProfile,
    is_valid,
    metamodel,
    validate,
    validate_file,
)


# The fixtures in examples/ are located from this file rather than from the
# working directory, so the tests pass whether pytest is started from the
# repository root or from anywhere else.

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "examples")


def example(kind, name):
    return os.path.join(EXAMPLES, kind, name)


def valid_examples():
    directory = os.path.join(EXAMPLES, "valid")
    return sorted(
        name for name in os.listdir(directory) if name.endswith(".candidate")
    )


# The profile of docs/formalization.md section 5.3, written out here so the
# structural assertions do not depend on a file.

SECTION_5_3 = """candidate {
    personal {
        name: "John Doe"
        email: john@example.com
    }

    education {
        degree: "Bachelor"
        field: "Computer Science"
    }

    experience {
        position: "Software Developer"
        years: 3
    }

    skills {
        skill: JAVASCRIPT
        skill: REACT
        skill: NODE_JS
        skill: SQL
        skill: REST_API
        skill: GIT
    }

    classification: FULL_STACK_DEVELOPER
}"""


# THE FIXTURES OF SECTION 8.1


@pytest.mark.parametrize("name", valid_examples())
def test_every_valid_example_parses(name):
    """
    The failure this guards against: a change to the grammar quietly makes an
    optional part of the language mandatory. Between them the five fixtures
    exercise every optional and repeated element, so one of them breaks.
    """

    assert validate_file(example("valid", name)) is not None


def test_there_are_five_valid_fixtures():
    """examples/README.md lists five, and each covers a different scenario."""

    assert len(valid_examples()) == 5


# THE MODEL textX BUILDS


def test_personal_information_is_read():
    model = validate(SECTION_5_3)

    assert model.personal.name == "John Doe"
    assert model.personal.email == "john@example.com"


def test_the_documented_example_of_section_5_3():
    model = validate(SECTION_5_3)

    assert [skill.symbol for skill in model.skills.skills] == [
        "JAVASCRIPT", "REACT", "NODE_JS", "SQL", "REST_API", "GIT",
    ]
    assert [entry.profile for entry in model.classifications] == [
        "FULL_STACK_DEVELOPER",
    ]


def test_education_and_experience_are_read():
    model = validate(SECTION_5_3)

    assert model.educations[0].degree == "Bachelor"
    assert model.educations[0].field == "Computer Science"
    assert model.experiences[0].position == "Software Developer"
    assert model.experiences[0].years == 3


def test_years_is_an_integer_not_a_string():
    """
    Number is a lexical element of its own, so textX produces an int. A caller
    that computes with years must not have to parse it back.
    """

    model = validate(SECTION_5_3)

    assert isinstance(model.experiences[0].years, int)


# OPTIONAL ELEMENTS, SECTION 5.3


def test_phone_is_optional():
    model = validate_file(example("valid", "minimal.candidate"))

    assert not model.personal.phone


def test_phone_is_read_when_present():
    model = validate_file(example("valid", "full_stack_accepted.candidate"))

    assert model.personal.phone == "+57 315 987 6543"


def test_education_and_experience_are_optional():
    model = validate_file(example("valid", "minimal.candidate"))

    assert model.educations == []
    assert model.experiences == []


def test_institution_is_optional():
    model = validate_file(example("valid", "several_records.candidate"))

    with_institution, without_institution = model.educations

    assert with_institution.institution == "Universidad Icesi"
    assert not without_institution.institution


def test_the_skills_block_may_be_empty():
    """
    A résumé stating no qualification of the controlled vocabulary still
    produces a valid profile, which is the same decision Stage 2 and Stage 3
    record in normalization.md section 6.3 and classification.md section 6.2.
    """

    model = validate_file(example("valid", "unclassified.candidate"))

    assert model.skills.skills == []


# REPEATED ELEMENTS, SECTION 5.4


def test_several_education_and_experience_records():
    model = validate_file(example("valid", "several_records.candidate"))

    assert len(model.educations) == 2
    assert len(model.experiences) == 2


# ZERO, ONE, OR SEVERAL CLASSIFICATIONS, SECTION 4.6


def test_zero_classifications_is_an_unclassified_candidate():
    model = validate_file(example("valid", "unclassified.candidate"))

    assert model.classifications == []


def test_one_classification():
    model = validate_file(example("valid", "full_stack_accepted.candidate"))

    assert [entry.profile for entry in model.classifications] == [
        "FULL_STACK_DEVELOPER",
    ]


def test_two_classifications():
    model = validate_file(example("valid", "two_profiles_accepted.candidate"))

    assert [entry.profile for entry in model.classifications] == [
        "DEVOPS_ENGINEER", "FULL_STACK_DEVELOPER",
    ]


def test_the_three_outcomes_are_ordinary_sentences_of_the_language():
    """
    None of the three results of Stage 3 is a special case in the grammar.
    They differ only in how many classification elements they carry, which is
    the design decision recorded in formalization.md section 5.1.
    """

    counts = [
        len(validate_file(example("valid", name)).classifications)
        for name in ("unclassified.candidate",
                     "full_stack_accepted.candidate",
                     "two_profiles_accepted.candidate")
    ]

    assert counts == [0, 1, 2]


# WHITESPACE


def test_indentation_and_blank_lines_carry_no_meaning():
    """
    The language is not layout sensitive: the generator may format a profile
    however it likes without changing whether it validates.
    """

    flattened = " ".join(SECTION_5_3.split())

    assert is_valid(flattened)


# THE API


def test_is_valid_answers_true_for_a_profile_that_parses():
    assert is_valid(SECTION_5_3)


def test_is_valid_answers_false_instead_of_raising():
    assert is_valid("candidate { }") is False


def test_an_empty_profile_is_rejected():
    """
    Guards against the opposite failure of the fixtures above: a grammar so
    permissive that everything parses would make every test here vacuous.
    """

    with pytest.raises(InvalidProfile):
        validate("")


def test_the_metamodel_is_built_once():
    assert metamodel() is metamodel()