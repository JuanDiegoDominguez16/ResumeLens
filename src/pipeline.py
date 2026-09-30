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
             not implemented yet, see below


STAGE 4 IS NOT WIRED IN YET

The candidate profile language is the remaining stage, and the place it plugs
into is marked in `run` below. When src/grammar/ exists it will take the
PipelineResult produced here, render it as a candidate profile document,
validate it against the textX grammar, and add the validated profile and its
HTML visualization to the result.

Nothing else in the pipeline has to change for that: the three stages below
already produce everything Stage 4 needs, which is the candidate information
from Stage 1, the canonical qualifications from Stage 2, and the accepted
profile keys from Stage 3.
"""

from dataclasses import dataclass

from src.classification.classifier import classify
from src.extraction.extractor import (
    extract_resume,
    qualification_strings,
    to_serializable,
)
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

    resume_text     the input, unchanged
    extraction      Stage 1, the structured extraction result
    normalization   Stage 2, the canonical set plus what was discarded and why
    classification  Stage 3, one answer per profile
    """

    resume_text: str
    extraction: dict
    normalization: object
    classification: object

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

    def as_dict(self):
        """
        A JSON-ready view of the run, for saving a result to a file or for
        handing the extraction output to another tool.

        Only the extraction part needs converting: its values are Finding
        objects. The other two stages are summarized rather than serialized
        whole, since their dataclasses carry Profile and Slot objects that
        have no useful JSON form.
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
        }


def run(resume_text):
    """
    Run a resume through the pipeline.

        >>> result = run("Ana Torres\\nSkills: TypeScript, Angular, "
        ...              "Spring Boot, NoSQL databases, REST APIs, Git.")
        >>> result.accepted_keys
        ('FULL_STACK_DEVELOPER',)

    An empty or unrecognizable resume is not an error: extraction finds
    nothing, normalization produces the empty set, and every automaton stays
    in its initial state, so the candidate comes back unclassified with every
    slot listed as missing.
    """

    extraction = extract_resume(resume_text)

    normalization = normalize(qualification_strings(resume_text))

    classification = classify(normalization.qualification_set)

    # Stage 4 goes here, once src/grammar/ exists:
    #
    #     profile_source = generator.render(extraction, normalization,
    #                                       classification)
    #     candidate_profile = validator.validate(profile_source)
    #     visualization = visualization.to_html(candidate_profile)
    #
    # and the three results join PipelineResult as further fields.

    return PipelineResult(
        resume_text=resume_text,
        extraction=extraction,
        normalization=normalization,
        classification=classification,
    )
