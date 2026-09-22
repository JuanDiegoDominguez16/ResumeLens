import re

from streamlit import text 

def extract_skills(text):
    pattern = r"(?i)(?:skills|habilidades)\s*:\s*(.*)"
    match = re.search(pattern, text)

    if not match:
        return []

    skills_text = match.group(1)
    return[skill.strip() for skill in skills_text.split(",") if skill.strip()]