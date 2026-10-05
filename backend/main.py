from pathlib import Path
import json
import re
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import get_connection
from backend.app.services.gemini_service import analyze_job_email, GeminiQuotaError
from backend.app.services.gmail_service import get_recent_emails


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Job Application Tracker",
    description="AI-powered job application detection and tracking system"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATUS CONFIGURATION
# ============================================================

STATUS_ORDER = {
    "Applied": 1,
    "Under Review": 2,
    "Assessment": 3,
    "Interview": 4,
    "Selected": 5,
    "Rejected": 5,
}

ALLOWED_STATUSES = [
    "Applied",
    "Under Review",
    "Assessment",
    "Interview",
    "Selected",
    "Rejected",
]


# ============================================================
# PYDANTIC MODELS
# ============================================================

class EmailPayload(BaseModel):
    subject: str
    body: str


class ApplicationUpdate(BaseModel):
    company: str | None = None
    job_role: str | None = None
    job_id: str | None = None
    status: str | None = None
    location: str | None = None
    application_date: str | None = None


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            job_role TEXT,
            job_id TEXT,
            status TEXT,
            location TEXT,
            application_date TEXT
        )
        """
    )

    conn.commit()
    conn.close()


initialize_database()


# ============================================================
# HELPERS
# ============================================================

def extract_json_from_gemini(response_text):

    if not response_text:
        raise ValueError("Gemini returned an empty response.")

    text = response_text.strip()

    # Remove markdown JSON fences
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        match = re.search(
            r"\{.*\}",
            text,
            flags=re.DOTALL
        )

        if not match:
            raise ValueError(
                "Could not extract JSON from Gemini response."
            )

        return json.loads(match.group(0))


def normalize_status(status):

    if not status:
        return "Applied"

    status_text = str(status).strip().lower()

    mapping = {
        "applied": "Applied",
        "under review": "Under Review",
        "review": "Under Review",
        "assessment": "Assessment",
        "interview": "Interview",
        "selected": "Selected",
        "hired": "Selected",
        "offer": "Selected",
        "rejected": "Rejected",
        "reject": "Rejected",
    }

    return mapping.get(
        status_text,
        "Applied"
    )


def normalize_application_date(value):

    if not value:
        return datetime.now().strftime("%Y-%m-%d")

    value = str(value).strip()

    if not value:
        return datetime.now().strftime("%Y-%m-%d")

    return value


def application_dict(row):

    return {
        "id": row["id"],
        "company": row["company"],
        "job_role": row["job_role"],
        "job_id": row["job_id"],
        "status": row["status"],
        "location": row["location"],
        "application_date": row["application_date"],
    }


def find_existing(company, job_role, job_id):

    conn = get_connection()
    cursor = conn.cursor()

    # First check by Job ID when available
    if job_id:

        cursor.execute(
            """
            SELECT *
            FROM applications
            WHERE job_id = ?
            LIMIT 1
            """,
            (job_id,)
        )

        row = cursor.fetchone()

        if row:
            conn.close()
            return row

    # Then check company + role
    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE LOWER(COALESCE(company, '')) = LOWER(?)
        AND LOWER(COALESCE(job_role, '')) = LOWER(?)
        LIMIT 1
        """,
        (
            company or "",
            job_role or "",
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row


def update_application(
    application_id,
    company,
    job_role,
    job_id,
    status,
    location,
    application_date
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE applications
        SET
            company = ?,
            job_role = ?,
            job_id = ?,
            status = ?,
            location = ?,
            application_date = ?
        WHERE id = ?
        """,
        (
            company,
            job_role,
            job_id,
            status,
            location,
            application_date,
            application_id,
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Job Application Tracker API is running."
    }


# ============================================================
# DETECT APPLICATION
# ============================================================

@app.post("/detect")
def detect_application(payload: EmailPayload):

    try:
        gemini_response = analyze_job_email(
            payload.subject,
            payload.body
        )

        result = extract_json_from_gemini(
            gemini_response
        )

    except GeminiQuotaError:

        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini daily quota is exhausted. "
                "Please retry after the quota resets."
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {error}"
        )

    if not result.get("is_job_related", False):

        return {
            "is_job_related": False,
            "message": "This does not appear to be a job application email."
        }

    company = (
        result.get("company")
        or "Unknown"
    )

    job_role = (
        result.get("job_role")
        or "Unknown"
    )

    job_id = result.get("job_id")

    status = normalize_status(
        result.get("status")
    )

    location = (
        result.get("location")
        or "Unknown"
    )

    application_date = normalize_application_date(
        result.get("application_date")
    )

    existing = find_existing(
        company,
        job_role,
        job_id
    )

    if existing:

        existing_status = existing["status"] or "Applied"

        current_rank = STATUS_ORDER.get(
            existing_status,
            0
        )

        new_rank = STATUS_ORDER.get(
            status,
            0
        )

        if new_rank > current_rank:

            update_application(
                existing["id"],
                company,
                job_role,
                job_id,
                status,
                location,
                application_date
            )

            return {
                "is_job_related": True,
                "action": "status_updated",
                "application": {
                    "id": existing["id"],
                    "company": company,
                    "job_role": job_role,
                    "job_id": job_id,
                    "status": status,
                    "location": location,
                    "application_date": application_date,
                }
            }

        return {
            "is_job_related": True,
            "action": "duplicate",
            "application": application_dict(existing)
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO applications
        (
            company,
            job_role,
            job_id,
            status,
            location,
            application_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            company,
            job_role,
            job_id,
            status,
            location,
            application_date,
        )
    )

    application_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "is_job_related": True,
        "action": "saved",
        "application": {
            "id": application_id,
            "company": company,
            "job_role": job_role,
            "job_id": job_id,
            "status": status,
            "location": location,
            "application_date": application_date,
        }
    }

@app.post("/sync-gmail")
def sync_gmail():

    try:

        emails = get_recent_emails(10)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Gmail fetching failed: {error}"
        )

    processed = 0
    job_related = 0
    saved = 0
    duplicates = 0
    status_updates = 0
    ignored = 0

    results = []

    job_keywords = [
        "application",
        "applied",
        "job",
        "career",
        "careers",
        "interview",
        "assessment",
        "recruitment",
        "recruiter",
        "hiring",
        "hired",
        "selection",
        "selected",
        "shortlisted",
        "shortlist",
        "offer",
        "position",
        "candidate",
        "employment",
        "role",
    ]

    candidate_emails = []

    # --------------------------------------------------------
    # SUBJECT FILTER
    # --------------------------------------------------------

    for email in emails:

        subject = email.get("subject") or ""

        subject_lower = subject.lower()

        if any(
            keyword in subject_lower
            for keyword in job_keywords
        ):

            candidate_emails.append(email)

        else:

            ignored += 1

            results.append({
                "email_subject": subject,
                "action": "ignored_by_subject_filter"
            })

    # Maximum three Gemini attempts
    candidate_emails = candidate_emails[:3]

    # --------------------------------------------------------
    # PROCESS EMAILS
    # --------------------------------------------------------

    for email in candidate_emails:

        processed += 1

        subject = email.get(
            "subject",
            ""
        )

        body = email.get(
            "body",
            ""
        )

        try:

            # ------------------------------------------------
            # GEMINI
            # ------------------------------------------------

            gemini_response = analyze_job_email(
                subject,
                body
            )

            ai_result = extract_json_from_gemini(
                gemini_response
            )

            if not ai_result.get(
                "is_job_related",
                False
            ):

                ignored += 1

                results.append({
                    "email_subject": subject,
                    "action": "ignored_by_ai"
                })

                continue

            company = (
                ai_result.get("company")
                or "Unknown"
            )

            job_role = (
                ai_result.get("job_role")
                or "Unknown"
            )

            job_id = ai_result.get(
                "job_id"
            )

            status = normalize_status(
                ai_result.get("status")
            )

            location = (
                ai_result.get("location")
                or "Unknown"
            )

            application_date = (
                normalize_application_date(
                    ai_result.get(
                        "application_date"
                    )
                )
            )

            job_related += 1

            action_source = "gemini"

        except Exception as error:

            error_text = str(error)

            # ------------------------------------------------
            # GEMINI QUOTA FALLBACK
            # ------------------------------------------------

            if (
                "429" not in error_text
                and "RESOURCE_EXHAUSTED" not in error_text
            ):

                results.append({
                    "email_subject": subject,
                    "action": "error",
                    "error": error_text
                })

                continue

            # ------------------------------------------------
            # RULE-BASED FALLBACK
            # ------------------------------------------------

            subject_lower = subject.lower()

            company = "Unknown"
            job_role = "Unknown"
            status = "Applied"
            job_id = None
            location = "Unknown"

            if (
                "l'oréal" in subject_lower
                or "l’oréal" in subject_lower
                or "loreal" in subject_lower
            ):

                company = "L'Oréal"

            elif "dataannotation" in subject_lower:

                company = "DataAnnotation"

            if "platform engineer" in subject_lower:

                job_role = (
                    "Platform Engineer - AI Trainer"
                )

            if (
                "shortlisted" in subject_lower
                or "shortlist" in subject_lower
            ):

                status = "Under Review"

            elif "interview" in subject_lower:

                status = "Interview"

            elif "assessment" in subject_lower:

                status = "Assessment"

            elif (
                "rejected" in subject_lower
                or "regret" in subject_lower
            ):

                status = "Rejected"

            elif (
                "selected" in subject_lower
                or "offer" in subject_lower
            ):

                status = "Selected"

            application_date = (
                normalize_application_date(None)
            )

            job_related += 1

            action_source = "fallback"

        # ----------------------------------------------------
        # CHECK DUPLICATE
        # ----------------------------------------------------

        existing = find_existing(
            company,
            job_role,
            job_id
        )

        # ----------------------------------------------------
        # NEW APPLICATION
        # ----------------------------------------------------

        if existing is None:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO applications
                (
                    company,
                    job_role,
                    job_id,
                    status,
                    location,
                    application_date
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    job_role,
                    job_id,
                    status,
                    location,
                    application_date,
                )
            )

            application_id = cursor.lastrowid

            conn.commit()
            conn.close()

            saved += 1

            results.append({
                "email_subject": subject,
                "company": company,
                "job_role": job_role,
                "status": status,
                "action": "saved",
                "source": action_source,
                "application_id": application_id,
            })

        # ----------------------------------------------------
        # EXISTING APPLICATION
        # ----------------------------------------------------

        else:

            existing_status = (
                existing["status"]
                or "Applied"
            )

            current_rank = STATUS_ORDER.get(
                existing_status,
                0
            )

            new_rank = STATUS_ORDER.get(
                status,
                0
            )

            # Only move forward
            if new_rank > current_rank:

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE applications
                    SET status = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        existing["id"],
                    )
                )

                conn.commit()
                conn.close()

                status_updates += 1

                results.append({
                    "email_subject": subject,
                    "company": company,
                    "job_role": job_role,
                    "old_status": existing_status,
                    "new_status": status,
                    "action": "status_updated",
                    "source": action_source,
                    "application_id": existing["id"],
                })

            else:

                duplicates += 1

                results.append({
                    "email_subject": subject,
                    "company": company,
                    "job_role": job_role,
                    "status": existing_status,
                    "action": "duplicate",
                    "source": action_source,
                    "application_id": existing["id"],
                })

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Gmail sync completed",
        "processed": processed,
        "job_related": job_related,
        "saved": saved,
        "duplicates": duplicates,
        "status_updates": status_updates,
        "ignored": ignored,
        "saved_applications": [
            result
            for result in results
            if result.get("action") == "saved"
        ],
        "results": results,
    }


# ============================================================
# GET ALL APPLICATIONS
# ============================================================

@app.get("/applications")
def get_applications():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            company,
            job_role,
            job_id,
            status,
            location,
            application_date
        FROM applications
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        application_dict(row)
        for row in rows
    ]


# ============================================================
# EDIT APPLICATION
# ============================================================

@app.put("/applications/{application_id}")
def edit_application(
    application_id: int,
    application: ApplicationUpdate
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE id = ?
        """,
        (application_id,)
    )

    existing = cursor.fetchone()

    if not existing:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    company = (
        application.company
        if application.company is not None
        else existing["company"]
    )

    job_role = (
        application.job_role
        if application.job_role is not None
        else existing["job_role"]
    )

    job_id = (
        application.job_id
        if application.job_id is not None
        else existing["job_id"]
    )

    status = (
        normalize_status(application.status)
        if application.status is not None
        else existing["status"]
    )

    location = (
        application.location
        if application.location is not None
        else existing["location"]
    )

    application_date = (
        application.application_date
        if application.application_date is not None
        else existing["application_date"]
    )

    # ========================================================
    # STATUS BACKWARD PROTECTION
    # ========================================================

    existing_status = existing["status"] or "Applied"

    current_rank = STATUS_ORDER.get(
        existing_status,
        0
    )

    new_rank = STATUS_ORDER.get(
        status,
        0
    )

    if new_rank < current_rank:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail=(
                f"Status cannot move backward from "
                f"'{existing_status}' to '{status}'."
            )
        )

    # ========================================================
    # UPDATE
    # ========================================================

    cursor.execute(
        """
        UPDATE applications
        SET
            company = ?,
            job_role = ?,
            job_id = ?,
            status = ?,
            location = ?,
            application_date = ?
        WHERE id = ?
        """,
        (
            company,
            job_role,
            job_id,
            status,
            location,
            application_date,
            application_id,
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE id = ?
        """,
        (application_id,)
    )

    updated = cursor.fetchone()

    conn.close()

    return {
        "message": "Application updated successfully.",
        "application": application_dict(updated),
    }


# ============================================================
# DELETE APPLICATION
# ============================================================

@app.delete("/applications/{application_id}")
def delete_application(application_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE id = ?
        """,
        (application_id,)
    )

    existing = cursor.fetchone()

    if not existing:

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    cursor.execute(
        """
        DELETE FROM applications
        WHERE id = ?
        """,
        (application_id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Application deleted successfully.",
        "application_id": application_id,
    }