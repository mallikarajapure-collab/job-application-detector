import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = BASE_DIR / "job_applications.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_processed_emails_table():

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_emails (
            gmail_message_id TEXT PRIMARY KEY,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def is_email_processed(gmail_message_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT gmail_message_id
        FROM processed_emails
        WHERE gmail_message_id = ?
        """,
        (gmail_message_id,)
    ).fetchone()

    connection.close()

    return row is not None


def mark_email_processed(gmail_message_id):

    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO processed_emails (
            gmail_message_id
        )
        VALUES (?)
        """,
        (gmail_message_id,)
    )

    connection.commit()
    connection.close()