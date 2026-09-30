# Stage 3 Module Design, Qualification Pattern Recognition

## 1. Purpose

This document describes the modules that implement the profile recognition
stage, the inputs and outputs of each function, and the design decisions that
`formalization.md` section 4 leaves open. It is the module design deliverable
for Stage 3.

The formal model is not restated here. The 5-tuple, the state construction and
the transition function are defined in `formalization.md` sections 4.2 to 4.6,
and the profile patterns in section 4.7.

## 2. Position in the Pipeline

The stage receives the canonical set that Stage 2 produced and reports, for
each of the four supported profiles, whether that set satisfies the profile's
accepted pattern.

```text
normalizer.normalize(...).qualification_set
    {JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT}
            |
            v
    classifier.classify(qualifications)
            |
            v
    four independent answers, one per profile
```

## 3. Module Map

| Module | Responsibility |
|---|---|
| `src/classification/profiles.py` | The requirement slots of the four profiles. Data only. |
| `src/classification/automata.py` | Builds one DFA per profile with pyformlang, and runs a set through it. |
| `src/classification/classifier.py` | The stage API: collects the four answers and the slots each one was missing. |

## 4. `profiles.py`

### 4.1 Contract

| Name | Kind | Meaning |
|---|---|---|
| `Slot(name, symbols)` | dataclass | one requirement, satisfied by any one of `symbols` |
| `Profile(key, name, state_label, slots)` | dataclass | a profile pattern |
| `Profile.slot_count` | property | k |
| `Profile.state_count` | property | 2^k, the size of its automaton |
| `Profile.symbols` | property | every symbol that satisfies some slot |
| `Profile.slot_index_for(symbol)` | method | the index of the slot it satisfies, or `None` |
| `PROFILES` | tuple | the four profiles in the order the assignment introduces them |
| `profile_for(key)` | function | lookup by key, or `None` |
| `UNUSED_SYMBOLS` | frozenset | symbols in Γ that satisfy no slot of any profile |

### 4.2 A Profile Is Slots, Not a Checklist

A profile is not a list of required qualifications but a list of requirement
slots, each satisfied by any one of a set of symbols. The Full Stack Developer
frontend slot is satisfied by `REACT` or `ANGULAR` or `VUE`, and satisfying it
twice is no better than satisfying it once.

That distinction is what keeps the pattern a formal language question rather
than a scoring question: acceptance is a yes or no property of a set of
symbols, not a count.

### 4.3 The Four Patterns

| Profile | Slots | States | Accepting state |
|---|---|---|---|
| Full Stack Developer | 6 | 2^6 = 64 | qFS |
| Machine Learning Engineer | 7 | 2^7 = 128 | qML |
| DevOps Engineer | 5 | 2^5 = 32 | qDO |
| Data Engineer | 5 | 2^5 = 32 | qDE |

### 4.4 The Invariant Section 4.5 Depends On

Within one profile, no symbol may belong to more than one slot. Section 4.5
relies on it when defining the transition function: a symbol satisfies at most
one slot of that profile, so the next state is unambiguous. Without the
invariant the transition function would have to choose between two slots and
would stop being a function.

Across profiles the situation is the opposite and entirely intended:

| Symbol | Required by |
|---|---|
| `GIT` | Full Stack, Machine Learning Engineer, DevOps |
| `SQL` | Full Stack, Machine Learning Engineer, Data Engineer |

Each profile runs its own automaton over the same alphabet, so a shared symbol
advances one machine and self loops in another without conflict.

`PYTHON` is a core qualification of the Machine Learning Engineer profile
only. Section 4.4 notes that it belongs to Γ for that reason; for Data
Engineer it is a supporting qualification, so it appears in no Data Engineer
slot and self loops in that automaton.

### 4.5 Checks Performed at Import

- every slot symbol belongs to Γ, since Stage 2 cannot produce anything else;
- the slots of one profile are pairwise disjoint;
- no slot is empty, which would make the profile unreachable;
- the slot counts match the ones section 4.7 states;
- the set of profiles is still the four that are documented.

`UNUSED_SYMBOLS` is currently empty: every canonical symbol is a core
qualification of at least one profile, which follows from keeping Γ restricted
to exactly those. It is computed rather than asserted to be empty, because a
later change to the patterns could legitimately leave a symbol unused.

## 5. `automata.py`

### 5.1 Contract

| Function | Input | Output |
|---|---|---|
| `build_automaton(profile)` | a `Profile` | a pyformlang `DeterministicFiniteAutomaton` |
| `automaton_for(profile_or_key)` | a `Profile` or its key | the cached automaton |
| `all_subsets(profile)` | a `Profile` | the 2^k states, ordered by size |
| `next_subset(profile, subset, symbol)` | state and symbol | the next state, per section 4.5 |
| `final_subset(profile, symbols)` | a set of symbols | the subset of slots satisfied when the input ends |
| `accepts(profile, symbols)` | a set of symbols | whether the automaton accepts |
| `missing_slots(profile, symbols)` | a set of symbols | the slots left unsatisfied, in section 4.7 order |
| `state_label(profile, subset)` | a state | `"q0"`, `"q{2,4}"` or the profile's accepting label |
| `formal_definition(profile)` | a `Profile` | a dict with `Q`, `Sigma`, `delta`, `q0`, `F` |

Constant: `ALPHABET`, the 33 canonical symbols, sorted so construction is
reproducible.

### 5.2 States Are Subsets of Slots

Section 4.3 builds the state set from the subsets of slots satisfied so far,
so states here are literally frozensets of slot indices:

```text
frozenset()           q0,  nothing satisfied yet
frozenset({1, 5})     the frontend and version control slots satisfied
frozenset(range(k))   the single accepting state
```

Every subset becomes a state and every `(state, symbol)` pair gets a
transition, so the machine is the explicit 2^k automaton the document
describes rather than a lazily explored one. Building all four takes about
0.2 s and 8448 transitions in total, which is small enough to build eagerly
and to inspect.

### 5.3 Why δ Has To Be Total

Section 4.5 defines δ for every state and every symbol:

```text
δ(q_T, a) = q_{T ∪ {i}}   if a satisfies slot i and i ∉ T
δ(q_T, a) = q_T           otherwise
```

The second case is not a formality. In pyformlang, a deterministic automaton
rejects any input symbol for which no transition is defined from the current
state. Without the self loops, a résumé that mentions Git twice would be
rejected by an automaton whose six slots are all satisfied, and so would a
Full Stack candidate who also knows Docker.

The self loops are therefore what make acceptance depend on which symbols are
present rather than on how many times they appear or what else appears beside
them, which is the property section 3.8 relies on when it hands this stage an
unordered set. A partial transition function is rejected at import by counting
transitions against `|Q| × |Σ|`.

### 5.4 Running a Candidate

`final_subset` walks the pyformlang machine one symbol at a time using
`dfa(state, symbol)`, rather than reapplying the rule of section 4.5 in
Python. The two agree, and the tests check that they do over all 8448
`(state, symbol)` pairs, but taking the machine's word for it is what makes
this an automaton and not a set comparison wearing one as a costume.

Symbols outside Γ are ignored rather than raising, since Stage 2 only ever
produces canonical symbols and this can only happen when a caller builds a set
by hand.

## 6. `classifier.py`

### 6.1 Contract

| Function | Input | Output |
|---|---|---|
| `classify(qualifications)` | an iterable of canonical symbols | a `ClassificationResult` |
| `classify_for(profile, qualifications)` | a profile and a set | a single `ProfileResult` |

`ProfileResult` carries `profile`, `accepted`, `satisfied_slots`,
`missing_slots` and `final_state`. `ClassificationResult` carries
`qualifications` and `results`, and exposes `accepted`, `accepted_keys`,
`is_unclassified` and `for_profile(key)`.

`classify_for` takes acceptance from the automaton and the slots from the
state it stopped in, so the two cannot disagree about what happened.

### 6.2 What This Stage Refuses To Produce

No score, no ranking, no percentage of completion, no best match. The
assignment states that ResumeLens does not rank candidates and does not make
hiring decisions, and `literature-review.md` section 2.2 explains why that is
worth taking seriously: the documented harms of automated screening come from
systems that infer an unstated judgement of suitability from something they
measured.

The temptation is concrete. Every `ProfileResult` knows how many slots it
satisfied, so a "73% Full Stack" field is three lines of code away. That number
would be a ranking, it would be read as a measure of how good a candidate is,
and nothing in the formal model supports it. Four slots out of six is not two
thirds of a Full Stack Developer.

What the stage reports instead is which slots are unsatisfied: the same
information without the ordering, and actionable in a way a percentage is not.
Two tests enforce this rather than merely documenting it, one asserting that
`ProfileResult` has no scoring field, and one asserting that two candidates
accepted by the same profile are indistinguishable in the result even when one
has more qualifications than the other.

### 6.3 None, One, or Several

Section 4.6 makes all three outcomes ordinary:

| Outcome | When |
|---|---|
| several | the set satisfies two patterns at once, which happens when profiles share requirements |
| one | the usual case |
| none | no complete pattern was satisfied; the candidate is unclassified for the four supported profiles |

`is_unclassified` is not an error and not a pipeline failure. It is what the
model says when no accepted pattern is matched, and the missing slots explain
what was absent. The interface presents it as a result, with the slot each
profile was still waiting for.
