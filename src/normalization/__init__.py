"""
Stage 2, qualification normalization.

Formal model: finite-state transducer, docs/formalization.md section 3.

The stage receives the qualification representations produced by Stage 1 and
transforms equivalent representations into a single canonical symbol, so that
the automata of Stage 3 never see the same qualification under two names:

    JS, Javascript, JavaScript   ->  JAVASCRIPT
    React, React.js, ReactJS     ->  REACT
    Postgres, PostgreSQL         ->  POSTGRESQL

The transducer is defined by the 7-tuple M = (Q, S, G, d, w, q0, F) given in
section 3.2, and is implemented with pyformlang so that the code exposes the
same components the document states.

Per section 3.8 the stage produces a set of canonical symbols with duplicates
removed. It does not reorder the qualifications by profile, because the profile
is the result that Stage 3 is meant to produce; any ordering applied here is
for readability only and has no effect on classification.

Contract, implemented in the commits that follow:

    vocabulary.py   the output alphabet G and the variant to canonical mapping
    transducer.py   construction of the FST and access to its 7-tuple
    normalizer.py   the stage API used by the pipeline
"""
