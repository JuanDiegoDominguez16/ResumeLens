from itertools import permutations

from src.extraction.extractor import qualification_strings
from src.normalization.normalizer import canonical_set, normalize


# The two resume fragments the assignment uses as reference profiles.

WEDNESDAY_ADDAMS = """Wednesday Addams
3 years of experience developing web applications.

Technical Skills:
JS, React.js, NodeJS, Postgres, Git."""

MARY_JANE_WATSON = """Mary Jane Watson
2 years of experience developing predictive models and data-processing pipelines.

Technical Skills:
Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git."""


def normalize_resume(text):
    """Run both stages, which is what the pipeline will do."""
    return normalize(qualification_strings(text))


# THE REFERENCE RESUMES


def test_full_stack_reference_resume():
    result = normalize_resume(WEDNESDAY_ADDAMS)

    assert result.qualification_set == {
        "JAVASCRIPT", "REACT", "NODE_JS", "POSTGRESQL", "GIT",
    }


def test_machine_learning_reference_resume():
    result = normalize_resume(MARY_JANE_WATSON)

    assert result.qualification_set == {
        "PYTHON", "PANDAS", "NUMPY", "SCIKIT_LEARN", "TENSORFLOW", "SQL", "GIT",
    }


def test_example_of_section_3_8():
    result = normalize(["Git", "NodeJS", "JS", "Postgres", "React.js"])

    assert result.qualification_set == {
        "GIT", "NODE_JS", "JAVASCRIPT", "POSTGRESQL", "REACT",
    }


# ORDER INDEPENDENCE, SECTION 3.8


def test_the_result_does_not_depend_on_the_order_of_the_input():
    representations = ["Git", "NodeJS", "JS", "Postgres", "React.js"]

    results = {canonical_set(order) for order in permutations(representations)}

    assert len(results) == 1


def test_qualifications_are_listed_alphabetically():
    result = normalize(["React.js", "Git", "JS"])

    assert result.qualifications == ("GIT", "JAVASCRIPT", "REACT")


def test_the_formal_output_is_a_set():
    # Section 3.8 defines the output as a set, and the type enforces it so no
    # consumer can come to rely on an order the model does not define.
    result = normalize(["Git"])

    assert isinstance(result.qualification_set, frozenset)


# DUPLICATES


def test_spellings_that_fold_together_are_collapsed():
    result = normalize(["JS", "js", "Js"])

    assert len(result.normalized) == 1
    assert result.normalized[0].representation == "JS"


def test_spellings_that_fold_apart_are_both_traced():
    # Both reach JAVASCRIPT, but the trace has to explain each string in the
    # resume, so neither entry may be dropped.
    result = normalize(["JS", "JavaScript"])

    assert [entry.representation for entry in result.normalized] == [
        "JS", "JavaScript",
    ]
    assert result.qualification_set == {"JAVASCRIPT"}


def test_a_repeated_qualification_appears_once_in_the_set():
    result = normalize(["Git", "Git", "Git"])

    assert result.qualifications == ("GIT",)


# WHAT DOES NOT REACH STAGE 3


def test_out_of_scope_representations_are_reported_with_a_reason():
    result = normalize(["Git", "Kubernetes"])

    assert result.qualifications == ("GIT",)
    assert len(result.out_of_scope) == 1
    assert result.out_of_scope[0].representation == "Kubernetes"
    assert result.out_of_scope[0].reason


def test_unknown_strings_are_reported_separately():
    result = normalize(["Git", "Kubernetes", "not a qualification"])

    assert [d.representation for d in result.out_of_scope] == ["Kubernetes"]
    assert list(result.unknown) == ["not a qualification"]


def test_discarded_combines_both_reasons():
    result = normalize(["Git", "Kubernetes", "not a qualification"])

    assert [d.representation for d in result.discarded] == [
        "Kubernetes", "not a qualification",
    ]
    assert all(entry.reason for entry in result.discarded)


def test_bare_machine_learning_does_not_reach_stage_three():
    # The decision recorded in vocabulary.py: only the full phrase fills the
    # model development slot of the Machine Learning Engineer profile.
    with_phrase = normalize(["Machine Learning Model Development"])
    with_abbreviation = normalize(["ML"])

    assert with_phrase.qualification_set == {"MLMD"}
    assert with_abbreviation.qualification_set == set()
    assert with_abbreviation.out_of_scope[0].representation == "ML"


# EDGE CASES


def test_an_empty_input_produces_an_empty_result():
    result = normalize([])

    assert result.qualifications == ()
    assert result.out_of_scope == ()
    assert result.unknown == ()


def test_blank_strings_are_ignored_rather_than_reported():
    result = normalize(["", "   ", "\t", "Git"])

    assert result.qualifications == ("GIT",)
    assert result.unknown == ()


def test_a_resume_with_no_recognized_qualification():
    result = normalize_resume("Wednesday Addams\nI enjoy long walks.")

    assert result.qualifications == ()


def test_canonical_set_is_a_shorthand_for_the_formal_output():
    representations = ["JS", "React.js", "Kubernetes"]

    assert canonical_set(representations) == (
        normalize(representations).qualification_set
    )


# TRACEABILITY


def test_every_input_is_accounted_for_somewhere():
    representations = [
        "JS", "React.js", "Kubernetes", "MongoDB", "not a qualification", "Git",
    ]

    result = normalize(representations)

    accounted = (
        [entry.representation for entry in result.normalized]
        + [entry.representation for entry in result.out_of_scope]
        + list(result.unknown)
    )

    assert sorted(accounted) == sorted(representations)
