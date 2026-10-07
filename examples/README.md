# Candidate Profile Examples

Profiles written in the Candidate Profile Language of `docs/formalization.md`
section 5. They are the fixtures of the Stage 4 scenarios listed in
`docs/test-cases.md` sections 8.1 and 8.2, and the samples the interface loads
to show validation of a profile that did not come from a résumé.

The extension is `.candidate`.

## `valid/`

Every file here must parse. Together they exercise each optional and repeated
element of the grammar, so that a change to the `.tx` that quietly makes a part
of the language mandatory fails on one of them.

| File | What it covers |
|---|---|
| `full_stack_accepted.candidate` | every section present, one `classification` |
| `two_profiles_accepted.candidate` | two `classification` elements, the Jane Smith case of section 5.6 |
| `several_records.candidate` | two `education` and two `experience` records, repetition |
| `minimal.candidate` | no `education`, no `experience`, no `phone`, no `classification` |
| `unclassified.candidate` | an empty `skills` block and zero `classification` elements |

`minimal.candidate` and `unclassified.candidate` are the two profiles that most
of the grammar is not required to produce: between them, every optional part of
`Candidate` is absent. A candidate whose résumé stated no recognized
qualification is a valid profile, not an error, which is the same decision
Stage 2 and Stage 3 record in `docs/normalization.md` section 6.3 and
`docs/classification.md` section 6.2.

## `invalid/`

Every file here must be rejected, and each one violates exactly one rule, so
the error message says which. A file that violated two rules would still be
rejected after the grammar stopped enforcing one of them.

| File | Rule violated |
|---|---|
| `missing_personal.candidate` | the `personal` block is required |
| `missing_email.candidate` | `email` is a required field of `personal` |
| `unquoted_string.candidate` | `name` is a `String`, which is quoted |
| `email_without_at.candidate` | `Email` requires `@` and a dot |
| `years_not_a_number.candidate` | `years` is a `Number` |
| `unbalanced_brace.candidate` | the closing brace of `candidate` is missing |
| `unknown_section.candidate` | `abilities` is not a section of the language |
| `raw_representation.candidate` | `React.js` and `NodeJS` are not canonical symbols |

The last one is the only rejection that is about the vocabulary rather than the
structure, and it is the one that matters most for the design: Stage 4 refuses
to represent a qualification that Stage 2 should have normalized. `Identifier`
cannot match `React.js`, because the dot is not a letter, a digit or an
underscore, so the rejection follows from the lexical rule of section 5.2 and
needs no extra check.