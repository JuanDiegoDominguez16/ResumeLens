"""
Stage 1, resume information extraction.

Formal model: regular expressions, docs/formalization.md section 2.

The extractor recognizes textual representations that may correspond to
qualifications or candidate data. It reports what the resume literally says,
with the position of every match, and it does not canonicalize: "React.js"
stays "React.js" and "JS" stays "JS". Mapping those representations to
canonical symbols is Stage 2.

Public entry points, see extractor.py:

    extract_resume(resume_text)          complete structured extraction
    qualification_strings(resume_text)   the input to Stage 2
    to_serializable(structure)           JSON-ready form of the result
"""
