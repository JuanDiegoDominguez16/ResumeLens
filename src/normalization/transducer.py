"""
The qualification normalization transducer, Stage 2.

This module builds the finite-state transducer defined in
docs/formalization.md section 3 using pyformlang, and exposes it in the same
terms the document states, so that the 7-tuple in the design and the object in
the code can be compared component by component.

    M = (Q, S, G, d, w, q0, F)

    Q   states                  {q0, qf}               section 3.5
    S   input alphabet          folded representations  section 3.3
    G   output alphabet         canonical symbols       section 3.4
    d   transition relation     d(q0, a) = qf           section 3.6
    w   output relation         w(q0, a) = b            section 3.6
    q0  initial state           q0                      section 3.5
    F   accepting states        {qf}                    section 3.5

Section 3.3 defines the input alphabet over complete qualification
representations rather than characters, so normalizing one qualification is a
single transition from the initial state to the accepting state:

    q0 ── React.js / REACT ──→ qf

The complete component contains one such transition for every representation in
the controlled vocabulary, which is why Q stays at two states no matter how many
qualifications the vocabulary grows to hold. What grows is the number of
transitions, not the number of states.

The vocabulary itself lives in vocabulary.py, which is the single source of
truth for S and G. This module only turns that data into a machine.


WHY THE TRANSITIONS CARRY FOLDED SYMBOLS

The input symbols of the machine are folded representations, produced by
vocabulary.fold(). The reason is given at length in that module: the extraction
stage returns whatever the resume literally wrote, and its patterns are mostly
case insensitive, so the set of strings that can arrive is not finite in any
useful sense.

The practical consequence here is that translate() folds before consulting the
machine. Calling fst.translate() directly with a raw string taken from a resume
will usually find nothing, because "React.js" is not an input symbol of the
machine while "reactjs" is.


RELATION TO pyformlang

pyformlang models a transducer as a set of transitions of the form

    (state, input_symbol) -> [(next_state, [output_symbols])]

which is slightly more general than section 3.6 needs, in two ways. It allows a
transition to produce several output symbols, while every transition here
produces exactly one canonical symbol; and it allows several start states, while
section 3.5 defines a single q0. Both restrictions are asserted when the machine
is built, so a future change that breaks the correspondence with the document
fails immediately instead of quietly producing a different model.
"""

import shutil
import subprocess
from pathlib import Path

from pyformlang.fst import FST

from src.normalization import vocabulary


# The two states of section 3.5.
INITIAL_STATE = "q0"
ACCEPTING_STATE = "qf"


# ---------------------------------------------------------------------------
# CONSTRUCTION
# ---------------------------------------------------------------------------

def build_transducer(canonical_symbols=None):
    """
    Build the normalization transducer.

    With no argument the machine covers the whole controlled vocabulary. Pass a
    collection of canonical symbols to build a machine restricted to them,
    which is what the per category diagrams use: a picture of all 51 transitions
    at once is not readable, so each diagram shows the transitions of one
    qualification category.

        build_transducer()                      the complete component
        build_transducer({"REACT", "VUE"})      two qualifications

    The result is a pyformlang FST whose transitions all run from INITIAL_STATE
    to ACCEPTING_STATE.
    """

    if canonical_symbols is None:
        canonical_symbols = vocabulary.CANONICAL_SYMBOLS

    unknown = set(canonical_symbols) - vocabulary.CANONICAL_SYMBOLS
    if unknown:
        raise ValueError(
            f"not canonical symbols of the vocabulary: {sorted(unknown)}"
        )

    transducer = FST()
    transducer.add_start_state(INITIAL_STATE)
    transducer.add_final_state(ACCEPTING_STATE)

    for input_symbol, canonical in sorted(vocabulary.VARIANT_TO_CANONICAL.items()):
        if canonical in canonical_symbols:
            transducer.add_transition(
                INITIAL_STATE,
                input_symbol,
                ACCEPTING_STATE,
                [canonical],
            )

    _assert_matches_document(transducer)

    return transducer


def _assert_matches_document(transducer):
    """
    Check the built machine against the definition in section 3.

    These are the properties the design document states and that pyformlang
    does not enforce on its own. Checking them here is what keeps the
    implementation and the formalization from drifting apart.
    """

    if transducer.start_states != {INITIAL_STATE}:
        raise ValueError(
            f"section 3.5 defines a single initial state; got "
            f"{sorted(transducer.start_states)}"
        )

    if transducer.final_states != {ACCEPTING_STATE}:
        raise ValueError(
            f"section 3.5 defines F = {{qf}}; got "
            f"{sorted(transducer.final_states)}"
        )

    if not transducer.states <= {INITIAL_STATE, ACCEPTING_STATE}:
        raise ValueError(
            f"section 3.5 defines Q = {{q0, qf}}; got "
            f"{sorted(transducer.states)}"
        )

    for (state, input_symbol), arrivals in transducer.transitions.items():

        # Section 3.2: the relations are functional, so one input
        # representation determines a unique next state and a unique output.
        if len(arrivals) != 1:
            raise ValueError(
                f"section 3.2 requires a functional relation, but "
                f"{input_symbol!r} from {state} has {len(arrivals)} arrivals"
            )

        next_state, outputs = arrivals[0]

        if len(outputs) != 1:
            raise ValueError(
                f"every transition produces exactly one canonical symbol, but "
                f"{input_symbol!r} produces {outputs}"
            )

        if outputs[0] not in vocabulary.CANONICAL_SYMBOLS:
            raise ValueError(
                f"{input_symbol!r} produces {outputs[0]!r}, which is not in G"
            )


# The complete component, built once at import time.
TRANSDUCER = build_transducer()


# ---------------------------------------------------------------------------
# TRANSLATION
# ---------------------------------------------------------------------------

def translate(representation, transducer=None):
    """
    Run one qualification representation through the transducer.

    The representation is folded first, so any casing and any accepted
    separator reaches the same input symbol:

        translate("React.js")   -> "REACT"
        translate("REACTJS")    -> "REACT"
        translate("JS")         -> "JAVASCRIPT"
        translate("Kubernetes") -> None
        translate("hello")      -> None

    Returns None when the representation is not in the relation. Stage 2 tells
    the two reasons for that apart, a variant deliberately left out of the
    vocabulary versus a string that is not a qualification, and normalizer.py
    is what reports it.
    """

    if transducer is None:
        transducer = TRANSDUCER

    translations = list(transducer.translate([vocabulary.fold(representation)]))

    if not translations:
        return None

    # Guaranteed single by _assert_matches_document.
    return translations[0][0]


# ---------------------------------------------------------------------------
# THE 7-TUPLE
# ---------------------------------------------------------------------------

def formal_definition(transducer=None):
    """
    Return the components of M = (Q, S, G, d, w, q0, F) as plain data.

    Used by the tests to compare the machine against section 3, and by the
    Streamlit interface to show the definition beside the result. The
    transition and output relations are returned together, keyed by the pair
    (state, input symbol), because in this model they are two readings of the
    same arrow:

        d(q0, "reactjs") = qf        the state part
        w(q0, "reactjs") = REACT     the output part
    """

    if transducer is None:
        transducer = TRANSDUCER

    delta = {}
    omega = {}

    for (state, input_symbol), arrivals in transducer.transitions.items():
        next_state, outputs = arrivals[0]
        delta[(state, input_symbol)] = next_state
        omega[(state, input_symbol)] = outputs[0]

    return {
        "Q": frozenset(transducer.states),
        "Sigma": frozenset(transducer.input_symbols),
        "Gamma": frozenset(transducer.output_symbols),
        "delta": delta,
        "omega": omega,
        "q0": INITIAL_STATE,
        "F": frozenset(transducer.final_states),
    }


def surface_forms_by_input_symbol():
    """
    Group the documented surface representations by the input symbol they fold
    to, so a diagram edge can be labelled with every spelling it accepts.

        "reactjs" -> ("React.js", "ReactJS")
        "react"   -> ("React",)

    This is what makes the folding visible in the graphical representation:
    two spellings on one arrow are two spellings the machine cannot tell apart.
    """

    grouped = {}

    for canonical in vocabulary.VARIANTS:
        for representation in vocabulary.representations_of(canonical):
            grouped.setdefault(vocabulary.fold(representation), []).append(
                representation
            )

    return {key: tuple(forms) for key, forms in grouped.items()}


# ---------------------------------------------------------------------------
# GRAPHICAL REPRESENTATION
# ---------------------------------------------------------------------------

# The assignment requires a graphical representation of the transducers. The
# DOT below is generated from the transitions of the pyformlang object itself,
# not drawn by hand, so the picture cannot fall out of step with the machine.
#
# pyformlang ships FST.write_as_dot(), which also works. It is not used here
# because it labels every arrow "input" -> ["OUTPUT"], with the quotes and
# brackets of the Python repr, while section 3.5 writes transitions as
# input / OUTPUT. The notation of the document is the one that belongs in a
# deliverable.

_DOT_HEADER = """\
digraph {name} {{
    rankdir=LR;
    labelloc="t";
    label={title};
    fontname="Helvetica";
    node [fontname="Helvetica", fontsize=11];
    edge [fontname="Helvetica", fontsize=10];

    {start_marker} [shape=none, label="", width=0, height=0];
"""


def _quote(text):
    """Quote a string for DOT, escaping what DOT treats specially."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_dot(transducer=None, name="fst", title=None):
    """
    Render a transducer as DOT.

    Every arrow is labelled in the notation of section 3.5, with the accepted
    spellings on the left of the slash and the canonical symbol on the right:

        React.js · ReactJS / REACT

    Arrows are sorted by canonical symbol so the picture is stable between
    runs, which keeps the committed .svg files from changing when nothing about
    the model changed.
    """

    if transducer is None:
        transducer = TRANSDUCER

    if title is None:
        title = "Qualification normalization transducer"

    surface_forms = surface_forms_by_input_symbol()
    start_marker = "start"

    lines = [
        _DOT_HEADER.format(
            name=name,
            title=_quote(title),
            start_marker=start_marker,
        )
    ]

    # The initial state, and the accepting state with the double outline that
    # marks membership in F.
    for state in sorted(transducer.states):
        shape = "doublecircle" if state in transducer.final_states else "circle"
        lines.append(f"    {_quote(state)} [shape={shape}];\n")

    lines.append(f"    {start_marker} -> {_quote(INITIAL_STATE)};\n\n")

    arrows = []

    for (state, input_symbol), arrivals in transducer.transitions.items():
        next_state, outputs = arrivals[0]
        canonical = outputs[0]

        spellings = surface_forms.get(input_symbol, (input_symbol,))
        label = f"{' · '.join(spellings)} / {canonical}"

        arrows.append((canonical, label, state, next_state))

    for _, label, state, next_state in sorted(arrows):
        lines.append(
            f"    {_quote(state)} -> {_quote(next_state)} "
            f"[label={_quote(label)}];\n"
        )

    lines.append("}\n")

    return "".join(lines)


def render_svg(dot_source, destination):
    """
    Render DOT to SVG with the Graphviz dot binary.

    Returns True when the file was written, False when Graphviz is not
    installed. The .dot sources are always written, so a machine without
    Graphviz can still produce the sources and render them elsewhere.
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


def diagram_specifications():
    """
    The diagrams that make up the graphical representation of Stage 2.

    One overview of the complete component, then one diagram per qualification
    category. The split is a readability decision, not a modelling one: all of
    them are views of the same transducer, showing different subsets of d and w.
    The complete machine has 51 transitions between the same two states, and
    51 labelled arrows drawn on top of each other cannot be read.

    Returns a list of (filename stem, title, canonical symbols or None).
    """

    specifications = [
        (
            "fst_overview",
            "Stage 2 transducer, complete controlled vocabulary",
            None,
        )
    ]

    for category, canonicals in vocabulary.CATEGORY_OF_CANONICAL.items():
        stem = "fst_" + category.lower().replace(" ", "_")
        specifications.append((stem, f"Stage 2 transducer, {category}", set(canonicals)))

    return specifications


def write_diagrams(output_directory):
    """
    Write every diagram of diagram_specifications() as .dot and, when Graphviz
    is available, as .svg.

    Returns the list of paths written.
    """

    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)

    written = []

    for stem, title, canonicals in diagram_specifications():

        transducer = build_transducer(canonicals)
        dot_source = to_dot(transducer, name=stem, title=title)

        dot_path = directory / f"{stem}.dot"
        dot_path.write_text(dot_source, encoding="utf-8")
        written.append(dot_path)

        svg_path = directory / f"{stem}.svg"
        if render_svg(dot_source, svg_path):
            written.append(svg_path)

    return written


if __name__ == "__main__":
    # Regenerate the committed diagrams:
    #     python -m src.normalization.transducer
    paths = write_diagrams(Path("docs") / "diagrams")

    for path in paths:
        print(path)

    if not any(path.suffix == ".svg" for path in paths):
        print(
            "\nGraphviz was not found, only the .dot sources were written. "
            "Install it and run this again to refresh the .svg files."
        )
