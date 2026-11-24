\# SkillBridge AI



\### An AI-Powered Career Intelligence Platform



SkillBridge AI helps job seekers understand their professional strengths, identify skill gaps, evaluate job opportunities, and build personalized learning roadmaps to become better prepared for their target roles.



Instead of treating resume analysis, job matching, and learning as separate activities, SkillBridge AI brings them together into one career development platform.



\[GitHub Repository](https://github.com/alishbaikhlaq20/SkillBridge-AI)



\---



\## Overview



Finding the right job involves more than submitting a resume. Candidates need to understand what employers expect, recognize missing competencies, and develop the skills required to become competitive.



SkillBridge AI addresses this challenge through an integrated workflow that connects:



\- Resume analysis and skill extraction

\- Job description analysis

\- Resume-to-job compatibility scoring

\- Skill gap identification and prioritization

\- Personalized AI-generated learning plans

\- Weekly learning tasks and progress tracking

\- Evidence-based resume improvement suggestions



The platform combines deterministic matching logic with generative AI to provide structured and actionable career guidance.



\## Key Features



\### 1. Resume Analysis

\- Upload and analyze resumes.

\- Extract relevant professional information and technical skills.

\- Organize extracted information into structured sections.

\- Use resume information as the foundation for job matching and skill analysis.



\### 2. AI-Powered Job Analysis

\- Analyze job descriptions using Google Gemini.

\- Identify required skills and role expectations.

\- Extract structured information to support the matching process.



\### 3. Intelligent Job Matching

\- Compare candidate skills and resume information against job requirements.

\- Calculate a compatibility score using a weighted matching approach.

\- Highlight matching qualifications and areas requiring improvement.



\### 4. Skill Gap Identification

\- Identify skills required by a job that are missing from the candidate's profile.

\- Classify skill gaps according to priority.

\- Help candidates focus on the most important competencies first.



\### 5. Personalized Learning Roadmaps

\- Generate personalized learning plans based on identified skill gaps.

\- Prioritize high-impact skills.

\- Organize learning into manageable weekly tasks.

\- Track task completion and learning progress.



\### 6. Evidence-Based Resume Improvement

\- Suggest skills that users may be ready to add to their resumes based on completed learning activities.

\- Distinguish between learned, practiced, and demonstrated skills.

\- Allow users to review, edit, and select suggestions before adding them.

\- Keep approved additions separate from the original extracted resume skills.



\### 7. User Authentication

\- User registration and login.

\- Password hashing.

\- Token-based authentication.

\- Protected application functionality.



\---



\## Technology Stack



| Layer | Technologies |

|---|---|

| Frontend | Next.js, React, TypeScript |

| Styling | Tailwind CSS |

| Backend | Python, FastAPI |

| Database | PostgreSQL |

| ORM | SQLAlchemy |

| AI Integration | Google Gemini API |

| Validation | Pydantic |

| Authentication | Token-based authentication, Argon2 password hashing |

| Development Tools | Git, GitHub, VS Code |



\---



\## System Architecture



SkillBridge AI follows a frontend-backend architecture.



```mermaid

flowchart TD

&#x20;   A\[User] --> B\[Next.js Frontend]

&#x20;   B --> C\[FastAPI Backend]

&#x20;   C --> D\[Authentication]

&#x20;   C --> E\[Resume Analysis]

&#x20;   C --> F\[Job Analysis]

&#x20;   E --> G\[Skill Extraction]

&#x20;   F --> H\[Job Requirements]

&#x20;   G --> I\[Matching Engine]

&#x20;   H --> I

&#x20;   I --> J\[Skill Gap Analysis]

&#x20;   J --> K\[AI Learning Plan]

&#x20;   K --> L\[Weekly Tasks and Progress]

&#x20;   L --> M\[Resume Improvement Suggestions]

&#x20;   C --> N\[(PostgreSQL Database)]

&#x20;   F --> O\[Google Gemini API]

&#x20;   K --> O

```



\### How It Works



1\. A user registers and uploads their resume.

2\. The backend extracts and structures relevant resume information.

3\. The user provides job information for analysis.

4\. The matching engine evaluates compatibility between the candidate and the job.

5\. Missing skills are identified and prioritized.

6\. Google Gemini helps generate personalized learning plans.

7\. Users complete learning activities and track their progress.

8\. The platform provides evidence-based resume improvement suggestions.



\---



\## Project Structure



```text

SkillBridge-AI/

│

├── backend/

│   ├── routers/

│   │   └── learning\_plans.py

│   │

│   ├── services/

│   │   ├── gemini\_client.py

│   │   ├── job\_ai.py

│   │   ├── learning\_plan.py

│   │   ├── learning\_plan\_ai.py

│   │   ├── matching.py

│   │   ├── resume\_ai.py

│   │   └── skill\_gap.py

│   │

│   ├── auth.py

│   ├── database.py

│   ├── gemini\_client.py

│   ├── init\_db.py

│   ├── main.py

│   ├── models.py

│   ├── resume\_parser.py

│   ├── schemas.py

│   └── security.py

│

├── frontend/

│   ├── app/

│   │   ├── dashboard/

│   │   ├── job/

│   │   ├── learning-plan/

│   │   ├── login/

│   │   ├── match/

│   │   ├── profile/

│   │   ├── register/

│   │   ├── resume/

│   │   └── skill-gaps/

│   │

│   ├── lib/

│   │   └── api.ts

│   │

│   └── package.json

│

├── docs/

├── requirements.txt

└── .gitignore

```



\---



\## Getting Started



\### Prerequisites



Make sure you have the following installed:



\- Python 3.10 or later

\- Node.js and npm

\- PostgreSQL

\- Google Gemini API key

\- Git



\### 1. Clone the Repository



```bash

git clone https://github.com/alishbaikhlaq20/SkillBridge-AI.git

cd SkillBridge-AI

```



\### 2. Configure the Backend



Create and activate a virtual environment:



\*\*Windows PowerShell\*\*



```powershell

cd backend

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



Install the backend dependencies required by the application:



```bash

pip install fastapi uvicorn sqlalchemy "psycopg\[binary]" python-dotenv google-genai pydantic "pwdlib\[argon2]" python-multipart

```



Create a PostgreSQL database named:



```text

skillbridge\_ai

```



Create a `backend/.env` file:



```env

DATABASE\_URL=postgresql+psycopg://YOUR\_USERNAME:YOUR\_PASSWORD@localhost:5432/skillbridge\_ai

GEMINI\_API\_KEY=YOUR\_GEMINI\_API\_KEY

```



Replace the placeholder values with your local configuration. Never commit real credentials or API keys.



Initialize the database tables:



```bash

python init\_db.py

```



Start the backend:



```bash

uvicorn main:app --reload

```



The backend should be available at:



```text

http://127.0.0.1:8000

```



Interactive API documentation:



```text

http://127.0.0.1:8000/docs

```



\### 3. Configure the Frontend



Open a second terminal:



```bash

cd frontend

npm install

```



Create a `frontend/.env.local` file:



```env

NEXT\_PUBLIC\_API\_URL=http://127.0.0.1:8000

```



Start the development server:



```bash

npm run dev

```



Open the application:



```text

http://localhost:3000

```



\---



\## Testing



The backend includes tests covering important application areas, including:



\- Authentication and token verification

\- Database functionality

\- Resume analysis

\- Job analysis

\- Matching logic

\- Skill gap identification

\- Learning plan logic and API functionality

\- Security-related functionality



Run the backend test suite from the backend directory:



```bash

pytest

```



\---



\## Security and Configuration



\- API keys and database credentials must be stored in environment variables.

\- Environment files are excluded from version control.

\- Uploaded resumes and local database files should not be committed.

\- Passwords are hashed rather than stored as plain text.

\- Protected API functionality requires authentication.



Users should review AI-generated recommendations before relying on them or adding suggested skills to a professional resume.



\---



\## Current Development Status



SkillBridge AI is an actively developed project. Its core workflows include resume analysis, job matching, skill gap prioritization, personalized learning plans, progress tracking, and resume improvement suggestions.



Further work includes improving deployment readiness, refining documentation, expanding automated testing, and enhancing the overall user experience.



\## Future Enhancements



\- Production deployment and cloud hosting

\- More advanced resume evaluation

\- Expanded job recommendation capabilities

\- Additional learning resource integrations

\- Improved analytics and career progress visualization

\- Expanded test coverage and CI/CD automation



\---



\## Author



\*\*Alishba Ikhlaq\*\*



Software Engineering | Full-Stack Development | AI-Powered Applications



\- GitHub: \[@alishbaikhlaq20](https://github.com/alishbaikhlaq20)



\---



\*SkillBridge AI — Bridging the gap between your current skills and your next career opportunity.\*

