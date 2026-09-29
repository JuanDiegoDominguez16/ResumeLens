from dataclasses import fields

from src.classification.classifier import ProfileResult, classify, classify_for
from src.classification.profiles import FULL_STACK_DEVELOPER, PROFILES
from src.extraction.extractor import qualification_strings
from src.normalization.normalizer import normalize


# Sets that satisfy one complete pattern each.

FULL_STACK = {"JAVASCRIPT", "REACT", "NODE_JS", "SQL", "REST_API", "GIT"}

MACHINE_LEARNING = {
    "PYTHON", "PANDAS", "SCIKIT_LEARN", "TENSORFLOW", "MLMD", "SQL", "GIT",
}

DEVOPS = {"DOCKER", "AWS", "GITHUB_ACTIONS", "TERRAFORM", "GIT"}

DATA = {"SQL", "AIRFLOW", "SPARK", "POSTGRESQL", "DATABRICKS"}


def classify_resume(text):
    """The first three stages, which is what the pipeline will do."""
    return classify(normalize(qualification_strings(text)).qualification_set)


# THE SHAPE OF THE RESULT


def test_every_profile_gets_an_answer_whether_accepted_or_not():
    result = classify(FULL_STACK)

    assert len(result.results) == len(PROFILES)
    assert [entry.key for entry in result.results] == [p.key for p in PROFILES]


def test_the_classified_set_is_kept_on_the_result():
    result = classify(FULL_STACK)

    assert result.qualifications == frozenset(FULL_STACK)


def test_for_profile_finds_one_answer():
    result = classify(FULL_STACK)

    assert result.for_profile("FULL_STACK_DEVELOPER").accepted
    assert result.for_profile("NOT_A_PROFILE") is None


def test_satisfied_and_missing_slots_partition_the_pattern():
    for entry in classify({"GIT", "SQL"}).results:
        assert len(entry.satisfied_slots) + len(entry.missing_slots) == len(
            entry.profile.slots
        )
        assert not set(entry.satisfied_slots) & set(entry.missing_slots)


# ONE PROFILE ACCEPTED


def test_a_full_stack_set_is_accepted_by_full_stack_only():
    result = classify(FULL_STACK)

    assert result.accepted_keys == ("FULL_STACK_DEVELOPER",)
    assert not result.is_unclassified


def test_each_reference_pattern_is_accepted_by_its_own_profile():
    cases = [
        (FULL_STACK, "FULL_STACK_DEVELOPER"),
        (MACHINE_LEARNING, "MACHINE_LEARNING_ENGINEER"),
        (DEVOPS, "DEVOPS_ENGINEER"),
        (DATA, "DATA_ENGINEER"),
    ]

    for qualifications, key in cases:
        assert key in classify(qualifications).accepted_keys


def test_an_accepted_result_reports_the_accepting_state():
    result = classify(FULL_STACK).for_profile("FULL_STACK_DEVELOPER")

    assert result.final_state == "qFS"
    assert result.missing_slots == ()


# SEVERAL PROFILES AT ONCE, SECTION 4.6


def test_a_set_may_be_accepted_by_more_than_one_profile():
    result = classify(MACHINE_LEARNING | DATA)

    assert set(result.accepted_keys) == {
        "MACHINE_LEARNING_ENGINEER", "DATA_ENGINEER",
    }


def test_accepted_profiles_keep_the_documented_order():
    result = classify(MACHINE_LEARNING | DATA)

    assert result.accepted_keys == (
        "MACHINE_LEARNING_ENGINEER", "DATA_ENGINEER",
    )


# NO PROFILE ACCEPTED, ALSO SECTION 4.6


def test_an_empty_set_is_unclassified():
    result = classify(set())

    assert result.is_unclassified
    assert result.accepted_keys == ()


def test_unclassified_still_explains_what_was_missing():
    # Being unclassified is a result, not an error, so it has to carry the
    # same explanation an accepted one would.
    result = classify({"GIT"})

    assert result.is_unclassified
    for entry in result.results:
        assert entry.missing_slots


def test_a_partial_set_is_rejected_with_the_slot_that_was_missing():
    result = classify(FULL_STACK - {"REST_API"})
    entry = result.for_profile("FULL_STACK_DEVELOPER")

    assert not entry.accepted
    assert [slot.name for slot in entry.missing_slots] == ["REST API"]


# THE STAGE PRODUCES NO RANKING
#
# The assignment states that ResumeLens does not rank candidates. This is
# checked rather than merely documented, because the fields below are exactly
# the ones a later change would be tempted to add.


def test_a_profile_result_carries_no_score_or_ranking_field():
    names = {field.name for field in fields(ProfileResult)}

    assert names == {
        "profile", "accepted", "satisfied_slots", "missing_slots",
        "final_state",
    }
    assert not any(
        candidate in dir(ProfileResult)
        for candidate in ["score", "ranking", "percentage", "match", "rating"]
    )


def test_two_candidates_accepted_by_the_same_profile_are_not_ordered():
    # One has extra qualifications, the other exactly the pattern. Neither
    # result says anything that would put one ahead of the other.
    plain = classify(FULL_STACK).for_profile("FULL_STACK_DEVELOPER")
    richer = classify(FULL_STACK | {"TYPESCRIPT", "VUE", "DOCKER"}).for_profile(
        "FULL_STACK_DEVELOPER"
    )

    assert plain.accepted == richer.accepted
    assert plain.final_state == richer.final_state
    assert plain.missing_slots == richer.missing_slots


# THE RESUMES THE ASSIGNMENT USES AS EXAMPLES
#
# The team's patterns in section 4.7 are stricter than the illustrative resume
# fragments in the assignment: those fragments do not mention REST APIs or
# model development, which the Full Stack Developer and Machine Learning
# Engineer patterns require. The decision was to keep the patterns as
# documented rather than relax them to fit the examples, so these tests record
# the rejection, and the slot that causes it, on purpose. See
# docs/test-cases.md.


WEDNESDAY_ADDAMS = """Wednesday Addams
3 years of experience developing web applications.

Technical Skills:
JS, React.js, NodeJS, Postgres, Git."""

MARY_JANE_WATSON = """Mary Jane Watson
2 years of experience developing predictive models and data-processing pipelines.

Technical Skills:
Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git."""


def test_the_full_stack_example_misses_the_database_and_rest_slots():
    entry = classify_resume(WEDNESDAY_ADDAMS).for_profile("FULL_STACK_DEVELOPER")

    assert not entry.accepted
    assert [slot.name for slot in entry.missing_slots] == ["database", "REST API"]


def test_postgresql_does_not_satisfy_the_full_stack_database_slot():
    # The reason for one of the two misses above: section 2.3 lists SQL and
    # NOSQL for Full Stack, and POSTGRESQL only for Data Engineer.
    assert "POSTGRESQL" not in FULL_STACK_DEVELOPER.slots[3].symbols


def test_the_machine_learning_example_misses_only_model_development():
    entry = classify_resume(MARY_JANE_WATSON).for_profile(
        "MACHINE_LEARNING_ENGINEER"
    )

    assert not entry.accepted
    assert [slot.name for slot in entry.missing_slots] == ["model development"]
    assert len(entry.satisfied_slots) == 6


def test_adding_the_missing_qualification_accepts_the_machine_learning_example():
    # The counterpart of the test above: the pattern is not unreachable, the
    # example resume simply does not state that qualification.
    text = MARY_JANE_WATSON.replace(
        "TensorFlow,", "TensorFlow, Machine Learning Model Development,"
    )

    assert "MACHINE_LEARNING_ENGINEER" in classify_resume(text).accepted_keys


# ONE PROFILE AT A TIME


def test_classify_for_agrees_with_classify():
    for profile in PROFILES:
        alone = classify_for(profile, FULL_STACK)
        together = classify(FULL_STACK).for_profile(profile.key)

        assert alone == together
