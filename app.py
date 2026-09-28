import re
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from flask import Flask, request, send_from_directory, abort

app = Flask(__name__)


DATABASE_PATH = Path(app.instance_path) / "zef-beauty.sqlite3"


@app.cli.command("init-db")
def init_db_command():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS enquiries (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT NOT NULL,
                    service TEXT NOT NULL
                        CHECK (service IN ('hair', 'makeup', 'bridal')),
                    preferred_date TEXT,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    print("Enquiry database is ready.")


def save_enquiry(enquiry):
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO enquiries (
                    customer_name,
                    customer_email,
                    service,
                    preferred_date,
                    message
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    enquiry["customerName"],
                    enquiry["customerEmail"],
                    enquiry["serviceSelect"],
                    enquiry["preferredDate"] or None,
                    enquiry["message"]
                )
            )

            enquiry_id = cursor.lastrowid

    return enquiry_id


WEBSITE_DIRECTORY = Path(__file__).resolve().parent


@app.get("/")
def homepage():
    return send_from_directory(WEBSITE_DIRECTORY, "index.html")


@app.get("/<filename>")
def website_file(filename):
    allowed_files = {"index.html", "style.css", "script.js"}

    if filename not in allowed_files:
        abort(404)

    return send_from_directory(WEBSITE_DIRECTORY, filename)


@app.get("/images/<path:filename>")
def website_image(filename):
    return send_from_directory(
        WEBSITE_DIRECTORY / "images",
        filename
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Zef Beauty API is running"
    }


@app.post("/api/enquiries")
def create_enquiry():
    if not request.is_json:
        return {"error": "Please send the enquiry as JSON."}, 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Please send a valid JSON object."}, 400

    errors = {}
    enquiry = {}

    # Read each field, check its type and remove surrounding spaces.
    field_limits = {
        "customerName": 100,
        "customerEmail": 254,
        "serviceSelect": 20,
        "preferredDate": 10,
        "message": 2000
    }

    for field, limit in field_limits.items():
        value = data.get(field, "")

        if not isinstance(value, str):
            errors[field] = "Please enter a text value."
            enquiry[field] = ""
            continue

        enquiry[field] = value.strip()

        if len(enquiry[field]) > limit:
            errors[field] = f"Please use no more than {limit} characters."

    # Required fields.
    required_fields = {
        "customerName": "Please enter your name.",
        "customerEmail": "Please enter your email.",
        "serviceSelect": "Please choose a service."
    }

    for field, error_message in required_fields.items():
        if not enquiry[field] and field not in errors:
            errors[field] = error_message

    # Basic email format check.
    email = enquiry["customerEmail"]

    if email and "customerEmail" not in errors:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            errors["customerEmail"] = "Please enter a valid email address."

    # Only accept services offered by the business.
    allowed_services = {"hair", "makeup", "bridal"}
    service = enquiry["serviceSelect"]

    if service and service not in allowed_services:
        errors["serviceSelect"] = "Please choose hair, makeup or bridal."

    # The date is optional, but must be valid when provided.
    preferred_date = enquiry["preferredDate"]

    if preferred_date and "preferredDate" not in errors:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", preferred_date):
                raise ValueError

            selected_date = date.fromisoformat(preferred_date)

            if selected_date < date.today():
                errors["preferredDate"] = "Please choose today or a future date."

        except ValueError:
            errors["preferredDate"] = "Please enter a valid date as YYYY-MM-DD."

    if errors:
        return {
            "error": "Please check the highlighted fields.",
            "fields": errors
        }, 400

    try:
        enquiry_id = save_enquiry(enquiry)

    except sqlite3.Error:
        app.logger.exception("Could not save enquiry.")

        return {
            "error": "We couldn't save your enquiry. Please try again."
        }, 500

    return {
        "message": "Thank you. Your enquiry has been saved.",
        "saved": True,
        "enquiryId": enquiry_id
    }, 201