from pathlib import Path
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Project root
BASE_DIR = Path(__file__).resolve().parents[3]

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = None

    # Use existing login token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # Login / refresh if required
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json was not found in the project root."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8"
        )

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service


def decode_message_part(part):
    """
    Decode a Gmail message body part.
    """
    data = part.get("body", {}).get("data")

    if not data:
        return ""

    try:
        decoded = base64.urlsafe_b64decode(data).decode(
            "utf-8",
            errors="ignore"
        )
        return decoded
    except Exception:
        return ""


def extract_message_body(payload):
    """
    Extract plain text body from Gmail message payload.
    """

    # Simple message
    if payload.get("body", {}).get("data"):
        return decode_message_part(payload)

    # Multipart message
    parts = payload.get("parts", [])

    for part in parts:

        if part.get("mimeType") == "text/plain":
            body = decode_message_part(part)

            if body:
                return body

        # Nested multipart
        if part.get("parts"):
            body = extract_message_body(part)

            if body:
                return body

    return ""


def get_recent_emails(max_results=10):
    """
    Fetch recent emails from Gmail.
    """

    service = get_gmail_service()

    response = service.users().messages().list(
        userId="me",
        q="newer_than:30d",
        maxResults=max_results
    ).execute()

    messages = response.get("messages", [])

    emails = []

    for message in messages:

        message_id = message["id"]

        email_data = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        payload = email_data.get("payload", {})

        headers = payload.get("headers", [])

        subject = ""
        sender = ""
        date = ""

        for header in headers:

            name = header.get("name", "").lower()
            value = header.get("value", "")

            if name == "subject":
                subject = value

            elif name == "from":
                sender = value

            elif name == "date":
                date = value

        body = extract_message_body(payload)

        emails.append({
            "id": message_id,
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body
        })

    return emails