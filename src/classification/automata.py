"""
The profile recognition automata, Stage 3.

This module builds one deterministic finite automaton per professional profile,
following docs/formalization.md sections 4.2 to 4.6, using pyformlang. The slot
definitions come from profiles.py; the stage API that reports results is
classifier.py.

    M = (Q, S, d, q0, F)

    Q   states            the subsets of satisfied slots, |Q| = 2^k   4.3
    S   alphabet          the canonical symbols of Stage 2            4.4
    d   transition        total, advance on a new slot else self loop 4.5
    q0  initial state     the empty subset                            4.6
    F   accepting states  the subset containing every slot            4.6


STATES ARE SUBSETS OF SLOTS

Section 4.3 builds the state set from the subsets of requirement slots that
have been satisfied so far, so for a profile with k slots there are 2^k states.
The states here are literally frozensets of slot indices, which keeps the code
and the document reading the same way:

    frozenset()           q0,  nothing satisfied yet
    frozenset({1, 5})     the frontend and version control slots satisfied
    frozenset(range(k))   the single accepting state

For the Full Stack Developer profile that is 64 states, for Machine Learning
Engineer 128. The count is exponential in the number of requirements but
finite, which is the whole point of section 4.2: however many qualifications a
profile asks for, the machine stays a valid DFA.


WHY THE TRANSITION FUNCTION HAS TO BE TOTAL

Section 4.5 defines d for every state and every symbol of S:

    d(q_T, a) = q_{T union {i}}   if a satisfies slot i and i is not in T
    d(q_T, a) = q_T               otherwise

The second case is not a formality, and it is not only a modelling
convenience. In pyformlang, a deterministic automaton rejects any input symbol
for which no transition is defined from the current state. Without the self
loops, a resume that merely mentions Git twice would be rejected by an
automaton whose six slots are all satisfied, and so would a Full Stack
candidate who happens to also know Docker.

So the self loops are what make acceptance depend on which symbols are present
rather than on how many times they appear or what else appears beside them.
That is the property section 3.8 relies on when it says normalization may hand
Stage 3 an unordered set.


THE FOUR AUTOMATA ARE INDEPENDENT

Each profile has its own machine, with its own q0 and its own accepting state,
and all four read the same alphabet. A candidate's set is run through each of
them separately, so it may be accepted by none, by one, or by several. Nothing
in this module compares profiles or ranks them; classifier.py collects the four
answers without combining them into a score.
"""

import shutil
import subprocess
from itertools import chain, combinations
from pathlib import Path

from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol

from src.classification.profiles import PROFILES, PROFILE_BY_KEY
from src.normalization.vocabulary import CANONICAL_SYMBOLS


# The alphabet of section 4.4, shared by all four automata. Sorted so that
# construction, and anything derived from it, is reproducible.
ALPHABET = tuple(sorted(CANONICAL_SYMBOLS))


def initial_subset():
    """q0 of section 4.6: no slot satisfied yet."""
    return frozenset()


def accepting_subset(profile):
    """The single accepting state of section 4.6: every slot satisfied."""
    return frozenset(range(profile.slot_count))


def all_subsets(profile):
    """
    Every state of section 4.3, the 2^k subsets of the slot indices.

    Ordered by size and then by content, so the state list reads from q0
    outwards rather than in whatever order the powerset happened to come out.
    """

    indices = range(profile.slot_count)

    return [
        frozenset(subset)
        for subset in chain.from_iterable(
            combinations(indices, size) for size in range(len(indices) + 1)
        )
    ]


def next_subset(profile, subset, symbol):
    """
    The transition rule of section 4.5, on subsets rather than on State objects.

    Returns the subset reached from `subset` on `symbol`: the subset with one
    more slot when the symbol satisfies a slot that is not yet in it, and the
    same subset otherwise. profiles.py guarantees a symbol satisfies at most
    one slot of a profile, which is what makes the result unique.
    """

    index = profile.slot_index_for(symbol)

    if index is None or index in subset:
        return subset

    return subset | {index}


def state_label(profile, subset):
    """
    A readable name for a state, for diagrams and for error messages.

        frozenset()            -> "q0"
        frozenset({1, 3})      -> "q{2,4}"     slot numbers as section 4.7 lists them
        the accepting subset   -> "qFS", "qML", "qDO" or "qDE", per section 4.6
    """

    if not subset:
        return "q0"

    if subset == accepting_subset(profile):
        return profile.state_label

    return "q{" + ",".join(str(index + 1) for index in sorted(subset)) + "}"


# ---------------------------------------------------------------------------
# CONSTRUCTION
# ---------------------------------------------------------------------------

def build_automaton(profile):
    """
    Build the deterministic finite automaton for one profile.

    Every subset of slots becomes a state and every (state, symbol) pair gets a
    transition, so the machine is the explicit 2^k state automaton that section
    4.3 describes rather than a lazily explored one. For the largest profile
    that is 128 states and 128 * 33 transitions, which is small enough to build
    eagerly and to inspect.
    """

    automaton = DeterministicFiniteAutomaton()

    automaton.add_start_state(State(initial_subset()))
    automaton.add_final_state(State(accepting_subset(profile)))

    for subset in all_subsets(profile):
        source = State(subset)

        for symbol in ALPHABET:
            automaton.add_transition(
                source,
                Symbol(symbol),
                State(next_subset(profile, subset, symbol)),
            )

    return automaton


AUTOMATA = {profile.key: build_automaton(profile) for profile in PROFILES}


def automaton_for(profile):
    """The automaton of a profile, accepting either a Profile or its key."""

    key = profile if isinstance(profile, str) else profile.key

    if key not in AUTOMATA:
        raise ValueError(f"unknown profile: {key}")

    return AUTOMATA[key]


# ---------------------------------------------------------------------------
# RUNNING A CANDIDATE
# ---------------------------------------------------------------------------

def final_subset(profile, symbols):
    """
    Run a set of canonical symbols through the profile's automaton and return
    the subset of slots satisfied when the input is exhausted.

    The walk goes through the pyformlang machine itself, one symbol at a time,
    rather than reapplying the rule of section 4.5 in Python. The two would
    agree, and the tests check that they do, but taking the machine's word for
    it is what makes this an automaton and not a set comparison wearing one as
    a costume.

    Symbols outside the alphabet are ignored rather than raising: Stage 2 only
    ever produces canonical symbols, so this can only happen when a caller
    builds a set by hand.
    """

    automaton = automaton_for(profile)
    state = State(initial_subset())

    for symbol in sorted(symbols):

        if symbol not in CANONICAL_SYMBOLS:
            continue

        arrivals = automaton(state, Symbol(symbol))

        # d is total, so exactly one arrival, but a missing transition would
        # silently leave the state unchanged if this were not checked.
        if len(arrivals) != 1:
            raise ValueError(
                f"the transition function is not total: no unique arrival "
                f"from {state.value} on {symbol}"
            )

        state = arrivals[0]

    return state.value


def accepts(profile, symbols):
    """
    Whether the profile's automaton accepts this set of canonical symbols.

    Delegates to pyformlang's own acceptance test. The symbols are sorted
    before being handed over so the word is reproducible; section 4.5 makes the
    result independent of that order, and the tests demonstrate it over every
    permutation of a representative set.
    """

    automaton = automaton_for(profile)

    word = [
        Symbol(symbol)
        for symbol in sorted(symbols)
        if symbol in CANONICAL_SYMBOLS
    ]

    return automaton.accepts(word)


def missing_slots(profile, symbols):
    """
    The slots this set leaves unsatisfied, in the order section 4.7 lists them.

    This is what turns a rejection into something a person can act on: not
    "not accepted", but "the deep learning framework and model development
    slots were never satisfied".
    """

    satisfied = final_subset(profile, symbols)

    return tuple(
        slot
        for index, slot in enumerate(profile.slots)
        if index not in satisfied
    )


# ---------------------------------------------------------------------------
# THE 5-TUPLE
# ---------------------------------------------------------------------------

def formal_definition(profile):
    """
    Return the components of M = (Q, S, d, q0, F) as plain data.

    Used by the tests to compare each machine against section 4, and by the
    interface to show the definition beside the result. d is keyed by
    (state subset, symbol), matching the way section 4.5 writes it.
    """

    automaton = automaton_for(profile)

    delta = {
        (subset, symbol): next_subset(profile, subset, symbol)
        for subset in all_subsets(profile)
        for symbol in ALPHABET
    }

    return {
        "Q": frozenset(state.value for state in automaton.states),
        "Sigma": frozenset(ALPHABET),
        "delta": delta,
        "q0": initial_subset(),
        "F": frozenset(state.value for state in automaton.final_states),
    }


def _check_automata():
    """
    Check each machine against section 4 at import time.

    pyformlang does not enforce any of this: it will happily hold a partial
    transition function, or a machine whose state count has drifted from the
    2^k the document states.
    """

    for profile in PROFILES:

        automaton = AUTOMATA[profile.key]

        if len(automaton.states) != profile.state_count:
            raise ValueError(
                f"{profile.key}: section 4.3 gives |Q| = 2^{profile.slot_count}"
                f" = {profile.state_count}, built {len(automaton.states)}"
            )

        if len(automaton.final_states) != 1:
            raise ValueError(
                f"{profile.key}: section 4.6 defines a single accepting state,"
                f" built {len(automaton.final_states)}"
            )

        if not automaton.is_deterministic():
            raise ValueError(f"{profile.key}: the automaton is not deterministic")

        # Section 4.5: d is defined for every state and every symbol.
        expected_transitions = profile.state_count * len(ALPHABET)
        if automaton.get_number_transitions() != expected_transitions:
            raise ValueError(
                f"{profile.key}: the transition function is not total, "
                f"expected {expected_transitions} transitions, "
                f"built {automaton.get_number_transitions()}"
            )


_check_automata()

# ---------------------------------------------------------------------------
# DIAGRAMS
# ---------------------------------------------------------------------------

# The transition diagram section 4 asks for, one per profile.
#
# WHAT IS DRAWN, AND WHAT IS LEFT OUT
#
# The states are the 2^k subsets of section 4.3, every one of them, arranged in
# levels by how many slots they have satisfied: q0 alone at the top, the single
# accepting state alone at the bottom. An arrow is drawn for each transition
# that advances the automaton, labelled with the slot it fills.
#
# The self loops are not drawn. Section 4.5 makes d total, so every state has
# an arrow back to itself for each of the 33 symbols that does not fill a new
# slot, which for the Full Stack Developer automaton is 64 states times 27
# symbols. Drawing them would add 1,728 arrows that all say the same thing and
# would leave nothing else visible. The caption of each diagram states that
# they are there, and automata_test.py asserts it on the machine itself rather
# than on the picture.
#
# An arrow stands for a slot rather than for a symbol for the same reason: the
# frontend slot of section 4.7 accepts REACT, ANGULAR and VUE, which are three
# transitions with the same source, the same target and the same meaning. The
# symbols behind each slot are listed in the legend.

_DOT_HEADER = """\
digraph {name} {{
    rankdir=TB;
    labelloc="t";
    label={title};
    fontname="Helvetica";
    node [shape=circle, fontname="Helvetica", fontsize=10, width=0.3];
    edge [fontname="Helvetica", fontsize=8, arrowsize=0.6];

    start [shape=none, label="", width=0, height=0];
"""


def _quote(text):
    """Quote a string for DOT, escaping what DOT treats specially."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'

def _quote_label(text):
    """
    Quote a caption for DOT, leaving its backslash escapes alone.

    The caption carries DOT's own line breaks, \\n for a centred line and
    \\l for a left aligned one, so unlike a node name it must not have its
    backslashes doubled: that is what turns a line break into the two
    characters printed on the picture.
    """

    return '"' + text.replace('"', '\\"') + '"'


def to_dot(profile, name=None, title=None):
    """
    Render one profile's automaton as DOT.

        >>> source = to_dot(PROFILE_BY_KEY["DATA_ENGINEER"])
        >>> source.startswith("digraph")
        True

    The accepting state is drawn as a double circle, as section 4.6 defines a
    single one, and the arrow with no source marks q0.
    """

    name = name or profile.key.lower()
    title = title or f"{profile.name}, M = (Q, S, d, q0, F)"

    accepting = accepting_subset(profile)

    legend = "\\l".join(
        f"slot {index + 1}, {slot.name}: " + " or ".join(sorted(slot.symbols))
        for index, slot in enumerate(profile.slots)
    )

    caption = (
        f"{title}\\n"
        f"|Q| = 2^{profile.slot_count} = {profile.state_count} states, "
        f"|S| = {len(ALPHABET)} symbols, q0 = q0, F = {{{profile.state_label}}}\\n"
        f"Arrows show the transitions that fill a slot. The self loops that "
        f"make d total, section 4.5, are not drawn.\\n\\l{legend}\\l"
    )

    lines = [_DOT_HEADER.format(name=name, title=_quote_label(caption))]

    # The states, grouped by how many slots they have satisfied, so that the
    # lattice reads from q0 downwards instead of as a cloud.

    by_level = {}

    for subset in all_subsets(profile):
        by_level.setdefault(len(subset), []).append(subset)

    for level in sorted(by_level):

        lines.append("    { rank=same;")

        for subset in by_level[level]:

            shape = "doublecircle" if subset == accepting else "circle"
            label = state_label(profile, subset)

            lines.append(
                f" {_quote(label)} [shape={shape}, "
                f"label={_quote(label)}];"
            )

        lines.append(" }\n")

    lines.append(f"    start -> {_quote(state_label(profile, frozenset()))};\n")

    # The advancing transitions: from every state, one arrow per slot it has
    # not satisfied yet.

    for subset in all_subsets(profile):

        source = state_label(profile, subset)

        for index, slot in enumerate(profile.slots):

            if index in subset:
                continue

            target = state_label(profile, subset | {index})

            lines.append(
                f"    {_quote(source)} -> {_quote(target)} "
                f"[label={_quote(str(index + 1))}];\n"
            )

    lines.append("}\n")

    return "".join(lines)


def render_svg(dot_source, destination):
    """
    Render DOT to SVG with the Graphviz dot binary.

    Returns True when the file was written, False when Graphviz is not
    installed. The .dot sources are always written, so a machine without
    Graphviz can still produce them and render them elsewhere.
    """

    if shutil.which("dot") is None:
        return False

    result = subprocess.run(
        ["dot", "-Tsvg", "-o", str(destination)],
        input=dot_source,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"dot failed: {result.stderr.strip()}")

    return True


def write_diagrams(output_directory):
    """
    Write the transition diagram of each of the four profiles as .dot and,
    when Graphviz is available, as .svg.

    Returns the list of paths written.
    """

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)

    written = []

    for profile in PROFILES:

        stem = "dfa_" + profile.key.lower()
        dot_source = to_dot(profile, name=stem)

        dot_path = directory / f"{stem}.dot"
        dot_path.write_text(dot_source, encoding="utf-8")
        written.append(dot_path)

        svg_path = directory / f"{stem}.svg"
        if render_svg(dot_source, svg_path):
            written.append(svg_path)

    return written


if __name__ == "__main__":
    # Regenerate the committed diagrams:
    #     python -m src.classification.automata
    paths = write_diagrams(Path("docs") / "diagrams")

    for path in paths:
        print(path)

    if not any(path.suffix == ".svg" for path in paths):
        print(
            "\nGraphviz was not found, only the .dot sources were written. "
            "Install it and run this again to refresh the .svg files."
        )