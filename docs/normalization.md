# Stage 2 Module Design, Qualification Normalization

## 1. Purpose

This document describes the modules that implement the qualification
normalization stage, the inputs and outputs of each function, and the design
decisions that `formalization.md` section 3 leaves open. It is the module
design deliverable for Stage 2, and it resolves part of what
`architecture.md` section 8 records as deferred.

The formal model itself is not restated here. The 7-tuple, the alphabets and
the transition and output relations are defined in `formalization.md`
section 3, and the graphical representations are in `docs/diagrams/`.

## 2. Position in the Pipeline

The stage receives the qualification representations that Stage 1 recognized
and produces the set of canonical symbols that Stage 3 classifies.

```text
extractor.qualification_strings(resume_text)
    ["JS", "React.js", "NodeJS", "Postgres", "Git"]
            |
            v
    normalizer.normalize(representations)
            |
            v
    {GIT, JAVASCRIPT, NODE_JS, POSTGRESQL, REACT}
```

The stage does not extract and does not classify. None of the three modules
below imports the extraction package: section 3.3 defines the input of this
stage as the representations Stage 1 produced, not as the résumé, and keeping
the dependency out is what allows the two stages to be tested independently,
as `architecture.md` section 7 requires. Joining them is `src/pipeline.py`.

## 3. Module Map

| Module | Responsibility |
|---|---|
| `src/normalization/vocabulary.py` | The alphabets Σ and Γ, the variant relation, and the orthographic folding function. Data only. |
| `src/normalization/transducer.py` | Builds the finite-state transducer with pyformlang and exposes its 7-tuple. Also renders the diagrams. |
| `src/normalization/normalizer.py` | The stage API: runs a sequence of representations and reports the canonical set plus what was discarded. |

The dependency direction is one way: `normalizer` uses `transducer`, which
uses `vocabulary`. Nothing points back.

## 4. `vocabulary.py`

### 4.1 Contract

| Function | Input | Output |
|---|---|---|
| `fold(representation)` | any string | the folded form: lowercase, separators removed |
| `canonical_for(representation)` | any string | the canonical symbol, or `None` |
| `is_out_of_scope(representation)` | any string | `True` when Stage 1 recognizes it and Stage 2 deliberately does not normalize it |
| `out_of_scope_reason(representation)` | any string | the documented reason, or `None` |
| `category_of(canonical)` | a canonical symbol | its qualification category from `profiles.md` section 6 |
| `representations_of(canonical)` | a canonical symbol | the documented surface spellings, in order |

Data exported: `VARIANTS`, `OUT_OF_SCOPE`, `CATEGORY_OF_CANONICAL`,
`VARIANT_TO_CANONICAL`, `SIGMA`, `CANONICAL_SYMBOLS`, `OUT_OF_SCOPE_FOLDED`.

### 4.2 Why Folding Is Needed

Section 3.3 defines the input alphabet over complete qualification
representations rather than characters. The extraction stage, however, does
not produce a fixed set of strings: most of its patterns are case insensitive
and return whatever the résumé literally wrote, and several accept alternative
separators. Enumerating every accepted casing as a distinct symbol of Σ is not
possible, since a case insensitive pattern of n letters accepts 2^n spellings.

Σ is therefore defined over folded representations, and `fold` is the total
function that maps any extracted string to its folded form:

```text
fold("JavaScript")  ->  "javascript"  --FST-->  JAVASCRIPT
fold("JS")          ->  "js"          --FST-->  JAVASCRIPT
fold("React.js")    ->  "reactjs"     --FST-->  REACT
fold("ReactJS")     ->  "reactjs"     --FST-->  REACT
```

Folding removes only distinctions that carry no information in this domain,
letter case and the choice of separator between the words of a technology
name. Deciding that `JS` and `JavaScript` denote the same qualification is not
folding: that decision is specific to this domain and belongs in the
transducer, where it is stated as part of the model.

The same effect could be obtained by composing a case folding transducer with
the normalization transducer, which is the construction Mohri (1997) describes
and `literature-review.md` section 4.1 reviews. Folding is kept as a separate
function so that the transducer of section 3 stays small enough to be written
out as a 7-tuple.

The characters `+` and `#` are deliberately not folded away: they are the only
thing distinguishing `C++`, `C#` and `C` from each other.

### 4.3 The Size of the Alphabets

| | Count |
|---|---|
| Γ, canonical symbols | 33 |
| Σ, folded input representations | 51 |
| Recognized but not normalized, folded | 18 |

Γ matches the alphabet written out in `formalization.md` section 4.4 exactly.

### 4.4 Decisions Recorded Here

**The `MLMD` slot requires the full phrase.** The Machine Learning Engineer
pattern has a slot for demonstrated model development. Only
`Machine Learning Model Development` and its hyphenated form map to `MLMD`.
The bare terms `ML`, `Machine Learning` and `Deep Learning` are recognized by
Stage 1 but given no canonical symbol, because mapping them to `MLMD` would
let any résumé that merely names the field satisfy a slot intended to
represent demonstrated work.

**The REST family collapses to one symbol.** `REST`, `REST API` and
`REST APIs` all produce `REST_API`. The Full Stack Developer pattern has a
single REST slot, so distinguishing the plural would create two symbols that
no slot tells apart.

**Variants outside Γ are discarded rather than added to the alphabet.** The
extractor recognizes technologies beyond the controlled vocabulary of section
2.3, among them Kubernetes, MongoDB, Redis, Keras, Flask, Java and C++.
Extending Γ with them would change no classification result, since no profile
slot accepts them and section 4.5 makes every symbol outside a profile's slots
a self loop; it would only enlarge the alphabet the design documents have to
state. They are therefore dropped at the end of this stage, with the reason
recorded, and `formalization.md` section 4.4 was corrected to describe this
mechanism accurately.

## 5. `transducer.py`

### 5.1 Contract

| Function | Input | Output |
|---|---|---|
| `build_transducer(canonical_symbols=None)` | optionally a subset of Γ | a pyformlang `FST` |
| `translate(representation, transducer=None)` | any string | the canonical symbol, or `None` |
| `formal_definition(transducer=None)` | optionally an FST | a dict with `Q`, `Sigma`, `Gamma`, `delta`, `omega`, `q0`, `F` |
| `surface_forms_by_input_symbol()` | — | folded symbol to the spellings that reach it |
| `to_dot(transducer, name, title)` | an FST | DOT source, generated from the machine's own transitions |
| `write_diagrams(output_directory)` | a directory | the `.dot` and `.svg` files written |

Constants: `INITIAL_STATE` (`"q0"`), `ACCEPTING_STATE` (`"qf"`), `TRANSDUCER`
(the complete component, built at import).

`translate` folds before consulting the machine. Calling
`fst.translate()` directly with a raw string from a résumé will usually find
nothing, because `"React.js"` is not an input symbol of the machine while
`"reactjs"` is.

### 5.2 Checks Performed at Import

pyformlang is more general than section 3 needs, and enforces none of the
following. `_assert_matches_document` raises rather than letting the
implementation drift from the document:

- a single initial state, where pyformlang allows several;
- `Q ⊆ {q0, qf}`;
- a functional relation, one arrival per input symbol, as section 3.2 requires;
- exactly one output symbol per transition, and that symbol in Γ.

### 5.3 Diagrams

Nine diagrams are generated: one overview of the complete component and one
per qualification category. All of them are views of the same transducer,
showing different subsets of δ and ω; the split is a readability decision, not
a modelling one, since 51 labelled arrows between two states cannot be read.

The DOT is generated from the transitions of the pyformlang object itself, so
the picture cannot fall out of step with the machine. Regenerate with:

```bash
python -m src.normalization.transducer
```

pyformlang ships `FST.write_as_dot()`, which also works. It is not used because
it labels every arrow `"input" -> ["OUTPUT"]`, with the quotes and brackets of
the Python repr, while section 3.5 writes transitions as `input / OUTPUT`.

## 6. `normalizer.py`

### 6.1 Contract

| Function | Input | Output |
|---|---|---|
| `normalize(representations)` | an iterable of strings | a `NormalizationResult` |
| `canonical_set(representations)` | an iterable of strings | the `frozenset` alone |

`NormalizationResult` carries `normalized`, `out_of_scope` and `unknown`, and
exposes `qualification_set` (the formal output of section 3.8, a frozenset),
`qualifications` (the same symbols sorted, for display) and `discarded` (both
kinds of omission together).

### 6.2 Two Views of One Output

Section 3.8 defines the output as a set with duplicates removed, and states
that the automata of section 4 are built so acceptance depends only on which
symbols are present. `qualification_set` is a frozenset rather than a sequence
so that no consumer can come to depend on an order the model does not define.
`qualifications` sorts the same content alphabetically for display and for
readable test assertions; the ordering is profile independent on purpose,
because section 3.8 rejects ordering by profile, which would assume the answer
Stage 3 is meant to produce.

### 6.3 Three Outcomes, Not Two

A transducer produces nothing for input outside its relation, so a
representation with no canonical symbol simply disappears. Beesley and
Karttunen (2003) note this as a property of the formalism rather than a bug.
A stage that silently drops part of its input cannot be audited, and
traceability is a design principle in `architecture.md` section 7, so the
result separates:

| Outcome | Meaning |
|---|---|
| normalized | the representation has a canonical symbol in Γ |
| out of scope | Stage 1 recognized it, the vocabulary deliberately gives it no symbol, reason attached |
| unknown | not a qualification representation at all |

The distinction is structural rather than a string to match on, so the
interface can show "recognized but not classified" separately from "not
understood".

### 6.4 Duplicate Handling

Representations that fold to the same input symbol are collapsed, keeping the
first spelling seen, so a résumé writing both `JS` and `js` produces one entry.
Spellings that fold differently are kept apart even when they share a canonical
symbol, so `JS` and `JavaScript` both appear in the trace, each mapped to
`JAVASCRIPT`. The point of the trace is to explain every string the résumé
contained, without repeating noise.

Blank strings are ignored rather than reported as unknown, since they carry no
information either way.
