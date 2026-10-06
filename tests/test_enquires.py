import sqlite3
from contextlib import closing
from datetime import date, timedelta

import pytest

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give each test its own database.
    test_database = tmp_path / "test.sqlite3"

    monkeypatch.setattr(app_module, "DATABASE_PATH", test_database)
    monkeypatch.setitem(app_module.app.config, "TESTING", True)

    # Create the table using our existing setup command.
    runner = app_module.app.test_cli_runner()
    result = runner.invoke(args=["init-db"])

    assert result.exit_code == 0, result.output

    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def valid_enquiry():
    return {
        "customerName": "Test Customer",
        "customerEmail": "test@example.com",
        "serviceSelect": "makeup",
        "preferredDate": (
            date.today() + timedelta(days=7)
        ).isoformat(),
        "message": "Makeup for a special occasion."
    }


def saved_enquiries():
    with closing(
        sqlite3.connect(app_module.DATABASE_PATH)
    ) as connection:
        return connection.execute(
            """
            SELECT id, customer_name, customer_email,
                   service, preferred_date, message
            FROM enquiries
            ORDER BY id
            """
        ).fetchall()


def test_valid_enquiry_is_saved(client, valid_enquiry):
    response = client.post("/api/enquiries", json=valid_enquiry)

    assert response.status_code == 201

    result = response.get_json()

    assert result["saved"] is True

    # Check that the returned reference matches the actual saved record.
    assert saved_enquiries() == [
        (
            result["enquiryId"],
            "Test Customer",
            "test@example.com",
            "makeup",
            valid_enquiry["preferredDate"],
            "Makeup for a special occasion."
        )
    ]


def test_optional_fields_can_be_empty(client, valid_enquiry):
    valid_enquiry["preferredDate"] = ""
    valid_enquiry["message"] = ""

    response = client.post("/api/enquiries", json=valid_enquiry)

    assert response.status_code == 201

    records = saved_enquiries()

    assert len(records) == 1
    assert records[0][4] is None
    assert records[0][5] == ""


@pytest.mark.parametrize(
    "field, value",
    [
        ("customerName", "   "),
        ("customerEmail", "not-an-email"),
        ("serviceSelect", ""),
        ("serviceSelect", "unknown"),
        (
            "preferredDate",
            (date.today() - timedelta(days=1)).isoformat()
        )
    ]
)
def test_invalid_enquiry_is_not_saved(
    client, valid_enquiry, field, value
):
    valid_enquiry[field] = value

    response = client.post("/api/enquiries", json=valid_enquiry)

    assert response.status_code == 400
    assert field in response.get_json()["fields"]
    assert saved_enquiries() == []


@pytest.mark.parametrize(
    "field",
    ["customerName", "customerEmail", "serviceSelect"]
)
def test_missing_required_field_is_not_saved(
    client, valid_enquiry, field
):
    del valid_enquiry[field]

    response = client.post("/api/enquiries", json=valid_enquiry)

    assert response.status_code == 400
    assert field in response.get_json()["fields"]
    assert saved_enquiries() == []