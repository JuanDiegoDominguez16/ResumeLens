"""
ResumeLens, Streamlit interface.

Run from the repository root:

    streamlit run app.py

The interface is organized as one tab per formal stage rather than as a single
verdict, because the point of the application is to show how a resume moves
through the four formal models. A tool that only printed the accepted profile
would hide exactly what this project is about.

Two things the interface deliberately does not show:

    no score and no ranking      The assignment states that ResumeLens does
                                 not rank candidates. Every rejection is shown
                                 as the slots that were not satisfied, which
                                 is the same information without the ordering.

    no silent discards           Qualifications the extractor recognized but
                                 the vocabulary does not normalize are listed
                                 with the reason, rather than disappearing.
"""

from html import escape

import streamlit as st
import streamlit.components.v1 as components

from src.classification import automata
from src.extraction.extractor import TECH_VARIANTS
from src.grammar import visualization
from src.normalization import transducer, vocabulary
from src.pipeline import run

# The browser tab carries the mark alone, which is what the brand
# specification asks of the favicon: the plane and the lens, no wordmark, since
# at sixteen pixels the name would be a smudge. assets/resumelens-mark.svg is
# the source the .png was exported from, and is the file to edit.

st.set_page_config(
    page_title="ResumeLens",
    page_icon="assets/resumelens-mark.png",
    layout="wide",
)


# ---------------------------------------------------------------------------
# APPEARANCE
# ---------------------------------------------------------------------------

# The palette lives in .streamlit/config.toml, which is what Streamlit's own
# widgets read. The rules below cover what the theme cannot reach: the type,
# the heading of the page, the section headings and the tables.
#
# They are written against our own class names wherever possible, because a
# rule that depends on Streamlit's internal markup breaks on an upgrade. The
# three data-testid selectors are the exception: they are the documented hooks
# for the sidebar, the metrics and the tab bar, and each one only changes a
# colour or a weight, so an upgrade that moved them would cost appearance
# rather than function.
#
# Plus Jakarta Sans is fetched from Google Fonts. A machine with no connection
# falls through the stack to Segoe UI or whatever the system provides, which
# is why the stack is written out rather than left to the browser.

STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Luckiest+Guy&display=swap');

:root {
    --rl-ink: #1b2a4a;
    --rl-ink-soft: #55628a;
    --rl-violet: #6d28d9;
    --rl-violet-deep: #4c1d95;
    --rl-blue: #2563eb;
    --rl-lilac: #f4f1fb;
    --rl-lilac-line: #e2dbf6;
    --rl-font: 'Plus Jakarta Sans', 'Manrope', 'Segoe UI', system-ui,
               -apple-system, 'Helvetica Neue', Arial, sans-serif;
    --rl-display: 'Luckiest Guy', 'Titan One', 'Segoe UI Black',
                  'Arial Black', var(--rl-font);
}

html, body, .stApp, button, input, textarea, select {
    font-family: var(--rl-font);
}

.stApp { color: var(--rl-ink); }

/* The page heading */

/* The lockup: the mark on the left, the wordmark on the right.

   It sits directly on the page rather than inside a panel of its own. The
   brand specification gives the logo a neutral white background, and the page
   already is one, so drawing the panel would only outline the logo as
   something pasted onto the application instead of part of it. */

.rl-lockup {
    display: flex;
    align-items: center;
    gap: 1.05rem;
    margin: 0.3rem 0 0.8rem;
}
.rl-lockup svg { flex: 0 0 auto; }
.rl-title {
    font-family: var(--rl-display);
    font-size: 2.9rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.015em;
    line-height: 1;
    margin: 0;
    color: #000000;

    /* The extrusion. Each shadow is one step of the relief, from the lilac
       that lifts the letter off the panel to the brand violet that carries
       the depth, so the name reads as a solid object rather than as flat
       type with a drop shadow. */
    text-shadow:
        1px 1px 0 #d8cfeb,
        2px 2px 0 #c6b8e3,
        3px 3px 0 #a98fd4,
        4px 4px 0 #7b2cbf,
        5px 5px 0 #5a2290;
}
.rl-subtitle {
    font-size: 0.97rem;
    font-weight: 400;
    line-height: 1.55;
    color: var(--rl-ink-soft);
    max-width: 46rem;
    margin: 0 0 1.9rem;
}

/* Headings inside the tabs */

.stApp h3 {
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--rl-ink);
}
.rl-section {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--rl-violet-deep);
    margin: 1.4rem 0 0.5rem;
}

/* Tables */

.rl-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 0.1rem 0 0.9rem;
    font-size: 0.9rem;
    border: 1px solid var(--rl-lilac-line);
    border-radius: 8px;
    overflow: hidden;
}
.rl-table th {
    background: var(--rl-lilac);
    color: var(--rl-ink);
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    text-align: left;
    padding: 0.62rem 0.85rem;
    border-bottom: 1px solid var(--rl-lilac-line);
    white-space: nowrap;
}
.rl-table td {
    padding: 0.56rem 0.85rem;
    border-bottom: 1px solid #f0f0f5;
    color: #2d3a58;
    vertical-align: top;
}
.rl-table tbody tr:last-child td { border-bottom: none; }
.rl-table tbody tr:hover td { background: #faf8ff; }

/* The result line: the candidate's name and the number of qualifications */

[data-testid="stMetricValue"] {
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--rl-ink);
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-size: 0.72rem;
    color: var(--rl-ink-soft);
}

/* The tab bar and the sidebar */

.stTabs [data-baseweb="tab"] { font-weight: 600; }

[data-testid="stSidebar"] { border-right: 1px solid var(--rl-lilac-line); }
[data-testid="stSidebar"] h2 {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: var(--rl-ink);
}
[data-testid="stSidebar"] label { font-weight: 600; color: var(--rl-ink); }

/* Messages. The green of an accepted pattern is the one Streamlit already
   uses, with the type brought in line with the rest of the page. */

[data-testid="stAlertContainer"] { border-radius: 8px; font-size: 0.93rem; }
"""

# The mark: a paper plane and a lens fused into one shape rather than set side
# by side, so that it still reads at the size of a favicon.
#
# It is drawn inline, which means the heading needs no image file, no icon font
# and no network, and the same markup scales from the 52 pixels it occupies
# here to a poster without going soft.

LENS_ICON = """<svg width="58" height="58" viewBox="0 0 68 68" fill="none"
     xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="rlWing" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#9D4EDD"/>
      <stop offset="100%" stop-color="#0096C7"/>
    </linearGradient>
    <linearGradient id="rlBody" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#7B2CBF"/>
      <stop offset="100%" stop-color="#0077B6"/>
    </linearGradient>
  </defs>
  <path d="M60 5 L5 28 L25 36.5 Z" fill="url(#rlWing)"/>
  <path d="M60 5 L25 36.5 L32 57 Z" fill="url(#rlBody)"/>
  <circle cx="22" cy="45" r="11.5" fill="#ffffff" stroke="url(#rlBody)"
          stroke-width="3.6"/>
  <path d="M30.5 53 L41 63.5" stroke="url(#rlBody)" stroke-width="4.6"
        stroke-linecap="round"/>
</svg>"""


# ---------------------------------------------------------------------------
# SAMPLE RESUMES
# ---------------------------------------------------------------------------

# The first two are the reference fragments from the assignment. Neither
# satisfies its profile's complete pattern, which is a property of the
# patterns the team defined in docs/formalization.md section 4.7 and is
# discussed in docs/test-cases.md; the third is included so the accepted case
# can be seen as well.

SAMPLES = {
    "Wednesday Addams, assignment example": """Wednesday Addams
wednesday.addams@example.com
+57 300 123 4567
3 years of experience developing web applications.

Education:
B.Sc. in Computer Science
Universidad Icesi

Technical Skills:
JS, React.js, NodeJS, Postgres, Git.""",

    "Mary Jane Watson, assignment example": """Mary Jane Watson
mj.watson@example.com
2 years of experience developing predictive models and data-processing pipelines.

Education:
Master's degree in Data Science

Technical Skills:
Python, Pandas, NumPy, Scikit-learn, TensorFlow, SQL, Git.""",

    "Ana Torres, satisfies the Full Stack pattern": """Ana Torres
ana.torres@example.com
+57 315 987 6543
5 years of experience building web platforms.
2019 - Present

Education:
Ingeniería de Sistemas
Universidad Icesi

Technical Skills:
TypeScript, Angular, Spring Boot, NoSQL databases, REST APIs, Git, Docker.""",

    "Sofía Ramírez, satisfies two patterns at once": """Sofía Ramírez
sofia.ramirez@example.com
6 years of experience in data platforms and predictive modelling.

Technical Skills:
Python, Pandas, Scikit-learn, PyTorch, Machine Learning Model Development,
SQL, Git, Apache Airflow, Apache Spark, PostgreSQL, Databricks.""",

    "Carlos Mena, no profile satisfied": """Carlos Mena
carlos.mena@example.com
1 year of experience.

Technical Skills:
Java, C++, Redis.""",
}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def finding_rows(findings):
    """Turn a list of Finding objects into rows for a table."""

    return [
        {
            "Representation": finding.text,
            "Category": finding.category,
            "Position": f"{finding.start}-{finding.end}",
        }
        for finding in findings
    ]


def section(label):
    """
    A heading for a block inside a tab.

    Written as markup rather than as bold text so that every one of them is
    the same size, weight and colour, and so that changing them is one rule in
    STYLE rather than a search through the file.
    """

    st.markdown(
        f'<p class="rl-section">{escape(label)}</p>', unsafe_allow_html=True
    )


def show_table(rows, empty_message):
    """
    Render rows as a table, or say why there are none.

    The table is written as HTML rather than handed to st.dataframe. The
    dataframe widget draws itself on a canvas, so its header cannot be styled
    from CSS, and these tables are a handful of rows that nobody needs to sort
    or resize. Writing the markup gives the column names the weight they need
    to read as headers.

    Every value is escaped: the cells come from the resume, which is text the
    person typed or uploaded, and it reaches this function unchanged.
    """

    if not rows:
        st.caption(empty_message)
        return

    columns = list(rows[0])

    head = "".join(f"<th>{escape(str(name))}</th>" for name in columns)

    body = "".join(
        "<tr>" + "".join(
            f"<td>{escape(str(row[name]))}</td>" for name in columns
        ) + "</tr>"
        for row in rows
    )

    st.markdown(
        f'<table class="rl-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# INPUT
# ---------------------------------------------------------------------------

st.markdown(f"<style>{STYLE}</style>", unsafe_allow_html=True)

st.markdown(
    f"""<div class="rl-lockup">{LENS_ICON}
    <h1 class="rl-title">ResumeLens</h1>
</div>
<p class="rl-subtitle">Formal language based resume screening.
Regular expressions, a finite-state transducer, finite automata and a
context-free grammar, one tab per stage.</p>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Input")

    sample = st.selectbox("Sample resume", ["(write my own)"] + list(SAMPLES))

    uploaded = st.file_uploader("or upload a .txt resume", type=["txt"])

    st.divider()
    st.caption(
        "ResumeLens decides whether the qualifications stated in a resume "
        "satisfy a formally defined pattern. It does not rank candidates and "
        "does not make hiring decisions."
    )

if uploaded is not None:
    default_text = uploaded.read().decode("utf-8", errors="replace")
elif sample != "(write my own)":
    default_text = SAMPLES[sample]
else:
    default_text = ""

resume_text = st.text_area("Resume text", value=default_text, height=220)

if not resume_text.strip():
    st.info("Pick a sample resume in the sidebar, or paste one above.")
    st.stop()

result = run(resume_text)


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------

left, right = st.columns([1, 2])

with left:
    st.metric("Candidate", result.candidate_name or "not found")
    st.metric("Canonical qualifications", len(result.qualifications))

with right:
    if result.is_unclassified:
        st.warning(
            "No profile pattern was fully satisfied. This is a result, not an "
            "error: the Classification tab lists the slot each profile was "
            "still waiting for."
        )
    else:
        names = ", ".join(
            entry.name for entry in result.classification.accepted
        )
        st.success(f"Accepted profile pattern: {names}")

st.divider()

extraction_tab, normalization_tab, classification_tab, profile_tab = st.tabs([
    "1. Extraction",
    "2. Normalization",
    "3. Classification",
    "4. Candidate profile",
])


# ---------------------------------------------------------------------------
# STAGE 1
# ---------------------------------------------------------------------------

with extraction_tab:
    st.subheader("Regular expressions")
    st.caption(
        "What the resume literally says. This stage reports representations "
        "and their position; it does not decide that two of them mean the "
        "same thing."
    )

    candidate_column, experience_column = st.columns(2)

    with candidate_column:
        section("Candidate and contact")
        st.write(f"Name: {result.candidate_name or 'not found'}")
        show_table(
            finding_rows(result.extraction["Contact Information"]["email"])
            + finding_rows(result.extraction["Contact Information"]["phone"]),
            "No contact information found.",
        )

        section("Academic qualifications")
        show_table(
            finding_rows(result.extraction["Academic Qualifications"]),
            "No academic qualifications found.",
        )

    with experience_column:
        section("Professional experience")
        experience = result.extraction["Professional Experience"]
        show_table(
            finding_rows(experience["years"])
            + finding_rows(experience["date_ranges"]),
            "No experience statements found.",
        )

    section("Technical qualifications")
    technical = [
        finding
        for category in TECH_VARIANTS
        for finding in result.extraction[category]
    ]
    show_table(
        finding_rows(sorted(technical, key=lambda finding: finding.start)),
        "No technical qualifications found.",
    )


# ---------------------------------------------------------------------------
# STAGE 2
# ---------------------------------------------------------------------------

with normalization_tab:
    st.subheader("Finite-state transducer")
    st.caption(
        "Equivalent representations collapse to one canonical symbol. "
        "The result is a set: its order carries no meaning and does not "
        "affect classification."
    )

    normalization = result.normalization

    section("Canonical qualification set")
    if result.qualifications:
        st.code("{ " + ", ".join(result.qualifications) + " }", language="text")
    else:
        st.caption("Empty: no representation reached a canonical symbol.")

    mapped_column, discarded_column = st.columns(2)

    with mapped_column:
        section("Normalized")
        show_table(
            [
                {"Representation": entry.representation,
                 "Canonical symbol": entry.canonical,
                 "Category": vocabulary.category_of(entry.canonical)}
                for entry in normalization.normalized
            ],
            "Nothing was normalized.",
        )

    with discarded_column:
        section("Recognized but not normalized")
        show_table(
            [
                {"Representation": entry.representation, "Reason": entry.reason}
                for entry in normalization.discarded
            ],
            "Nothing was discarded.",
        )

    with st.expander("The transducer, M = (Q, Σ, Γ, δ, ω, q₀, F)"):
        definition = transducer.formal_definition()
        st.write(
            {
                "Q": sorted(definition["Q"]),
                "q₀": definition["q0"],
                "F": sorted(definition["F"]),
                "|Σ| input representations": len(definition["Sigma"]),
                "|Γ| canonical symbols": len(definition["Gamma"]),
                "|δ| transitions": len(definition["delta"]),
            }
        )
        st.caption(
            "Transition diagrams for every qualification category are in "
            "docs/diagrams/."
        )


# ---------------------------------------------------------------------------
# STAGE 3
# ---------------------------------------------------------------------------

with classification_tab:
    st.subheader("Finite automata")
    st.caption(
        "Each profile runs its own automaton over the same set. A candidate "
        "may be accepted by none, one, or several of them."
    )

    for entry in result.classification.results:

        profile = entry.profile
        header = f"{entry.name} · {len(entry.satisfied_slots)} of " \
                 f"{len(profile.slots)} slots · state {entry.final_state}"

        with st.expander(header, expanded=entry.accepted):

            if entry.accepted:
                st.success(
                    f"Accepted. The automaton reached {entry.final_state}, "
                    "its accepting state."
                )
            else:
                missing = ", ".join(slot.name for slot in entry.missing_slots)
                st.info(f"Not accepted. Slots never satisfied: {missing}.")

            show_table(
                [
                    {
                        "Slot": f"{index + 1}. {slot.name}",
                        "Satisfied by any of": " or ".join(sorted(slot.symbols)),
                        "Status": (
                            "satisfied" if slot in entry.satisfied_slots
                            else "missing"
                        ),
                    }
                    for index, slot in enumerate(profile.slots)
                ],
                "This profile defines no slots.",
            )

            st.caption(
                f"M = (Q, Σ, δ, q₀, F) with |Q| = 2^{profile.slot_count} = "
                f"{profile.state_count} states, |Σ| = {len(automata.ALPHABET)}, "
                f"q₀ = q0, F = {{{profile.state_label}}}."
            )

    with st.expander("Why extra qualifications never hurt"):
        st.markdown(
            "The transition function of section 4.5 is total: a symbol that "
            "satisfies a slot already filled, or that belongs to another "
            "profile entirely, is a self loop. That is what makes acceptance "
            "depend only on which symbols are present, and not on their "
            "order or on how many times they appear."
        )


# ---------------------------------------------------------------------------
# STAGE 4
# ---------------------------------------------------------------------------

with profile_tab:
    st.subheader("Context-free grammar")
    st.caption(
        "The results of the three stages above, written as a sentence of the "
        "candidate profile language, parsed by textX, and rendered."
    )

    if not result.has_profile:

        st.warning(result.profile_error.capitalize() + ".")

        st.markdown(
            "This is a result rather than a failure. The `Email` rule of "
            "section 5.2 requires an `@` and a dot, so the language has no way "
            "to write \"no email address\", and the generator reports it "
            "instead of inventing one. The three stages above ran normally "
            "and their results are the ones shown in the other tabs."
        )

    else:

        source_column, document_column = st.columns(2)

        with source_column:
            section("The profile")
            st.code(result.profile_source, language="text")

            st.success(
                "Accepted by the grammar: textX parsed this text and built "
                "the model the document on the right is rendered from."
            )

            st.download_button(
                "Download the profile",
                data=result.profile_source,
                file_name="candidate.candidate",
                mime="text/plain",
            )

        with document_column:
            section("The visualization")
            components.html(result.visualization, height=560, scrolling=True)

            st.download_button(
                "Download the HTML document",
                data=result.visualization,
                file_name="candidate.html",
                mime="text/html",
            )

        with st.expander("The Markdown rendering of the same profile"):
            st.code(
                visualization.to_markdown(result.candidate_profile),
                language="markdown",
            )

    with st.expander("What this stage refuses to represent"):
        st.markdown(
            "A qualification reaches this stage as a canonical symbol or not "
            "at all: `Identifier` admits letters, digits and the underscore, "
            "so `skill: React.js` is not a sentence of the language and the "
            "parser rejects it. A profile carrying a representation that "
            "Stage 2 should have normalized is therefore caught by the "
            "lexical rule itself, with no check written in Python.\n\n"
            "The profiles in `examples/invalid/` are the eight ways a profile "
            "can be rejected, one rule each."
        )