# Stage 1 Module Design, Resume Information Extraction

## 1. Purpose

This document describes the module that implements the resume information
extraction stage, the inputs and outputs of each function, and the design
decisions that `formalization.md` section 2 leaves open. It is the module
design deliverable for Stage 1, and it resolves, for this stage, what
`architecture.md` section 8 records as the deferred Python object and data
structure design.

The formal model itself is not restated here. The regular languages, the
controlled vocabulary and the shape of the extraction output are defined in
`formalization.md` section 2.

## 2. Position in the Pipeline

The stage receives the raw text of a résumé and produces the textual
representations it recognized, which are the input of Stage 2.

```text
resume_text
    "Wednesday Addams\n...\nTechnical Skills: JS, React.js, NodeJS, Postgres, Git."
            |
            v
    extractor.extract_resume(resume_text)        the structured result
    extractor.qualification_strings(resume_text) the input of Stage 2
            |
            v
    ["JS", "React.js", "NodeJS", "Postgres", "Git"]
```

The stage reports what the résumé literally says. It does not decide that two
representations denote the same qualification, and it does not decide a
professional profile: `"React.js"` stays `"React.js"` and `"JS"` stays `"JS"`.
Mapping them to `REACT` and `JAVASCRIPT` is Stage 2, which is why the
extraction package imports neither `normalization` nor `classification`, as
`architecture.md` section 7 requires. Joining the stages is `src/pipeline.py`.

## 3. Module Map

| Module | Responsibility |
|---|---|
| `src/extraction/extractor.py` | The variant table, the regular expressions, the master pattern, and the stage API. |

Stage 1 is a single module, unlike Stages 2 and 3. The reason is that the stage
has one kind of output, a list of matches with their positions, and no internal
interface worth separating: the variant table is data consumed by exactly one
function in the same file, and splitting it out would add an import without
removing a dependency.

## 4. `extractor.py`

### 4.1 Contract

| Function | Input | Output |
|---|---|---|
| `extract_resume(resume_text)` | the résumé text | the structured extraction result, section 4.2 |
| `qualification_strings(resume_text)` | the résumé text | the representations for Stage 2, in order of appearance, without exact duplicates |
| `extract_qualifications(resume_text)` | the résumé text | every technical `Finding`, in order of position |
| `extract_name(resume_text)` | the résumé text | the candidate's name, or `None` |
| `extract_phones(resume_text, date_ranges)` | the text and the date ranges already found | the phone `Finding` objects that do not overlap a date range |
| `to_serializable(structure)` | any nesting of dicts, lists and `Finding` objects | the same structure with every `Finding` as a dict, ready for JSON |

Data exported: `TECH_VARIANTS`, `TECH_PATTERN`, `TECH_GROUP_CATEGORY`,
`NAME_PATTERN`, `HEADER_PATTERN`, `EMAIL_PATTERN`, `PHONE_PATTERN`,
`YEARS_EXPERIENCE_PATTERN`, `DATE_RANGE_PATTERN`, `DEGREE_PATTERN`, and the
`LEFT`, `RIGHT` and `HS` fragments the patterns are built from.

`extract_phones` takes the date ranges as a parameter rather than finding them
itself, so that the dependency between the two patterns, section 4.6, is
visible in the signature instead of hidden inside the function.

### 4.2 The Structured Result

`extract_resume` returns a dictionary with one key per type of information
listed in `formalization.md` section 2.3:

| Key | Value |
|---|---|
| `Candidate` | `{"name": str or None}` |
| `Contact Information` | `{"email": [Finding], "phone": [Finding]}` |
| `Academic Qualifications` | `[Finding]` |
| `Professional Experience` | `{"years": [Finding], "date_ranges": [Finding]}` |
| `Programming Languages` | `[Finding]` |
| `Frameworks and Libraries` | `[Finding]` |
| `Databases` | `[Finding]` |
| `Tools and Technologies` | `[Finding]` |
| `Other Qualifications` | `[Finding]` |

The five technical keys are not written out in the code: they are the keys of
`TECH_VARIANTS`, so adding a category to the table adds it to the result.

A dictionary keyed by category is used rather than one dataclass with nine
fields because the consumers want exactly that: the interface renders one table
per category, and Stage 2 wants all of the technical findings together
regardless of category. A `Finding` is a dataclass rather than a tuple because
its four fields are read by name in the interface and in the tests.

### 4.3 `Finding`

```python
@dataclass
class Finding:
    text: str        # the representation exactly as the résumé wrote it
    category: str    # the category that recognized it
    start: int       # character position where the match begins
    end: int         # character position where the match ends
```

The positions are kept because traceability is a design principle in
`architecture.md` section 7: a canonical symbol in the final candidate profile
can be traced back to the characters of the résumé that produced it. They are
also what makes the overlap rule of section 4.6 expressible.

### 4.4 One Master Pattern

The 75 technical representations of `TECH_VARIANTS` are compiled into a single
regular expression rather than into 75 separate ones. `_build_master_pattern`
gives each alternative its own named group, and `TECH_GROUP_CATEGORY` maps the
group name back to its category, so one pass with `finditer` yields every
technical match already labelled.

| Category | Variants |
|---|---|
| Programming Languages | 10 |
| Frameworks and Libraries | 26 |
| Databases | 10 |
| Tools and Technologies | 25 |
| Other Qualifications | 4 |
| Total, the alternatives of the master pattern | 75 |

Beyond doing one pass instead of 75, the master pattern is what makes the
alternatives compete with each other, which is what section 4.5 depends on.
`literature-review.md` section 3.2 reviews this construction.

### 4.5 Longest Alternative First

`_build_master_pattern` sorts the alternatives by decreasing length before
joining them with `|`. Python's `re` is leftmost, then alternation order: at a
given position the first alternative that matches wins, even when a later one
would match more text.

The ordering is therefore not cosmetic. `RIGHT` only forbids a word character
after the match, so a space is allowed, and with `REST` tried first the résumé
text `REST APIs` would be reported as `REST`:

```text
REST APIs    before REST    ->  "REST APIs"
REST         before REST APIs  ->  "REST"
```

The same applies to `NoSQL databases` against `NoSQL`, to
`Machine Learning Model Development` against `Machine Learning`, and to
`Apache Spark` against `Spark`. In `TECH_VARIANTS` the longer form is also
written first in each group, so the table reads in the order it is applied,
but the sort is what guarantees it.

### 4.6 Boundaries

Two decisions keep matches inside the text they belong to.

**Lookarounds instead of `\b`.** `LEFT` is `(?<![\w.])` and `RIGHT` is
`(?![\w])`. A word boundary would accept the positions that produce these
false matches:

```text
JS   inside React.js
SQL  inside MySQL
Git  inside GitHub
```

The dot is in the left boundary because a dot is part of technical names such
as `React.js` and `Node.js`, so a match may not begin just after one. `RIGHT`
excludes only word characters, which is what allows `C++` and `C#` to match at
all, since a trailing `+` or `#` is not a word character.

**Horizontal whitespace inside multi-word patterns.** `HS` is `[ \t]`, never
`\s`, because `\s` matches a line break: a degree pattern using `\s+` absorbs
the heading `Technical Skills` written on the next line, and a phone pattern
using `\s` matches digits split across two lines. The boundary of a résumé
field is usually the end of its line.

### 4.7 Decisions Recorded Here

**Case sensitivity is per variant, not per pattern.** Each entry of
`TECH_VARIANTS` carries a flag, and the master pattern wraps the insensitive
ones in `(?i:...)`. Representations that are also ordinary words or ordinary
abbreviations are case sensitive, so that prose does not produce
qualifications:

| Case sensitive | Why |
|---|---|
| `JS`, `TS`, `ML`, `AWS`, `GCP` | short enough to collide with ordinary abbreviations |
| `Java`, `Go`, `React`, `Vue`, `Angular`, `Flask`, `Spark`, `Airflow`, `Mongo`, `Jenkins`, `Azure` | ordinary words, surnames, or place names |
| `REST`, `REST API`, `REST APIs` | `rest` is an ordinary English word |

`JavaScript`, `TypeScript`, `PostgreSQL`, `TensorFlow`, `scikit-learn` and the
other unambiguous technical names are case insensitive, so `javascript` and
`JAVASCRIPT` are both recognized. Deciding that those spellings denote the same
qualification is not this stage's decision; folding them is Stage 2, see
`normalization.md` section 4.2.

**A phone number that overlaps a date range is discarded.** `2015-2019 2020`
has the shape of a phone number. Both patterns run, and `extract_phones` drops
any phone candidate sharing a character with a date range. Experience dates are
the more specific pattern, so they win; no other pair of patterns competes this
way.

**The name is read from the first line, not matched anywhere.** A pattern for
capitalized words would match a line of prose. `extract_name` instead takes the
first non-empty line, skipping a heading such as `Curriculum Vitae` or
`Hoja de Vida`, and requires that whole line to be between two and five
capitalized words, with optional surrounding `*` for Markdown résumés,
lowercase particles (`de`, `del`, `van`, `von`), and hyphenated surnames. If
that line is not a name, the function returns `None` rather than searching
further: a résumé whose first line is not the candidate's name gives no
evidence that the name appears anywhere else.

**A degree stops before the institution.** `_FIELD_WORD` is a capitalized word
with a negative lookahead for `Universi`, `Institut`, `College`, `School` and
`Escuela`, so `B.Sc. in Computer Science` followed by `Universidad Icesi`
yields the degree alone. `Bachelor` and `Master` additionally require a
connector (`of` or `in`), which is what keeps `Master Chef` out. Spanish
degrees (`Ingeniería de Sistemas`, `Licenciatura en Matemáticas`) are matched
by their own alternative, since résumés in this context are frequently written
in Spanish.

**Duplicates are removed only in the Stage 2 input.**
`extract_qualifications` keeps every occurrence with its position, because the
interface shows where each representation was found.
`qualification_strings` removes exact duplicates, keeping the first spelling
seen, because Stage 2 maps representations to symbols and a repetition carries
no further information. Spellings that differ are both kept: a résumé writing
`JS` and `JavaScript` sends both, and collapsing them is Stage 2's decision,
recorded in `normalization.md` section 6.4.

### 4.8 Limitations

**Plain text only.** The stage takes a string. Extracting text from PDF or
DOCX résumés is out of scope, and `app.py` accepts `.txt` uploads for that
reason.

**A closed vocabulary.** Only the 75 representations of `TECH_VARIANTS` are
recognized. A qualification nobody wrote into the table is invisible to the
whole pipeline, which is the trade-off of rule-based extraction that
`literature-review.md` section 3.1 discusses. The table is the place to extend
the system, and no other module has to change.

**No section awareness.** The patterns run over the whole document, so a
technology named in a sentence about a previous employer's stack is reported
exactly like one listed under `Technical Skills`. Stage 1 claims only that the
representation occurs in the résumé.

## 5. Tests

`test/extraction/extractor_test.py`, 17 tests. Every one of them exists because
a pattern can fail in a way that is invisible in the happy case, so the table
records what each scenario is there to prevent.

| Scenario | Guards against |
|---|---|
| `Wednesday Addams` | the name of a plain résumé is not read |
| `Ana María de la Torre` | lowercase particles break the name pattern |
| `José Rodríguez-López` | a hyphenated surname is truncated |
| a `Curriculum Vitae` heading before the name | the heading is reported as the candidate |
| `Bachelor of Science` with `Technical Skills` on the next line | a degree absorbs the next line, section 4.6 |
| `Master Chef` | an ordinary phrase is read as a degree |
| `Bachelor's degree in Computer Science` | the `'s degree` form is not recognized |
| `B.Sc. in Computer Science` then `Universidad Icesi` | the institution is absorbed into the field, section 4.7 |
| `3 years of professional experience` | the optional `of` and `professional` words regress |
| `3 years` with `of experience` on the next line | `\s` creeps back into the pattern |
| `2020-2024` | a date range form is dropped |
| `2015-2019 2020-2024` | a date range is reported as a phone number, section 4.7 |
| `+57 300 123 4567` | a separator or an international prefix is rejected |
| `300` with `123 4567` on the next line | a phone number is assembled from two fields |
| the assignment's Wednesday Addams fragment | the documented example of `formalization.md` section 2.4 stops producing the documented output, category by category |
| `john.doe@example.com`, `john+resume@example.co` | a dotted local part or the `+` form is rejected |

The extractor is additionally covered from Stage 2: the coverage test described
in `test-cases.md` section 3.2 expands every pattern into the 223 concrete
strings it can produce and feeds each one back to the extractor, which must
reproduce it exactly. A pattern that stops matching its own vocabulary fails
there even when no scenario above names it.