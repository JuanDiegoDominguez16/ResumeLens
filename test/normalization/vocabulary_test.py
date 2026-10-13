from src.extraction.extractor import extract_qualifications
from src.normalization import vocabulary
from src.normalization.vocabulary import (
    CANONICAL_SYMBOLS,
    OUT_OF_SCOPE,
    SIGMA,
    VARIANT_TO_CANONICAL,
    canonical_for,
    category_of,
    fold,
    is_out_of_scope,
    out_of_scope_reason,
)


# The alphabet written out in docs/formalization.md section 4.4. Repeated here
# on purpose: if the document and the code disagree, one of them changed
# without the other, and that is what this file is for.
DOCUMENTED_ALPHABET = {
    "JAVASCRIPT", "TYPESCRIPT", "REACT", "ANGULAR", "VUE", "NODE_JS", "DJANGO",
    "SPRING_BOOT", "SQL", "NOSQL", "REST_API", "GIT", "PYTHON", "PANDAS",
    "NUMPY", "SCIKIT_LEARN", "TENSORFLOW", "PYTORCH", "MLMD", "DOCKER", "AWS",
    "AZURE", "GOOGLE_CLOUD", "JENKINS", "GITHUB_ACTIONS", "GITLAB_CI_CD",
    "TERRAFORM", "ANSIBLE", "AIRFLOW", "SPARK", "POSTGRESQL", "MYSQL",
    "DATABRICKS",
}


# FOLDING


def test_fold_ignores_case():
    assert fold("JavaScript") == fold("javascript") == fold("JAVASCRIPT")


def test_fold_ignores_the_dot():
    assert fold("React.js") == fold("ReactJS")


def test_fold_ignores_the_hyphen_and_the_space():
    assert fold("scikit-learn") == fold("scikit learn")


def test_fold_ignores_the_slash():
    assert fold("GitLab CI/CD") == fold("gitlab cicd")


def test_fold_keeps_plus_and_hash():
    # Without these, C++, C# and C would all fold together.
    assert fold("C++") != fold("C#")
    assert fold("C++") != fold("C")


def test_fold_strips_surrounding_whitespace():
    assert fold("  Git  ") == "git"


def test_fold_is_total():
    assert fold("") == ""
    assert fold("something that is not a qualification") == (
        "somethingthatisnotaqualification"
    )


# LOOKUP


def test_canonical_for_accepts_any_casing():
    for spelling in ["React.js", "react.js", "REACT.JS", "ReactJS", "React"]:
        assert canonical_for(spelling) == "REACT"


def test_different_variants_reach_the_same_symbol():
    assert canonical_for("JS") == canonical_for("JavaScript") == "JAVASCRIPT"


def test_canonical_for_returns_none_outside_the_relation():
    assert canonical_for("Kubernetes") is None
    assert canonical_for("not a qualification") is None


def test_out_of_scope_is_distinguishable_from_unknown():
    assert is_out_of_scope("Kubernetes")
    assert not is_out_of_scope("not a qualification")


def test_out_of_scope_carries_a_reason():
    assert out_of_scope_reason("Kubernetes")
    assert out_of_scope_reason("not a qualification") is None


def test_bare_machine_learning_is_out_of_scope():
    # The Machine Learning Engineer slot requires demonstrated model
    # development, so only the full phrase may reach MLMD.
    assert canonical_for("Machine Learning Model Development") == "MLMD"
    assert canonical_for("ML") is None
    assert is_out_of_scope("ML")
    assert is_out_of_scope("Machine Learning")


def test_the_rest_family_collapses_to_one_symbol():
    for spelling in ["REST", "REST API", "REST APIs"]:
        assert canonical_for(spelling) == "REST_API"


# THE ALPHABETS


def test_gamma_matches_the_documented_alphabet():
    assert CANONICAL_SYMBOLS == DOCUMENTED_ALPHABET


def test_gamma_has_thirty_three_symbols():
    assert len(CANONICAL_SYMBOLS) == 33


def test_every_canonical_symbol_is_reachable():
    # A symbol no representation maps to could never appear in a result.
    assert CANONICAL_SYMBOLS == set(VARIANT_TO_CANONICAL.values())


def test_sigma_is_the_set_of_folded_variants():
    assert SIGMA == set(VARIANT_TO_CANONICAL)


def test_variants_and_out_of_scope_are_disjoint():
    folded_out_of_scope = {fold(name) for name in OUT_OF_SCOPE}
    assert SIGMA & folded_out_of_scope == set()


def test_every_canonical_symbol_has_exactly_one_category():
    categorized = [
        symbol
        for symbols in vocabulary.CATEGORY_OF_CANONICAL.values()
        for symbol in symbols
    ]

    assert sorted(categorized) == sorted(CANONICAL_SYMBOLS)
    assert all(category_of(symbol) for symbol in CANONICAL_SYMBOLS)


# COVERAGE OF THE EXTRACTOR


def test_expander_agrees_with_extractor(extractor_samples):
    # Guards the fixture itself: if the expander produced strings the extractor
    # does not return, the coverage test below would be checking fiction.
    assert len(extractor_samples) > 200

    for _, sample in extractor_samples:
        found = extract_qualifications(sample)
        assert found and found[0].text == sample


def test_every_extractable_variant_is_accounted_for(extractor_samples):
    # The failure this prevents: the extractor recognizes something, Stage 2
    # has no rule for it, and it disappears without anyone noticing.
    unaccounted = [
        sample
        for _, sample in extractor_samples
        if canonical_for(sample) is None and not is_out_of_scope(sample)
    ]

    assert unaccounted == []


def test_every_pattern_in_the_extractor_is_covered(pattern_expansions):
    # The test above only sees samples the extractor confirmed. This one works
    # from the patterns directly, so a variant that the extractor declines to
    # reproduce in isolation is still required to have a rule in Stage 2.
    for pattern, literal in pattern_expansions:
        assert (
            canonical_for(literal) is not None or is_out_of_scope(literal)
        ), f"{pattern!r} produces {literal!r}, which Stage 2 ignores"
