from services.resume_ai import extract_resume_with_ai


sample_resume = """
ALISHBA IKHLAQ

BS Software Engineering
Usman Institute of Technology, Karachi
CGPA: 3.03
Expected Graduation: 2027

SKILLS
Python, Java, JavaScript, SQL, Git, Flask, Django, C++

EXPERIENCE

Electronic Arts
Remote Internship
June 2025 - July 2025

- Proposed a new feature for EA Sports College Football.
- Designed class diagrams.
- Created C++ header files.
- Improved data structures.

Walmart Global Tech
Remote Internship
January 2025 - February 2025

- Built a custom heap data structure in Java.
- Designed UML class diagrams.
- Created ERDs for databases.
"""


result = extract_resume_with_ai(sample_resume)

print("\nSTRUCTURED RESUME\n")
print(result.model_dump_json(indent=2))