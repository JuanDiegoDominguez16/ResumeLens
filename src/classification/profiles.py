"""
Professional profile patterns, Stage 3.

This module is the single source of truth for the requirement slots that
docs/formalization.md section 4.7 defines for each of the four supported
profiles. It contains data only. Turning these slots into finite automata is
automata.py, and running a candidate through them is classifier.py.

A profile is not a list of required qualifications. It is a list of
requirement SLOTS, and each slot is satisfied by any one of a set of canonical
symbols. The Full Stack Developer frontend slot, for example, is satisfied by
REACT or ANGULAR or VUE, and satisfying it twice is no better than satisfying
it once.

That distinction is what makes the pattern a formal language question rather
than a scoring question. A candidate is accepted when every slot has been
satisfied at least once, which is a yes or no property of the set of symbols,
not a count and not a ranking. Nothing here assigns a weight to any
qualification.


THE INVARIANT THAT SECTION 4.5 DEPENDS ON

Within one profile, no symbol may belong to more than one slot. Section 4.5
relies on it when it defines the transition function: a symbol satisfies at
most one slot of that profile, so the automaton advances by exactly one slot or
not at all, and the next state is unambiguous. Without the invariant the
transition function would have to choose between two slots and would stop being
a function.

Across profiles the situation is the opposite and entirely intended. GIT
appears in three profiles, SQL in three, PYTHON in two. Each profile runs its
own independent automaton over the same alphabet, so a shared symbol advances
one machine and self loops in another without any conflict.

The invariant is checked when the module is imported, so a slot definition that
breaks it fails immediately rather than producing an automaton that silently
disagrees with section 4.5.
"""

from dataclasses import dataclass

from src.normalization.vocabulary import CANONICAL_SYMBOLS


@dataclass(frozen=True)
class Slot:
    """
    One requirement of a profile, and the canonical symbols that satisfy it.

    name      how section 4.7 describes the requirement, used in the interface
              and in the diagrams
    symbols   any one of these satisfies the slot
    """

    name: str
    symbols: frozenset

    def is_satisfied_by(self, symbol):
        return symbol in self.symbols


@dataclass(frozen=True)
class Profile:
    """
    A professional profile, as a sequence of requirement slots.

    key         the identifier used as a classification result and in the
                candidate profile language of Stage 4
    name        the human readable name used by profiles.md and the interface
    state_label the name section 4.6 gives this profile's accepting state
    slots       the requirement slots, in the order section 4.7 lists them
    """

    key: str
    name: str
    state_label: str
    slots: tuple

    @property
    def slot_count(self):
        """k, the number of requirement slots."""
        return len(self.slots)

    @property
    def state_count(self):
        """
        |Q| = 2^k, the number of states of this profile's automaton.

        Section 4.3 builds the states from the subsets of satisfied slots, so
        the count is exponential in k but finite, which is what keeps the
        machine a valid DFA no matter how many requirements a profile has.
        """
        return 2 ** self.slot_count

    @property
    def symbols(self):
        """Every canonical symbol that satisfies some slot of this profile."""
        return frozenset(
            symbol for slot in self.slots for symbol in slot.symbols
        )

    def slot_index_for(self, symbol):
        """
        The index of the slot this symbol satisfies, or None when the symbol
        satisfies no slot of this profile.

        The invariant above is what makes the answer unique, and it is what
        section 4.5 needs in order to define the next state.
        """

        for index, slot in enumerate(self.slots):
            if slot.is_satisfied_by(symbol):
                return index

        return None


# ---------------------------------------------------------------------------
# THE FOUR PROFILE PATTERNS OF SECTION 4.7
# ---------------------------------------------------------------------------

FULL_STACK_DEVELOPER = Profile(
    key="FULL_STACK_DEVELOPER",
    name="Full Stack Developer",
    state_label="qFS",
    slots=(
        Slot("programming language", frozenset({"JAVASCRIPT", "TYPESCRIPT"})),
        Slot("frontend", frozenset({"REACT", "ANGULAR", "VUE"})),
        Slot("backend", frozenset({"NODE_JS", "DJANGO", "SPRING_BOOT"})),
        Slot("database", frozenset({"SQL", "NOSQL"})),
        Slot("REST API", frozenset({"REST_API"})),
        Slot("version control", frozenset({"GIT"})),
    ),
)


MACHINE_LEARNING_ENGINEER = Profile(
    key="MACHINE_LEARNING_ENGINEER",
    name="Machine Learning Engineer",
    state_label="qML",
    slots=(
        Slot("programming language", frozenset({"PYTHON"})),
        Slot("data manipulation", frozenset({"PANDAS", "NUMPY"})),
        Slot("machine learning library", frozenset({"SCIKIT_LEARN"})),
        Slot("deep learning framework", frozenset({"TENSORFLOW", "PYTORCH"})),
        Slot("model development", frozenset({"MLMD"})),
        Slot("database", frozenset({"SQL"})),
        Slot("version control", frozenset({"GIT"})),
    ),
)


DEVOPS_ENGINEER = Profile(
    key="DEVOPS_ENGINEER",
    name="DevOps Engineer",
    state_label="qDO",
    slots=(
        Slot("containerization", frozenset({"DOCKER"})),
        Slot("cloud provider", frozenset({"AWS", "AZURE", "GOOGLE_CLOUD"})),
        Slot(
            "CI/CD",
            frozenset({"JENKINS", "GITHUB_ACTIONS", "GITLAB_CI_CD"}),
        ),
        Slot("infrastructure automation", frozenset({"TERRAFORM", "ANSIBLE"})),
        Slot("version control", frozenset({"GIT"})),
    ),
)


DATA_ENGINEER = Profile(
    key="DATA_ENGINEER",
    name="Data Engineer",
    state_label="qDE",
    slots=(
        Slot("query language", frozenset({"SQL"})),
        Slot("orchestration", frozenset({"AIRFLOW"})),
        Slot("distributed processing", frozenset({"SPARK"})),
        Slot("database", frozenset({"POSTGRESQL", "MYSQL"})),
        Slot("data platform", frozenset({"DATABRICKS"})),
    ),
)


# In the order the assignment introduces them: the two reference profiles
# first, then the two the team defined.
PROFILES = (
    FULL_STACK_DEVELOPER,
    MACHINE_LEARNING_ENGINEER,
    DEVOPS_ENGINEER,
    DATA_ENGINEER,
)

PROFILE_BY_KEY = {profile.key: profile for profile in PROFILES}


def profile_for(key):
    """Look a profile up by its key, or None when the key is unknown."""
    return PROFILE_BY_KEY.get(key)


# ---------------------------------------------------------------------------
# CONSISTENCY WITH THE DOCUMENT
# ---------------------------------------------------------------------------

# The slot counts section 4.7 states, and the state counts it derives from
# them. Repeated here so that changing a profile without updating the document
# fails at import time instead of quietly producing a different model.
_DOCUMENTED_SLOT_COUNTS = {
    "FULL_STACK_DEVELOPER": 6,
    "MACHINE_LEARNING_ENGINEER": 7,
    "DEVOPS_ENGINEER": 5,
    "DATA_ENGINEER": 5,
}


def _check_profiles():

    for profile in PROFILES:

        # Every slot symbol has to be a canonical symbol, otherwise the slot
        # could never be satisfied: Stage 2 cannot produce a symbol outside G.
        outside_gamma = profile.symbols - CANONICAL_SYMBOLS
        if outside_gamma:
            raise ValueError(
                f"{profile.key} requires symbols that are not in the output "
                f"alphabet of Stage 2: {sorted(outside_gamma)}"
            )

        # Section 4.5: within one profile the slots are pairwise disjoint.
        seen = {}
        for index, slot in enumerate(profile.slots):
            for symbol in slot.symbols:
                if symbol in seen:
                    raise ValueError(
                        f"{profile.key}: {symbol} satisfies both the "
                        f"{profile.slots[seen[symbol]].name!r} and the "
                        f"{slot.name!r} slots, which would make the "
                        f"transition function of section 4.5 ambiguous"
                    )
                seen[symbol] = index

        # An empty slot could never be satisfied, so the profile could never
        # be accepted by anyone.
        for slot in profile.slots:
            if not slot.symbols:
                raise ValueError(
                    f"{profile.key}: the {slot.name!r} slot accepts no symbol"
                )

        expected = _DOCUMENTED_SLOT_COUNTS.get(profile.key)
        if expected is not None and profile.slot_count != expected:
            raise ValueError(
                f"{profile.key} has {profile.slot_count} slots, but section "
                f"4.7 of docs/formalization.md documents {expected}; update "
                f"the document and this table together"
            )

    if set(PROFILE_BY_KEY) != set(_DOCUMENTED_SLOT_COUNTS):
        raise ValueError(
            "the set of profiles no longer matches the four documented in "
            "section 4.7"
        )


_check_profiles()


# Symbols that satisfy no slot of any profile. Section 4.5 makes these self
# loops in every automaton, so they can appear in a candidate's set without
# affecting any result.
#
# The set is currently empty: every canonical symbol of the controlled
# vocabulary is a core qualification of at least one profile, which is the
# consequence of the decision recorded in vocabulary.py to keep G restricted to
# exactly those. It is computed rather than asserted to be empty, because a
# later profile change could legitimately leave a symbol unused.
UNUSED_SYMBOLS = CANONICAL_SYMBOLS - frozenset(
    symbol for profile in PROFILES for symbol in profile.symbols
)
