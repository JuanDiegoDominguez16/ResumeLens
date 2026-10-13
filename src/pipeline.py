"""
The ResumeLens processing pipeline.

This module is the one place where the stages are joined. Each stage package
is deliberately independent of the others, as docs/architecture.md section 7
requires: extraction does not know about canonical symbols, normalization does
not import the extractor, and classification receives a set of symbols without
caring where they came from. Wiring them together is this module's only job.

    raw resume text
        |
        v
    Stage 1  extraction        regular expressions      docs/formalization.md 2
        |    representations found in the resume
        v
    Stage 2  normalization     finite-state transducer  docs/formalization.md 3
        |    canonical qualification symbols
        v
    Stage 3  classification    finite automata          docs/formalization.md 4
        |    accepted profiles, and the slots that were missing
        v
    Stage 4  candidate profile language                 docs/formalization.md 5
             the profile written in the DSL, validated, and rendered


STAGE 4 AND THE RESUMES IT CANNOT REPRESENT

The fourth stage runs in three steps, each in its own module: the generator
writes the results of the first three stages as a candidate profile, the
validator parses it, and the visualization renders the model.

A resume that states no email address has no representation in the language,
since the Email rule of section 5.2 has no empty form, and the generator
raises IncompleteProfile rather than inventing an address. That is not an
error of the run: the first three stages produced their results and those
results are worth showing. The pipeline therefore catches it, leaves the
profile fields empty, and records the reason in `profile_error`.

An InvalidProfile is not caught. The profile the validator rejected would be
one this system had just written itself, so a rejection means the generator
and the grammar disagree, which is a defect rather than a property of the
resume. Letting it propagate is what makes the tests of that disagreement
fail loudly instead of silently producing a result with no profile in it.
"""

from dataclasses import dataclass

from src.classification.classifier import classify
from src.extraction.extractor import (
    extract_resume,
    qualification_strings,
    to_serializable,
)
from src.grammar import visualization
from src.grammar.generator import IncompleteProfile, render
from src.grammar.validator import validate
from src.normalization.normalizer import normalize


@dataclass(frozen=True)
class PipelineResult:
    """
    Everything the pipeline produced for one resume, stage by stage.

    The intermediate results are kept rather than discarded, because the point
    of the application is to show how a resume moves through the formal models,
    not only what the final answer was. The interface renders one tab per field
    here, and docs/architecture.md section 7 lists that traceability as a
    design principle.

    resume_text        the input, unchanged
    extraction         Stage 1, the structured extraction result
    normalization      Stage 2, the canonical set plus what was discarded
    classification     Stage 3, one answer per profile
    profile_source     Stage 4, the profile written in the DSL, or None
    candidate_profile  Stage 4, the model textX built from it, or None
    visualization      Stage 4, the HTML document, or None
    profile_error      why there is no profile, when there is none
    """

    resume_text: str
    extraction: dict
    normalization: object
    classification: object
    profile_source: str = None
    candidate_profile: object = None
    visualization: str = None
    profile_error: str = None

    @property
    def qualifications(self):
        """The canonical symbols, alphabetically, for display."""
        return self.normalization.qualifications

    @property
    def accepted_keys(self):
        """The profiles whose pattern the candidate satisfied."""
        return self.classification.accepted_keys

    @property
    def is_unclassified(self):
        """True when no profile pattern was satisfied, which is a valid result."""
        return self.classification.is_unclassified

    @property
    def candidate_name(self):
        """The candidate's name, or None when the resume did not state one."""
        return self.extraction["Candidate"]["name"]

    @property
    def has_profile(self):
        """
        True when Stage 4 produced a validated profile.

        False is a result, not a failure: it means the resume did not state
        something the language requires, and `profile_error` says what.
        """

        return self.candidate_profile is not None

    def as_dict(self):
        """
        A JSON-ready view of the run, for saving a result to a file or for
        handing the extraction output to another tool.

        Only the extraction part needs converting: its values are Finding
        objects. The other three stages are summarized rather than serialized
        whole, since their dataclasses carry Profile and Slot objects, and the
        textX model carries parser state, that have no useful JSON form. The
        profile is represented by its source, which is the form the language
        defines and the only one that can be read back.
        """

        return {
            "candidate": self.candidate_name,
            "extraction": to_serializable(self.extraction),
            "qualifications": list(self.qualifications),
            "discarded": [
                {"representation": entry.representation, "reason": entry.reason}
                for entry in self.normalization.discarded
            ],
            "classification": [
                {
                    "profile": entry.key,
                    "accepted": entry.accepted,
                    "final_state": entry.final_state,
                    "missing_slots": [slot.name for slot in entry.missing_slots],
                }
                for entry in self.classification.results
            ],
            "accepted_profiles": list(self.accepted_keys),
            "candidate_profile": self.profile_source,
            "profile_error": self.profile_error,
        }


def run(resume_text):
    """
    Run a resume through the four stages.

        >>> result = run("Ana Torres\\nana@example.com\\nSkills: TypeScript, "
        ...              "Angular, Spring Boot, NoSQL databases, REST APIs, Git.")
        >>> result.accepted_keys
        ('FULL_STACK_DEVELOPER',)
        >>> result.has_profile
        True

    An empty or unrecognizable resume is not an error: extraction finds
    nothing, normalization produces the empty set, and every automaton stays
    in its initial state, so the candidate comes back unclassified with every
    slot listed as missing. Stage 4 then reports that the resume states no
    email address, and the first three stages are returned as they are.
    """

    extraction = extract_resume(resume_text)

    normalization = normalize(qualification_strings(resume_text))

    classification = classify(normalization.qualification_set)

    try:
        profile_source = render(extraction, normalization, classification)

    except IncompleteProfile as error:
        return PipelineResult(
            resume_text=resume_text,
            extraction=extraction,
            normalization=normalization,
            classification=classification,
            profile_error=str(error),
        )

    candidate_profile = validate(profile_source)

    return PipelineResult(
        resume_text=resume_text,
        extraction=extraction,
        normalization=normalization,
        classification=classification,
        profile_source=profile_source,
        candidate_profile=candidate_profile,
        visualization=visualization.to_html(candidate_profile),
    )