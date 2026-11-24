"""
Manual test of the real job-analysis service (run from the backend folder):

    python test_job_ai.py

Shows which model answered, how long it took, and the structured result.
"""
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

from services.gemini_client import GeminiServiceError
from services.job_ai import analyze_job_with_ai

SAMPLE_JOB = """
Backend Developer at Acme Corp.
Required: 2+ years of Python, FastAPI, PostgreSQL.
Nice to have: Docker.
Education: BSc in Computer Science.
Responsibilities: build and maintain REST APIs.
"""

start = time.time()

try:
    job = analyze_job_with_ai(SAMPLE_JOB)
    print(f"\nSUCCESS in {time.time() - start:.1f}s")
    print(job.model_dump_json(indent=2))
except GeminiServiceError as e:
    print(f"\nGeminiServiceError after {time.time() - start:.1f}s")
    print("  status_code:", e.status_code)
    print("  message    :", e.message)
