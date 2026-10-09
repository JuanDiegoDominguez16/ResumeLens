"""
The candidate profile validator, Stage 4.

This module decides whether a candidate profile is a sentence of the language
defined in docs/formalization.md section 5. It loads candidate_profile.tx with
textX, parses the profile, and either returns the model textX built or raises
with the position of the token that broke the rule.

    candidate profile source
            |
            v
        validate(source)
            |
        +---+---+
        |       |
      model   InvalidProfile


WHY VALIDATION IS ITS OWN MODULE

The profile that the pipeline validates is one this system wrote itself, a few
milliseconds earlier, from its own Stage 1 to 3 results. Validating it may
therefore look circular: if the generator is correct the parser can only
succeed, and if the generator is wrong the parser is the thing that says so.

That is the point. Section 5 defines the structure of a candidate profile as a
grammar, not as whatever the generator happens to emit, so the grammar has to
be able to reject. Keeping the parser in a module that knows nothing about the
generator is what makes the check real: examples/invalid/ is parsed by exactly
the same function as a generated profile, and a profile a person wrote by hand
gets exactly the same answer.


WHAT A REJECTION MEANS

A rejection is a statement about structure, never about the candidate. The
language has no way to say that a résumé is weak, and this module has no
opinion on whether the information in a profile is true, which
docs/formalization.md section 7.7 states as a limitation of the whole stage.
A profile is rejected when it is not written in the language: a missing
required block, an unquoted string, an email without its `@`, a qualification
that is not a canonical symbol.

That last case is worth naming, because it is the one that ties this stage to
the earlier ones. `skill: React.js` is not in the language, since Identifier
admits letters, digits and the underscore but not a dot. A profile carrying a
representation that Stage 2 should have normalized is therefore rejected by the
lexical rule itself, with no extra check written in Python.
"""

import os

from textx import metamodel_from_file
from textx.exceptions import TextXError


# The grammar file lives next to this module, so the path is derived from
# __file__ rather than from the working directory: pytest, Streamlit and a
# plain python -m all start from different places.

GRAMMAR_PATH = os.path.join(os.path.dirname(__file__), "candidate_profile.tx")


class InvalidProfile(Exception):
    """
    A candidate profile that is not a sentence of the language.

    The attributes are kept separate from the message so that a caller can
    place the error, which the interface needs in order to point at the line:

        message   what textX reported
        line      1-based line of the offending token, or None
        column    1-based column, or None
        source    the profile that was rejected, for context
    """

    def __init__(self, message, line=None, column=None, source=None):
        super().__init__(message)

        self.message = message
        self.line = line
        self.column = column
        self.source = source

    def __str__(self):
        if self.line is None:
            return self.message

        return f"line {self.line}, column {self.column}: {self.message}"


# The metamodel is built once and reused. Building it parses the grammar
# itself, which is wasted work on every call, and a single instance also means
# that a grammar that does not compile fails on the first use rather than
# silently on some later one.

_METAMODEL = None


def metamodel():
    """The textX metamodel of the Candidate Profile Language."""

    global _METAMODEL

    if _METAMODEL is None:
        _METAMODEL = metamodel_from_file(GRAMMAR_PATH)

    return _METAMODEL


def validate(source):
    """
    Parse a candidate profile and return the model textX built.

        >>> model = validate('candidate { personal { name: "Ana Torres" '
        ...                  'email: ana@example.com } skills { skill: GIT } }')
        >>> model.personal.name
        'Ana Torres'
        >>> [skill.symbol for skill in model.skills.skills]
        ['GIT']

    Raises InvalidProfile when the text is not a sentence of the language.
    """

    try:
        return metamodel().model_from_str(source)

    except TextXError as error:
        raise InvalidProfile(
            message=_message_of(error),
            line=getattr(error, "line", None),
            column=getattr(error, "col", None),
            source=source,
        ) from error


def validate_file(path):
    """
    Parse a candidate profile stored in a file, such as the fixtures in
    examples/. The file is read as UTF-8 and handed to validate(), so a profile
    on disk and a profile in memory follow exactly the same path.
    """

    with open(path, encoding="utf-8") as handle:
        return validate(handle.read())


def is_valid(source):
    """
    True when the profile parses, for callers that only want the answer.

    Anything that has to report what went wrong should call validate() and
    catch InvalidProfile instead, since this function discards the reason.
    """

    try:
        validate(source)

    except InvalidProfile:
        return False

    return True


def _message_of(error):
    """
    The part of a TextXError worth showing.

    textX prefixes its message with the position it already reports in its own
    attributes, for example "None:4:16: Expected EMAIL => ...". The prefix is
    dropped here so that InvalidProfile.__str__ can format the position once,
    and so that a caller that only wants the explanation does not have to strip
    it itself.
    """

    message = str(error)

    marker = ": "

    if message.startswith("None:") and marker in message:
        return message.split(marker, 1)[1].strip()

    return message.strip()