# ResumeLens

A résumé screening system built on formal language theory. It reads the text
of a résumé, recognizes the qualifications stated in it, normalizes the
different ways of writing the same qualification, decides which professional
profiles those qualifications satisfy, and writes the result as a sentence of
a small domain-specific language.

Integrative Task 1, Computación y Estructuras Discretas III, Universidad
Icesi, 2026-2.

**ResumeLens does not rank candidates and does not make hiring decisions.** It
reports whether the qualifications a résumé states satisfy a formally defined
pattern, and nothing else.

## Team

| Name | GitHub |
|---|---|
| Isabella Sandoval Montaño | [issa04-sand](https://github.com/issa04-sand) |
| Felipe Cuadros Muñoz | [WertyDeluxe](https://github.com/WertyDeluxe) |
| Juan Diego Domínguez Arias | [JuanDiegoDominguez16](https://github.com/JuanDiegoDominguez16) |

Course code 09834, group 3, professor Andrés Aristizabal.

## The four stages

Each stage applies one formal model, lives in its own package, and is
independent of the others. `src/pipeline.py` is the only module that joins
them.

| Stage | Formal model | Package | Design document |
|---|---|---|---|
| 1. Extraction | Regular expressions | `src/extraction/` | `docs/extraction.md` |
| 2. Normalization | Finite-state transducer | `src/normalization/` | `docs/normalization.md` |
| 3. Classification | Finite automata | `src/classification/` | `docs/classification.md` |
| 4. Candidate profile | Context-free grammar | `src/grammar/` | `docs/grammar.md` |

A résumé moves through them in order:

```text
raw text
    |  regular expressions          JS, React.js, NodeJS, Postgres, Git
    v
representations
    |  finite-state transducer      {GIT, JAVASCRIPT, NODE_JS, POSTGRESQL, REACT}
    v
canonical symbols
    |  finite automata              one answer per profile
    v
accepted profiles
    |  context-free grammar         a validated candidate profile, and its document
    v
candidate profile
```

The four supported profiles are Full Stack Developer, Machine Learning
Engineer, DevOps Engineer and Data Engineer. The last two are the ones the
team defined; their requirements are in `docs/profiles.md`.

## Running it

Python 3.12 or later. From the repository root:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The interface opens in the browser with one tab per stage, so a résumé can be
followed from the text it was written in to the profile it produced. The
sidebar offers five sample résumés, and a `.txt` file can be uploaded instead.

To run the tests:

```bash
pytest
```

348 tests. `pytest.ini` sets `pythonpath = .`, which is what lets the tests
import the `src` packages, so they have to be run from the repository root.

If `streamlit` or `pytest` are not recognized as commands, use
`python -m streamlit run app.py` and `python -m pytest`.

## Repository layout

```text
ResumeLens/
├── app.py                  the Streamlit interface
├── src/
│   ├── extraction/         Stage 1
│   ├── normalization/      Stage 2
│   ├── classification/     Stage 3
│   ├── grammar/            Stage 4, including candidate_profile.tx
│   └── pipeline.py         the four stages joined
├── test/                   one directory per stage, plus pipeline_test.py
├── examples/               candidate profiles, the valid and the rejected ones
├── docs/                   the design documents, with the diagrams
└── .streamlit/config.toml  the interface theme
```

## Documents

| File | What it contains |
|---|---|
| `docs/formalization.md` | The formal models: the regular languages, the 7-tuple of the transducer, the 5-tuple of each automaton, the EBNF grammar |
| `docs/architecture.md` | The components, the data flow between them, the design principles |
| `docs/extraction.md`, `normalization.md`, `classification.md`, `grammar.md` | One module design document per stage: contracts, decisions, limitations |
| `docs/profiles.md` | The four professional profiles and their requirement slots |
| `docs/test-cases.md` | What each test exists to prevent, stage by stage |
| `docs/literature-review.md` | The literature the design was built on |

The graphical representations are in `docs/diagrams/`: nine for the Stage 2
transducer (`fst_*`) and one transition diagram per automaton (`dfa_*`), as
`.dot` sources and rendered `.svg`.

Both sets are generated from the models themselves rather than drawn by hand,
so a change to a model changes its picture:

```bash
python -m src.normalization.transducer
python -m src.classification.automata
```

Rendering the `.svg` files needs [Graphviz](https://graphviz.org) installed.
Without it only the `.dot` sources are written; the committed `.svg` files
were rendered with it.

## Notes for whoever opens this next

**IDE.** The project was written in Visual Studio Code.
`.vscode/settings.json` is tracked on purpose: it records the interpreter and
the test configuration the team shared, so the Test Explorer finds the suite
without anyone configuring it again.

**Line endings.** The repository is written with CRLF, which is what Windows
and VS Code produce by default here.

**Fonts.** The interface asks Google Fonts for Plus Jakarta Sans and Luckiest
Guy. A machine with no connection falls back to the system fonts and the
application works exactly the same, it only looks plainer.

**The grammar file.** `src/grammar/candidate_profile.tx` is the textX grammar.
It is the implementation of the EBNF in `docs/formalization.md` section 5.1,
and the two are meant to be read together.