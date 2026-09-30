import pytest

from src.classification.profiles import (
    DATA_ENGINEER,
    DEVOPS_ENGINEER,
    FULL_STACK_DEVELOPER,
    MACHINE_LEARNING_ENGINEER,
    PROFILES,
    UNUSED_SYMBOLS,
    profile_for,
)
from src.normalization.vocabulary import CANONICAL_SYMBOLS


# The slot definitions written out in docs/formalization.md section 4.7,
# repeated here so that changing a pattern without updating the document, or
# the other way round, fails.
DOCUMENTED_PATTERNS = {
    "FULL_STACK_DEVELOPER": [
        ("programming language", {"JAVASCRIPT", "TYPESCRIPT"}),
        ("frontend", {"REACT", "ANGULAR", "VUE"}),
        ("backend", {"NODE_JS", "DJANGO", "SPRING_BOOT"}),
        ("database", {"SQL", "NOSQL"}),
        ("REST API", {"REST_API"}),
        ("version control", {"GIT"}),
    ],
    "MACHINE_LEARNING_ENGINEER": [
        ("programming language", {"PYTHON"}),
        ("data manipulation", {"PANDAS", "NUMPY"}),
        ("machine learning library", {"SCIKIT_LEARN"}),
        ("deep learning framework", {"TENSORFLOW", "PYTORCH"}),
        ("model development", {"MLMD"}),
        ("database", {"SQL"}),
        ("version control", {"GIT"}),
    ],
    "DEVOPS_ENGINEER": [
        ("containerization", {"DOCKER"}),
        ("cloud provider", {"AWS", "AZURE", "GOOGLE_CLOUD"}),
        ("CI/CD", {"JENKINS", "GITHUB_ACTIONS", "GITLAB_CI_CD"}),
        ("infrastructure automation", {"TERRAFORM", "ANSIBLE"}),
        ("version control", {"GIT"}),
    ],
    "DATA_ENGINEER": [
        ("query language", {"SQL"}),
        ("orchestration", {"AIRFLOW"}),
        ("distributed processing", {"SPARK"}),
        ("database", {"POSTGRESQL", "MYSQL"}),
        ("data platform", {"DATABRICKS"}),
    ],
}


# THE FOUR PATTERNS


def test_there_are_four_profiles():
    assert len(PROFILES) == 4


def test_the_profiles_are_the_ones_the_assignment_names():
    assert [profile.key for profile in PROFILES] == [
        "FULL_STACK_DEVELOPER",
        "MACHINE_LEARNING_ENGINEER",
        "DEVOPS_ENGINEER",
        "DATA_ENGINEER",
    ]


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_slots_match_the_documented_pattern(profile):
    documented = DOCUMENTED_PATTERNS[profile.key]

    assert [(slot.name, set(slot.symbols)) for slot in profile.slots] == [
        (name, symbols) for name, symbols in documented
    ]


@pytest.mark.parametrize(
    "profile,slot_count",
    [
        (FULL_STACK_DEVELOPER, 6),
        (MACHINE_LEARNING_ENGINEER, 7),
        (DEVOPS_ENGINEER, 5),
        (DATA_ENGINEER, 5),
    ],
    ids=lambda value: getattr(value, "key", value),
)
def test_slot_counts_match_section_4_7(profile, slot_count):
    assert profile.slot_count == slot_count


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_state_count_is_two_to_the_number_of_slots(profile):
    assert profile.state_count == 2 ** profile.slot_count


def test_the_accepting_state_labels_of_section_4_6():
    assert [profile.state_label for profile in PROFILES] == [
        "qFS", "qML", "qDO", "qDE",
    ]


# THE INVARIANT SECTION 4.5 DEPENDS ON


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_slots_of_one_profile_are_pairwise_disjoint(profile):
    # Without this, a symbol could satisfy two slots at once and the
    # transition function of section 4.5 would have to choose between two
    # next states, which would stop it being a function.
    seen = set()

    for slot in profile.slots:
        assert not (seen & slot.symbols)
        seen |= slot.symbols


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_slot_index_is_unique_for_every_symbol(profile):
    for symbol in profile.symbols:
        index = profile.slot_index_for(symbol)

        assert index is not None
        assert profile.slots[index].is_satisfied_by(symbol)


def test_slot_index_is_none_for_a_symbol_of_another_profile():
    assert FULL_STACK_DEVELOPER.slot_index_for("PYTHON") is None
    assert FULL_STACK_DEVELOPER.slot_index_for("DOCKER") is None
    assert DATA_ENGINEER.slot_index_for("PYTHON") is None


# SHARING BETWEEN PROFILES IS THE OPPOSITE, AND INTENDED


def test_git_is_required_by_three_profiles():
    holders = [profile.key for profile in PROFILES if "GIT" in profile.symbols]

    assert set(holders) == {
        "FULL_STACK_DEVELOPER", "MACHINE_LEARNING_ENGINEER", "DEVOPS_ENGINEER",
    }


def test_sql_is_required_by_three_profiles():
    holders = [profile.key for profile in PROFILES if "SQL" in profile.symbols]

    assert set(holders) == {
        "FULL_STACK_DEVELOPER", "MACHINE_LEARNING_ENGINEER", "DATA_ENGINEER",
    }


def test_python_is_a_core_qualification_of_one_profile_only():
    # Section 4.4 notes that PYTHON is in the alphabet because it is the
    # Machine Learning Engineer language slot; for Data Engineer it is only a
    # supporting qualification, so it must not appear in any Data Engineer slot.
    holders = [profile.key for profile in PROFILES if "PYTHON" in profile.symbols]

    assert holders == ["MACHINE_LEARNING_ENGINEER"]


# CONSISTENCY WITH STAGE 2


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_every_slot_symbol_is_a_canonical_symbol(profile):
    # A slot requiring a symbol outside G could never be satisfied, because
    # Stage 2 cannot produce one.
    assert profile.symbols <= CANONICAL_SYMBOLS


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_no_slot_is_empty(profile):
    for slot in profile.slots:
        assert slot.symbols


def test_every_canonical_symbol_is_used_by_some_profile():
    # A consequence of keeping G restricted to core qualifications: nothing in
    # the alphabet is inert. If this ever fails, the symbol it names only ever
    # produces self loops and should be reviewed.
    assert UNUSED_SYMBOLS == frozenset()


# LOOKUP


def test_profile_for_finds_each_profile_by_key():
    for profile in PROFILES:
        assert profile_for(profile.key) is profile


def test_profile_for_returns_none_on_an_unknown_key():
    assert profile_for("NOT_A_PROFILE") is None
