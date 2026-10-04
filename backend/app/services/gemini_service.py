import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from backend/.env")


client = genai.Client(api_key=GEMINI_API_KEY)


class GeminiQuotaError(Exception):
    """Raised when Gemini free-tier quota is exhausted."""
    pass


def analyze_job_email(subject, body):

    prompt = f"""
You are an intelligent job application email analyzer.

Analyze the email below.

Determine whether it is related to a job application.

If it is job-related, extract:
- company
- job_role
- job_id
- status
- location
- application_date

Allowed status values:
Applied
Under Review
Assessment
Interview
Selected
Rejected

Return ONLY valid JSON.

Use this format:

{{
    "is_job_related": true,
    "company": "",
    "job_role": "",
    "job_id": null,
    "status": "Applied",
    "location": "",
    "application_date": ""
}}

If the email is not job-related, return:

{{
    "is_job_related": false,
    "company": null,
    "job_role": null,
    "job_id": null,
    "status": null,
    "location": null,
    "application_date": null
}}

Email Subject:
{subject}

Email Body:
{body}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    except Exception as error:

        error_message = str(error)

        if (
            "RESOURCE_EXHAUSTED" in error_message
            or "429" in error_message
            or "quota" in error_message.lower()
        ):
            raise GeminiQuotaError(
                "Gemini daily quota has been exhausted."
            ) from error

        raise