from itertools import permutations

import pytest
from pyformlang.finite_automaton import State, Symbol

from src.classification import automata
from src.classification.profiles import FULL_STACK_DEVELOPER, PROFILES
from src.normalization.vocabulary import CANONICAL_SYMBOLS


# A set that satisfies every Full Stack Developer slot exactly once, used as
# the base for the order and self loop tests.
FULL_STACK_SET = {
    "JAVASCRIPT", "REACT", "NODE_JS", "SQL", "REST_API", "GIT",
}


# THE 5-TUPLE OF SECTION 4.2


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_q_has_two_to_the_k_states(profile):
    definition = automata.formal_definition(profile)

    assert len(definition["Q"]) == 2 ** profile.slot_count


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_the_alphabet_is_the_canonical_symbols(profile):
    assert automata.formal_definition(profile)["Sigma"] == CANONICAL_SYMBOLS


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_the_initial_state_is_the_empty_subset(profile):
    assert automata.formal_definition(profile)["q0"] == frozenset()


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_there_is_a_single_accepting_state(profile):
    definition = automata.formal_definition(profile)

    assert definition["F"] == {frozenset(range(profile.slot_count))}


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_the_automaton_is_deterministic(profile):
    assert automata.automaton_for(profile).is_deterministic()


# SECTION 4.5: THE TRANSITION FUNCTION IS TOTAL


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_delta_is_defined_for_every_state_and_symbol(profile):
    automaton = automata.automaton_for(profile)

    expected = profile.state_count * len(CANONICAL_SYMBOLS)

    assert automaton.get_number_transitions() == expected


@pytest.mark.parametrize("profile", PROFILES, ids=lambda p: p.key)
def test_the_built_machine_agrees_with_the_rule_of_section_4_5(profile):
    # Every (state, symbol) pair of every automaton, compared against the rule
    # the document states. For the four profiles together this is 8448 pairs.
    automaton = automata.automaton_for(profile)

    for subset in automata.all_subsets(profile):
        for symbol in automata.ALPHABET:

            arrivals = automaton(State(subset), Symbol(symbol))

            assert len(arrivals) == 1
            assert arrivals[0].value == automata.next_subset(
                profile, subset, symbol
            )


def test_a_symbol_that_fills_a_new_slot_advances():
    subset = frozenset()

    assert automata.next_subset(FULL_STACK_DEVELOPER, subset, "GIT") == {5}


def test_a_symbol_that_fills_a_satisfied_slot_is_a_self_loop():
    subset = frozenset({5})

    assert automata.next_subset(FULL_STACK_DEVELOPER, subset, "GIT") == {5}


def test_a_symbol_of_another_profile_is_a_self_loop():
    subset = frozenset({5})

    assert automata.next_subset(FULL_STACK_DEVELOPER, subset, "DOCKER") == {5}


# THE WORKED EXAMPLE OF SECTION 4.5


def test_the_worked_example_reaches_the_accepting_state():
    subset = automata.initial_subset()

    walk = ["GIT", "SQL", "REACT", "JAVASCRIPT", "NODE_JS", "REST_API"]
    labels = []

    for symbol in walk:
        subset = automata.next_subset(FULL_STACK_DEVELOPER, subset, symbol)
        labels.append(automata.state_label(FULL_STACK_DEVELOPER, subset))

    assert labels == [
        "q{6}", "q{4,6}", "q{2,4,6}", "q{1,2,4,6}", "q{1,2,3,4,6}", "qFS",
    ]
    assert subset == automata.accepting_subset(FULL_STACK_DEVELOPER)


# ORDER INDEPENDENCE


def test_acceptance_does_not_depend_on_the_order_of_the_symbols():
    # 720 orderings of the same set, one answer.
    outcomes = {
        automata.accepts(FULL_STACK_DEVELOPER, order)
        for order in permutations(FULL_STACK_SET)
    }

    assert outcomes == {True}


def test_the_final_state_does_not_depend_on_the_order_either():
    states = {
        automata.final_subset(FULL_STACK_DEVELOPER, order)
        for order in permutations(FULL_STACK_SET)
    }

    assert len(states) == 1


# SELF LOOPS


def test_a_repeated_qualification_does_not_break_acceptance():
    # This is the case that fails without the self loops of section 4.5: a
    # deterministic automaton rejects a symbol it has no transition for.
    assert automata.accepts(
        FULL_STACK_DEVELOPER, list(FULL_STACK_SET) + ["GIT", "GIT"]
    )


def test_qualifications_of_other_profiles_do_not_break_acceptance():
    assert automata.accepts(
        FULL_STACK_DEVELOPER,
        list(FULL_STACK_SET) + ["DOCKER", "PYTHON", "AIRFLOW"],
    )


def test_a_second_symbol_for_a_satisfied_slot_does_not_break_acceptance():
    assert automata.accepts(
        FULL_STACK_DEVELOPER, list(FULL_STACK_SET) + ["VUE", "ANGULAR"]
    )


def test_symbols_outside_the_alphabet_are_ignored():
    assert automata.accepts(
        FULL_STACK_DEVELOPER, list(FULL_STACK_SET) + ["NOT_A_SYMBOL"]
    )


# ACCEPTANCE IS EXACT


def test_removing_any_single_qualification_rejects():
    for symbol in sorted(FULL_STACK_SET):
        assert not automata.accepts(FULL_STACK_DEVELOPER, FULL_STACK_SET - {symbol})


def test_the_empty_set_is_rejected_by_every_profile():
    for profile in PROFILES:
        assert not automata.accepts(profile, set())


def test_missing_slots_names_what_was_not_satisfied():
    missing = automata.missing_slots(
        FULL_STACK_DEVELOPER, {"JAVASCRIPT", "REACT", "NODE_JS", "GIT"}
    )

    assert [slot.name for slot in missing] == ["database", "REST API"]


def test_missing_slots_is_empty_when_accepted():
    assert automata.missing_slots(FULL_STACK_DEVELOPER, FULL_STACK_SET) == ()


# STATE LABELS


def test_the_empty_subset_is_labelled_q0():
    assert automata.state_label(FULL_STACK_DEVELOPER, frozenset()) == "q0"


def test_the_accepting_subset_uses_the_label_of_section_4_6():
    accepting = automata.accepting_subset(FULL_STACK_DEVELOPER)

    assert automata.state_label(FULL_STACK_DEVELOPER, accepting) == "qFS"


def test_a_partial_subset_is_labelled_with_slot_numbers():
    assert automata.state_label(FULL_STACK_DEVELOPER, frozenset({0, 3})) == "q{1,4}"


# LOOKUP


def test_automaton_for_accepts_a_profile_or_a_key():
    assert automata.automaton_for(FULL_STACK_DEVELOPER) is automata.automaton_for(
        "FULL_STACK_DEVELOPER"
    )


def test_automaton_for_rejects_an_unknown_profile():
    with pytest.raises(ValueError):
        automata.automaton_for("NOT_A_PROFILE")
