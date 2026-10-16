import re

import pytest
from werkzeug.security import generate_password_hash

import app as app_module


# Used only by automated tests, never for the real admin account.
TEST_PASSWORD = "test-only-admin-password"


@pytest.fixture(scope="module")
def admin_password_hash():
    return generate_password_hash(TEST_PASSWORD)


@pytest.fixture
def admin_client(tmp_path, monkeypatch, admin_password_hash):
    # Redirect database operations to a temporary test database.
    monkeypatch.setattr(
        app_module,
        "DATABASE_PATH",
        tmp_path / "admin-test.sqlite3",
    )

    settings = {
        "TESTING": True,
        "SECRET_KEY": "test-only-session-secret",
        "ADMIN_PASSWORD_HASH": admin_password_hash,
        "SESSION_COOKIE_SECURE": False,
    }

    for key, value in settings.items():
        monkeypatch.setitem(app_module.app.config, key, value)

    result = app_module.app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0, result.output

    return app_module.app.test_client()


@pytest.fixture
def sample_enquiry(admin_client):
    enquiry = {
        "customerName": "Dashboard Test Customer",
        "customerEmail": "dashboard-test@example.com",
        "serviceSelect": "makeup",
        "preferredDate": "",
        "message": "Please tell me about your makeup services.",
    }

    response = admin_client.post("/api/enquiries", json=enquiry)
    assert response.status_code == 201

    return enquiry


def csrf_token_from(response):
    assert response.status_code == 200

    match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        response.get_data(as_text=True),
    )

    assert match is not None, "The form must contain a CSRF token."
    return match.group(1)


def sign_in(client, password=TEST_PASSWORD):
    login_page = client.get("/admin/login")

    return client.post(
        "/admin/login",
        data={
            "password": password,
            "csrf_token": csrf_token_from(login_page),
        },
    )


def test_anonymous_visitor_cannot_read_enquiries(
    admin_client, sample_enquiry
):
    response = admin_client.get("/admin")

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/login"
    assert sample_enquiry["customerEmail"] not in response.get_data(
        as_text=True
    )


def test_wrong_password_does_not_grant_access(admin_client):
    response = sign_in(admin_client, password="incorrect-password")

    assert response.status_code == 401
    assert "Incorrect password" in response.get_data(as_text=True)

    protected_page = admin_client.get("/admin")
    assert protected_page.status_code == 302
    assert protected_page.headers["Location"] == "/admin/login"


def test_admin_can_sign_in_and_read_enquiries(
    admin_client, sample_enquiry
):
    response = sign_in(admin_client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"

    dashboard = admin_client.get("/admin")
    html = dashboard.get_data(as_text=True)

    assert dashboard.status_code == 200
    assert sample_enquiry["customerName"] in html
    assert sample_enquiry["customerEmail"] in html
    assert sample_enquiry["message"] in html
    assert dashboard.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("token", [None, "incorrect-token"])
def test_login_rejects_missing_or_invalid_csrf(admin_client, token):
    admin_client.get("/admin/login")

    form = {"password": TEST_PASSWORD}
    if token is not None:
        form["csrf_token"] = token

    response = admin_client.post("/admin/login", data=form)

    assert response.status_code == 400
    assert admin_client.get("/admin").status_code == 302


def test_logout_removes_admin_access(admin_client):
    assert sign_in(admin_client).status_code == 302

    dashboard = admin_client.get("/admin")
    response = admin_client.post(
        "/admin/logout",
        data={"csrf_token": csrf_token_from(dashboard)},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin/login"

    protected_page = admin_client.get("/admin")
    assert protected_page.status_code == 302
    assert protected_page.headers["Location"] == "/admin/login"


@pytest.mark.parametrize("token", [None, "incorrect-token"])
def test_logout_rejects_missing_or_invalid_csrf(admin_client, token):
    assert sign_in(admin_client).status_code == 302
    admin_client.get("/admin")

    form = {}
    if token is not None:
        form["csrf_token"] = token

    response = admin_client.post("/admin/logout", data=form)

    assert response.status_code == 400
    assert admin_client.get("/admin").status_code == 200


@pytest.mark.parametrize(
    "setting",
    ["SECRET_KEY", "ADMIN_PASSWORD_HASH"],
)
def test_missing_configuration_disables_admin(
    admin_client, monkeypatch, setting
):
    monkeypatch.setitem(app_module.app.config, setting, None)

    assert admin_client.get("/admin/login").status_code == 503
    assert admin_client.get("/admin").status_code == 503

    # The public health endpoint must still work.
    assert admin_client.get("/api/health").status_code == 200


def test_customer_message_is_escaped(admin_client):
    response = admin_client.post(
        "/api/enquiries",
        json={
            "customerName": "Escaping Test",
            "customerEmail": "escaping@example.com",
            "serviceSelect": "hair",
            "message": "<script>alert(1)</script>",
        },
    )
    assert response.status_code == 201

    assert sign_in(admin_client).status_code == 302
    html = admin_client.get("/admin").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_enquiries_are_paginated_newest_first(admin_client):
    for number in range(21):
        response = admin_client.post(
            "/api/enquiries",
            json={
                "customerName": f"Pagination Customer {number:02d}",
                "customerEmail": f"customer{number}@example.com",
                "serviceSelect": "bridal",
            },
        )
        assert response.status_code == 201

    assert sign_in(admin_client).status_code == 302

    first_page = admin_client.get("/admin")
    second_page = admin_client.get("/admin?page=2")

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_html = first_page.get_data(as_text=True)
    second_html = second_page.get_data(as_text=True)

    assert "Pagination Customer 20" in first_html
    assert "Pagination Customer 00" not in first_html
    assert "Pagination Customer 00" in second_html
    assert "Pagination Customer 20" not in second_html

    assert first_html.index("Pagination Customer 20") < first_html.index(
        "Pagination Customer 19"
    )

def test_sixth_login_attempt_is_blocked(admin_client, monkeypatch):
    monkeypatch.setattr(app_module, "time", lambda: 2_000_000_000)

    for _ in range(5):
        assert sign_in(admin_client, password="wrong").status_code == 401

    # Even the correct password must wait once the limit is reached.
    response = sign_in(admin_client)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "900"
    assert "Too many sign-in attempts" in response.get_data(as_text=True)

    # Another blocked request must not restart the waiting period.
    monkeypatch.setattr(app_module, "time", lambda: 2_000_000_060)

    response = sign_in(admin_client)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "840"
    assert admin_client.get("/admin").status_code == 302


def test_login_is_allowed_after_limit_expires(admin_client, monkeypatch):
    monkeypatch.setattr(app_module, "time", lambda: 2_000_000_000)

    for _ in range(5):
        assert sign_in(admin_client, password="wrong").status_code == 401

    assert sign_in(admin_client).status_code == 429

    # Advance the limiter's clock without waiting in real time.
    monkeypatch.setattr(app_module, "time", lambda: 2_000_000_900)

    response = sign_in(admin_client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"


def test_new_browser_does_not_reset_limit(admin_client):
    for _ in range(5):
        assert sign_in(admin_client, password="wrong").status_code == 401

    other_browser = app_module.app.test_client()

    assert sign_in(other_browser).status_code == 429


def test_different_ip_has_its_own_limit(admin_client):
    admin_client.environ_base["REMOTE_ADDR"] = "192.0.2.10"

    for _ in range(5):
        assert sign_in(admin_client, password="wrong").status_code == 401

    assert sign_in(admin_client).status_code == 429

    admin_client.environ_base["REMOTE_ADDR"] = "192.0.2.11"

    assert sign_in(admin_client).status_code == 302


def test_forwarded_header_does_not_bypass_limit(admin_client):
    for _ in range(5):
        assert sign_in(admin_client, password="wrong").status_code == 401

    admin_client.environ_base["HTTP_X_FORWARDED_FOR"] = "198.51.100.25"

    assert sign_in(admin_client).status_code == 429