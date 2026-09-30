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

import streamlit as st

from src.classification import automata
from src.extraction.extractor import TECH_VARIANTS
from src.normalization import transducer, vocabulary
from src.pipeline import run

st.set_page_config(page_title="ResumeLens", layout="wide")


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


def show_table(rows, empty_message):
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.caption(empty_message)


# ---------------------------------------------------------------------------
# INPUT
# ---------------------------------------------------------------------------

st.title("ResumeLens")
st.caption(
    "Formal language based resume screening. "
    "Regular expressions, a finite-state transducer, and finite automata, "
    "one tab per stage."
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
        st.markdown("**Candidate and contact**")
        st.write(f"Name: {result.candidate_name or 'not found'}")
        show_table(
            finding_rows(result.extraction["Contact Information"]["email"])
            + finding_rows(result.extraction["Contact Information"]["phone"]),
            "No contact information found.",
        )

        st.markdown("**Academic qualifications**")
        show_table(
            finding_rows(result.extraction["Academic Qualifications"]),
            "No academic qualifications found.",
        )

    with experience_column:
        st.markdown("**Professional experience**")
        experience = result.extraction["Professional Experience"]
        show_table(
            finding_rows(experience["years"])
            + finding_rows(experience["date_ranges"]),
            "No experience statements found.",
        )

    st.markdown("**Technical qualifications**")
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

    st.markdown("**Canonical qualification set**")
    if result.qualifications:
        st.code("{ " + ", ".join(result.qualifications) + " }", language="text")
    else:
        st.caption("Empty: no representation reached a canonical symbol.")

    mapped_column, discarded_column = st.columns(2)

    with mapped_column:
        st.markdown("**Normalized**")
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
        st.markdown("**Recognized but not normalized**")
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

            st.dataframe(
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
                hide_index=True,
                width="stretch",
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
    st.subheader("Candidate profile language")
    st.info(
        "Stage 4 is not implemented yet. Once the textX grammar exists, this "
        "tab will show the validated candidate profile and its HTML "
        "visualization, built from the results of the three stages above."
    )

    st.markdown("**What Stage 4 will receive**")
    st.json(
        {
            "candidate": result.candidate_name,
            "qualifications": list(result.qualifications),
            "classification": list(result.accepted_keys),
        }
    )
