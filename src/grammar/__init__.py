"""
Stage 4, candidate profile language.

Formal model: context-free grammar, docs/formalization.md section 5.

The stage does not read the resume. Its input is what the first three stages
already produced, and its job is to state that information in a language whose
structure is defined by a grammar, then check it against that grammar:

    candidate {
        personal {
            name: "Ana Torres"
            email: ana.torres@example.com
        }

        skills {
            skill: ANGULAR
            skill: GIT
            skill: TYPESCRIPT
        }

        classification: FULL_STACK_DEVELOPER
    }

The grammar is written in EBNF in section 5.1 and implemented in
candidate_profile.tx, which textX reads. A profile that follows it produces a
model; one that violates a lexical or syntactic rule is rejected with the
position of the offending token.

Three properties of the language are worth stating here, because they are what
connect this stage to the previous ones:

    qualifications are canonical      `skill: React.js` is not in the language.
                                     Identifier admits letters, digits and the
                                     underscore, so the dot cannot be matched.
                                     Only Stage 2 output parses.

    classification repeats 0..n       Section 4.6 allows a candidate to satisfy
                                     none, one, or several profile patterns.
                                     Each accepted profile is one
                                     `classification` element, so all three
                                     outcomes are ordinary sentences of the
                                     language and none is a special case.

    nothing is re-derived            The grammar does not extract, normalize or
                                     classify. It defines how an already
                                     computed result must be written down, and
                                     rejects what is not written that way.

Contract, implemented in the commits that follow:

    generator.py      PipelineResult  ->  candidate profile source
    validator.py      source          ->  a textX model, or a rejection
    visualization.py  a textX model   ->  the HTML or Markdown view

The order is the data flow: the pipeline generates a profile, the validator
accepts or rejects it, and only a validated model is rendered. Generation and
validation are deliberately separate modules rather than one function that
returns a model, so that a profile written by hand, such as the fixtures in
examples/, goes through exactly the same validator as a generated one.
"""