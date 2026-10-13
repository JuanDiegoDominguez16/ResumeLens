"""
Stage 3, qualification pattern recognition.

Formal model: finite automata, docs/formalization.md section 4.

The stage receives the set of canonical symbols produced by Stage 2 and decides,
for each of the four supported professional profiles, whether the candidate's
qualifications satisfy that profile's accepted pattern:

    Full Stack Developer        6 requirement slots
    Machine Learning Engineer   7 requirement slots
    DevOps Engineer             5 requirement slots
    Data Engineer               5 requirement slots

Each profile has its own automaton, defined by the 5-tuple M = (Q, S, d, q0, F)
of section 4.2. For a profile with k slots the states are the subsets of slots
already satisfied, so |Q| = 2^k, with q0 the empty subset and a single accepting
state where every slot is satisfied.

The transition function of section 4.5 is total. A symbol that satisfies a slot
not yet recognized advances the automaton; every other symbol, whether it is a
redundant qualification or a core qualification of a different profile, is a
self loop. Totality is what makes acceptance depend only on which symbols are
present and not on their order, and it is required in practice as well as in
theory: a deterministic automaton rejects any symbol for which no transition is
defined, so without the self loops a resume that mentions Git twice would be
rejected even with every slot satisfied.

The four automata are independent and are evaluated separately against the same
set, so a candidate may be accepted by none, one, or several profiles.

Contract, implemented in the commits that follow:

    profiles.py    the requirement slots of each profile
    automata.py    construction of the four DFAs
    classifier.py  the stage API, accepted profiles and unsatisfied slots
"""
