import re
import pdfplumber


def extract_resume_data(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        resume_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    def _extract_section(pattern):
        match = re.search(pattern, resume_text, re.DOTALL)
        return [line.strip() for line in match.group(1).split("\n") if line.strip()] if match else []

    return {
        "name": resume_text.split("\n")[0].strip(),
        "email": (re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", resume_text) or
                  re.search(r"\b\w+@\w+\.\w+(?:\.\w+)?\b", resume_text)).group(0),
        "phone": re.search(r"\+?\d{10,15}", resume_text).group(0),
        "skills": _extract_section(r"Skills(.*?)(?:Experience|Education|Projects|$)"),
        "education": _extract_section(r"Education(.*?)(?:Experience|Projects|$)"),
        "experience": _extract_section(r"Experience(.*?)(?:Education|Skills|Projects|$)")
    }
