# Ganesh Contribution Dashboard

Free, static contribution tracking for a housing society event using only Google Sheets as the live data source, Python for report generation, and GitHub Pages for publishing.

## Architecture

```text
Committee updates Google Sheets
  |
  v
Google Sheet tabs exported as CSV
      |
      v
GitHub Actions
      |
      v
Python build script
      |
      v
GitHub Pages dashboard
```

## Project Layout

```text
data/
  owners.csv
  sponsors.csv
  deductions.csv
  settings.json
scripts/
  build.py
  fetch_sheets.py
templates/
  index.html
  admin.html
website/
  assets/
.github/
  workflows/
```

## Data Model

### Owners Sheet

Parse from Google Sheet tab: `owners`

**Columns:**
- `FLAT NUMBER` → `flat`
- `NAME` → `owner_name`
- `BLOCK` → `wing` (extract letter: A, B, C)
- `AMOUNT PAID` → `paid_amount`
- `PAYMENT DATE` → `last_payment_date`
- `PAYMENT MODE` → `payment_mode`
- `PAYMENT REFERENCE NUMBER` → `reference`

**Expected amount** is auto-calculated as: `goal_amount ÷ number_of_flats`

### Combined Response Sheet

Parse from Google Sheet tab: `response` (or your admin form tab)

**Columns (used based on ENTRY TYPE):**

When `ENTRY TYPE = "BUSINESS SPONSORSHIP"`:
- `SPONSOR NAME`
- `SPONSOR CONTCT NUMBER`
- `PAYMENT DATE`
- `AMOUNT RECEIVED`
- `MODE OF PAYMENT`
- `PAYMENT REFERENCE`
- `REMARKS`

When `ENTRY TYPE = "EVENT EXPENDITURE"`:
- `VENDOR NAME`
- `VENDOR PHONE NUMBER`
- `EXPENDITURE DETAILS`
- `EXPENDITURE DATE`
- `EXPENDITURE AMOUNT PAID`
- `MODE OF PAYMENT`
- `PAYMENT REFERENCE`

### Settings File

Update [data/settings.json](/data/settings.json) with the society name, event year, and fund goal.

## Local Usage

1. Install Python 3.11 or newer.
2. Optionally replace the sample CSV files in [data/owners.csv](/c:/G/repo/contibuition.dashboard/data/owners.csv) and [data/sponsors.csv](/c:/G/repo/contibuition.dashboard/data/sponsors.csv) with your exported Google Sheet CSV files.
3. Run `python scripts/build.py`.
4. Open `dist/index.html` in a browser for the public board.
5. Open `dist/admin.html` in a browser for the admin board.

## Google Sheets Setup

1. Create one Google Sheet with two tabs:
   - `owners` — Owner flat details and payment amounts
   - `response` — Combined admin response form (sponsors + expenditures)

2. The `response` tab can be a Google Form response sheet or manual entries. It must have a column `ENTRY TYPE` that is either:
   - `BUSINESS SPONSORSHIP` (for sponsor entries)
   - `EVENT EXPENDITURE` (for expenditure entries)

3. Publish each tab as CSV. Generate export links for each tab:
   - Right-click tab → "Get link to sheet" (gets the gid)
   - Export URL format: `https://docs.google.com/spreadsheets/d/<sheet-id>/export?format=csv&gid=<tab-gid>`

4. Add these repository variables in GitHub Settings > Secrets and variables > Actions:
   - `OWNERS_CSV_URL` = CSV export link for `owners` tab (GID: 277875549)
   - `RESPONSE_CSV_URL` = CSV export link for `response` tab (GID: 866511772)

5. Add these repository secrets for nightly email delivery:
   - `SMTP_SERVER` = SMTP server (e.g., smtp.gmail.com)
   - `SMTP_PORT` = SMTP port (e.g., 587)
   - `SMTP_USERNAME` = Email address
   - `SMTP_PASSWORD` = App password or email password
   - `EMAIL_FROM` = Sender email address
   - `ADMIN_EMAILS` = Comma-separated list of admin emails

6. The workflow runs every 15 minutes to rebuild dashboards and every day at 10 PM IST to send email summary.
```

## GitHub Pages Deployment

The workflow in [.github/workflows/build-and-deploy.yml](/c:/G/repo/contibuition.dashboard/.github/workflows/build-and-deploy.yml) builds the dashboard and deploys the generated `dist` folder to GitHub Pages on every push to `main`, on a schedule, or when manually triggered.

It also sends a nightly admin email summary at 10:00 PM IST (16:30 UTC) when SMTP secrets are configured:

- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `ADMIN_EMAILS`

## Notes

- Owners and committee members should use Google Forms or a lightweight Apps Script form to avoid exposing GitHub credentials.
- Google Sheets gives you a usable audit trail before publishing.
- GitHub Actions and Pages keep hosting free.
