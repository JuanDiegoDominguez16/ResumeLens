# Stage 4 Module Design, Candidate Profile Language

## 1. Purpose

This document describes the modules that implement the candidate profile
language, the inputs and outputs of each function, and the design decisions
that `formalization.md` section 5 leaves open. It is the module design
deliverable for Stage 4.

The formal model itself is not restated here. The EBNF grammar, its lexical
elements and the valid and rejected profiles are defined in
`formalization.md` section 5.

## 2. Position in the Pipeline

The stage receives what the first three stages produced and returns a profile
that the grammar accepts, together with the document rendered from it.

```text
extraction, normalization, classification
            |
            v
    generator.render(...)        the profile written in the language
            |
            v
    validator.validate(source)   the model, or InvalidProfile
            |
            v
    visualization.to_html(model) the document
```

The stage does not read the résumé, and it does not re-derive anything the
earlier stages decided. It states their results in a language whose structure
is defined by a grammar, checks them against that grammar, and renders them.

## 3. Module Map

| Module | Responsibility |
|---|---|
| `src/grammar/candidate_profile.tx` | The grammar of section 5.1, in the form textX reads. |
| `src/grammar/generator.py` | Writes the stage results as a sentence of the language. |
| `src/grammar/validator.py` | Parses a profile, or rejects it with the position of the offending token. |
| `src/grammar/visualization.py` | Renders a validated model as HTML or Markdown. |

The dependency direction is one way, and none of the three modules imports
another: the pipeline calls them in order. That is what allows the fixtures in
`examples/` to be validated and rendered without a generator ever running, and
it is why a profile written by hand reaches exactly the same parser as a
generated one.

## 4. `validator.py`

### 4.1 Contract

| Function | Input | Output |
|---|---|---|
| `validate(source)` | a profile as text | the textX model, or raises `InvalidProfile` |
| `validate_file(path)` | a path | the same, with the file name attached to a rejection |
| `is_valid(source)` | a profile as text | `True` or `False`, discarding the reason |
| `metamodel()` | — | the textX metamodel, built once and reused |

Data exported: `GRAMMAR_PATH`, `InvalidProfile`.

`InvalidProfile` carries `message`, `line`, `column`, `source` and `path`
separately rather than only a formatted string, and `excerpt()` returns the
offending line with a caret under the offending column.

### 4.2 Why Validation Is Not Circular

The profile the pipeline validates is one this system wrote itself a few
milliseconds earlier. If the generator is correct the parser can only succeed,
which makes the check look like a formality.

It is not, because section 5 defines a candidate profile as what the grammar
accepts, not as whatever the generator emits. The grammar therefore has to be
able to reject, and keeping the parser in a module that knows nothing about
the generator is what keeps the check real. `examples/invalid/` is parsed by
the same function as a generated profile, and `rejection_test.py` takes a
profile that parses and breaks one rule at a time.

### 4.3 Decisions Recorded Here

**The metamodel is built once.** Building it parses the grammar file, which is
wasted work on every call. A single instance also means a grammar that does not
compile fails on the first use rather than on some later one.

**The position prefix is stripped from the message.** textX writes the position
into its message as well as into its attributes, as
`None:4:16: Expected EMAIL => ...`. Keeping both would print it twice, so the
prefix is removed and `__str__` formats the position once.

**`InvalidProfile` is raised, not returned.** A rejection is an exceptional
outcome for a generated profile, since it means the generator and the grammar
disagree. Returning a result object would let a caller ignore it.

## 5. `generator.py`

### 5.1 Contract

| Function | Input | Output |
|---|---|---|
| `render(extraction, normalization, classification)` | the three stage results | the profile as text |
| `quote(value)` | any string or `None` | the value as a `String` of the language |
| `split_degree(text)` | an academic qualification | `(degree, field)` |
| `years_in(text)` | an experience phrase | the number of years, or `None` |
| `first_text(findings)` | a list of `Finding` | the text of the first, or `None` |

Data exported: `INDENT`, `IncompleteProfile`.

### 5.2 What It Refuses To Invent

Every value comes from a stage: the name and the contact details from Stage 1,
the skills from Stage 2, the classifications from Stage 3. Where the résumé
said nothing and the grammar requires a value, the generator writes an empty
string rather than a plausible default:

| Written as `""` | Why |
|---|---|
| `name` | the résumé's first line was not a name |
| `field` | the degree names no field of study, as in `Ingeniería de Sistemas` |
| `position` | the résumé states years of experience but no job title |

An empty string is a value of the language, so these profiles still validate,
and a reader can tell "not stated" from "stated as such".

### 5.3 The One Value With No Empty Form

The `Email` rule of section 5.2 requires an `@` and a dot, so there is no way
to write "no email address" in the language. A résumé without one cannot be
represented, and `render` raises `IncompleteProfile` rather than inventing an
address.

`test-cases.md` section 8.4 originally expected an empty résumé to produce a
valid profile. Implementing this stage showed that it cannot, and the row was
corrected rather than satisfied with a fabricated value. The pipeline catches
the exception, keeps the results of the first three stages, and records the
reason in `profile_error`.

### 5.4 Decisions Recorded Here

**A degree is split at `in` or `en`.** Those are the connectors that introduce
a field of study in the patterns of section 2. `of` and `de` are deliberately
not in the list: `Bachelor of Science` and `Ingeniería de Sistemas` are degree
names, and splitting them would invent a field.

**Only the quotation mark is escaped.** Section 5.1 defines `String` as any run
of characters between quotes, and textX returns `\"` as a plain quotation mark,
so the round trip is exact. A backslash is not an escape character in this
language and is written through unchanged.

**Date ranges are not written.** Stage 1 extracts them, but they say when, and
the language has no field for that. An experience record whose phrase carries
no number is dropped rather than written without its `years`.

**The output is indented.** None of it is meaningful, since the language is not
layout sensitive, and `validator_test.py` checks that a profile flattened onto
one line still validates. The formatting exists because the interface shows
this text to a person.

## 6. `visualization.py`

### 6.1 Contract

| Function | Input | Output |
|---|---|---|
| `to_html(model)` | a validated model | a complete, self contained HTML document |
| `to_markdown(model)` | a validated model | the same content as Markdown |
| `name_of(model)` | a validated model | the candidate's name, or `not stated` |

Data exported: `NOT_STATED`, `STYLE`, `DISCLAIMER`.

### 6.2 It Renders the Model, Not the Source

The argument is the object textX built, never the profile text. Rendering the
text would mean parsing it a second time with a second, informal grammar
written in Python, and the two would drift. Taking the model also means
nothing reaches this module without having been validated, so the renderer has
no error case: every field it reads is one the grammar guaranteed.

### 6.3 Decisions Recorded Here

**The canonical symbols are shown as they are.** A qualification appears as
`GIT` and a classification as `FULL_STACK_DEVELOPER`, not as "Git" and "Full
Stack Developer". The prettier names live in `profiles.py`, and importing them
would make Stage 4 depend on Stage 3 for presentation. The better reason is
that the canonical symbol is what the system actually concluded: it is the
output of the transducer of section 3 and the input of the automata of section
4, so showing it keeps the document traceable to the formal models.

**The document is self contained.** No stylesheet, no script, no image: the
assignment asks for a visualization that can be downloaded and opened in a
browser, and a document that depends on a file it cannot find is not that.
`visualization_test.py` asserts that no `http://` or `https://` reference
appears in the output.

**The background is set explicitly.** The interface embeds the document in an
iframe, which inherits the surrounding page's background, so a document that
only set its text colour would render dark text on a dark page for a viewer
whose Streamlit theme is dark.

**An empty value prints `not stated`.** A blank where a job title should be
reads as information missing from the system rather than from the résumé.

**The document repeats what the system does not do.** A page showing a person
and a verdict reads as a recommendation unless it says otherwise, and the
assignment is explicit that ResumeLens does not rank candidates.

## 7. Tests

| File | Tests | Covers |
|---|---|---|
| `test/grammar/validator_test.py` | 25 | the model textX builds, the optional and repeated elements, section 8.1 |
| `test/grammar/rejection_test.py` | 46 | the eight rejected fixtures and one broken rule at a time, section 8.2 |
| `test/grammar/generator_test.py` | 32 | the round trip from the stage results to a profile the grammar accepts, section 8.3 |
| `test/grammar/visualization_test.py` | 30 | both documents, the empty cases, escaping |
| `test/pipeline_test.py` | 28 | the four stages end to end, section 8.4 |

Two of them are worth naming. `rejection_test.py` starts from a profile that
parses and breaks exactly one rule per test, so what the parser reports can be
attributed to that rule and nothing else. And the round trip in
`generator_test.py` guards the failure this stage exists to prevent: the
generator and the grammar drifting apart until the system produces profiles
its own language rejects.

## 8. Limitations

**The grammar does not check the vocabulary.** `Identifier` accepts any run of
letters, digits and underscores, so `skill: BANANA` parses. What it rejects is
`skill: React.js`, because the dot is not one of those characters, which is
what ties this stage to Stage 2. Checking that a symbol belongs to Γ would
duplicate `vocabulary.py` inside the grammar.

**Syntactic validity says nothing about the candidate.** The language can
represent a profile whose information is wrong, which `formalization.md`
section 7.7 records as a limitation of the whole system.