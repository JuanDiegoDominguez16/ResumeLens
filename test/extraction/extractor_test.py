from src.extraction.extractor import (
    extract_name,
    extract_resume,
)


def test_normal_name():
    text = "Wednesday Addams"

    result = extract_name(text)

    assert result == "Wednesday Addams"


def test_hispanic_name_with_particles():
    text = "Ana María de la Torre"

    result = extract_name(text)

    assert result == "Ana María de la Torre"


def test_hyphenated_surname():
    text = "José Rodríguez-López"

    result = extract_name(text)

    assert result == "José Rodríguez-López"


def test_skip_resume_header():
    text = """Curriculum Vitae
Ana María de la Torre"""

    result = extract_name(text)

    assert result == "Ana María de la Torre"


def test_degree_does_not_cross_lines():
    text = """Bachelor of Science
Technical Skills"""

    result = extract_resume(text)

    degrees = result["Academic Qualifications"]

    assert len(degrees) == 1
    assert degrees[0].text == "Bachelor of Science"


def test_master_chef_is_not_degree():
    text = "Master Chef"

    result = extract_resume(text)

    degrees = result["Academic Qualifications"]

    assert degrees == []


def test_bachelors_degree():
    text = "Bachelor's degree in Computer Science"

    result = extract_resume(text)

    degrees = result["Academic Qualifications"]

    assert len(degrees) == 1
    assert degrees[0].text == "Bachelor's degree in Computer Science"


def test_degree_stops_before_university():
    text = """B.Sc. in Computer Science
Universidad Icesi"""

    result = extract_resume(text)

    degrees = result["Academic Qualifications"]

    assert len(degrees) == 1
    assert degrees[0].text == "B.Sc. in Computer Science"


def test_experience():
    text = "3 years of professional experience"

    result = extract_resume(text)

    experience = result["Professional Experience"]["years"]

    assert len(experience) == 1
    assert experience[0].text == "3 years of professional experience"


def test_experience_does_not_cross_lines():
    text = """3 years
of experience"""

    result = extract_resume(text)

    experience = result["Professional Experience"]["years"]

    assert experience == []


def test_date_range():
    text = "2020-2024"

    result = extract_resume(text)

    dates = result["Professional Experience"]["date_ranges"]

    assert len(dates) == 1
    assert dates[0].text == "2020-2024"


def test_date_ranges_are_not_phones():
    text = "2015-2019 2020-2024"

    result = extract_resume(text)

    phones = result["Contact Information"]["phone"]
    dates = result["Professional Experience"]["date_ranges"]

    assert phones == []
    assert len(dates) == 2


def test_phone():
    text = "+57 300 123 4567"

    result = extract_resume(text)

    phones = result["Contact Information"]["phone"]

    assert len(phones) == 1
    assert phones[0].text == "+57 300 123 4567"


def test_phone_does_not_cross_lines():
    text = """300
123 4567"""

    result = extract_resume(text)

    phones = result["Contact Information"]["phone"]

    assert phones == []


def test_original_project_example():
    text = """Wednesday Addams
3 years of experience developing web applications.

Technical Skills:
JS, React.js, NodeJS, Postgres, Git."""

    result = extract_resume(text)

    assert result["Candidate"]["name"] == "Wednesday Addams"

    assert [
        finding.text
        for finding in result["Programming Languages"]
    ] == ["JS"]

    assert [
        finding.text
        for finding in result["Frameworks and Libraries"]
    ] == ["React.js", "NodeJS"]

    assert [
        finding.text
        for finding in result["Databases"]
    ] == ["Postgres"]

    assert [
        finding.text
        for finding in result["Tools and Technologies"]
    ] == ["Git"]