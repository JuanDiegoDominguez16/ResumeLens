"""
Shared fixtures for the Stage 2 tests.

The important one is `extractor_samples`, which enumerates every concrete
string the extraction patterns can produce. Several tests need to assert
something about all of them, and writing them out by hand would mean the list
drifts the moment someone adds a pattern to the extractor.
"""

import pytest

from src.extraction.extractor import TECH_VARIANTS, extract_qualifications


def expand_pattern(pattern):
    """
    Expand one of the extractor's patterns into every literal string it matches.

    The patterns in TECH_VARIANTS use only three constructs, so a full regex
    engine is not needed here:

        \\+  \\.     an escaped literal
        [- ]       a character class, one alternative per character
        s?         an optional character

        expand_pattern(r"scikit[- ]learn")  -> ["scikit-learn", "scikit learn"]
        expand_pattern(r"NoSQL databases?") -> ["NoSQL databases", "NoSQL database"]
        expand_pattern(r"C\\+\\+")            -> ["C++"]

    If a pattern ever uses something else, this expander will produce the wrong
    strings rather than fail loudly, which is why the tests that use it also
    check that the extractor really reproduces each sample.
    """

    alternatives = [[]]
    index = 0

    while index < len(pattern):
        character = pattern[index]

        if character == "\\":
            pieces, index = [pattern[index + 1]], index + 2

        elif character == "[":
            closing = pattern.index("]", index)
            pieces, index = list(pattern[index + 1:closing]), closing + 1

        else:
            pieces, index = [character], index + 1

        if index < len(pattern) and pattern[index] == "?":
            pieces, index = pieces + [""], index + 1

        alternatives = [
            prefix + [piece] for prefix in alternatives for piece in pieces
        ]

    return ["".join(alternative) for alternative in alternatives]


def _casings(text, case_sensitive):
    """
    The spellings a pattern accepts. A case sensitive pattern accepts only what
    it literally says; a case insensitive one accepts any casing, so the
    obvious few are tried.
    """

    if case_sensitive:
        return [text]

    return list(dict.fromkeys([text, text.lower(), text.upper(), text.title()]))


@pytest.fixture(scope="session")
def pattern_expansions():
    """
    Every (pattern, literal) pair the extractor's patterns expand to, before
    any casing is applied and without asking the extractor to confirm them.

    Offered as a fixture rather than as an import so the test files do not have
    to import conftest, which would need this directory to be a package and
    would put a module named `test` ahead of the standard library's.
    """

    return [
        (pattern, literal)
        for variants in TECH_VARIANTS.values()
        for pattern, _ in variants
        for literal in expand_pattern(pattern)
    ]


@pytest.fixture(scope="session")
def extractor_samples():
    """
    Every concrete representation the extractor can return, as a list of
    (category, sample) pairs.

    Only samples the extractor actually reproduces in full are included. A
    pattern whose expansion the extractor does not match back exactly would
    mean the expander above is wrong, and test_expander_agrees_with_extractor
    is what catches that.
    """

    samples = []

    for category, variants in TECH_VARIANTS.items():
        for pattern, case_sensitive in variants:
            for literal in expand_pattern(pattern):
                for sample in _casings(literal, case_sensitive):

                    found = extract_qualifications(sample)

                    if found and found[0].text == sample:
                        samples.append((category, sample))

    return samples
