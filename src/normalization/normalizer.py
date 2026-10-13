"""
The normalization stage API, Stage 2.

This module is what the pipeline and the user interface call. It takes the
qualification representations produced by Stage 1, runs each one through the
transducer of docs/formalization.md section 3, and returns the set of canonical
symbols that Stage 3 classifies, together with an account of everything that
did not make it into that set.

    extractor.qualification_strings(resume_text)
        ["JS", "React.js", "NodeJS", "Postgres", "Git"]
                    |
                    v
            normalize(representations)
                    |
                    v
    {GIT, JAVASCRIPT, NODE_JS, POSTGRESQL, REACT}


WHAT THIS MODULE DOES NOT DO

It does not extract, and it does not import the extraction package. Section 3.3
defines the input of this stage as the representations produced by Stage 1, and
keeping the dependency out means the two stages can be tested independently, as
docs/architecture.md section 7 requires. Wiring extraction to normalization is
the pipeline's job.

It also does not classify. The result of this stage is a set of qualifications,
not a profile. Deciding which professional profiles that set satisfies is
Stage 3, and section 3.8 is explicit that normalization must not anticipate it.


WHY THE RESULT IS A SET, AND WHY IT IS ALSO A SORTED TUPLE

Section 3.8 defines the output of this stage as a set of canonical symbols with
duplicates removed, and states that the automata of Section 4 are built so that
acceptance depends only on which symbols are present, never on their order.

The result therefore exposes two views of the same thing. `qualification_set`
is the formal output, a frozenset, and it is what Stage 3 must consume.
`qualifications` is the same content sorted alphabetically, for display and for
readable test assertions. The ordering is profile independent on purpose:
section 3.8 rejects ordering by profile, because the profile is precisely what
Stage 3 is meant to determine, so using it to arrange Stage 3's input would
assume the answer.


WHY DISCARDED REPRESENTATIONS ARE REPORTED

A transducer produces nothing for input outside its relation, so a
representation with no canonical symbol simply disappears. Section 4.4 and
vocabulary.py establish that this is intended for a known list of technologies,
but a stage that silently drops part of its input cannot be audited, and
traceability is one of the design principles in docs/architecture.md section 7.

The result therefore separates the two reasons a representation produced
nothing:

    out_of_scope    recognized by Stage 1, deliberately given no canonical
                    symbol, with the documented reason attached
    unknown         not a qualification representation at all, which normally
                    means the caller passed something that did not come from
                    Stage 1

The distinction is structural rather than a string to match on, so the user
interface can show "recognized but not classified" separately from "not
understood", and the tests of the next commit can assert on each.
"""

from dataclasses import dataclass, field

from src.normalization import transducer, vocabulary


@dataclass(frozen=True)
class Normalized:
    """
    One representation and the canonical symbol the transducer produced for it.

    Several representations may carry the same canonical symbol, which is the
    normal case when a resume writes a qualification more than one way, for
    example "JS" in a skills list and "JavaScript" in a project description.
    Both entries are kept, because the point of this record is to explain how
    each string in the resume was treated.
    """

    representation: str
    canonical: str


@dataclass(frozen=True)
class Discarded:
    """A representation that produced no canonical symbol, and why."""

    representation: str
    reason: str


@dataclass(frozen=True)
class NormalizationResult:
    """
    The complete outcome of Stage 2.

    normalized     the representations that produced a canonical symbol, in the
                   order they were received, so the trace follows the resume
    out_of_scope   representations deliberately left out of the vocabulary
    unknown        strings that are not qualification representations
    """

    normalized: tuple = field(default=())
    out_of_scope: tuple = field(default=())
    unknown: tuple = field(default=())

    @property
    def qualification_set(self):
        """
        The output of section 3.8: the canonical symbols, duplicates removed.

        This is the input Stage 3 consumes. It is a frozenset rather than a
        sequence so that no consumer can accidentally come to depend on an
        order that the model does not define.
        """

        return frozenset(entry.canonical for entry in self.normalized)

    @property
    def qualifications(self):
        """
        The same symbols in alphabetical order, for display and for readable
        assertions. Sorting is presentation only and has no effect on
        classification.
        """

        return tuple(sorted(self.qualification_set))

    @property
    def discarded(self):
        """
        Every representation that produced no canonical symbol, out of scope
        and unknown together, for callers that only need to show what was left
        out without distinguishing why.
        """

        return self.out_of_scope + tuple(
            Discarded(representation, "not a recognized qualification")
            for representation in self.unknown
        )


# The reason attached to a representation that Stage 1 recognizes but that the
# controlled vocabulary leaves without a canonical symbol, when vocabulary.py
# has no more specific one. In practice every entry in OUT_OF_SCOPE carries its
# own reason, so this is a fallback rather than the usual case.
_DEFAULT_OUT_OF_SCOPE_REASON = "outside the controlled vocabulary of section 2.3"


def normalize(representations):
    """
    Run a sequence of qualification representations through the transducer.

    The argument is any iterable of strings, normally the output of
    extractor.qualification_strings(). Blank strings are ignored rather than
    reported, since they carry no information either way.

    Representations that fold to the same input symbol are collapsed, keeping
    the first spelling seen, so a resume that writes both "JS" and "js"
    produces one entry rather than two identical ones. Spellings that fold
    differently are kept apart even when they share a canonical symbol, so
    "JS" and "JavaScript" both appear in the trace, each mapped to JAVASCRIPT.

        >>> result = normalize(["JS", "React.js", "Kubernetes", "Git"])
        >>> result.qualifications
        ('GIT', 'JAVASCRIPT', 'REACT')
        >>> [d.representation for d in result.out_of_scope]
        ['Kubernetes']
    """

    normalized = []
    out_of_scope = []
    unknown = []

    seen = set()

    for representation in representations:

        if not representation or not representation.strip():
            continue

        folded = vocabulary.fold(representation)

        if folded in seen:
            continue

        seen.add(folded)

        canonical = transducer.translate(representation)

        if canonical is not None:
            normalized.append(Normalized(representation, canonical))

        elif vocabulary.is_out_of_scope(representation):
            out_of_scope.append(
                Discarded(
                    representation,
                    vocabulary.out_of_scope_reason(representation)
                    or _DEFAULT_OUT_OF_SCOPE_REASON,
                )
            )

        else:
            unknown.append(representation)

    return NormalizationResult(
        normalized=tuple(normalized),
        out_of_scope=tuple(out_of_scope),
        unknown=tuple(unknown),
    )


def canonical_set(representations):
    """
    Shorthand for the formal output alone, when the caller does not need the
    trace. Equivalent to normalize(representations).qualification_set.
    """

    return normalize(representations).qualification_set
