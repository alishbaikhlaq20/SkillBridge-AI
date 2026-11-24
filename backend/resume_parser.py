import re


SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node.js",
    "html",
    "css",
    "tailwind",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "oracle",
    "git",
    "github",
    "docker",
    "fastapi",
    "flask",
    "django",
    "c++",
    "c#",
    "machine learning",
    "deep learning",
    "data analysis",
    "power bi",
    "excel",
]


def extract_sections(text: str):
    sections = {
        "skills": "",
        "education": "",
        "experience": "",
        "projects": "",
        "certifications": "",
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    current_section = None

    section_names = {
        "skills": [
            "skills",
            "technical skills",
            "core skills",
            "technical competencies",
        ],
        "education": [
            "education",
            "academic background",
            "academic qualifications",
        ],
        "experience": [
            "experience",
            "work experience",
            "professional experience",
            "employment",
        ],
        "projects": [
            "projects",
            "academic projects",
            "personal projects",
        ],
        "certifications": [
            "certifications",
            "certificates",
        ],
    }

    for line in lines:
        normalized = line.lower().strip(" :-")

        detected_section = None

        for section, names in section_names.items():
            if normalized in names:
                detected_section = section
                break

        if detected_section:
            current_section = detected_section
            continue

        if current_section:
            sections[current_section] += line + "\n"

    return sections


def extract_skills(text: str):
    text_lower = text.lower()

    found_skills = []

    for skill in SKILL_KEYWORDS:
        pattern = (
            r"(?<!\w)"
            + re.escape(skill.lower())
            + r"(?!\w)"
        )

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


def parse_resume(text: str):
    sections = extract_sections(text)

    skills = extract_skills(
        sections["skills"]
        if sections["skills"]
        else text
    )

    return {
        "sections": sections,
        "skills": skills,
        "education": sections["education"],
        "experience": sections["experience"],
        "projects": sections["projects"],
        "certifications": sections["certifications"],
    }