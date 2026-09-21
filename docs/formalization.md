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

### 3.8 Normalized Qualification Sequence

After the transformations are applied, the resulting canonical qualifications are prepared for the qualification pattern recognition stage.

The normalized qualifications can be organized according to the canonical vocabulary defined for the supported professional profiles. This ensures that equivalent textual representations produce the same sequence of canonical symbols.

For example, a resume containing:

    Git, NodeJS, JS, Postgres, React.js

can be normalized to:

    GIT
    NODE_JS
    JAVASCRIPT
    POSTGRESQL
    REACT

The normalized qualifications may then be organized according to the canonical order defined for the corresponding profile:

    JAVASCRIPT
    REACT
    NODE_JS
    POSTGRESQL
    GIT

This ordering ensures that the classification process does not depend on the order in which qualifications appear in the original resume.

The resulting sequence is then provided as input to the finite automaton used for qualification pattern recognition.

### 3.9 Graphical Representation and Implementation

Each finite-state transducer used by ResumeLens will have a graphical representation showing its states, transitions, input representations, and canonical output

## 4. Qualification Pattern Recognition
   ### 4.1 Finite Automaton
   ### 4.2 5-tuple
   ### 4.3 States
   ### 4.4 Alphabet
   ### 4.5 Transition function
   ### 4.6 Initial and accepting states
   ### 4.7 Profile patterns

## 5. Candidate Profile Language
   ### 5.1 Context-Free Grammar
   ### 5.2 Terminals
   ### 5.3 Non-terminals
   ### 5.4 Production rules
   ### 5.5 EBNF representation
   ### 5.6 Valid and invalid structures

## 6. Relationship Between Formal Models

## 7. Design Decisions and Limitations