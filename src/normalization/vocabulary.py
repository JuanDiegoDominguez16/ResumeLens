"""
Canonical qualification vocabulary, Stage 2.

This module is the single source of truth for two of the components of the
finite-state transducer defined in docs/formalization.md section 3:

    the output alphabet   G   (section 3.4), CANONICAL_SYMBOLS here
    the input alphabet    S   (section 3.3), SIGMA here

and for the relation between them, which transducer.py turns into the
transition and output relations d and w of section 3.6.

The module defines data, not behaviour. It contains no transducer and no
automaton. Building the FST is transducer.py, running the stage is
normalizer.py, and the profile slots that consume these symbols belong to
Stage 3.


WHY A FOLDING FUNCTION IS NEEDED

Section 3.3 defines the input alphabet as complete qualification
representations rather than individual characters, so a transition consumes one
extracted representation and produces one canonical symbol.

The extraction stage, however, does not produce a fixed set of strings. Most of
its patterns are case insensitive, so "JavaScript", "javascript" and
"JAVASCRIPT" are all recognized and all returned literally, exactly as the
resume wrote them. Several patterns also accept alternative separators, so
"scikit-learn" and "scikit learn" are both recognized. Enumerating every
accepted casing as a distinct symbol of S is not possible, since a case
insensitive pattern of n letters accepts 2^n spellings.

The vocabulary therefore defines S over folded representations, and fold() is
the total function that maps any extracted string to its folded form. The
relation the transducer implements is then finite and explicit:

    fold("JavaScript")  ->  "javascript"  --FST-->  JAVASCRIPT
    fold("javascript")  ->  "javascript"  --FST-->  JAVASCRIPT
    fold("JS")          ->  "js"          --FST-->  JAVASCRIPT
    fold("React.js")    ->  "reactjs"     --FST-->  REACT
    fold("ReactJS")     ->  "reactjs"     --FST-->  REACT

Folding is an orthographic equivalence, not a semantic one. It only removes
distinctions that carry no information in this domain, letter case and the
choice of separator between the words of a technology name. Deciding that JS
and JavaScript denote the same qualification is not folding, it is the job of
the transducer, because that decision is specific to this domain and has to be
stated as part of the model.

The same effect could be obtained by composing a case folding transducer with
the normalization transducer, which is the standard construction described by
Mohri (1997) and reviewed in docs/literature-review.md section 4.1. Folding is
kept as a separate function here because it keeps the transducer of section 3
small enough to be written out as a 7-tuple, which the assignment requires.


THE THREE OUTCOMES OF A LOOKUP

A variant that the extractor produced can end in one of three states, and the
distinction matters because Stage 2 has to be able to explain what it did with
every string it received:

    normalized      the variant has a canonical symbol in G
    out of scope    the extractor recognizes it, but the controlled vocabulary
                    of section 2.3 deliberately assigns it no canonical symbol,
                    so it is dropped here and never reaches Stage 3
    unknown         the string is not a qualification variant at all

Beesley and Karttunen (2003) note that a transducer produces nothing for input
outside its lexicon, so it fails silently. Separating "deliberately dropped"
from "never seen" is what turns that silence into something the pipeline can
report.
"""

import re


# ---------------------------------------------------------------------------
# ORTHOGRAPHIC FOLDING
# ---------------------------------------------------------------------------

# Characters removed when folding a representation. These are the separators
# that technology names vary in without changing meaning:
#
#   the dot      React.js   vs  ReactJS
#   the hyphen   scikit-learn   vs  scikit learn
#   the space    Spring Boot  vs  SpringBoot,  Tensor Flow  vs  TensorFlow
#   the slash    GitLab CI/CD  vs  GitLab CICD
#
# Note which characters are NOT removed. "+" and "#" are kept, because they are
# the only thing distinguishing C++ and C# from C and from each other.

_FOLD_SEPARATORS = re.compile(r"[.\-/\s]+")


def fold(representation):
    """
    Reduce a qualification representation to its folded form.

    The folded form is lowercase with separators removed, which makes the
    function insensitive to the two variations the extraction patterns allow
    but that carry no meaning:

        fold("JavaScript")    -> "javascript"
        fold("JAVASCRIPT")    -> "javascript"
        fold("Node.js")       -> "nodejs"
        fold("NodeJS")        -> "nodejs"
        fold("scikit learn")  -> "scikitlearn"
        fold("scikit-learn")  -> "scikitlearn"
        fold("Spring Boot")   -> "springboot"
        fold("C++")           -> "c++"

    The function is total: any string has a folded form, whether or not that
    form belongs to the input alphabet.
    """

    return _FOLD_SEPARATORS.sub("", representation.strip().lower())


# ---------------------------------------------------------------------------
# THE VARIANT RELATION
# ---------------------------------------------------------------------------

# Each canonical symbol is listed with the surface representations that must
# map to it. The representations are written in their conventional spelling for
# readability; fold() is what makes the lookup accept any casing, so
# "JavaScript" below also covers "javascript" and "JAVASCRIPT".
#
# Where a pattern in the extractor accepts alternative separators, only one
# spelling needs to be listed, since both fold to the same key. Where a pattern
# accepts a genuinely different word, such as the optional plural in
# "NoSQL databases?", both forms are listed, because they fold differently.
#
# Every representation here corresponds to a pattern in
# src/extraction/extractor.py. The correspondence is checked by the tests of
# commit 6: a variant the extractor can produce but that is missing from this
# table would be silently dropped, which is exactly the failure this table
# exists to prevent.

VARIANTS = {

    # -- Programming languages ------------------------------------------
    "JAVASCRIPT": ("JavaScript", "JS"),
    "TYPESCRIPT": ("TypeScript", "TS"),
    "PYTHON": ("Python",),

    # -- Frameworks and libraries ---------------------------------------
    "REACT": ("React", "React.js", "ReactJS"),
    "ANGULAR": ("Angular",),
    "VUE": ("Vue", "Vue.js", "VueJS"),
    "NODE_JS": ("Node.js", "NodeJS"),
    "DJANGO": ("Django",),
    "SPRING_BOOT": ("Spring Boot", "SpringBoot"),

    # -- Databases ------------------------------------------------------
    # SQL and NoSQL are the two symbols the Full Stack database slot accepts;
    # PostgreSQL and MySQL are named separately because the Data Engineer
    # profile requires a concrete database engine, not the query language.
    "SQL": ("SQL",),
    "NOSQL": ("NoSQL", "NoSQL DB", "NoSQL database", "NoSQL databases"),
    "POSTGRESQL": ("PostgreSQL", "Postgres"),
    "MYSQL": ("MySQL",),

    # -- Machine learning and data technologies -------------------------
    "PANDAS": ("Pandas",),
    "NUMPY": ("NumPy",),
    "SCIKIT_LEARN": ("scikit-learn", "sklearn"),
    "TENSORFLOW": ("TensorFlow", "Tensor Flow"),
    "PYTORCH": ("PyTorch", "Py Torch"),
    "MLMD": (
        "Machine Learning Model Development",
        "Machine-Learning Model Development",
    ),
    "AIRFLOW": ("Airflow", "Apache Airflow"),
    "SPARK": ("Spark", "Apache Spark"),
    "DATABRICKS": ("Databricks",),

    # -- Cloud and infrastructure ---------------------------------------
    "DOCKER": ("Docker",),
    "AWS": ("AWS", "Amazon Web Services"),
    "AZURE": ("Azure", "Microsoft Azure"),
    "GOOGLE_CLOUD": ("Google Cloud", "Google Cloud Platform", "GCP"),
    "TERRAFORM": ("Terraform",),
    "ANSIBLE": ("Ansible",),

    # -- Tools and technologies -----------------------------------------
    "JENKINS": ("Jenkins",),
    "GITHUB_ACTIONS": ("GitHub Actions",),
    "GITLAB_CI_CD": ("GitLab CI", "GitLab CI/CD"),

    # -- APIs -----------------------------------------------------------
    # The three surface forms collapse to one symbol. The Full Stack pattern
    # has a single REST slot, so distinguishing the plural would create two
    # symbols that no slot tells apart.
    "REST_API": ("REST", "REST API", "REST APIs"),

    # -- Version control ------------------------------------------------
    "GIT": ("Git",),
}


# ---------------------------------------------------------------------------
# VARIANTS THAT ARE RECOGNIZED BUT NOT NORMALIZED
# ---------------------------------------------------------------------------

# The extractor recognizes technologies beyond the controlled vocabulary of
# section 2.3. Section 4.4 fixes the alphabet of the automata to the 33 symbols
# of G below, so these representations are given no canonical symbol and are
# dropped at the end of Stage 2.
#
# The decision is to drop rather than to extend G. Extending it would mean
# adding symbols that no profile slot accepts, so they would only ever produce
# self loops in all four automata, while making the alphabet that the design
# documents have to state considerably larger. Dropping them here keeps the
# formal model as documented and loses nothing, since a symbol that satisfies
# no slot cannot change any classification result.
#
# The bare term "machine learning" is listed here deliberately, and this is the
# one entry that changes a result rather than merely tidying the alphabet. The
# Machine Learning Engineer profile requires MLMD, model development. Mapping a
# bare mention of "ML" to MLMD would let any resume that names the field at all
# satisfy a slot meant to represent demonstrated model development, which would
# make the pattern considerably weaker than profiles.md describes. Only the full
# phrase maps to MLMD; see docs/literature-review.md section 8.

OUT_OF_SCOPE = {
    "Java": "language, not a core qualification of any supported profile",
    "C++": "language, not a core qualification of any supported profile",
    "C#": "language, not a core qualification of any supported profile",
    "Go": "language, not a core qualification of any supported profile",
    "Golang": "language, not a core qualification of any supported profile",

    "Express.js": "backend framework outside the documented Full Stack slot",
    "ExpressJS": "backend framework outside the documented Full Stack slot",
    "Flask": "backend framework outside the documented Full Stack slot",
    "FastAPI": "backend framework outside the documented Full Stack slot",

    "Matplotlib": "plotting library, supporting qualification only",
    "Keras": "deep learning library, supporting qualification only",

    "MongoDB": "supporting qualification of Data Engineer, no slot accepts it",
    "Mongo": "supporting qualification of Data Engineer, no slot accepts it",
    "Redis": "supporting qualification, no slot accepts it",

    "Kubernetes": "supporting qualification of DevOps, no slot accepts it",
    "K8s": "supporting qualification of DevOps, no slot accepts it",

    "ML": "names the field, not model development; MLMD needs the full phrase",
    "Machine Learning": "names the field, not model development",
    "Machine-Learning": "names the field, not model development",
    "Deep Learning": "names the field, no slot accepts it",
    "Deep-Learning": "names the field, no slot accepts it",
}


# ---------------------------------------------------------------------------
# CATEGORIES
# ---------------------------------------------------------------------------

# The qualification categories of docs/profiles.md section 6, restricted to the
# ones that classify a canonical symbol. Academic Qualifications, Professional
# Experience and Other Relevant Qualifications are extraction categories that
# produce no canonical symbol, so they do not appear here.
#
# These categories are presentation only. No automaton reads them: Stage 3
# groups symbols by requirement slot, which is a per profile grouping and is
# defined in src/classification/profiles.py.

CATEGORY_OF_CANONICAL = {
    "Programming Languages": (
        "JAVASCRIPT", "TYPESCRIPT", "PYTHON",
    ),
    "Frameworks and Libraries": (
        "REACT", "ANGULAR", "VUE", "NODE_JS", "DJANGO", "SPRING_BOOT",
    ),
    "Databases": (
        "SQL", "NOSQL", "POSTGRESQL", "MYSQL",
    ),
    "Machine Learning and Data Technologies": (
        "PANDAS", "NUMPY", "SCIKIT_LEARN", "TENSORFLOW", "PYTORCH", "MLMD",
        "AIRFLOW", "SPARK", "DATABRICKS",
    ),
    "Cloud and Infrastructure": (
        "DOCKER", "AWS", "AZURE", "GOOGLE_CLOUD", "TERRAFORM", "ANSIBLE",
    ),
    "Tools and Technologies": (
        "JENKINS", "GITHUB_ACTIONS", "GITLAB_CI_CD",
    ),
    "APIs and Software Development Technologies": (
        "REST_API",
    ),
    "Version Control": (
        "GIT",
    ),
}


# ---------------------------------------------------------------------------
# DERIVED ALPHABETS AND LOOKUP TABLES
# ---------------------------------------------------------------------------

def _build_relation(variants_by_canonical):
    """
    Turn the variant table into the folded lookup used by the transducer.

    Two representations that fold to the same key must agree on their canonical
    symbol, otherwise the relation would not be functional and section 3.2
    would no longer hold, since it states that each input representation
    determines a unique output. A conflict here is a bug in the table above, so
    it is raised at import time rather than resolved silently.
    """

    relation = {}

    for canonical, representations in variants_by_canonical.items():
        for representation in representations:

            key = fold(representation)
            previous = relation.get(key)

            if previous is not None and previous != canonical:
                raise ValueError(
                    f"folded representation {key!r} is claimed by both "
                    f"{previous} and {canonical}"
                )

            relation[key] = canonical

    return relation


# The input alphabet S of section 3.3, as folded representations, paired with
# the canonical symbol each one produces. This is the data behind d and w.
VARIANT_TO_CANONICAL = _build_relation(VARIANTS)

SIGMA = frozenset(VARIANT_TO_CANONICAL)

# The output alphabet G of section 3.4, and the alphabet the automata of
# section 4.4 read.
CANONICAL_SYMBOLS = frozenset(VARIANTS)

# Folded representations that are recognized by Stage 1 and deliberately
# discarded by Stage 2.
OUT_OF_SCOPE_FOLDED = frozenset(fold(name) for name in OUT_OF_SCOPE)

_OUT_OF_SCOPE_REASON = {fold(name): reason for name, reason in OUT_OF_SCOPE.items()}

_CANONICAL_CATEGORY = {
    canonical: category
    for category, canonicals in CATEGORY_OF_CANONICAL.items()
    for canonical in canonicals
}


# A representation cannot be both normalized and out of scope. The two tables
# are written by hand, so the disjointness is checked once at import time.
_CONFLICTS = SIGMA & OUT_OF_SCOPE_FOLDED

if _CONFLICTS:
    raise ValueError(
        f"representations appear in both VARIANTS and OUT_OF_SCOPE: "
        f"{sorted(_CONFLICTS)}"
    )

# Section 4.4 fixes the alphabet of the automata at the 33 symbols of the
# controlled vocabulary. Catching a drift here is cheaper than discovering it
# when an automaton receives a symbol no slot was written for.
_EXPECTED_CANONICAL_COUNT = 33

if len(CANONICAL_SYMBOLS) != _EXPECTED_CANONICAL_COUNT:
    raise ValueError(
        f"G has {len(CANONICAL_SYMBOLS)} symbols, but section 4.4 of "
        f"docs/formalization.md documents {_EXPECTED_CANONICAL_COUNT}; update "
        f"the document and this check together"
    )

if set(_CANONICAL_CATEGORY) != set(CANONICAL_SYMBOLS):
    raise ValueError(
        "every canonical symbol needs exactly one category; missing: "
        f"{sorted(CANONICAL_SYMBOLS - set(_CANONICAL_CATEGORY))}, unknown: "
        f"{sorted(set(_CANONICAL_CATEGORY) - CANONICAL_SYMBOLS)}"
    )


# ---------------------------------------------------------------------------
# LOOKUP
# ---------------------------------------------------------------------------

def canonical_for(representation):
    """
    Return the canonical symbol for an extracted representation.

    Returns None when the representation has no canonical symbol, whether
    because it is deliberately out of scope or because it is not a
    qualification at all. Use is_out_of_scope() to tell those apart.

        canonical_for("React.js")  -> "REACT"
        canonical_for("js")        -> "JAVASCRIPT"
        canonical_for("Kubernetes") -> None
        canonical_for("hello")     -> None
    """

    return VARIANT_TO_CANONICAL.get(fold(representation))


def is_out_of_scope(representation):
    """
    Return True when Stage 1 recognizes the representation but Stage 2
    deliberately assigns it no canonical symbol.
    """

    return fold(representation) in OUT_OF_SCOPE_FOLDED


def out_of_scope_reason(representation):
    """
    Return why a representation is out of scope, or None if it is not.
    """

    return _OUT_OF_SCOPE_REASON.get(fold(representation))


def category_of(canonical):
    """
    Return the qualification category of a canonical symbol, as defined in
    docs/profiles.md section 6.
    """

    return _CANONICAL_CATEGORY.get(canonical)


def representations_of(canonical):
    """
    Return the documented surface representations of a canonical symbol, in the
    order the vocabulary lists them. Used by the transducer to build one
    transition per representation, and by the diagrams to label them.
    """

    return VARIANTS[canonical]
