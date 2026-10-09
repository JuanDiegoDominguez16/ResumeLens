import os

import pytest

from src.grammar.validator import InvalidProfile, validate, validate_file


EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "examples")


def example(kind, name):
    return os.path.join(EXAMPLES, kind, name)


def invalid_examples():
    directory = os.path.join(EXAMPLES, "invalid")
    return sorted(
        name for name in os.listdir(directory) if name.endswith(".candidate")
    )


def rejection_of(source):
    """Validate something that must fail, and return the error."""

    with pytest.raises(InvalidProfile) as raised:
        validate(source)

    return raised.value


# A profile that parses, used as the starting point for the single mutations
# below. Each test breaks exactly one rule of it, so what the parser reports
# can be attributed to that rule and nothing else.

VALID = """candidate {
    personal {
        name: "Ana Torres"
        email: ana.torres@example.com
    }

    skills {
        skill: GIT
    }
}"""


def test_the_starting_point_parses():
    """Without this, every mutation below could be failing for another reason."""

    assert validate(VALID) is not None


# THE FIXTURES OF SECTION 8.2


@pytest.mark.parametrize("name", invalid_examples())
def test_every_invalid_example_is_rejected(name):
    with pytest.raises(InvalidProfile):
        validate_file(example("invalid", name))


def test_there_are_eight_invalid_fixtures():
    assert len(invalid_examples()) == 8


@pytest.mark.parametrize("name", invalid_examples())
def test_a_rejection_says_where(name):
    """
    A rejection without a position is not actionable. textX reports one for
    every syntax error, and the stage must not lose it on the way out.
    """

    with pytest.raises(InvalidProfile) as raised:
        validate_file(example("invalid", name))

    error = raised.value

    assert error.line is not None and error.line >= 1
    assert error.column is not None and error.column >= 1


@pytest.mark.parametrize("name", invalid_examples())
def test_a_rejection_from_a_file_names_the_file(name):
    with pytest.raises(InvalidProfile) as raised:
        validate_file(example("invalid", name))

    assert raised.value.path.endswith(name)
    assert name in str(raised.value)


# ONE RULE AT A TIME, SECTION 5.1 AND 5.2


def test_a_missing_personal_block_is_rejected():
    error = rejection_of(VALID.replace(
        """    personal {
        name: "Ana Torres"
        email: ana.torres@example.com
    }

""", ""))

    assert "personal" in error.message


def test_a_missing_email_is_rejected():
    error = rejection_of(VALID.replace(
        "        email: ana.torres@example.com\n", ""))

    assert "email" in error.message


def test_an_unquoted_string_is_rejected():
    error = rejection_of(VALID.replace('"Ana Torres"', "Ana Torres"))

    assert "STRING" in error.message


def test_an_email_without_an_at_sign_is_rejected():
    error = rejection_of(VALID.replace("ana.torres@example.com",
                                       "ana.torres.example.com"))

    assert "EMAIL" in error.message


def test_an_email_without_a_dot_is_rejected():
    error = rejection_of(VALID.replace("ana.torres@example.com",
                                       "ana@example"))

    assert "EMAIL" in error.message


def test_a_quoted_email_is_rejected():
    """
    Email is a lexical element of its own, not a String. The distinction is
    the one recorded in formalization.md section 5.6: a quoted value is opaque
    to the parser, while an Email is a structure it checks.
    """

    error = rejection_of(VALID.replace("ana.torres@example.com",
                                       '"ana.torres@example.com"'))

    assert "EMAIL" in error.message


def test_a_non_numeric_year_is_rejected():
    error = rejection_of(VALID.replace(
        "    skills {",
        """    experience {
        position: "Developer"
        years: three
    }

    skills {"""))

    assert "INT" in error.message


def test_an_unbalanced_brace_is_rejected():
    error = rejection_of(VALID.rstrip().removesuffix("}"))

    assert error.line is not None


def test_an_unknown_section_is_rejected():
    error = rejection_of(VALID.replace("skills {", "abilities {"))

    assert "skills" in error.message


# THE REJECTION THAT TIES STAGE 4 TO STAGE 2


@pytest.mark.parametrize("representation", [
    "React.js", "ReactJS.js", "Node.js", "scikit-learn",
])
def test_a_representation_that_stage_2_should_have_normalized_is_rejected(
        representation):
    """
    Identifier admits letters, digits and the underscore, so a dot or a hyphen
    cannot be matched. A profile carrying a raw representation is rejected by
    the lexical rule itself, with no check written in Python.
    """

    with pytest.raises(InvalidProfile):
        validate(VALID.replace("skill: GIT", f"skill: {representation}"))


def test_canonical_symbols_are_accepted_where_representations_are_not():
    """The other half of the test above: the canonical form of the same thing."""

    assert validate(VALID.replace("skill: GIT", "skill: SCIKIT_LEARN"))


# THE EXCERPT


def test_the_excerpt_points_at_the_offending_token():
    error = rejection_of(VALID.replace("ana.torres@example.com",
                                       "ana.torres.example.com"))

    offending, caret = error.excerpt().splitlines()

    assert offending.strip() == "email: ana.torres.example.com"
    assert caret.index("^") == offending.index("ana.torres.example.com")


def test_the_excerpt_is_none_without_a_position():
    error = InvalidProfile("something went wrong")

    assert error.excerpt() is None


def test_the_excerpt_is_none_when_the_position_falls_outside_the_source():
    error = InvalidProfile("out of range", line=99, column=1, source=VALID)

    assert error.excerpt() is None


# THE MESSAGE


def test_the_position_prefix_is_not_repeated_in_the_message():
    """
    textX writes the position into its message as well as into its attributes.
    Keeping both would print it twice, once in the message and once in the
    formatting of __str__.
    """

    error = rejection_of("")

    assert not error.message.startswith("None:")


def test_str_formats_the_position_once():
    error = rejection_of(VALID.replace('"Ana Torres"', "Ana Torres"))

    assert str(error).startswith(f"line {error.line}, column {error.column}: ")


def test_a_rejection_keeps_the_source_it_rejected():
    error = rejection_of(VALID.replace('"Ana Torres"', "Ana Torres"))

    assert error.source.startswith("candidate {")