import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from services.job_ai import StructuredJob, build_prompt

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30_000),  # milliseconds
)

SAMPLE_JOB = """
Backend Developer at Acme Corp.
Required: 2+ years of Python, FastAPI, PostgreSQL.
Nice to have: Docker.
Education: BSc in Computer Science.
Responsibilities: build and maintain REST APIs.
"""

for model in ["gemini-3.8-flash", "gemini-3.5-flash-lite"]:
    start = time.time()
    try:
        response = client.models.generate_content(
            model=model,
            contents=build_prompt(SAMPLE_JOB),
            config={
                "response_mime_type": "application/json",
                "response_schema": StructuredJob,
            },
        )
        job = StructuredJob.model_validate_json(response.text)
        print(f"{model}: OK in {time.time() - start:.1f}s")
        print("   title:", job.job_title, "| required:", job.required_skills)
    except errors.APIError as e:
        print(f"{model}: API ERROR {type(e).__name__} code={e.code} "
              f"after {time.time() - start:.1f}s")
        print("   ", str(e)[:200])
    except Exception as e:
        print(f"{model}: {type(e).__name__} after {time.time() - start:.1f}s")
        print("   ", str(e)[:200])