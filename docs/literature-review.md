# ResumeLens Literature Review

## 1. Purpose and Scope

This document reviews the work related to the problem addressed by ResumeLens:
deciding whether the qualifications stated in a résumé satisfy a formally
defined pattern for a professional profile.

The review has three goals. First, to establish which parts of the problem are
already solved in the literature, so the project does not reimplement them
without reason. Second, to justify the formal models chosen for each stage of
the pipeline, since the assignment requires regular expressions, finite-state
transducers, finite automata, and context-free grammars, and each of those
choices should be defensible rather than imposed. Third, to identify the
limitations reported by other authors, so the scope declared in
`formalization.md` Section 7 is an informed decision instead of an omission.

The review is organized to follow the four stages of the system. Sections 3 to
6 correspond to extraction, normalization, classification, and the candidate
profile language. Section 7 covers the libraries used. Section 8 states how
ResumeLens positions itself with respect to the reviewed work.

## 2. Problem Context

### 2.1 Résumé Screening as an Information Extraction Problem

Résumé screening is usually studied as a case of information extraction from
semi-structured documents. Résumés share a small set of recurring information
types, education, experience, skills, and contact data, but the surface form of
that information varies widely between candidates. Yu, Guan, and Zhou (2005)
addressed this with a cascaded hybrid model: a first pass segments the résumé
into blocks corresponding to general information types, and a second pass
extracts detailed fields inside each block. Their central observation is
relevant here, namely that different information types in a résumé have
different structural regularity, so a single uniform technique performs worse
than a staged approach in which each stage handles what it models well.

ResumeLens follows the same staged logic, although with a different motivation.
The stages of this project are separated by formal model rather than by document
region, and the models are fixed by the assignment. Even so, the result is
comparable: extraction is not asked to decide equivalence, and normalization is
not asked to decide the profile. This separation of responsibilities is stated
in `formalization.md` Section 6.7.

More recent work on résumé parsing relies on statistical sequence labeling and,
increasingly, on transformer-based entity extraction. Those approaches obtain
better coverage on unseen surface forms, but they do not produce the artifact
this project requires, which is an explicit, inspectable formal model of the
accepted language. A classifier that scores a résumé cannot be presented as a
5-tuple, and its decision cannot be traced to a transition. That mismatch, not
a claim of superior accuracy, is what justifies the rule-based approach here.

### 2.2 Automated Screening and the Decision Not to Rank Candidates

The literature on automated hiring documents a consistent risk. Raghavan,
Barocas, Kleinberg, and Levy (2020) surveyed vendors of algorithmic hiring tools
and found that claims about bias mitigation were frequently vague and rarely
verifiable, and that the assessments being automated often had no established
validity. The most widely cited practical failure is Amazon's internal recruiting
model, which was abandoned after it was found to penalize résumés containing
indicators associated with women (Dastin, 2018); the system had learned the
historical composition of the applicant pool rather than any property related to
competence.

Both cases share a mechanism. The harm appears when a system infers an unstated
judgment, a ranking or a prediction of suitability, from correlations in
historical data. This is precisely what the assignment excludes when it states
that ResumeLens does not rank candidates and does not make hiring decisions.

This review treats that restriction as a design constraint with a technical
consequence, not as a disclaimer. The system decides membership in a formal
language: a normalized qualification set either reaches an accepting state or it
does not, and when it does not, the unsatisfied slots can be named exactly. No
weight is assigned to any qualification, no score is produced, and no ordering
between candidates is defined. The decision is therefore auditable in a way a
learned ranking is not, which is the property that makes the formal-language
framing appropriate for this problem rather than merely required by the course.

## 3. Stage 1: Extraction with Regular Expressions

### 3.1 Rule-Based Extraction

Chiticariu, Li, and Reiss (2013) examined the gap between academic work on
information extraction, which is dominated by machine learning, and industrial
practice, where rule-based systems remain common. They report that rule-based
systems are preferred when the output must be interpretable, when errors must be
traceable to a specific rule, and when the domain vocabulary is controlled and
known in advance. They also identify the main cost, which is the manual effort
required to write and maintain the rules, and the main failure mode, which is
poor generalization to surface forms the rules do not anticipate.

All three conditions favouring rules hold for ResumeLens. The vocabulary is
closed by construction, since the supported qualifications are exactly those
listed in `profiles.md` for the four profiles. The output must be interpretable,
because the extraction stage must expose the expression used and the language it
recognizes. Errors must be traceable, because the project is evaluated on the
correspondence between each component and its formal model. The cost identified
by the authors is accepted explicitly in `formalization.md` Section 7.1, which
records the controlled vocabulary as a known limitation: a technology for which
no expression is defined is never extracted at all.

### 3.2 Regular Expression Matching and the Master Pattern

Thompson (1968) introduced the construction that compiles a regular expression
into a nondeterministic automaton simulated over the input, establishing the
equivalence between the notation and the machine that underlies every regular
expression engine in use today. This equivalence is what allows the extraction
stage to be described as a formal model rather than as string manipulation.

A second result is relevant to the concrete implementation. Aho and Corasick
(1975) showed that a set of keywords can be recognized in a single pass, in time
independent of the number of keywords, by combining them into one automaton with
failure transitions. The extractor already follows this idea in
`src/extraction/extractor.py`, where every qualification variant is compiled
into a single master alternation with one named group per variant, so that one
scan of the résumé both finds the matches and identifies the category that
produced each one.

The implementation also shows where the theory is not sufficient by itself.
Python's `re` module resolves an alternation by leftmost-first preference rather
than by longest match, so `REST` placed before `REST APIs` would shadow it. The
extractor handles this by sorting the alternatives by decreasing length before
compiling. This is a property of the engine, not of regular languages, and it is
the kind of detail the literature on rule-based extraction refers to as
maintenance cost.

Two further decisions in the existing extractor are worth recording, because
they are implementation knowledge that the reviewed sources do not supply. Word
boundaries are expressed with explicit lookarounds instead of `\b`, so that `JS`
is not matched inside `React.js` and `SQL` is not matched inside `MySQL`; and
horizontal whitespace is matched explicitly rather than with `\s`, so a multi-word
pattern such as a degree name cannot continue across a line break into the next
section heading.

## 4. Stage 2: Normalization with Finite-State Transducers

### 4.1 Transducers for Text Normalization

Mohri (1997) gives the reference treatment of finite-state transducers in
language processing, presenting them as machines that define a relation between
an input and an output string rather than a set of accepted strings, and
describing the operations, in particular composition, that make them practical
for building normalization cascades. The property this project relies on is the
one Mohri emphasizes: a transducer separates what is recognized from what is
produced, so several distinct inputs may map to a single output without the
recognizer having to know why they are equivalent.

Sproat, Black, Chen, Kumar, Ostendorf, and Richards (2001) studied text
normalization directly, under the name non-standard words, covering abbreviations,
acronyms, and alternative spellings that must be mapped to a canonical form
before further processing. Their taxonomy of non-standard word types matches the
variation found in résumés closely: `JS` for JavaScript is an abbreviation,
`sklearn` for Scikit-learn is a conventionalized contraction, and
`scikit learn`, `scikit-learn`, and `Scikit-learn` differ only in orthographic
convention. Their conclusion, that normalization is best handled as a dedicated
stage with its own model rather than folded into the consumer of the text, is the
argument for keeping Stage 2 separate from Stage 3.

Beesley and Karttunen (2003) provide the engineering counterpart, describing how
lexical transducers are built and composed in practice, and documenting a
consequence that applies here: once a normalizer is defined over a fixed lexicon,
any input outside that lexicon is simply not in the relation and produces no
output. The transducer does not fail loudly, it produces nothing. Stage 2
therefore needs an explicit decision about unrecognized variants, which is the
gap recorded in Section 8.

### 4.2 Canonical Forms and Skill Taxonomies

The problem of assigning one canonical identifier to many surface names for the
same skill is addressed at scale by occupational taxonomies. O\*NET, maintained
for the United States Department of Labor, and ESCO, the European classification
of Skills, Competences, Qualifications and Occupations, both provide controlled
vocabularies in which a concept has one preferred label and a set of alternative
labels. The structure is exactly the one Stage 2 needs, a many-to-one mapping
from observed forms to a preferred form.

These taxonomies were reviewed and deliberately not adopted. They contain tens of
thousands of concepts organized in a hierarchy, and the assignment requires an
output alphabet small enough to be written out as part of a 7-tuple and used as
the input alphabet of automata that are presented explicitly. ResumeLens
therefore defines its own canonical vocabulary, restricted to the qualifications
that characterize the four supported profiles, following the same preferred-label
and alternative-label structure at a scale that can be formalized. The naming
convention adopted, uppercase with underscores for multi-word qualifications, is
recorded in `formalization.md` Section 3.4.

## 5. Stage 3: Pattern Recognition with Finite Automata

The classification stage rests on standard automata theory. Hopcroft, Motwani,
and Ullman (2006) and Sipser (2013) both establish the equivalence of
deterministic finite automata, nondeterministic finite automata, and automata
with ε-transitions, and give the subset construction that converts a
nondeterministic machine into a deterministic one with up to 2^n states. This
equivalence is what allows the assignment to offer DFA, NFA, and ε-NFA as
alternatives: the choice is one of convenience in presentation, not of expressive
power.

The design recorded in `formalization.md` Sections 4.2 to 4.6 applies the subset
idea directly rather than as a conversion step. A profile is defined by k
requirement slots, and the automaton's states are the subsets of slots already
satisfied, giving 2^k states with a single accepting state where every slot is
satisfied. The transition function is total: a symbol that satisfies a new slot
advances, and every other symbol, whether redundant or belonging to another
profile, is a self-loop. This construction makes acceptance depend only on which
symbols are present and not on their order, which is the property the assignment
asks for when it notes that the result should not depend on the order in which
the candidate wrote the information.

The literature also marks the boundary of this model clearly. A finite automaton
cannot count beyond a fixed bound and cannot compare quantities, so requirements
such as a minimum number of years of experience, or a rule that a candidate must
hold more of one category than another, are not regular properties and cannot be
expressed by these automata. This is recorded as a limitation in
`formalization.md` Section 7.7 rather than worked around, and it is the reason
the years of experience extracted in Stage 1 do not participate in
classification.

One practical consequence of the totality requirement deserves emphasis, because
it was confirmed against the library rather than taken from the literature. In
`pyformlang`, a deterministic automaton rejects any input symbol for which no
transition is defined from the current state. Without the self-loops of Section
4.5, a résumé that mentions Git twice, or that mentions a technology belonging to
another profile, would be rejected by an automaton whose slots are otherwise all
satisfied. The self-loop is therefore load-bearing, not a formality.

## 6. Stage 4: Domain-Specific Languages and Context-Free Grammars

Mernik, Heering, and Sloane (2005) survey when a domain-specific language is
worth developing and how to go about it. Among the patterns they identify, the
one that applies here is notation for a structured artifact that is produced and
consumed by programs but must remain readable and verifiable by people. They also
warn about the main risk, which is language creep: a DSL that grows to absorb
functionality already handled elsewhere in the system. Fowler (2010) makes the
same point in terms of scope, arguing that a DSL should be limited to expressing
the domain and should not become a general-purpose programming notation.

This warning shaped the scope of Stage 4. The candidate profile language defines
only how a validated candidate profile is structured. It does not extract, does
not normalize, and does not classify, because all three have already happened.
The grammar in `formalization.md` Section 5.1 is correspondingly small: a
candidate contains personal information, optional repeated education and
experience records, a skills section, and zero or more classification results.
The choice to allow zero or more classifications rather than exactly one is
inherited from Section 4.6, where a normalized set may be accepted by none, one,
or several of the four automata.

A context-free grammar is the right model for this stage for a reason the
automata sections make clear by contrast. The structure to be validated is
nested and balanced, with blocks inside blocks delimited by braces, and balanced
nesting to arbitrary depth is not a regular property. The grammar is used for
validation rather than for recognition of natural language, which is the use for
which EBNF and parser generators are designed.

## 7. Tooling

Two libraries are fixed by the assignment, and both were published with
educational use as an explicit goal.

Romero (2021) presents `pyformlang` as a library for manipulating formal
languages and automata, intended for teaching and for experimentation with the
constructions found in automata theory courses. It provides finite automata,
transducers, and grammars with an interface that stays close to the formal
definitions, which is what allows the implementation to expose the same tuples
that the design documents state. The library also exports automata and
transducers in DOT format, which covers the graphical representations the
assignment requires for Stages 2 and 3 without a separate drawing step.

Dejanović, Vaderna, Milosavljević, and Vuković (2017) present `textX`, a
meta-language for Python built on the Arpeggio PEG parser, which generates both a
parser and a metamodel from a single grammar description. The relevant property
for this project is that a grammar written in textX notation stays close to the
EBNF that documents it, so the grammar in the design document and the grammar in
the code can be compared rule by rule. Because textX is based on PEG rather than
on a classical context-free parsing algorithm, ordered choice replaces ambiguous
alternation; this does not affect a grammar as constrained as the one defined
here, but it is a difference worth stating when the EBNF and the implementation
are presented side by side.

## 8. Gaps and Positioning

The review leaves four questions that the reviewed sources do not settle and that
the implementation must decide.

The first is the treatment of variants that are extracted but have no canonical
form. Beesley and Karttunen (2003) note that a transducer produces nothing for
input outside its lexicon, so the behaviour must be chosen rather than inherited.
The extractor currently recognizes technologies, among them Kubernetes, Redis,
Keras, Flask, and Matplotlib, that `formalization.md` Section 4.4 excludes from
the alphabet of the automata. Stage 2 must either give them canonical symbols
that only trigger self-loops, or discard them explicitly and record that
decision.

The second is the granularity of the model development qualification. The
Machine Learning Engineer profile requires a slot satisfied by the symbol MLMD,
while the extractor recognizes three different surface forms, the full phrase
machine learning model development, the bare term machine learning, and the
abbreviation ML. Mapping all three to MLMD would let any mention of machine
learning satisfy a slot intended to represent demonstrated model development,
which weakens the pattern. Separating them keeps the slot meaningful at the cost
of a longer vocabulary.

The third is the collapsing of the REST family. The extractor recognizes
`REST APIs`, `REST API`, and `REST` as distinct variants, and all three must map
to the single canonical symbol REST_API that the Full Stack Developer pattern
requires.

The fourth concerns evaluation. The sources reviewed for résumé extraction report
precision and recall against annotated corpora, which is not available here and
would not measure what this system does. Since ResumeLens decides membership in a
formally defined language, correctness means agreement between the implementation
and the formal definition, not agreement with human judgment about candidates.
The project is therefore evaluated through test cases derived from the formal
models, including the order-independence property of Section 4.5 and the
rejection of profiles that violate the grammar of Section 5.1. The design of
those test cases is documented separately in `docs/test-cases.md`.

Taken together, the review supports the architecture already recorded in
`architecture.md` and `formalization.md`. The staged pipeline follows the
observation of Yu, Guan, and Zhou (2005) that different information types need
different treatment; the rule-based extraction is justified by the conditions
Chiticariu, Li, and Reiss (2013) identify; the separate normalization stage
follows Sproat et al. (2001); the order-insensitive automata apply the subset
construction of standard automata theory; and the deliberately small DSL respects
the scope warnings of Mernik et al. (2005) and Fowler (2010). The contribution of
ResumeLens is not a new technique but an end-to-end system in which every stage
is presented as an explicit formal model whose decisions can be traced, which is
what distinguishes it from both the statistical parsers and the opaque screening
tools discussed in Section 2.

## 9. References

Aho, A. V., and Corasick, M. J. (1975). Efficient string matching: an aid to
bibliographic search. *Communications of the ACM*, 18(6), 333–340.

Beesley, K. R., and Karttunen, L. (2003). *Finite State Morphology*. CSLI
Publications, Stanford.

Chiticariu, L., Li, Y., and Reiss, F. R. (2013). Rule-Based Information
Extraction is Dead! Long Live Rule-Based Information Extraction Systems! In
*Proceedings of the 2013 Conference on Empirical Methods in Natural Language
Processing*, pages 827–832. Association for Computational Linguistics, Seattle.

Dastin, J. (2018). Amazon scraps secret AI recruiting tool that showed bias
against women. *Reuters*, October 10, 2018.

Dejanović, I., Vaderna, R., Milosavljević, G., and Vuković, Ž. (2017). TextX: A
Python tool for Domain-Specific Languages implementation. *Knowledge-Based
Systems*, 115, 1–4.

Fowler, M. (2010). *Domain-Specific Languages*. Addison-Wesley, Boston.

Hopcroft, J. E., Motwani, R., and Ullman, J. D. (2006). *Introduction to Automata
Theory, Languages, and Computation*, 3rd edition. Addison-Wesley, Boston.

Mernik, M., Heering, J., and Sloane, A. M. (2005). When and how to develop
domain-specific languages. *ACM Computing Surveys*, 37(4), 316–344.

Mohri, M. (1997). Finite-State Transducers in Language and Speech Processing.
*Computational Linguistics*, 23(2), 269–311.

Raghavan, M., Barocas, S., Kleinberg, J., and Levy, K. (2020). Mitigating bias in
algorithmic hiring: evaluating claims and practices. In *Proceedings of the 2020
Conference on Fairness, Accountability, and Transparency (FAT\* '20)*, pages
469–481. ACM, Barcelona.

Romero, J. (2021). Pyformlang: An Educational Library for Formal Language
Manipulation. In *Proceedings of the 52nd ACM Technical Symposium on Computer
Science Education (SIGCSE '21)*. ACM.

Sipser, M. (2013). *Introduction to the Theory of Computation*, 3rd edition.
Cengage Learning, Boston.

Sproat, R., Black, A. W., Chen, S., Kumar, S., Ostendorf, M., and Richards, C.
(2001). Normalization of non-standard words. *Computer Speech & Language*, 15(3),
287–333.

Thompson, K. (1968). Programming Techniques: Regular expression search algorithm.
*Communications of the ACM*, 11(6), 419–422.
