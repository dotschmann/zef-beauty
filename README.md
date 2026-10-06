# Zef Beauty

A responsive website for **Zef Beauty**, a family hair and makeup business in Haatso, Ghana. Visitors can explore the business's work, learn about its services, and get in touch.

This is also a practical software engineering project: building an authentic business website while developing skills in HTML, CSS, JavaScript, Python, SQL, and Git workflows.

## Project status

**In development.** The frontend and backend currently live on different branches:

| Branch | What is available |
| --- | --- |
| [`main`](https://github.com/dotschmann/zef-beauty/tree/main) | Responsive website, portfolio carousel, contact links, and a demo enquiry form. The form does **not** send or save entries. |
| [`feature/enquiry-api`](https://github.com/dotschmann/zef-beauty/tree/feature/enquiry-api) | Website served by Flask, with a connected enquiry form, server-side validation, and local SQLite storage. |

The backend instructions below apply to `feature/enquiry-api`. Saving an enquiry does **not** confirm a booking or send an email or WhatsApp notification.

## Features

### Website

- Responsive layouts with warm neutral colours, terracotta accents, and business photography.
- Hair styling, makeup artistry, and bridal service sections.
- Portfolio carousel with previous/next controls, touch scrolling, and arrow navigation that returns to the beginning or end at the boundaries.
- Sliding mobile navigation with keyboard focus management and Escape-to-close behaviour.
- Permanently visible About section.
- Service links that preselect the corresponding enquiry option.
- WhatsApp, Instagram, and TikTok links.
- Embedded Google Maps location.
- Labelled form controls, visible keyboard focus styles, status feedback, and reduced-motion handling.

### Backend branch

- JSON API built with Flask.
- Required-field, input-type, length, service, basic email-format, and date validation.
- SQLite persistence using parameterised SQL.
- Enquiry reference numbers returned after a successful save.
- Form loading, success, validation-error, and request-failure feedback.
- Submit button disabled while a request is in progress.
- Explicit routes for frontend files and images.

## Technology

| Area | Tools |
| --- | --- |
| Page structure | HTML5 |
| Styling | CSS, Flexbox, Grid, media queries |
| Browser behaviour | Vanilla JavaScript, Fetch API |
| Icons | Bootstrap Icons via CDN |
| Backend | Python, Flask |
| Database | SQLite through Python's `sqlite3` module |
| Version control | Git and GitHub feature branches and pull requests |

The local development environment used Python **3.12.5**. Backend dependencies are pinned in `requirements.txt` on the backend branch. No frontend package installation or build step is required.

## Preview the frontend

Clone the repository:

```powershell
git clone https://github.com/dotschmann/zef-beauty.git
cd zef-beauty
```

On `main`, open `index.html` in a browser or use VS Code Live Server.

This previews the website and its demo form. An internet connection is needed for CDN icons, the embedded map, and external social links.

## Run the website with the backend

Start from the cloned repository and switch to the backend branch:

```powershell
git switch feature/enquiry-api
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

These commands use the virtual environment directly; activation is optional.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app init-db
.venv/bin/python -m flask --app app run --debug
```

Open:

- Website: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- Health check: [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)

Use the Flask website address when testing the connected form. Opening the HTML file directly or using a separate Live Server does not connect the relative `/api/enquiries` request to Flask.

Press **Ctrl + C** to stop the server. The development server and debugger are intended for local development, not production hosting.

### Check on a phone

Connect the computer and phone to the same trusted Wi-Fi network. Stop the existing server, then run:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --host=0.0.0.0 --no-debug
```

Run `ipconfig` on Windows and find the Wi-Fi adapter's IPv4 address. On the phone, open `http://YOUR-COMPUTER-IP:5000`.

Keep the computer awake and Flask running. If Windows Firewall prompts, allow Python on the trusted private network. Enquiries submitted from the phone are stored on the computer running Flask.

## Enquiry API

Available on `feature/enquiry-api`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Check that the application responds |
| POST | `/api/enquiries` | Validate and save an enquiry |

### Request

Send JSON with the header `Content-Type: application/json`:

```json
{
  "customerName": "Test Customer",
  "customerEmail": "test@example.com",
  "serviceSelect": "makeup",
  "preferredDate": "",
  "message": "I would like to ask about availability."
}
```

| Field | Required | Rules |
| --- | --- | --- |
| `customerName` | Yes | Nonblank string; up to 100 characters |
| `customerEmail` | Yes | Basic email-format check; up to 254 characters |
| `serviceSelect` | Yes | `hair`, `makeup`, or `bridal` |
| `preferredDate` | No | Empty or a valid `YYYY-MM-DD` date, today or later |
| `message` | No | String; up to 2,000 characters |

Surrounding whitespace is removed. Optional fields can be omitted or supplied as empty strings; `null` is not accepted. The date check currently uses the server's local date. Email validation checks formatting, not mailbox ownership or deliverability.

### Successful response

HTTP `201 Created`:

```json
{
  "message": "Thank you. Your enquiry has been saved.",
  "saved": true,
  "enquiryId": 1
}
```

The reference number depends on the database contents.

Other responses:

- `400`: invalid JSON object or invalid field values; field errors are returned in `fields` where applicable.
- `415`: request content type is not JSON.
- `500`: database save failed.

### PowerShell example

With Flask running, open a second terminal:

```powershell
$enquiry = @{
    customerName = "Test Customer"
    customerEmail = "test@example.com"
    serviceSelect = "makeup"
    preferredDate = ""
    message = "Testing the enquiry API."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/enquiries" -Method Post -ContentType "application/json" -Body $enquiry
```

Each successful submission creates a new record.

## Database and files

The backend's `init-db` command creates `instance/zef-beauty.sqlite3` and an `enquiries` table. Running the command again preserves existing records.

| Path | Purpose |
| --- | --- |
| `index.html` | Website sections and enquiry form |
| `style.css` | Layout, colours, typography, and responsive styles |
| `script.js` | Navigation, carousel, and form behaviour |
| `images/` | Business portfolio images |
| `app.py` | Flask routes, validation, database setup, and saving; backend branch |
| `requirements.txt` | Pinned Python dependencies; backend branch |
| `instance/zef-beauty.sqlite3` | Generated local database; backend branch, ignored by Git |
| `.gitignore` | Excludes local environments, caches, and secrets; backend branch also excludes `instance/` |

Use test details during development. The database contains submitted names, email addresses, and messages, so it should stay out of Git. The backend branch ignores `instance/`, `.venv/`, and local `.env` files.

## Manual checks

These checks can be repeated after changes:

- Narrow the viewport and check the menu, layout, and carousel.
- Navigate the mobile menu with a keyboard and close it with Escape.
- Check previous/next carousel controls at both ends.
- Follow a service enquiry link and check the selected form option.
- Submit a valid enquiry on the backend branch and confirm the saved reference and database record.
- Check that blank required fields, unsupported services, malformed email addresses, and past dates are rejected.
- Confirm that an empty optional date and message are accepted.

## Automated tests

The enquiry API has 10 automated test cases covering:

- Saving a valid enquiry and returning its database reference.
- Accepting empty optional date and message fields.
- Rejecting blank names, malformed email addresses, unsupported services, and past dates.
- Rejecting missing required fields.
- Confirming rejected enquiries do not create database records.

Each test uses a separate temporary SQLite database.

Install the development dependencies and run the tests on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

On macOS or Linux:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v
```

GitHub Actions runs these tests on pushes and pull requests.
The workflow is defined in `.github/workflows/tests.yml`.

These tests cover the enquiry API and database behaviour.
They do not test the browser layout or establish production readiness.

## Next steps

- Add a secure way for the business to review enquiries.
- Implement notifications and improve duplicate-submission handling.
- Add abuse protection, production configuration, and database backup arrangements.
- Prepare deployment and business-specific privacy information.

## Project learning goals

The implemented work provides practical examples of responsive frontend development, DOM events, asynchronous requests, HTTP/JSON APIs, server-side validation, SQL persistence, and Git branch workflows.

Automated integration testing and continuous integration are now implemented. Containerisation and deployment remain planned learning areas.

## Business links

- [WhatsApp](https://wa.me/233540628077)
- [Makeup on Instagram](https://www.instagram.com/zefglam/)
- [Hair on Instagram](https://www.instagram.com/zefhair/)
- [Makeup on TikTok](https://www.tiktok.com/@zefglam)
- [Hair on TikTok](https://www.tiktok.com/@zefhair_)

**Location:** Haatso, Ghana.
