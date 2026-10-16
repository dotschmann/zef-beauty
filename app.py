import os
import re
import sqlite3
import secrets
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
import hmac
from time import time

from flask import (
    Flask,
    request,
    send_from_directory,
    abort,
    render_template,
    redirect,
    url_for,
    session,
)
from werkzeug.security import check_password_hash

load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("ZEF_SECRET_KEY"),
    ADMIN_PASSWORD_HASH=os.environ.get("ZEF_ADMIN_PASSWORD_HASH"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.environ.get("ZEF_COOKIE_SECURE", "false").lower() == "true"
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=False,
)

DATABASE_PATH = Path(app.instance_path) / "zef-beauty.sqlite3"

LOGIN_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60

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

            connection.execute("""
                CREATE TABLE IF NOT EXISTS login_rate_limits (
                    client_key TEXT PRIMARY KEY NOT NULL,
                    attempt_count INTEGER NOT NULL
                        CHECK (attempt_count >= 0),
                    expires_at INTEGER NOT NULL
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_login_rate_limits_expires_at
                ON login_rate_limits (expires_at)
            """)

    print("Database tables are ready.")

# Admin authentication
def login_client_key():
    address = request.remote_addr or "unknown"

    return hmac.new(
        app.config["SECRET_KEY"].encode("utf-8"),
        f"admin-login:{address}".encode("utf-8"),
        "sha256",
    ).hexdigest()


def reserve_login_attempt(client_key):
    """Return 0 if allowed, otherwise seconds until another attempt."""

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            # Keep the check and counter update in one transaction.
            connection.execute("BEGIN IMMEDIATE")

            now = int(time())

            connection.execute(
                "DELETE FROM login_rate_limits WHERE expires_at <= ?",
                (now,),
            )

            row = connection.execute(
                """
                SELECT attempt_count, expires_at
                FROM login_rate_limits
                WHERE client_key = ?
                """,
                (client_key,),
            ).fetchone()

            if row is not None:
                attempt_count, expires_at = row

                if attempt_count >= LOGIN_LIMIT:
                    return max(1, expires_at - now)

                connection.execute(
                    """
                    UPDATE login_rate_limits
                    SET attempt_count = attempt_count + 1
                    WHERE client_key = ?
                    """,
                    (client_key,),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO login_rate_limits (
                        client_key, attempt_count, expires_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (client_key, 1, now + LOGIN_WINDOW_SECONDS),
                )

    return 0

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

# Admin authentication

def is_admin_request():
    return request.path == "/admin" or request.path.startswith("/admin/")


def admin_csrf_token():
    if "admin_csrf_token" not in session:
        session["admin_csrf_token"] = secrets.token_urlsafe(32)

    return session["admin_csrf_token"]


@app.before_request
def protect_admin_routes():
    if not is_admin_request():
        return

    # Keep admin access disabled if credentials are missing.
    if not (
        app.config["SECRET_KEY"]
        and app.config["ADMIN_PASSWORD_HASH"]
    ):
        abort(503, description="Admin access is not configured.")

    # Limit the size of admin form submissions.
    request.max_content_length = 16 * 1024

    # Every admin route except login requires authentication.
    if (
        request.endpoint != "admin_login"
        and session.get("admin_authenticated") is not True
    ):
        return redirect(url_for("admin_login"))

    # Check the form token on requests that change state.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected_token = session.get("admin_csrf_token", "")
        submitted_token = request.form.get("csrf_token", "")

        if not expected_token or not secrets.compare_digest(
            expected_token.encode("utf-8"),
            submitted_token.encode("utf-8"),
        ):
            abort(
                400,
                description="The form expired or is invalid. Reload and try again.",
            )


@app.after_request
def set_admin_response_headers(response):
    if is_admin_request():
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_authenticated") is True:
        return redirect(url_for("admin_home"))

    error = None
    status_code = 200

    if request.method == "POST":
        try:
            retry_after = reserve_login_attempt(login_client_key())
        except sqlite3.Error:
            app.logger.exception("Could not check the login attempt limit.")
            abort(503, description="Sign-in is temporarily unavailable.")

        if retry_after > 0:
            return render_template(
                "admin.html",
                authenticated=False,
                csrf_token=admin_csrf_token(),
                error=(
                    "Too many sign-in attempts. "
                    f"Please try again in {retry_after} seconds."
                ),
            ), 429, {"Retry-After": str(retry_after)}

        password = request.form.get("password", "")

        if (
            0 < len(password) <= 1024
            and check_password_hash(
                app.config["ADMIN_PASSWORD_HASH"],
                password,
            )
        ):
            session.clear()
            session.permanent = True
            session["admin_authenticated"] = True

            return redirect(url_for("admin_home"))

        error = "Incorrect password. Please try again."
        status_code = 401

    return render_template(
        "admin.html",
        authenticated=False,
        csrf_token=admin_csrf_token(),
        error=error,
    ), status_code


@app.get("/admin")
def admin_home():
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        abort(400, description="Invalid page number.")

    if page < 1:
        abort(400, description="Invalid page number.")

    per_page = 20

    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            connection.row_factory = sqlite3.Row

            total = connection.execute(
                "SELECT COUNT(*) FROM enquiries"
            ).fetchone()[0]

            total_pages = max(1, (total + per_page - 1) // per_page)

            if page > total_pages:
                abort(404, description="This page does not exist.")

            enquiries = connection.execute(
                """
                SELECT
                    id,
                    customer_name,
                    customer_email,
                    service,
                    preferred_date,
                    message,
                    created_at
                FROM enquiries
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (per_page, (page - 1) * per_page),
            ).fetchall()

    except sqlite3.Error:
        app.logger.exception("Could not load admin enquiries.")
        abort(503, description="Enquiries are temporarily unavailable.")

    return render_template(
        "admin.html",
        authenticated=True,
        csrf_token=admin_csrf_token(),
        enquiries=enquiries,
        total=total,
        page=page,
        total_pages=total_pages,
        service_names={
            "hair": "Hair Styling",
            "makeup": "Makeup Artistry",
            "bridal": "Bridal Packages",
        },
    )


@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))