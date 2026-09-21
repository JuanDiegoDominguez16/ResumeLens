# ResumeLens Architecture

## 1. Overview

ResumeLens is a formal-language-based resume screening system designed to extract relevant information from resumes, normalize equivalent qualifications, recognize qualification patterns, and validate structured candidate profiles.

The system is composed of four main formal stages, each mapped directly to a formal model required by the Integrative Task:

1. Resume Information Extraction, using regular expressions.
2. Qualification Normalization, using finite-state transducers.
3. Qualification Pattern Recognition, using finite automata.
4. Candidate Profile Language, using a context-free grammar (EBNF) implemented with textX.

A Streamlit based user interface provides access to the complete processing pipeline.

---

## 2. System Pipeline

The ResumeLens processing pipeline is organized as follows:

```text
Raw Resume
    |
    v
Resume Information Extraction
    |  Regular Expressions / Python re
    v
Extracted Resume Information
    |
    v
Qualification Normalization
    |  Finite-State Transducer / pyformlang
    v
Normalized Qualifications
    |
    v
Qualification Pattern Recognition
    |  Finite Automaton / pyformlang
    v
Candidate Profile Classification
    |
    v
Candidate Profile Language
    |  CFG / EBNF / textX
    v
Validated Candidate Profile
```

The Streamlit interface provides the user facing layer through which the processing pipeline is executed and its results are displayed.

---

## 3. System Components

### 3.1 Resume Information Extraction

The extraction module receives the raw textual content of a resume and identifies relevant information using regular expressions.

The module is responsible for extracting information such as:

- Contact information
- Programming languages
- Frameworks and libraries
- Databases
- Academic qualifications
- Professional experience
- Tools and technologies
- Other relevant qualifications

Input: raw resume text.

Output: extracted resume information.

The extraction stage is implemented in Python using the `re` module. For each type of information above, this module must expose the regular expression used, a short explanation of the textual pattern it recognizes, and the data structure where the matches are stored. The exact form of that data structure is a deferred decision, see section 8.

### 3.2 Qualification Normalization

The normalization module transforms equivalent representations of qualifications into canonical representations, for example:

| Input variant | Canonical form |
|---|---|
| JS | JAVASCRIPT |
| Javascript | JAVASCRIPT |
| React.js | REACT |
| ReactJS | REACT |
| NodeJS | NODE_JS |
| Node.js | NODE_JS |
| Postgres | POSTGRESQL |
| PostgreSQL | POSTGRESQL |

The normalization process is modeled using finite-state transducers and implemented using pyformlang.

Input: extracted qualifications.

Output: normalized qualifications, optionally reordered into the canonical order associated with the candidate profile.

### 3.3 Qualification Pattern Recognition

The classification module uses finite automata to recognize qualification patterns associated with the professional profiles supported by ResumeLens.

The system supports four professional profiles:

- Full Stack Developer
- Machine Learning Engineer
- DevOps Engineer
- Data Engineer

The specific qualification patterns for each profile are defined separately in the project profile specification (`profiles.md`), see section 8. The automata may be implemented as DFAs, NFAs, or ε-NFAs using pyformlang.

Input: normalized qualifications.

Output: candidate profile classification.

### 3.4 Candidate Profile Language

The candidate profile module defines a structured language for representing the information obtained from the previous stages, including:

- Personal information
- Contact information
- Professional experience
- Education
- Skills
- Normalized qualifications
- Candidate classification

The grammar is specified using EBNF and implemented using textX, and must support repeated elements such as multiple experiences, education records, and skills.

Input: candidate information, normalized qualifications, candidate classification.

Output: validated candidate profile, plus a short HTML or Markdown visualization once the profile is validated.

---

## 4. Data Flow Between Components

```text
                  Raw Resume
                      |
                      v
              +---------------+
              |   Extraction  |
              +---------------+
                      |
                      v
          Extracted Resume Information
                      |
                      v
              +---------------+
              | Normalization |
              +---------------+
                      |
                      v
             Normalized Qualifications
                      |
                      v
              +---------------+
              | Classification|
              +---------------+
                      |
                      v
             Candidate Classification
                      |
                      v
              +---------------+
              |    Grammar    |
              +---------------+
                      |
                      v
             Validated Candidate Profile
```

Each component exposes a clear input and output so the modules can be tested independently and integrated into a single processing pipeline.

---

## 5. Project Structure

```text
ResumeLens/
├── docs/
├── src/
│   ├── extraction/
│   ├── normalization/
│   ├── classification/
│   └── grammar/
├── tests/
├── app.py
├── README.md
├── requirements.txt
└── .gitignore
```

The `docs/` directory contains the project's technical documentation, `src/` contains the implementation of the formal language components, and `tests/` contains unit and integration tests. `app.py` provides the Streamlit application that connects the different components.

---

## 6. Technologies

| Component | Technology |
|---|---|
| Regular expressions | Python `re` |
| Finite-state transducers | pyformlang |
| Finite automata | pyformlang |
| Context-free grammar | EBNF / textX |
| User interface | Streamlit |
| Programming language | Python |

---

## 7. Design Principles

**Modularity.** Each formal model is implemented as an independent module with a defined input and output.

**Reusability.** The same software solution supports all four professional profiles, with profile specific information separated from the general processing logic.

**Testability.** The individual formal components and the complete processing pipeline are tested using representative inputs and expected outputs, including edge cases per profile.

**Integration.** The four formal stages operate as a single pipeline rather than as independent applications.

**Traceability.** The transformations performed by each stage are understandable and traceable from the original resume information to the final candidate profile.

---

## 8. Scope and Deferred Decisions

This document defines the architecture and data flow of ResumeLens. Two categories of decisions are deliberately left open at this stage, and will be addressed in later commits and documents:

Qualification patterns for the team defined profiles. The exact skills required to satisfy the DevOps Engineer and Data Engineer profiles are not yet fixed. These will be defined in `docs/profiles.md`, once the team confirms the scope of both profiles, following the same format used by the assignment's reference profiles (Full Stack Developer, Machine Learning Engineer).

Python object and data structure design. The concrete representation of extracted, normalized, and classified data (dictionaries, dataclasses, or another structure) is not yet fixed. This depends on the regular expressions defined for extraction and on the profile specification above, so it will be addressed after both are settled, in the module design documents under `docs/`.

Formal definitions (7-tuple transducers, 5-tuple automata, EBNF terminals and non-terminals) are also outside the scope of this architecture document and belong to `docs/formalization.md`, part of the Design deliverable.