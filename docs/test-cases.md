# Test Case Design

## 1. What Correctness Means Here

The literature on résumé extraction reports precision and recall against
annotated corpora. That measure is not available to this project and would not
measure what this system does.

ResumeLens decides membership in a formally defined language. A candidate's
qualifications either satisfy a profile's accepted pattern or they do not, and
that is settled by the definitions in `formalization.md`, not by anyone's
opinion about the candidate. Correctness therefore means **agreement between
the implementation and the formal model**, and the test suite is organized
around that:

| Question | How it is answered |
|---|---|
| Does the code implement the documented model? | the tuples, alphabets and transition functions are compared component by component against the document |
| Does the model behave as its design claims? | the properties the design relies on, above all order independence, are tested over every permutation of a representative input |
| Does the pipeline handle real résumés? | the reference fragments from the assignment are run end to end |
| Would a regression be noticed? | the code is deliberately broken and the suite is required to fail |

The last row matters as much as the first three. A suite that passes proves
nothing on its own; what it has to do is fail when the code is wrong. Section
6 records the evidence that it does.

## 2. Test Inventory

185 tests, run with `pytest` from the repository root.

| File | Tests | Covers |
|---|---|---|
| `test/extraction/extractor_test.py` | 15 | Stage 1, names, contact, degrees, experience, the assignment example |
| `test/normalization/vocabulary_test.py` | 23 | folding, lookup, the alphabets, coverage of every extractor pattern |
| `test/normalization/transducer_test.py` | 25 | the 7-tuple, translation, restricted machines, the import guards |
| `test/normalization/normalizer_test.py` | 18 | the stage API, duplicates, discards, order independence |
| `test/classification/profiles_test.py` | 38 | the four patterns against section 4.7, the disjointness invariant |
| `test/classification/automata_test.py` | 47 | the 5-tuple, δ totality, the worked example, self loops |
| `test/classification/classifier_test.py` | 19 | the stage API, multiple acceptance, unclassified, no ranking |

`test/normalization/conftest.py` provides the fixtures that enumerate every
concrete string the extraction patterns can produce; several tests need them,
and writing the list by hand would mean it drifts as soon as a pattern is
added.

## 3. Scenarios, Stage 2

### 3.1 Folding

| Scenario | Input | Expected |
|---|---|---|
| casing is irrelevant | `JavaScript`, `javascript`, `JAVASCRIPT` | one input symbol |
| the dot is irrelevant | `React.js`, `ReactJS` | one input symbol |
| hyphen and space are interchangeable | `scikit-learn`, `scikit learn` | one input symbol |
| `+` and `#` are preserved | `C++`, `C#`, `C` | three distinct forms |
| the function is total | `""`, arbitrary prose | a folded form, not an error |

### 3.2 Coverage of the Extractor

The failure this guards against: the extractor recognizes something, Stage 2
has no rule for it, and it disappears without anyone noticing.

| Scenario | Expected |
|---|---|
| every concrete string the patterns can produce | has a canonical symbol or a documented reason for being dropped |
| every canonical symbol | is reachable from at least one representation |
| Γ | matches the 33 symbols in section 4.4 exactly |
| the variant table and the out of scope table | are disjoint |

223 concrete representations are generated from the patterns and checked. The
test that expands the patterns is itself guarded: every sample is fed back to
the extractor, which must reproduce it exactly, so a faulty expander cannot
make the coverage test vacuous.

### 3.3 The Transducer

| Scenario | Expected |
|---|---|
| the 7-tuple | `Q = {q0, qf}`, one initial state, `F = {qf}`, Σ and Γ as the vocabulary defines them |
| one transition per input symbol | `|δ| = |Σ| = 51` |
| the example of section 3.5 | `React.js` produces `REACT` |
| a restricted machine | carries only the requested symbols, keeps two states |
| an out of scope representation | produces nothing |
| the machine and the vocabulary | agree on all 223 samples |

Five guards are exercised directly: a second initial state, a state outside
`Q`, an output outside Γ, a non functional relation, and a transition with
several outputs. Each must raise.

### 3.4 The Stage API

| Scenario | Input | Expected |
|---|---|---|
| the Full Stack reference résumé | Wednesday Addams | `{GIT, JAVASCRIPT, NODE_JS, POSTGRESQL, REACT}` |
| the ML reference résumé | Mary Jane Watson | `{GIT, NUMPY, PANDAS, PYTHON, SCIKIT_LEARN, SQL, TENSORFLOW}` |
| order independence | 120 permutations of one set | one result |
| spellings that fold together | `JS`, `js`, `Js` | one trace entry |
| spellings that fold apart | `JS`, `JavaScript` | two trace entries, one symbol |
| out of scope | `Kubernetes` | reported with a reason, not silently dropped |
| unknown | arbitrary prose | reported separately from out of scope |
| blank input | `""`, whitespace | ignored, not reported |
| everything received | any mix | appears in exactly one of the three outcomes |

## 4. Scenarios, Stage 3

### 4.1 The Patterns

| Scenario | Expected |
|---|---|
| the four profiles | slots and symbols match section 4.7 entry by entry |
| slot counts | 6, 7, 5, 5 |
| state counts | 64, 128, 32, 32 |
| accepting state labels | qFS, qML, qDO, qDE |
| slots within one profile | pairwise disjoint |
| `GIT` and `SQL` | shared by three profiles each |
| `PYTHON` | a core qualification of Machine Learning Engineer only |
| every slot symbol | belongs to Γ |

### 4.2 The Automata

| Scenario | Expected |
|---|---|
| the 5-tuple | `|Q| = 2^k`, `q0 = ∅`, one accepting state, Σ the 33 symbols |
| δ is total | `|δ| = |Q| × |Σ|` for each profile |
| δ against the rule of section 4.5 | all 8448 `(state, symbol)` pairs agree |
| the worked example of section 4.5 | `q0 → q{6} → q{4,6} → q{2,4,6} → q{1,2,4,6} → q{1,2,3,4,6} → qFS` |
| order independence | 720 permutations, one answer and one final state |
| a repeated qualification | `GIT` twice does not break acceptance |
| a qualification of another profile | `DOCKER` in the Full Stack automaton is a self loop |
| a second symbol for a filled slot | `VUE` and `ANGULAR` together do not break acceptance |
| a symbol outside Γ | ignored |
| removing any one symbol | rejects |
| the empty set | rejected by every profile |

The three self loop scenarios are the ones that fail without the totality of
section 4.5, because pyformlang rejects an input symbol with no transition
from the current state.

### 4.3 The Stage API

| Scenario | Expected |
|---|---|
| any input | four answers, one per profile, in the documented order |
| a complete pattern | that profile accepted, `missing_slots` empty, state is the accepting label |
| a set satisfying two patterns | both accepted |
| an incomplete set | not accepted, the missing slot named |
| the empty set | unclassified, every slot listed as missing |
| satisfied and missing slots | partition the pattern, with no overlap |
| `ProfileResult` | has no `score`, `ranking`, `percentage`, `match` or `rating` field |
| two accepted candidates, one with extra qualifications | indistinguishable in the result |

The last two scenarios are how the no ranking decision is enforced rather than
merely documented. See section 7.

## 5. Scenarios, End to End

| Résumé | Canonical set | Result |
|---|---|---|
| Ana Torres | TypeScript, Angular, Spring Boot, NoSQL, REST API, Git | Full Stack Developer accepted |
| Sofía Ramírez | the ML and data engineering stacks | two profiles accepted |
| Wednesday Addams | see section 7 | unclassified, two slots missing |
| Mary Jane Watson | see section 7 | unclassified, one slot missing |
| Carlos Mena | empty | unclassified, everything missing |
| no technical qualifications | empty | unclassified, not an error |

The interface is exercised with `streamlit.testing.v1.AppTest`, which runs the
script rather than only importing it. The five sample résumés and six
degenerate inputs, among them whitespace only, a single word, a résumé with no
name, markup in the body and a 400 fold repetition, all render without an
exception.

## 6. Mutation Evidence

Every mutation below was applied to working code, the suite was run, and the
result recorded. A mutation that produced no failure would mean the
corresponding tests are blind.

### 6.1 Stage 2

| Mutation | Result |
|---|---|
| remove the `JS` variant from the vocabulary | 9 tests fail |
| map `ML` to `MLMD`, reversing the decision | 4 tests fail |
| stop lowercasing in `fold` | 10 tests fail |
| stop removing separators in `fold` | 7 tests fail |
| stop collapsing `REST` into `REST_API` | 3 tests fail |
| drop the reason from a discard | 1 test fails |
| stop deduplicating in the normalizer | 1 test fails |
| return a tuple instead of a frozenset | 7 tests fail |
| swallow unknown representations | 3 tests fail |
| add a 34th symbol to Γ | **import fails** |
| give the transducer two initial states | **import fails** |

### 6.2 Stage 3

| Mutation | Result |
|---|---|
| remove `TYPESCRIPT` from the Full Stack language slot | 2 tests fail |
| accept on any non empty subset | 17 tests fail |
| make `next_subset` never advance | 19 tests fail |
| return only the accepted profiles from `classify` | 5 tests fail |
| add a `score` field to `ProfileResult` | 1 test fails |
| make `missing_slots` return every slot | 2 tests fail |
| change the state label format | 2 tests fail |
| make δ partial, dropping the self loops | **import fails** |

The four import failures are a stronger outcome than a red test: the modules
refuse to load when the code stops matching `formalization.md`, so a drift
cannot reach a demo.

## 7. A Recorded Decision, the Assignment's Example Résumés

### 7.1 The Observation

The résumé fragments the assignment uses to illustrate the two reference
profiles do not satisfy the patterns this team defined in section 4.7:

| Example | Result | Slots never satisfied |
|---|---|---|
| Wednesday Addams, presented as Full Stack | not accepted | database, REST API |
| Mary Jane Watson, presented as ML Engineer | not accepted | model development |
| the sequence the assignment labels "Output: ACCEPTED" | not accepted | machine learning library, model development, database |

Two separate causes:

**A symbol that is not in the slot.** The Full Stack database slot accepts
`SQL` or `NOSQL`. Wednesday Addams's résumé says "Postgres", which normalizes
to `POSTGRESQL`, a symbol section 2.3 lists only under Data Engineer.

**A qualification the example does not state.** The Full Stack profile
description in the assignment lists REST APIs, and the Machine Learning
Engineer description lists machine-learning model development. The patterns
require them. The example fragments do not mention them.

### 7.2 The Decision

**The patterns stay as documented in section 4.7. They are not relaxed to fit
the illustrative examples.**

The assignment instructs each team to determine its own four profile patterns,
and the patterns were derived from the qualification lists the assignment
gives for each profile, not from the fragments it uses as illustrations. Those
two parts of the statement do not agree with each other. Following the
qualification lists is the more defensible reading, since they are what the
document presents as the definition of each profile.

The consequence is accepted deliberately: the system rejects two of the
assignment's own examples, and the rejection is correct with respect to the
model this project documents.

### 7.3 Why This Is Not a Defect

Both rejections are narrow and nameable. Mary Jane Watson reaches
`q{1,2,3,4,6,7}`, six of seven slots, and is missing one requirement that her
résumé does not state. A pattern that accepted her would also accept any
résumé mentioning Python and a framework, which is not what the profile
description describes.

The suite records both sides of this. One test asserts the rejection and the
slot that causes it; a second adds the missing qualification to the same
résumé and asserts that the profile is then accepted. Together they show the
pattern is reachable, and that the example résumé simply does not declare that
qualification.

The interface presents an unsatisfied pattern as a result rather than a
failure, naming the slot each automaton was still waiting for, and its sample
list includes two résumés that are accepted, one of them by two profiles at
once.

### 7.4 What Would Change the Decision

If the course confirms that the illustrative examples are normative rather
than illustrative, the change is small and local: adding `POSTGRESQL` and
`MYSQL` to the Full Stack database slot, and reconsidering the `REST_API` and
`MLMD` slots. Only `profiles.py` and section 4.7 would change; no automaton,
no test of the formal model and nothing in Stages 1, 2 or 4 depends on the
particular slot contents.

## 8. Scenarios for Stage 4, Not Yet Implemented

Stage 4 is the candidate profile language. These scenarios are written here in
advance so the implementation has a specification to work against, following
the grammar in `formalization.md` section 5.1.

### 8.1 Valid Profiles

| Scenario | Expected |
|---|---|
| a candidate with personal information, one education record, one experience record and skills | parses |
| several education records | parses, repetition is allowed |
| several experience records | parses |
| no education and no experience records | parses, both are optional |
| zero `classification` elements | parses, an unclassified candidate |
| one `classification` element | parses |
| two or more `classification` elements | parses, a candidate accepted by several profiles |

### 8.2 Rejected Profiles

| Scenario | Expected |
|---|---|
| a missing `personal` block | rejected, the block is required |
| a missing `name` or `email` field | rejected |
| an unquoted string value | rejected, lexically invalid |
| an email without `@` or without a dot | rejected |
| a non numeric value for `years` | rejected |
| an unbalanced brace | rejected, syntactically invalid |
| an unknown keyword in place of a section name | rejected |

### 8.3 Generation and Visualization

| Scenario | Expected |
|---|---|
| a pipeline result for an accepted candidate | renders a profile that the grammar validates |
| a pipeline result for an unclassified candidate | renders a profile with zero `classification` elements, which still validates |
| a candidate whose résumé states no phone number | renders without the optional field, which still validates |
| a validated profile | produces the HTML visualization |

### 8.4 End to End

| Scenario | Expected |
|---|---|
| each of the five sample résumés | traverses all four stages without error |
| an accepted candidate | the classification in the rendered profile matches what Stage 3 reported |
| an empty résumé | reaches Stage 4 and produces a valid, unclassified profile |
