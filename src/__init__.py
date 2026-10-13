"""
ResumeLens implementation packages.

Each subpackage implements one stage of the pipeline described in
docs/architecture.md, using the formal model defined for that stage in
docs/formalization.md:

    extraction      Stage 1, regular expressions        (docs/formalization.md 2)
    normalization   Stage 2, finite-state transducer    (docs/formalization.md 3)
    classification  Stage 3, finite automata            (docs/formalization.md 4)
    grammar         Stage 4, context-free grammar       (docs/formalization.md 5)

The stages are sequential. The output of one stage is the input of the next,
and no stage takes on the responsibility of another: extraction does not decide
whether two representations are equivalent, normalization does not decide the
professional profile, and the grammar does not re-derive information that the
earlier stages already produced.
"""
