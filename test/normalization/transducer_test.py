import pytest
from pyformlang.fst import FST

from src.normalization import vocabulary
from src.normalization.transducer import (
    ACCEPTING_STATE,
    INITIAL_STATE,
    TRANSDUCER,
    _assert_matches_document,
    build_transducer,
    formal_definition,
    surface_forms_by_input_symbol,
    translate,
)


# THE 7-TUPLE OF SECTION 3.2


def test_q_has_exactly_two_states():
    # Section 3.5: one transition consumes a whole representation, so the
    # machine never needs an intermediate state, however large the vocabulary.
    assert formal_definition()["Q"] == {INITIAL_STATE, ACCEPTING_STATE}


def test_there_is_a_single_initial_state():
    # pyformlang allows several; section 3.5 defines one.
    assert TRANSDUCER.start_states == {INITIAL_STATE}


def test_f_contains_only_the_accepting_state():
    assert formal_definition()["F"] == {ACCEPTING_STATE}


def test_sigma_is_the_vocabulary_input_alphabet():
    assert formal_definition()["Sigma"] == vocabulary.SIGMA


def test_gamma_is_the_vocabulary_output_alphabet():
    assert formal_definition()["Gamma"] == vocabulary.CANONICAL_SYMBOLS


def test_there_is_one_transition_per_input_symbol():
    definition = formal_definition()
    assert len(definition["delta"]) == len(vocabulary.SIGMA)


def test_delta_and_omega_share_a_domain():
    definition = formal_definition()
    assert set(definition["delta"]) == set(definition["omega"])


def test_every_transition_reaches_the_accepting_state():
    definition = formal_definition()
    assert set(definition["delta"].values()) == {ACCEPTING_STATE}


def test_omega_only_produces_canonical_symbols():
    definition = formal_definition()
    assert set(definition["omega"].values()) <= vocabulary.CANONICAL_SYMBOLS


# TRANSLATION


def test_translates_the_example_of_section_3_5():
    assert translate("React.js") == "REACT"


def test_translation_is_insensitive_to_casing_and_separators():
    for spelling in ["React.js", "react.js", "REACT.JS", "ReactJS", "reactjs"]:
        assert translate(spelling) == "REACT"


def test_abbreviation_and_full_name_reach_the_same_symbol():
    assert translate("JS") == translate("JavaScript") == "JAVASCRIPT"


def test_translate_returns_none_for_out_of_scope_representations():
    assert translate("Kubernetes") is None


def test_translate_returns_none_for_unknown_strings():
    assert translate("not a qualification") is None
    assert translate("") is None


def test_transducer_agrees_with_the_vocabulary_on_every_sample(extractor_samples):
    # Two independent paths to the same answer: the machine, and the table the
    # machine was built from. They must not diverge.
    for _, sample in extractor_samples:
        assert translate(sample) == vocabulary.canonical_for(sample)


# RESTRICTED MACHINES


def test_a_restricted_machine_only_carries_the_requested_symbols():
    machine = build_transducer({"REACT", "VUE"})

    assert machine.output_symbols == {"REACT", "VUE"}
    assert translate("React.js", machine) == "REACT"
    assert translate("Git", machine) is None


def test_a_restricted_machine_keeps_the_two_states():
    machine = build_transducer({"GIT"})
    assert machine.states == {INITIAL_STATE, ACCEPTING_STATE}


def test_building_with_an_unknown_symbol_is_rejected():
    with pytest.raises(ValueError):
        build_transducer({"NOT_A_CANONICAL_SYMBOL"})


# THE GUARDS THAT KEEP THE MACHINE AND THE DOCUMENT IN STEP
#
# _assert_matches_document is private, and exercised directly on purpose: it is
# the mechanism that makes a drift from section 3 fail loudly, so it needs a
# test of its own rather than being covered only through build_transducer,
# which never produces a machine that violates it.


def test_guard_rejects_a_second_initial_state():
    machine = build_transducer({"GIT"})
    machine.add_start_state("q9")

    with pytest.raises(ValueError):
        _assert_matches_document(machine)


def test_guard_rejects_a_state_outside_q():
    machine = build_transducer({"GIT"})
    machine.add_transition(INITIAL_STATE, "x", "q7", ["GIT"])

    with pytest.raises(ValueError):
        _assert_matches_document(machine)


def test_guard_rejects_an_output_outside_gamma():
    machine = build_transducer({"GIT"})
    machine.add_transition(INITIAL_STATE, "y", ACCEPTING_STATE, ["NOT_A_SYMBOL"])

    with pytest.raises(ValueError):
        _assert_matches_document(machine)


def test_guard_rejects_a_non_functional_relation():
    # Section 3.2 requires one input to determine one output. Two arrivals for
    # the same input symbol would make the relation ambiguous.
    machine = build_transducer({"GIT"})
    machine.add_transition(INITIAL_STATE, "git", ACCEPTING_STATE, ["PYTHON"])

    with pytest.raises(ValueError):
        _assert_matches_document(machine)


def test_guard_rejects_a_transition_with_several_outputs():
    machine = FST()
    machine.add_start_state(INITIAL_STATE)
    machine.add_final_state(ACCEPTING_STATE)
    machine.add_transition(INITIAL_STATE, "git", ACCEPTING_STATE, ["GIT", "SQL"])

    with pytest.raises(ValueError):
        _assert_matches_document(machine)


# LABELLING USED BY THE DIAGRAMS


def test_spellings_that_fold_together_share_one_transition():
    grouped = surface_forms_by_input_symbol()

    assert set(grouped[vocabulary.fold("React.js")]) == {"React.js", "ReactJS"}
    assert grouped[vocabulary.fold("React")] == ("React",)


def test_every_input_symbol_has_at_least_one_spelling():
    grouped = surface_forms_by_input_symbol()
    assert set(grouped) == vocabulary.SIGMA
