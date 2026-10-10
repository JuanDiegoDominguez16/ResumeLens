import os

import pytest

from src.grammar.validator import validate, validate_file
from src.grammar.visualization import NOT_STATED, to_html, to_markdown


EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "examples")


def example(name):
    return os.path.join(EXAMPLES, "valid", name)


def model_of(name):
    return validate_file(example(name))


def valid_examples():
    directory = os.path.join(EXAMPLES, "valid")
    return sorted(
        name for name in os.listdir(directory) if name.endswith(".candidate")
    )


# EVERY VALIDATED PROFILE RENDERS


@pytest.mark.parametrize("name", valid_examples())
def test_every_valid_profile_renders_as_html(name):
    assert to_html(model_of(name))


@pytest.mark.parametrize("name", valid_examples())
def test_every_valid_profile_renders_as_markdown(name):
    assert to_markdown(model_of(name))


@pytest.mark.parametrize("name", valid_examples())
def test_the_html_is_a_complete_document(name):
    """
    The assignment asks for a file that can be downloaded and opened in a
    browser, so a fragment would not do.
    """

    html = to_html(model_of(name))

    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")
    assert "<style>" in html


def test_the_html_carries_no_external_reference():
    """A document that depends on a file it cannot find is not self contained."""

    html = to_html(model_of("full_stack_accepted.candidate"))

    assert "<link" not in html
    assert "<script" not in html
    assert "http://" not in html and "https://" not in html


# WHAT THE DOCUMENT SHOWS


def test_the_candidate_and_contact_details_appear():
    html = to_html(model_of("full_stack_accepted.candidate"))

    assert "Ana Torres" in html
    assert "ana.torres@example.com" in html
    assert "+57 315 987 6543" in html


def test_a_profile_without_a_phone_shows_only_the_email():
    html = to_html(model_of("minimal.candidate"))

    assert "mj.watson@example.com" in html
    assert "·" not in html.split("</h1>")[1].split("</p>")[0]


def test_the_qualifications_appear_as_canonical_symbols():
    html = to_html(model_of("full_stack_accepted.candidate"))

    assert "TYPESCRIPT" in html
    assert "SPRING_BOOT" in html


def test_the_classifications_appear():
    html = to_html(model_of("two_profiles_accepted.candidate"))

    assert "DEVOPS_ENGINEER" in html
    assert "FULL_STACK_DEVELOPER" in html


def test_the_education_and_experience_records_appear():
    html = to_html(model_of("several_records.candidate"))

    assert "Data Science" in html
    assert "Machine Learning Engineer" in html
    assert "Universidad Icesi" in html


# THE EMPTY CASES


def test_an_unclassified_candidate_says_so():
    html = to_html(model_of("unclassified.candidate"))

    assert "No profile pattern was satisfied." in html


def test_an_empty_skills_block_says_so():
    html = to_html(model_of("unclassified.candidate"))

    assert "No qualification of the controlled vocabulary was recognized." \
        in html


def test_a_profile_without_education_says_so():
    html = to_html(model_of("minimal.candidate"))

    assert "No academic qualification was stated." in html


def test_an_empty_value_is_shown_as_not_stated():
    """
    The generator writes an empty string where the résumé said nothing, and a
    blank space in the document would read as information missing from the
    system rather than from the résumé.
    """

    model = validate('candidate { personal { name: "" email: a@b.co } '
                     'experience { position: "" years: 2 } skills { } }')

    html = to_html(model)

    assert html.count(NOT_STATED) >= 2


# ESCAPING


def test_html_special_characters_in_a_value_are_escaped():
    model = validate('candidate { personal { name: "Ana <b>&</b> Torres" '
                     'email: a@b.co } skills { } }')

    html = to_html(model)

    assert "&lt;b&gt;" in html
    assert "<b>" not in html


def test_the_disclaimer_is_present_in_both_formats():
    """
    The assignment is explicit that the system does not rank candidates, and a
    page showing a person and a verdict reads as a recommendation unless it
    says otherwise.
    """

    model = model_of("full_stack_accepted.candidate")

    assert "does not rank candidates" in to_html(model)
    assert "does not rank candidates" in to_markdown(model)


# MARKDOWN


def test_the_markdown_starts_with_the_candidate_name_as_a_heading():
    markdown = to_markdown(model_of("full_stack_accepted.candidate"))

    assert markdown.startswith("# Ana Torres")


def test_the_markdown_lists_the_qualifications():
    markdown = to_markdown(model_of("full_stack_accepted.candidate"))

    assert "`ANGULAR`" in markdown
    assert "`GIT`" in markdown


def test_the_markdown_reports_an_unclassified_candidate():
    markdown = to_markdown(model_of("unclassified.candidate"))

    assert "No profile pattern was satisfied." in markdown