"""
The classification stage API, Stage 3.

This module is what the pipeline and the user interface call. It takes the set
of canonical symbols produced by Stage 2, runs it through each of the four
profile automata of automata.py, and reports what each one decided.

    normalizer.normalize(...).qualification_set
        {JAVASCRIPT, REACT, NODE_JS, POSTGRESQL, GIT}
                    |
                    v
            classify(qualifications)
                    |
                    v
    four independent answers, one per profile


WHAT THIS STAGE DELIBERATELY DOES NOT PRODUCE

It produces no score, no ranking, no percentage of completion and no best
match. The assignment is explicit that ResumeLens does not rank candidates and
does not make hiring decisions, and docs/literature-review.md section 2.2
explains why that restriction is worth taking seriously rather than treating as
a disclaimer: the documented harms of automated screening come from systems
that infer an unstated judgement of suitability from something they measured.

The temptation here is concrete. Every ProfileResult below knows how many slots
it satisfied, so a "73% Full Stack" field would be three lines of code away.
That number would be a ranking, it would immediately be read as a measure of
how good a candidate is, and nothing in the formal model supports it. Four slots
out of six is not two thirds of a Full Stack Developer.

What the stage reports instead is which slots are still unsatisfied. That is
the same information without the ordering, and it is actionable in a way a
percentage is not: "the REST API slot was never satisfied" tells a person
exactly what the automaton was waiting for.


NONE, ONE, OR SEVERAL

Section 4.6 is explicit that the four automata are independent and are
evaluated separately against the same set, so a candidate may be accepted by
none of them, by one, or by several. All three are ordinary outcomes:

    several   the qualifications satisfy two patterns at once, which happens
              when profiles share requirements, for example a candidate with
              both the machine learning and the data engineering stacks
    one       the usual case
    none      the set satisfies no complete pattern; the application treats
              the candidate as unclassified for the four supported profiles

`unclassified` is not an error and not a failure of the pipeline. It is what
the model says when no accepted pattern is matched, and the missing slots
explain what was absent.
"""

from dataclasses import dataclass

from src.classification import automata
from src.classification.profiles import PROFILES


@dataclass(frozen=True)
class ProfileResult:
    """
    What one profile's automaton decided about one candidate.

    profile          the Profile this answer is about
    accepted         whether the automaton reached its accepting state
    satisfied_slots  the slots the qualifications filled, in section 4.7 order
    missing_slots    the slots left unfilled, in section 4.7 order
    final_state      the label of the state the automaton stopped in, for
                     example "qFS" when accepted or "q{1,2,4,6}" when not
    """

    profile: object
    accepted: bool
    satisfied_slots: tuple
    missing_slots: tuple
    final_state: str

    @property
    def key(self):
        return self.profile.key

    @property
    def name(self):
        return self.profile.name


@dataclass(frozen=True)
class ClassificationResult:
    """
    The outcome of Stage 3: one answer per profile, collected, not combined.

    qualifications  the canonical set that was classified
    results         one ProfileResult per profile, in the order PROFILES lists
                    them, whether accepted or not
    """

    qualifications: frozenset
    results: tuple

    @property
    def accepted(self):
        """The ProfileResult entries whose automaton accepted, in profile order."""
        return tuple(result for result in self.results if result.accepted)

    @property
    def accepted_keys(self):
        """
        The keys of the accepted profiles, which is what Stage 4 writes into
        the candidate profile language as Classification elements.
        """
        return tuple(result.key for result in self.accepted)

    @property
    def is_unclassified(self):
        """
        True when no automaton accepted. Section 4.6 treats this as a normal
        outcome, so callers should present it as a result, not as an error.
        """
        return not self.accepted

    def for_profile(self, key):
        """The result for one profile key, or None when the key is unknown."""

        for result in self.results:
            if result.key == key:
                return result

        return None


def classify_for(profile, qualifications):
    """
    Run one set of canonical symbols through one profile's automaton.

    Acceptance comes from the automaton itself; the satisfied and missing slots
    come from the state it stopped in, so the two cannot disagree about what
    happened.
    """

    satisfied = automata.final_subset(profile, qualifications)

    return ProfileResult(
        profile=profile,
        accepted=automata.accepts(profile, qualifications),
        satisfied_slots=tuple(
            slot
            for index, slot in enumerate(profile.slots)
            if index in satisfied
        ),
        missing_slots=tuple(
            slot
            for index, slot in enumerate(profile.slots)
            if index not in satisfied
        ),
        final_state=automata.state_label(profile, satisfied),
    )


def classify(qualifications):
    """
    Run a set of canonical symbols through all four profile automata.

    The argument is normally normalizer.normalize(...).qualification_set. Any
    iterable of canonical symbols works; symbols outside the alphabet are
    ignored by the automata, as automata.final_subset explains.

        >>> result = classify({"JAVASCRIPT", "REACT", "NODE_JS", "SQL",
        ...                    "REST_API", "GIT"})
        >>> result.accepted_keys
        ('FULL_STACK_DEVELOPER',)
        >>> result.is_unclassified
        False
    """

    qualifications = frozenset(qualifications)

    return ClassificationResult(
        qualifications=qualifications,
        results=tuple(
            classify_for(profile, qualifications) for profile in PROFILES
        ),
    )
