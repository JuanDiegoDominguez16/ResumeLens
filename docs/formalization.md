# ResumeLens Formalization

## 1. Overview

ResumeLens uses formal language theory to model the main stages involved in
resume processing and candidate classification.

The system is organized into four formal stages:

1. Resume Information Extraction using regular expressions.
2. Qualification Normalization using finite-state transducers.
3. Qualification Pattern Recognition using finite automata.
4. Candidate Profile Language using context-free grammars and EBNF.

Each stage produces information that is used as input by the following stage.
This creates a sequential processing pipeline in which extracted resume
information is transformed, normalized, classified, and finally represented
as a structured candidate profile.

The formal models defined in this document provide the theoretical basis for
the implementation of ResumeLens using Python, `re`, `pyformlang`, and
`textX`.

The specific formalization of each stage is described in the following
sections, including the corresponding alphabets, states, transition or
production functions, and accepted patterns where applicable.

## 2. Resume Information Extraction

The first stage of ResumeLens consists of extracting relevant information from the resume using regular expressions.

The extraction process identifies textual patterns corresponding to the qualification categories defined for the system. These include contact information, programming languages, frameworks and libraries, databases, academic qualifications, professional experience, tools and technologies, and other relevant qualifications.

Regular expressions are used to recognize predefined textual representations of relevant qualifications. Since resumes may use different spellings, abbreviations, and formats, the extraction stage is designed to recognize the representations that are relevant to the supported professional profiles.

The extracted information is stored in a structured representation so that it can be processed by the qualification normalization stage.

### 2.1 Formalization

For each qualification category, ResumeLens defines regular languages whose strings correspond to textual representations that can be recognized by the extraction rules.

A regular expression is used to describe each relevant pattern. The Python `re` module is used to implement these expressions and determine whether specific substrings of the resume correspond to known qualifications.

The extraction stage can therefore be represented as:

    Resume text
        ↓
    Regular expressions
        ↓
    Recognized qualification representations
        ↓
    Structured extracted information

The extraction process does not perform canonical normalization. Different representations of the same qualification may be recognized at this stage.

For example, the representations `JS`, `Javascript`, and `JavaScript` can all be recognized as representations of the same qualification. However, the extraction stage preserves the representation found in the resume.

Canonicalization of these representations is performed in the following stage using a finite-state transducer.

For a textual pattern represented by a regular expression `R`, the corresponding language can be described as:

    L(R) = { w ∈ Σ* | R matches w }

where `Σ*` represents the set of possible strings over the resume alphabet.

All expressions used by ResumeLens are compiled with the `re.IGNORECASE` flag. This means that letter case is never a distinguishing factor for a match, `Docker`, `docker`, and `DOCKER` are all recognized by the same expression. As a consequence, alternation with the `|` operator inside a pattern is reserved exclusively for genuine differences in wording, such as an abbreviation versus a full name (`JS` versus `JavaScript`), a spacing or punctuation variant (`Tensor Flow` versus `TensorFlow`, `scikit learn` versus `scikit-learn`), or a short form versus a long form (`GCP` versus `Google Cloud Platform`). It is not used to enumerate capitalization variants, since `re.IGNORECASE` already covers those.

The following regular expressions define the textual representations recognized by the extraction stage for the technical qualifications of the four supported profiles:

| Profile | Qualification | Regular Expression | Recognized representations (case-insensitive) |
|---|---|---|---|
| Full Stack | JavaScript | `\b(?:JS\|JavaScript)\b` | `JS`, `Javascript`, `JavaScript` |
| Full Stack | TypeScript | `\b(?:TS\|TypeScript)\b` | `TS`, `Typescript`, `TypeScript` |
| Full Stack | React | `\b(?:React\.js\|ReactJS\|React)\b` | `React.js`, `ReactJS`, `React` |
| Full Stack | Angular | `\bAngular\b` | `Angular` |
| Full Stack | Vue | `\b(?:Vue\.js\|VueJS\|Vue)\b` | `Vue.js`, `VueJS`, `Vue` |
| Full Stack | Node.js | `\b(?:Node\.js\|NodeJS)\b` | `Node.js`, `NodeJS` |
| Full Stack | Django | `\bDjango\b` | `Django` |
| Full Stack | Spring Boot | `\b(?:Spring Boot\|SpringBoot)\b` | `Spring Boot`, `SpringBoot` |
| Full Stack | SQL | `\bSQL\b` | `SQL` |
| Full Stack | NoSQL | `\b(?:NoSQL database\|NoSQL DB\|NoSQL)\b` | `NoSQL database`, `NoSQL DB`, `NoSQL` |
| Full Stack | REST API | `\b(?:REST APIs\|REST API\|REST)\b` | `REST APIs`, `REST API`, `REST` |
| Full Stack | Git | `\bGit\b` | `Git` |
| Machine Learning | Python | `\bPython\b` | `Python` |
| Machine Learning | Pandas | `\bPandas\b` | `Pandas` |
| Machine Learning | NumPy | `\bNumPy\b` | `NumPy` |
| Machine Learning | Scikit-learn | `\b(?:sklearn\|scikit[- ]learn)\b` | `sklearn`, `scikit learn`, `scikit-learn` |
| Machine Learning | TensorFlow | `\b(?:Tensor Flow\|TensorFlow)\b` | `Tensor Flow`, `TensorFlow` |
| Machine Learning | PyTorch | `\b(?:Py Torch\|PyTorch)\b` | `Py Torch`, `PyTorch` |
| Machine Learning | Machine Learning Model Development | `\bMachine[- ]Learning Model Development\b` | `Machine Learning Model Development`, `Machine-Learning Model Development` |
| Machine Learning | SQL | `\bSQL\b` | `SQL` |
| Machine Learning | Git | `\bGit\b` | `Git` |
| DevOps | Docker | `\bDocker\b` | `Docker` |
| DevOps | AWS | `\b(?:AWS\|Amazon Web Services)\b` | `AWS`, `Amazon Web Services` |
| DevOps | Azure | `\b(?:Microsoft Azure\|Azure)\b` | `Microsoft Azure`, `Azure` |
| DevOps | Google Cloud | `\b(?:Google Cloud Platform\|Google Cloud\|GCP)\b` | `Google Cloud Platform`, `Google Cloud`, `GCP` |
| DevOps | Jenkins | `\bJenkins\b` | `Jenkins` |
| DevOps | GitHub Actions | `\bGitHub Actions\b` | `GitHub Actions` |
| DevOps | GitLab CI/CD | `\b(?:GitLab CI/CD\|GitLab CI)\b` | `GitLab CI/CD`, `GitLab CI` |
| DevOps | Terraform | `\bTerraform\b` | `Terraform` |
| DevOps | Ansible | `\bAnsible\b` | `Ansible` |
| DevOps | Git | `\bGit\b` | `Git` |
| Data Engineer | SQL | `\bSQL\b` | `SQL` |
| Data Engineer | Apache Airflow | `\b(?:Apache Airflow\|Airflow)\b` | `Apache Airflow`, `Airflow` |
| Data Engineer | Apache Spark | `\b(?:Apache Spark\|Spark)\b` | `Apache Spark`, `Spark` |
| Data Engineer | PostgreSQL | `\b(?:PostgreSQL\|Postgres)\b` | `PostgreSQL`, `Postgres` |
| Data Engineer | MySQL | `\bMySQL\b` | `MySQL` |
| Data Engineer | Databricks | `\bDatabricks\b` | `Databricks` |

The expressions are implemented using Python's `re` module, compiled once with `re.IGNORECASE`. For example:

    import re

    pattern = re.compile(r"\b(?:JS|JavaScript)\b", re.IGNORECASE)
    matches = pattern.findall(resume_text)

If the resume contains:

    Technical Skills:
    JS, React.js, NodeJS, Postgres, Git.

the expression for JavaScript extracts:

    JS

The extracted value remains `JS` and is not changed to `JAVASCRIPT` at this stage.

The use of word boundaries such as `\b` prevents the expression from matching the target qualification as part of a larger word. For example, `\bSQL\b` does not match the `SQL` substring inside `MySQL` or `NoSQL`, because there is no word boundary between two consecutive letters.

Alternatives that represent a more specific or longer textual form are always placed before shorter alternatives. For example, the REST API expression is written as:

    \b(?:REST APIs|REST API|REST)\b

This is necessary because Python's `re` module tries alternatives left to right and stops at the first one that matches at a given position, rather than searching for the longest possible match. Without this ordering, a resume containing `REST APIs` would only yield the shorter match `REST`. The same principle is applied to the NoSQL, Google Cloud, GitLab CI/CD, Apache Airflow, Apache Spark, and PostgreSQL expressions.

In particular, PostgreSQL and SQL are treated as different qualifications. PostgreSQL represents a specific database technology, while SQL represents the database language and qualification defined in the controlled vocabulary. Therefore, `Postgres` is normalized to `POSTGRESQL`, not to `SQL`.

The qualification `Machine Learning Model Development` is also handled as a textual representation during extraction. The canonical representation `MLMD` is not produced during extraction, it is introduced during the normalization stage.

### 2.2 Contact Information, Academic Qualifications, and Professional Experience

Unlike the technical qualifications listed in section 2.1, which are recognized from a closed set of literal alternatives, contact information, academic qualifications, and professional experience are described by more general structural patterns. These fields still define regular languages, but the languages are characterized by repeated character classes and structural rules rather than by an enumeration of specific strings.

| Category | Regular Expression | Recognized language (informal) | Example match |
|---|---|---|---|
| Email address | `[\w.+-]+@[\w-]+\.[A-Za-z]{2,}` | A local part of word characters, dots, plus or hyphen signs, an `@`, a domain, and a top-level domain of at least two letters | `wednesday.addams@email.com` |
| Phone number | `\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}` | A phone-number structure consisting of an optional country code followed by numeric groups separated by common phone-number delimiters | `+57 300 123 4567` |
| Years of experience | `\d+\+?\s+years?\s+of\s+experience` | One or more digits, an optional `+`, followed by the phrase "year(s) of experience" | `3 years of experience` |
| Academic degree | `\b(?:Bachelor(?:'s)?\|Master(?:'s)?\|Ph\.?D\.?\|B\.Sc\.\|M\.Sc\.\|Licenciatura\|Ingenier[ií]a)\b` | A predefined set of degree designations in English or Spanish | `Master's` |

As with the technical qualifications, these expressions are compiled with `re.IGNORECASE` and implemented using Python's `re` module. The extracted values (an email string, a phone string, a years-of-experience phrase, a degree designation) are stored under their corresponding category and are not modified at this stage, any further interpretation, such as converting `3 years of experience` into a numeric value, is left to later processing.

### 2.3 Controlled Vocabulary and Recognized Patterns

The extraction rules are based on a controlled vocabulary of qualifications relevant to the four professional profiles supported by ResumeLens.

The main types of information extracted are:

- Contact information
- Programming languages
- Frameworks and libraries
- Databases
- Academic qualifications
- Professional experience
- Tools and technologies
- Other relevant qualifications

The controlled vocabulary for each professional profile is:

**Full Stack Developer**

    JAVASCRIPT
    TYPESCRIPT
    REACT
    ANGULAR
    VUE
    NODE_JS
    DJANGO
    SPRING_BOOT
    SQL
    NOSQL
    REST_API
    GIT

**Machine Learning Engineer**

    PYTHON
    PANDAS
    NUMPY
    SCIKIT_LEARN
    TENSORFLOW
    PYTORCH
    MLMD
    SQL
    GIT

**DevOps Engineer**

    DOCKER
    AWS
    AZURE
    GOOGLE_CLOUD
    JENKINS
    GITHUB_ACTIONS
    GITLAB_CI_CD
    TERRAFORM
    ANSIBLE
    GIT

**Data Engineer**

    SQL
    AIRFLOW
    SPARK
    POSTGRESQL
    MYSQL
    DATABRICKS

These symbols represent the canonical vocabulary used by the subsequent normalization and classification stages. The extraction stage, however, operates on the textual representations found in the resume, not on the canonical symbols themselves.

### 2.4 Extraction Output

The result of the extraction stage is a structured collection of the information recognized in the resume.

The extracted information is organized according to qualification categories, allowing subsequent stages to process the data consistently.

For example, a resume containing the following information:

    Skills: JS, React.js, NodeJS, Postgres, Git

could produce a structured representation such as:

    Programming Languages:
        JS

    Frameworks and Libraries:
        React.js

    Databases:
        Postgres

    Tools and Technologies:
        NodeJS
        Git

The extraction process preserves the original representations:

    JS
    React.js
    NodeJS
    Postgres
    Git

rather than immediately converting them into:

    JAVASCRIPT
    REACT
    NODE_JS
    POSTGRESQL
    GIT

Contact information, academic qualifications, and professional experience are stored under their own categories in the same structure, following the patterns defined in section 2.2.

This representation is then passed to the qualification normalization stage, where equivalent representations are converted into their canonical forms.

The extraction stage therefore acts as the interface between the raw resume and the formal normalization process.

## 3. Qualification Normalization

The second stage of ResumeLens consists of normalizing the qualifications extracted from the resume.

The same qualification may appear using different abbreviations, spelling conventions, capitalization, spacing, or textual representations. The purpose of this stage is to transform equivalent representations into a common canonical representation.

Finite-state transducers are used to model these transformations. The input of the normalization stage is the structured qualification information produced by the extraction stage, while the output consists of canonical qualification symbols defined by the controlled vocabulary.

The normalization process can therefore be represented as:

    Extracted qualifications
        ↓
    Finite-State Transducer
        ↓
    Canonical qualifications
        ↓
    Qualification Pattern Recognition

For example, different textual representations can be transformed as follows:

    JS → JAVASCRIPT
    Javascript → JAVASCRIPT
    React.js → REACT
    NodeJS → NODE_JS
    Postgres → POSTGRESQL

The normalization stage does not determine the candidate's professional profile. Its purpose is to ensure that equivalent qualification representations are represented consistently before classification.

### 3.1 Finite-State Transducer

A finite-state transducer is used to represent the transformation from an input qualification representation to its canonical output representation.

For ResumeLens, the transducer receives qualification representations recognized during the extraction stage and produces the corresponding canonical symbols defined by the controlled vocabulary.

Different input representations may therefore produce the same output.

For example:

    JS ─────────────→ JAVASCRIPT
    Javascript ─────→ JAVASCRIPT
    JavaScript ─────→ JAVASCRIPT

Similarly:

    React ──────────→ REACT
    React.js ───────→ REACT
    ReactJS ────────→ REACT

The input and output representations belong to different alphabets. The input alphabet contains the qualification representations that may be extracted from resumes, while the output alphabet contains the canonical qualification symbols used by the following stages.

The transducer therefore implements a mapping between equivalent textual representations and their canonical forms.

### 3.2 7-tuple

The finite-state transducer used for qualification normalization is formally defined by the 7-tuple:

    M = (Q, Σ, Γ, δ, ω, q₀, F)

where:

- `Q` is the finite set of states.
- `Σ` is the input alphabet.
- `Γ` is the output alphabet.
- `δ` is the transition relation.
- `ω` is the output relation.
- `q₀` is the initial state.
- `F` is the set of accepting states.

The components of the tuple define how an extracted qualification is processed and transformed into its canonical representation.

For the normalization model used by ResumeLens, the transition and output relations are functional. Each supported input representation determines a unique next state and a unique canonical output.

For a transition from state `q` using an input representation `a`, the transition relation determines the next state:

    δ(q, a) = q'

The output relation determines the canonical symbol produced by that transition:

    ω(q, a) = b

where `b ∈ Γ`.

Therefore, a transition can be represented conceptually as:

    q ── a / b ──→ q'

where `a` is the input qualification representation and `b` is the corresponding canonical output.

For example:

    q₀ ── JS / JAVASCRIPT ──→ qf

This represents the transformation:

    JS → JAVASCRIPT

### 3.3 Input Alphabet

The input alphabet `Σ` contains the qualification representations that may be received from the extraction stage.

These representations correspond to the textual forms recognized by the regular expressions defined in Section 2.

Examples include:

    JS
    Javascript
    JavaScript
    React
    React.js
    ReactJS
    NodeJS
    Node.js
    Postgres
    PostgreSQL
    pandas
    sklearn
    scikit learn
    scikit-learn
    Tensor Flow
    TensorFlow
    Py Torch
    PyTorch

The input alphabet therefore contains textual qualification representations rather than canonical symbols.

The complete input alphabet is defined according to the final qualification vocabulary selected for the four supported professional profiles.

### 3.4 Output Alphabet

The output alphabet `Γ` contains the canonical qualification symbols produced by the transducer.

ResumeLens uses canonical representations in uppercase, with underscores used when a qualification consists of multiple words.

Examples include:

    JAVASCRIPT
    TYPESCRIPT
    REACT
    NODE_JS
    PANDAS
    SCIKIT_LEARN
    TENSORFLOW
    PYTORCH
    POSTGRESQL
    GOOGLE_CLOUD
    GITHUB_ACTIONS
    GITLAB_CI_CD

The output alphabet corresponds to the canonical vocabulary defined for the four professional profiles.

These canonical representations are used as the input vocabulary for the qualification pattern recognition stage.

### 3.5 States

The set of states `Q` represents the processing stages of the transducer.

Since the input alphabet contains complete qualification representations rather than individual characters, the normalization of each qualification can be modeled as a direct transition from the initial state to an accepting state.

For the normalization of an individual qualification:

    Q = {q₀, qf}

where:

- `q₀` is the initial state.
- `qf` is the accepting state.

A transition consumes one extracted qualification representation and produces its canonical representation.

For example:

    q₀ ── React.js / REACT ──→ qf

After reaching `qf`, the transformation of that qualification is complete.

The same structure can be used for other direct qualification transformations. The input and output labels of the transitions determine which qualification is being normalized.

For the complete normalization component, the transducer contains transitions for all supported qualification representations.

### 3.6 Transition and Output Relations

The transition relation `δ` determines the next state after an input representation is processed.

The output relation `ω` determines the canonical qualification produced by that transition.

Together, these relations describe the normalization process.

For example, consider the transformation:

    React.js → REACT

The transducer can represent it as:

    δ(q₀, React.js) = qf
    ω(q₀, React.js) = REACT

The corresponding transition is:

    q₀ ── React.js / REACT ──→ qf

Multiple input representations can transition to the same accepting state while producing the same canonical output.

For example:

    δ(q₀, React.js) = qf
    ω(q₀, React.js) = REACT

    δ(q₀, ReactJS) = qf
    ω(q₀, ReactJS) = REACT

    δ(q₀, React) = qf
    ω(q₀, React) = REACT

Therefore:

    React.js → REACT
    ReactJS → REACT
    React → REACT

This convergence is the main purpose of the normalization stage.

### 3.7 Example Transformations

ResumeLens must support transformations that normalize equivalent qualification representations.

The following transformations are used as part of the normalization vocabulary:

| Input representation | Canonical representation |
|---|---|
| `JS` | `JAVASCRIPT` |
| `Javascript` | `JAVASCRIPT` |
| `JavaScript` | `JAVASCRIPT` |
| `TS` | `TYPESCRIPT` |
| `Typescript` | `TYPESCRIPT` |
| `TypeScript` | `TYPESCRIPT` |
| `React` | `REACT` |
| `React.js` | `REACT` |
| `ReactJS` | `REACT` |
| `Vue` | `VUE` |
| `Vue.js` | `VUE` |
| `VueJS` | `VUE` |
| `NodeJS` | `NODE_JS` |
| `Node.js` | `NODE_JS` |
| `Spring Boot` | `SPRING_BOOT` |
| `SpringBoot` | `SPRING_BOOT` |
| `NoSQL` | `NOSQL` |
| `NoSQL DB` | `NOSQL` |
| `NoSQL database` | `NOSQL` |
| `REST` | `REST_API` |
| `REST API` | `REST_API` |
| `REST APIs` | `REST_API` |
| `Git` | `GIT` |
| `git` | `GIT` |
| `Pandas` | `PANDAS` |
| `pandas` | `PANDAS` |
| `NumPy` | `NUMPY` |
| `Numpy` | `NUMPY` |
| `numpy` | `NUMPY` |
| `sklearn` | `SCIKIT_LEARN` |
| `scikit learn` | `SCIKIT_LEARN` |
| `scikit-learn` | `SCIKIT_LEARN` |
| `Tensor Flow` | `TENSORFLOW` |
| `TensorFlow` | `TENSORFLOW` |
| `Py Torch` | `PYTORCH` |
| `PyTorch` | `PYTORCH` |
| `Machine Learning Model Development` | `MLMD` |
| `Machine-Learning Model Development` | `MLMD` |
| `AWS` | `AWS` |
| `Amazon Web Services` | `AWS` |
| `Microsoft Azure` | `AZURE` |
| `Azure` | `AZURE` |
| `GCP` | `GOOGLE_CLOUD` |
| `Google Cloud` | `GOOGLE_CLOUD` |
| `Google Cloud Platform` | `GOOGLE_CLOUD` |
| `GitHub Actions` | `GITHUB_ACTIONS` |
| `GitLab CI` | `GITLAB_CI_CD` |
| `GitLab CI/CD` | `GITLAB_CI_CD` |
| `Apache Airflow` | `AIRFLOW` |
| `Airflow` | `AIRFLOW` |
| `Apache Spark` | `SPARK` |
| `Spark` | `SPARK` |
| `Postgres` | `POSTGRESQL` |
| `PostgreSQL` | `POSTGRESQL` |
| `MySQL` | `MYSQL` |
| `Databricks` | `DATABRICKS` |

For qualifications with a single textual representation in the extraction vocabulary, the transducer applies the corresponding canonical mapping independently of letter case.

For example:

    Angular → ANGULAR
    angular → ANGULAR

    Django → DJANGO
    django → DJANGO

    SQL → SQL
    sql → SQL

    Python → PYTHON
    python → PYTHON

    Docker → DOCKER
    docker → DOCKER

    Jenkins → JENKINS
    jenkins → JENKINS

    Terraform → TERRAFORM
    terraform → TERRAFORM

    Ansible → ANSIBLE
    ansible → ANSIBLE

This behavior is consistent with the extraction stage, where all regular expressions are compiled using `re.IGNORECASE`.

Representations that are already written in canonical form are therefore mapped to themselves. For example:

    REACT → REACT
    PYTHON → PYTHON
    DOCKER → DOCKER

The normalization stage thus defines a canonical mapping for every qualification representation supported by the extraction vocabulary.

### 3.8 Normalized Qualification Set

After the transformations are applied, the resulting canonical qualifications are prepared as input for the qualification pattern recognition stage.

Earlier versions of this document proposed reordering the normalized qualifications according to a canonical order defined by the candidate's professional profile before passing them to the automaton. That approach introduces a dependency that is difficult to justify, the professional profile is precisely the result that the pattern recognition stage in Section 4 is meant to produce, so using it to decide how the input should be arranged beforehand adds an assumption the pipeline should not need.

To avoid this, ResumeLens does not rely on qualification order at all during classification. The normalization stage produces a set of canonical qualification symbols, with duplicates removed, and the finite automata defined in Section 4 are designed so that acceptance depends only on which symbols are present, never on the order in which they were extracted from the resume. Section 4.5 describes the transition mechanism that makes this possible.

For example, a resume containing:

    Git, NodeJS, JS, Postgres, React.js

produces the canonical set:

    { GIT, NODE_JS, JAVASCRIPT, POSTGRESQL, REACT }

This set may optionally be listed in a fixed, profile independent order, for example alphabetically, purely for readability when the qualifications are displayed or logged later, for instance in the candidate profile visualization of Section 5. This ordering has no effect on the classification result and is not required by the automata.

The resulting set is then provided as input to the finite automata used for qualification pattern recognition.

### 3.9 Graphical Representation and Implementation

Each finite-state transducer used by ResumeLens will have a graphical representation showing its states, transitions, input representations, and canonical output

## 4. Qualification Pattern Recognition

The third stage of ResumeLens consists of recognizing qualification patterns in order to classify a candidate into one of the four professional profiles defined for the system:

    Full Stack Developer
    Machine Learning Engineer
    DevOps Engineer
    Data Engineer

The input of this stage is the set of canonical qualification symbols produced by the normalization stage, as defined in Section 3.8.

The purpose of the finite automata is not to classify a candidate based on a single qualification. Several of the supported profiles share common technologies such as GIT, PYTHON, or SQL, so an individual qualification is never sufficient, by itself, to determine a professional profile. Instead, each automaton recognizes whether the complete combination of core qualifications required by a specific profile is present in the candidate's normalized set, independently of the order in which those qualifications were extracted from the resume.

The classification process can therefore be represented as:

    Extracted qualifications
        ↓
    Qualification Normalization
        ↓
    Canonical qualification set
        ↓
    Finite Automata (one per profile)
        ↓
    Candidate Profile Classification

Because classification does not depend on order, the normalized set can be given to each automaton exactly as produced by Section 3, without any profile specific reordering.

### 4.1 Finite Automaton

A deterministic finite automaton (DFA) is used to recognize the qualification pattern associated with each professional profile. ResumeLens defines one DFA per profile, all four sharing the same input alphabet Σ, the full canonical vocabulary defined in Section 2.3, but each with its own states, transition function, and accepting state, since each profile requires a different combination of core qualifications.

A DFA is appropriate here because, for a given state and input symbol, each automaton has a unique next state, which provides deterministic classification once the normalized qualification set is processed.

Each automaton is built around the notion of a requirement slot. A profile's core qualifications are organized into a fixed number of slots, where each slot represents one category of qualification that the profile requires, for example a frontend technology, or a cloud provider, and each slot accepts one or more equivalent symbols, for example the frontend slot accepts REACT, ANGULAR, or VUE. A candidate satisfies a profile's pattern once at least one accepted symbol has been recognized for every slot required by that profile, regardless of the order in which the symbols appear in the candidate's qualification set.

The state of each automaton therefore represents which slots have already been satisfied, not a position in a fixed sequence. This has two consequences. First, the automaton does not depend on any particular ordering of the input symbols, an accepted symbol advances the automaton whenever it is read, regardless of position. Second, symbols that are not part of the current profile's slots, technologies belonging to another profile, or supporting qualifications, leave the automaton in its current state instead of causing rejection, so their presence in the candidate's résumé never prevents an otherwise complete pattern from being recognized.

Conceptually, for a profile with slots s1 through sk:

    State represents: which of s1 ... sk have been satisfied so far
        ↓ (read a symbol that fills an unfilled slot)
    State with one additional slot satisfied
        ↓ (read a symbol that fills an unfilled slot)
        ...
    State where all slots s1 ... sk are satisfied
        ↓
    Accepting state

### 4.2 5-tuple

The finite automaton used for each profile is formally defined by the 5-tuple:

    M = (Q, Σ, δ, q₀, F)

where:

    Q is the finite set of states.
    Σ is the input alphabet.
    δ is the transition function.
    q₀ is the initial state.
    F is the set of accepting states.

For a profile whose core qualifications are organized into k slots, the set of states corresponds to the subsets of slots that have been satisfied:

    Q = { q_T : T ⊆ {1, 2, ..., k} }

where q_T denotes the state reached after the slots indexed by T have been satisfied. Since there are k slots, |Q| = 2^k, which is finite, so the automaton remains a valid DFA regardless of how many core qualifications a profile requires.

The transition function is defined as:

    δ : Q × Σ → Q

For every state q_T and every input symbol a ∈ Σ, δ(q_T, a) determines the unique next state, following the rule given in Section 4.5. Because δ is defined for every combination of state and symbol, including symbols that are not part of the profile's slots, the transition function is total, as required for a DFA.

The automaton receives only canonical qualification symbols, representations such as React.js, ReactJS, and React have already been normalized to REACT before entering this stage.

### 4.3 States

For a profile with k core requirement slots, the set of states is:

    Q = { q_T : T ⊆ {1, ..., k} }

The initial state corresponds to the empty subset, no slot has been satisfied yet:

    q₀ = q_∅

The unique accepting state corresponds to the subset containing every slot, all of the profile's core qualifications have been recognized:

    F = { q_{1,...,k} }

Every other state, q_T with T a proper subset of {1,...,k}, represents partial recognition, the candidate has satisfied the slots in T but not yet the remaining ones.

For example, for the Machine Learning Engineer profile, defined in Section 4.7 with seven slots, a candidate whose normalized set contains only PYTHON and PANDAS reaches the state where the Python slot and the data manipulation slot are satisfied, but not the accepting state, because the scikit-learn, deep learning framework, MLMD, SQL, and Git slots remain unsatisfied.

### 4.4 Alphabet

The input alphabet Σ consists of the canonical qualification symbols produced by the normalization stage. The same alphabet is shared by all four automata, and includes:

    JAVASCRIPT
    TYPESCRIPT
    REACT
    ANGULAR
    VUE
    NODE_JS
    DJANGO
    SPRING_BOOT
    SQL
    NOSQL
    REST_API
    GIT
    PYTHON
    PANDAS
    NUMPY
    SCIKIT_LEARN
    TENSORFLOW
    PYTORCH
    MLMD
    DOCKER
    AWS
    AZURE
    GOOGLE_CLOUD
    JENKINS
    GITHUB_ACTIONS
    GITLAB_CI_CD
    TERRAFORM
    ANSIBLE
    AIRFLOW
    SPARK
    POSTGRESQL
    MYSQL
    DATABRICKS

For a given profile's automaton, only a subset of Σ is associated with one of its slots, the remaining symbols are still valid input, but they are treated as irrelevant to that particular profile, as defined in Section 4.5.

Σ contains only the canonical symbols for which Sections 2 and 3 currently define an extraction rule and a normalization transformation, the controlled vocabulary established in Section 2.3. Technologies that the profile definitions list only as supporting qualifications, such as Kubernetes, Linux, Prometheus, Grafana, Apache Kafka, MongoDB, or Hadoop, are not part of Σ, no regular expression or transducer transformation has been defined for them, so they are never extracted from a résumé in the first place and never reach this stage. The single exception is PYTHON, which does belong to Σ, since it is already defined as the core qualification of the Machine Learning Engineer profile's programming language slot, even though it is also listed as a supporting qualification for Data Engineer.

### 4.5 Transition Function

Let a profile have slots s1, ..., sk, and let Ai ⊆ Σ denote the set of symbols that satisfy slot si, for example, for the Full Stack Developer frontend slot, Ai = {REACT, ANGULAR, VUE}. No symbol belongs to more than one slot within the same profile, so a given input symbol satisfies at most one slot of that profile.

For a state q_T, where T ⊆ {1,...,k} is the set of slots already satisfied, the transition function is defined as:

    δ(q_T, a) = q_{T ∪ {i}}   if a ∈ Ai for some i ∉ T
    δ(q_T, a) = q_T            otherwise

The first case covers a symbol that satisfies a slot not yet recognized, the automaton advances by adding that slot to T. The second case covers every other symbol received from Σ, a symbol that satisfies a slot already in T, a redundant qualification, for example a candidate listing both REACT and VUE, or a symbol that belongs to Σ but does not correspond to any of this profile's slots, typically a core qualification from a different profile, such as DOCKER appearing while the Full Stack Developer automaton is running, or PYTHON appearing while the DevOps Engineer automaton is running. In both cases the automaton remains in its current state, it neither advances toward acceptance nor moves away from it. Because Σ only contains the vocabulary defined in Section 2.3, as clarified in Section 4.4, qualifications that were never given extraction or normalization rules, such as Kubernetes or Apache Kafka, never occur as input symbols at all, so the transition function does not need a separate case for them.

This self loop on irrelevant or redundant symbols is what makes the automaton insensitive to order and to the presence of extra qualifications in the candidate's set, only the recognition of a new, still missing slot changes the state.

As a worked example, consider the Full Stack Developer automaton, whose slots are defined in Section 4.7, and a candidate whose normalized qualification set is processed in the following order:

    GIT, SQL, REACT, JAVASCRIPT, NODE_JS, REST_API

The automaton progresses as follows:

    q_∅              ── GIT ──────→   q_{version_control}
    q_{vc}           ── SQL ──────→   q_{vc, database}
    q_{vc,db}        ── REACT ────→   q_{vc,db,frontend}
    q_{vc,db,fe}     ── JAVASCRIPT → q_{vc,db,fe,language}
    q_{...,lang}     ── NODE_JS ──→   q_{...,backend}
    q_{...,be}       ── REST_API ─→   q_FULL   (accepting)

Because every symbol in this example fills a slot that had not yet been satisfied, the automaton reaches the accepting state after six transitions, regardless of the order in which GIT, SQL, REACT, JAVASCRIPT, NODE_JS, and REST_API were listed in the résumé. If the candidate's set additionally contained DOCKER or PYTHON, those symbols would simply trigger a self loop at whatever state the automaton was in when they were read, without preventing the Full Stack Developer pattern from being accepted.

### 4.6 Initial and Accepting States

For every profile automaton, the initial state is the one where no slot has been satisfied:

    q₀ = q_∅

The set of accepting states contains a single state, the one where every core slot of the profile has been satisfied:

    F = { q_{1,...,k} }

Because the four profiles have different numbers of slots and different slot definitions, each profile has its own automaton with its own q₀ and F, even though all four automata share the same input alphabet Σ. The four accepting states are referred to as qFS, qML, qDO, and qDE, corresponding to Full Stack Developer, Machine Learning Engineer, DevOps Engineer, and Data Engineer respectively.

A candidate's normalized qualification set is accepted by a given profile's automaton if and only if processing every symbol in the set, in any order, leaves the automaton in that profile's accepting state. If none of the four automata accept the candidate's set, the application treats the candidate as unclassified or insufficiently matched for the four supported profiles.

### 4.7 Profile Patterns

Each profile pattern is defined as a set of requirement slots, together with the canonical symbols that satisfy each slot. The same recognition mechanism, described in Sections 4.1 through 4.6, is applied to every profile, only the slot definitions differ.

#### Full Stack Developer

    Slot 1, programming language:      JAVASCRIPT or TYPESCRIPT
    Slot 2, frontend:                  REACT or ANGULAR or VUE
    Slot 3, backend:                   NODE_JS or DJANGO or SPRING_BOOT
    Slot 4, database:                  SQL or NOSQL
    Slot 5, REST API:                  REST_API
    Slot 6, version control:           GIT

Six slots are required, so |Q| = 2^6 = 64 for this automaton, with a single accepting state where all six slots are satisfied. A candidate whose normalized set contains, for example, JAVASCRIPT, REACT, NODE_JS, SQL, REST_API, and GIT satisfies all six slots and is accepted, regardless of the order in which these symbols were extracted.

#### Machine Learning Engineer

    Slot 1, programming language:      PYTHON
    Slot 2, data manipulation:         PANDAS or NUMPY
    Slot 3, machine learning library:  SCIKIT_LEARN
    Slot 4, deep learning framework:   TENSORFLOW or PYTORCH
    Slot 5, model development:         MLMD
    Slot 6, database:                  SQL
    Slot 7, version control:           GIT

Seven slots are required, so |Q| = 2^7 = 128 for this automaton. SQL alone only satisfies slot 6, it does not by itself lead to acceptance, and the same SQL symbol is shared with the Data Engineer automaton without causing any conflict, because each profile runs its own independent automaton.

#### DevOps Engineer

    Slot 1, containerization:            DOCKER
    Slot 2, cloud provider:              AWS or AZURE or GOOGLE_CLOUD
    Slot 3, CI/CD:                       JENKINS or GITHUB_ACTIONS or GITLAB_CI_CD
    Slot 4, infrastructure automation:   TERRAFORM or ANSIBLE
    Slot 5, version control:             GIT

Five slots are required, so |Q| = 2^5 = 32 for this automaton. Kubernetes, Linux, Prometheus, and Grafana are listed as supporting qualifications for this profile, but none of them are part of Σ, as clarified in Section 4.4, Sections 2 and 3 do not currently define an extraction rule or a normalization transformation for them. They are therefore never extracted from a résumé and never reach this automaton at all.

#### Data Engineer

    Slot 1, query language:              SQL
    Slot 2, orchestration:               AIRFLOW
    Slot 3, distributed processing:      SPARK
    Slot 4, database:                    POSTGRESQL or MYSQL
    Slot 5, data platform:               DATABRICKS

Five slots are required, so |Q| = 2^5 = 32 for this automaton. As with Machine Learning Engineer, SQL alone only satisfies one of the five slots, so it never causes acceptance by itself. Among the supporting qualifications listed for this profile, PYTHON is part of Σ, since it is already defined as the Machine Learning Engineer's programming language slot, so if it appears in a candidate's set it triggers a self loop in this automaton without contributing to acceptance. Apache Kafka, MongoDB, and Hadoop, by contrast, are not part of Σ, Sections 2 and 3 do not currently define extraction or normalization rules for them, so they never reach this automaton at all.

The four automata are independent of one another and are evaluated separately against the same normalized qualification set. A candidate may therefore be accepted by more than one automaton, if their qualifications happen to satisfy the core requirements of two profiles at once, or by none, if no profile's complete set of core slots is satisfied.

## 5. Candidate Profile Language

The fourth stage of ResumeLens defines a small domain-specific language for representing the structured information obtained from the previous stages of the system. The purpose of this language is to validate that a candidate profile follows a predefined syntactic structure before it is used for visualization or further processing.

The input to this stage is not the original résumé text. The information has already been extracted using regular expressions, normalized into canonical qualification symbols using the finite-state transducer, and classified using the finite automata defined in the previous sections.

Therefore, the Candidate Profile Language operates on structured information and canonical representations such as `JAVASCRIPT`, `REACT`, `NODE_JS`, `GIT`, and `FULL_STACK_DEVELOPER`.

The process can be represented as:

    Extracted and normalized information
                |
                v
        Candidate Profile Language
                |
                v
          EBNF / textX
                |
          +-----+-----+
          |           |
        Valid       Invalid
          |           |
          v           v
    Candidate      Parsing
      Model         Error
          |
          v
    Visualization

### 5.1 Context-Free Grammar and EBNF

The Candidate Profile Language is defined using an Extended Backus-Naur Form (EBNF) grammar. The grammar describes the syntactic structure that a valid candidate profile must follow.

The main non-terminal is `Candidate`, which represents the complete candidate profile. A candidate contains personal information, zero or more education records, zero or more professional experience records, a collection of skills, and zero or more classification results.

The EBNF grammar is defined as follows:

    Candidate
        = "candidate" "{"
          PersonalInformation
          { Education }
          { Experience }
          Skills
          { Classification }
          "}" ;

    PersonalInformation
        = "personal" "{"
          "name" ":" String
          "email" ":" Email
          [ "phone" ":" String ]
          "}" ;

    Education
        = "education" "{"
          "degree" ":" String
          "field" ":" String
          [ "institution" ":" String ]
          "}" ;

    Experience
        = "experience" "{"
          "position" ":" String
          "years" ":" Number
          "}" ;

    Skills
        = "skills" "{"
          { Skill }
          "}" ;

    Skill
        = "skill" ":" Identifier ;

    Classification
        = "classification" ":" Identifier ;

    String
        = '"' { Character } '"' ;

    Email
        = Identifier "@" Identifier "." Identifier ;

    Number
        = Digit { Digit } ;

    Identifier
        = Letter { Letter | Digit | "_" } ;

In this grammar, `Candidate`, `PersonalInformation`, `Education`, `Experience`, `Skills`, `Skill`, and `Classification` are non-terminal symbols that describe the structure of the language.

The terminals are the literal keywords and symbols such as `candidate`, `personal`, `education`, `experience`, `skills`, `classification`, `{`, `}`, `:`, and `"`. The lexical elements `String`, `Email`, `Number`, and `Identifier` represent values that can occur within the candidate profile.

`Classification` is repeated using the same `{ ... }` operator already used for `Education` and `Experience`, directly inside `Candidate`, without a wrapping section keyword. This is a deliberate choice to represent, without extending the grammar any further, the design decision made in Section 4.6, a candidate's normalized qualification set may be accepted by none, one, or several of the four profile automata. A candidate profile with zero `Classification` elements represents an unclassified candidate, one element represents a single accepted profile, and two or more elements represent a candidate accepted by more than one profile.

The grammar is intentionally limited to the structure required by ResumeLens. It does not perform the extraction or normalization of résumé text because those operations have already been performed in previous stages.

### 5.2 Lexical Elements

The lexical elements define the basic values that can appear inside the candidate profile.

`String` represents textual information enclosed in double quotation marks. It is used for values such as names, academic degrees, fields of study, institutions, and professional positions.

`Email` represents an email address using the structure defined by the grammar:

    Identifier "@" Identifier "." Identifier

`Number` represents a non-negative integer composed of one or more digits. It is used to represent the number of years of professional experience.

`Identifier` represents canonical symbols used by the system. In particular, qualifications received by this stage must use the canonical vocabulary defined in Section 3.

Examples of valid canonical qualification identifiers include:

    JAVASCRIPT
    TYPESCRIPT
    REACT
    NODE_JS
    PYTHON
    SCIKIT_LEARN
    POSTGRESQL
    GIT

Profile classifications reuse the same `Identifier` rule, restricted in practice to the four canonical profile names:

    FULL_STACK_DEVELOPER
    MACHINE_LEARNING_ENGINEER
    DEVOPS_ENGINEER
    DATA_ENGINEER

Each `Classification` element carries exactly one of these identifiers, and, as defined in Section 5.1, the number of `Classification` elements present in a candidate profile corresponds directly to the number of profile automata that accepted that candidate's qualification set.

The grammar therefore does not recognize original résumé representations such as `React.js`, `ReactJS`, or `Node.js` as qualification values. Those representations must have already been converted into their canonical forms during the normalization stage.

### 5.3 Candidate Profile Structure

A valid candidate profile must contain the elements defined by the `Candidate` rule in the order specified by the grammar.

The `personal` section contains the candidate's name and email address, with the phone number being optional.

The `education` section represents academic qualifications. Each education record contains a degree and field of study, while the institution is optional.

The `experience` section represents professional experience. Each experience record contains a position and the number of years of experience.

The `skills` section contains zero or more canonical qualifications. Each qualification is represented using the `skill` keyword followed by a canonical identifier.

Finally, zero or more `classification` elements represent the profile or profiles recognized by the qualification pattern recognition stage, no element present means the candidate did not satisfy any of the four profile patterns, one element means the candidate satisfies exactly one profile, and more than one element means the candidate simultaneously satisfies more than one profile pattern.

A simplified valid profile with a single classification can therefore be represented as:

    candidate {
        personal {
            name: "John Doe"
            email: "john@example.com"
        }

        education {
            degree: "Bachelor"
            field: "Computer Science"
        }

        experience {
            position: "Software Developer"
            years: 3
        }

        skills {
            skill: JAVASCRIPT
            skill: REACT
            skill: NODE_JS
            skill: SQL
            skill: REST_API
            skill: GIT
        }

        classification: FULL_STACK_DEVELOPER
    }

The qualifications in this example are already canonical. No additional normalization is performed by the grammar. Section 5.6 shows equivalent profiles with zero and with more than one classification element.

### 5.4 Repeated Elements

The grammar allows multiple education records, professional experience records, and classification results through the repetition operator `{ ... }`, applied directly inside `Candidate`.

For example, the rule:

    Candidate
        = "candidate" "{"
          PersonalInformation
          { Education }
          { Experience }
          Skills
          { Classification }
          "}" ;

allows a candidate to have zero or more `Education` elements, zero or more `Experience` elements, and zero or more `Classification` elements.

Similarly, the `Skills` rule contains:

    { Skill }

which allows the candidate to have multiple skills.

This makes the language capable of representing candidates with different numbers of academic qualifications, professional experiences, and technical skills without changing the grammar itself. The same mechanism, applied to `Classification`, is also what allows the language to represent the outcome of Section 4's classification stage without any special case in the grammar, an unclassified candidate, a candidate matching a single profile, and a candidate matching several profiles are all valid `Candidate` instances, they only differ in how many `Classification` elements they contain.

### 5.5 Validation with textX

The EBNF structure is implemented using `textX`, which provides a parser for the Candidate Profile Language and generates a model from valid input.

The validation process consists of the following steps:

    Candidate Profile
          |
          v
      textX Parser
          |
       +--+--+
       |     |
     Valid Invalid
       |     |
       v     v
    Model   Parsing Error

If the candidate profile follows the grammar, `textX` successfully parses the input and creates the corresponding model.

If the input violates the grammar, the parser rejects the profile and reports a parsing error. This allows ResumeLens to distinguish between structurally valid and invalid candidate profiles.

The textX grammar follows the same conceptual structure as the EBNF specification. The main model is the candidate profile, with nested objects representing personal information, education, experience, skills, and a list of zero or more classification results.

The validation stage does not replace the previous extraction, normalization, or classification stages. Instead, it validates the structure of the information produced by them.

### 5.6 Valid and Invalid Profiles

A valid candidate profile must follow the structure defined by the grammar and use canonical qualification identifiers.

For example, the following skill declarations are valid:

    skill: REACT
    skill: NODE_JS
    skill: JAVASCRIPT
    skill: GIT

The following declaration is not valid for the Candidate Profile Language:

    skill: React.js

because `React.js` is an original representation rather than the canonical symbol `REACT`. The normalization stage should have converted it before the candidate profile was generated.

Since `Classification` now repeats zero or more times, three additional cases are worth illustrating explicitly.

A candidate accepted by more than one profile automaton is a valid profile with more than one `classification` line, for example a candidate whose qualification set satisfies both the Full Stack Developer and the DevOps Engineer patterns defined in Section 4.7:

    candidate {
        personal {
            name: "Jane Smith"
            email: "jane@example.com"
        }

        skills {
            skill: JAVASCRIPT
            skill: REACT
            skill: NODE_JS
            skill: REST_API
            skill: SQL
            skill: GIT
            skill: DOCKER
            skill: AWS
            skill: JENKINS
            skill: TERRAFORM
        }
## 6. Relationship Between Formal Models

The formal models used in ResumeLens are connected sequentially. Each model performs a specific transformation or recognition task, and the output of one stage becomes the input of the next stage.

### 6.1 Overall Relationship

The complete relationship between the formal models is represented by the following pipeline:

Raw Resume  
↓  
Regular Expressions  
↓  
Extracted Resume Information  
↓  
Finite-State Transducer  
↓  
Normalized Qualification Set  
↓  
DFA-based Qualification Pattern Recognition  
↓  
Candidate Profile Classification  
↓  
CFG / EBNF with textX  
↓  
Validated Candidate Profile

Each stage has a specific responsibility within the system. Regular expressions extract relevant information from the raw resume, the finite-state transducer normalizes equivalent qualification representations, the finite automata recognize qualification patterns associated with the defined candidate profiles, and the context-free grammar validates the structure of the resulting candidate profile.

### 6.2 Relationship Between Regular Expressions and the Finite-State Transducer

Regular expressions are applied first to the raw resume text. Their purpose is to identify relevant textual representations of qualifications and other candidate information.

For example, the extraction stage can recognize different representations of the same qualification:

- `JS`
- `Javascript`
- `JavaScript`

These representations are extracted as qualification values and passed to the normalization stage.

The finite-state transducer maps equivalent representations to their corresponding canonical symbols:

`JS` → `JAVASCRIPT`  
`Javascript` → `JAVASCRIPT`  
`JavaScript` → `JAVASCRIPT`

Therefore, regular expressions identify the representations present in the resume, while the finite-state transducer establishes a canonical representation for them.

### 6.3 Relationship Between the Finite-State Transducer and the DFA

The output of the finite-state transducer is the input to the qualification pattern recognition stage.

The transducer produces canonical qualification symbols such as:

- `JAVASCRIPT`
- `REACT`
- `NODE_JS`
- `SQL`
- `GIT`

These symbols form the canonical qualification set used by the profile-specific DFAs.

The DFAs operate over this canonical alphabet rather than directly processing the different textual representations that may occur in resumes. This separation allows the recognition stage to work with a controlled and consistent representation of qualifications.

For example, the extracted representations:

`JS, Javascript, JavaScript, React.js, NodeJS`

can be normalized to:

`{JAVASCRIPT, REACT, NODE_JS}`

The corresponding DFA can then process these canonical symbols and update its requirement slots according to the qualification pattern defined for the selected profile.

### 6.4 Relationship Between the DFAs and Candidate Profile Classification

ResumeLens uses one DFA for each defined candidate profile:

- Full Stack Developer
- Machine Learning Engineer
- DevOps Engineer
- Data Engineer

Each DFA uses the same canonical qualification alphabet but defines different requirement slots and accepting conditions.

The input to each DFA is the normalized qualification set produced by the finite-state transducer. The DFA evaluates whether the normalized qualifications satisfy the requirement slots associated with its profile.

If the accepting state is reached, the candidate satisfies the qualification pattern represented by that DFA.

Because the four DFAs are independent, a candidate may be accepted by more than one DFA. If none of the DFAs reaches an accepting state, the candidate is considered unclassified or insufficient with respect to the defined qualification patterns.

### 6.5 Relationship Between Classification and the Candidate Profile Language

The classification results obtained from the DFA stage, together with the extracted and normalized candidate information, are used to construct the structured candidate profile.

The Candidate Profile Language defines the syntax that this structured representation must follow.

For example, the profile may contain:

- Personal information
- Education
- Professional experience
- Skills
- Classification

The DFA therefore performs qualification-pattern recognition, while the CFG/EBNF defines the syntactic structure of the resulting candidate profile.

The two models consequently address different aspects of the system:

- The DFA determines whether a set of normalized qualifications satisfies a defined profile pattern.
- The CFG defines how the candidate information must be structured.
- textX validates whether the resulting profile conforms to that grammar.

### 6.6 Complete Relationship Between the Formal Models

The complete data flow between the formal models can be summarized as follows:

| Stage | Formal Model | Input | Output | Purpose |
|---|---|---|---|---|
| 1 | Regular Expressions | Raw resume text | Extracted information | Identify relevant textual patterns |
| 2 | Finite-State Transducer | Extracted qualification representations | Canonical Qualification Set | Normalize equivalent representations |
| 3 | DFA | Canonical Qualification Set | Profile classification | Recognize qualification patterns |
| 4 | CFG / EBNF + textX | Structured candidate information | Valid or invalid profile | Validate syntactic structure |

The models are therefore complementary. No single formal model performs the complete screening process. Instead, each model performs a specific formal operation and produces information that contributes to the subsequent stages of the pipeline..

### 6.7 Separation of Responsibilities

The responsibilities of the formal models are separated as follows:

- **Regular Expressions:** extraction of relevant textual information from resumes.
- **Finite-State Transducer:** normalization of equivalent qualification representations.
- **DFA:** recognition of qualification patterns associated with candidate profiles.
- **CFG / EBNF:** definition of the syntax of the structured candidate profile.
- **textX:** implementation and validation of the Candidate Profile Language.

This separation allows the different formal components to be developed and tested independently while maintaining a defined relationship between their inputs and outputs.

The resulting architecture combines regular-expression-based extraction, finite-state transformation, finite-state recognition, and context-free syntax validation to transform an unstructured resume into a structured and formally validated candidate profile.

## 7. Design Decisions and Limitations

The formal models defined for ResumeLens involve several design decisions that establish the scope and behavior of the system. These decisions ensure that the different stages use consistent representations and that the formal models remain clearly separated according to their responsibilities.

### 7.1 Controlled Qualification Vocabulary

ResumeLens uses a controlled vocabulary of qualifications for the extraction and normalization stages. Each qualification can have several recognized textual representations, which are mapped to a single canonical symbol.

For example:

- `JS`, `Javascript`, and `JavaScript` are normalized to `JAVASCRIPT`.
- `React`, `React.js`, and `ReactJS` are normalized to `REACT`.
- `NodeJS` and `Node.js` are normalized to `NODE_JS`.

The controlled vocabulary is intentionally limited to the qualifications defined for the four selected candidate profiles. This prevents the normalization and recognition stages from assigning unsupported meanings to arbitrary technologies.

The vocabulary can be extended in future versions by adding new recognized representations and their corresponding canonical symbols.

### 7.2 Separation Between Normalization and Classification

Normalization and classification are treated as independent stages.

The finite-state transducer does not determine which candidate profile a qualification belongs to. Its only responsibility is to transform recognized qualification representations into canonical symbols.

The profile-specific DFAs operate after normalization and use the resulting canonical qualification set to evaluate their corresponding requirement patterns.

This separation prevents profile-specific rules from being embedded into the normalization process and allows the same normalized representation to be evaluated by all four profile-specific DFAs.

### 7.3 Order Independence of Qualifications

The normalized qualification set does not impose a profile-specific ordering on qualifications.

A candidate's qualifications may appear in any order in the original resume. During normalization, duplicate canonical symbols are removed, and the resulting set can be processed independently of the order in which the qualifications appeared.

The profile-specific DFAs therefore track satisfied requirement slots rather than relying on a fixed sequence of qualifications.

This design allows equivalent qualification sets to produce the same recognition result even when their original textual order differs.

### 7.4 Independent Profile Recognition

ResumeLens uses four independent DFAs:

- Full Stack Developer
- Machine Learning Engineer
- DevOps Engineer
- Data Engineer

Each DFA uses the same canonical qualification alphabet but defines its own requirement slots and accepting state.

The input to each DFA is the normalized qualification set produced by the finite-state transducer. The DFA evaluates whether the normalized qualifications satisfy the requirement slots associated with its profile.

If the accepting state is reached, the candidate satisfies the qualification pattern represented by that DFA.

Because the four DFAs are independent, a candidate may be accepted by more than one DFA. If none of the DFAs reaches an accepting state, the candidate is considered unclassified or insufficient with respect to the defined qualification patterns.

### 7.5 Scope of the Qualification Alphabet

The DFA alphabet is restricted to the canonical qualification symbols defined by the controlled vocabulary.

Supporting technologies that were not included in the controlled vocabulary are not part of the DFA alphabet. Therefore, their presence alone does not cause a candidate to satisfy a profile requirement.

For example, technologies such as Kubernetes, Linux, Prometheus, Grafana, Apache Kafka, MongoDB, and Hadoop are treated as supporting technologies and are not used as main qualification requirements in the profile recognition DFAs.

Python is an exception because it is included in the canonical qualification alphabet as a core requirement of the Machine Learning Engineer profile, even though it is also listed as a supporting technology for the Data Engineer profile.

This restriction keeps the formal recognition models deterministic and aligned with the explicitly defined profile requirements.

### 7.6 Candidate Profile Language Input

The Candidate Profile Language operates on structured information produced by the previous stages rather than directly on the raw resume.

In particular, qualifications included in the structured candidate profile use their canonical representations. For example, a normalized qualification is represented as `REACT` rather than `React.js`.

This maintains the separation between textual normalization and syntactic validation. Raw qualification variants are handled by the extraction and normalization stages, while the grammar validates the structure of the resulting candidate profile.

### 7.7 System Limitations

The current formalization has the following limitations:

- The system only recognizes qualifications included in the controlled vocabulary.
- Qualifications with representations that are not defined by the extraction patterns may not be extracted or normalized.
- Supporting technologies are not sufficient by themselves to satisfy the main qualification requirements of a profile.
- The profile recognition stage is based on predefined qualification patterns and does not perform semantic evaluation of a candidate's actual level of expertise.
- The system does not establish a ranking between candidates or between profile classifications.
- The formal models do not independently determine the quality, relevance, or truthfulness of the information contained in a resume.
- The Candidate Profile Language validates the structure of the generated profile, but syntactic validity does not imply that the candidate information is factually correct.

### 7.8 Scope and Future Extensions

The current implementation focuses on demonstrating the integration of regular expressions, finite-state transducers, finite automata, and context-free grammar within the ResumeLens pipeline.

Future extensions could expand the controlled vocabulary, introduce additional candidate profiles, add more qualification representations, and extend the candidate profile language with additional structured information.

Such extensions would preserve the same general architecture:

**Regular Expressions → Finite-State Transducer → DFA → CFG / EBNF**

The formal models can therefore be extended independently while maintaining the defined interfaces between the stages.


