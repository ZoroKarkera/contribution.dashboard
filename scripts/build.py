from __future__ import annotations

import csv
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "website" / "assets"
DIST_DIR = ROOT / "dist"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        return []

    raw_headers = rows[0]
    header_counts: dict[str, int] = defaultdict(int)
    headers = []
    for header in raw_headers:
        name = (header or "").strip()
        header_counts[name] += 1
        if header_counts[name] == 1:
            headers.append(name)
        else:
            headers.append(f"{name}__{header_counts[name]}")

    return [dict(zip(headers, row)) for row in rows[1:]]


def normalize_header(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def get_value(record: dict, *aliases: str) -> str:
    normalized_aliases = {normalize_header(alias) for alias in aliases}
    for key, value in record.items():
        if normalize_header(key) in normalized_aliases:
            return str(value or "").strip()
    return ""


def parse_amount(value: str | None) -> float:
    if not value:
        return 0.0
    normalized = str(value).replace(",", "").replace("Rs.", "").replace("₹", "").strip()
    if not normalized:
        return 0.0
    return float(normalized)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def format_currency(amount: float, currency_symbol: str) -> str:
    return f"{currency_symbol}{amount:,.0f}"


def sort_key_by_date(record: dict, key: str) -> tuple[datetime, str]:
    parsed = parse_date(record.get(key))
    if parsed is None:
        return (datetime.min, "")
    return (parsed, parsed.strftime("%Y-%m-%d"))


def split_response_records(responses: list[dict]) -> tuple[list[dict], list[dict]]:
    """Parse combined response sheet and split into sponsors and deductions."""
    sponsors = []
    deductions = []
    
    for row in responses:
        entry_type = get_value(row, "ENTRY TYPE", "Untitled Question", "TYPE", "ENTRYTYPE").upper()
        
        if entry_type == "BUSINESS SPONSORSHIP":
            sponsors.append({
                "sponsor_name": get_value(row, "SPONSOR NAME"),
                "category": "",
                "pledged_amount": parse_amount(get_value(row, "AMOUNT RECEIVED", "AMPOUNT RECEIVED")),
                "received_amount": parse_amount(get_value(row, "AMOUNT RECEIVED", "AMPOUNT RECEIVED")),
                "received_date": get_value(row, "PAYMENT DATE"),
                "status": "Received",
                "contact_person": get_value(row, "SPONSOR CONTCT NUMBER", "SPONSOR CONTACT NUMBER"),
                "phone": get_value(row, "SPONSOR CONTCT NUMBER", "SPONSOR CONTACT NUMBER"),
                "reference": get_value(row, "PAYMENT REFERENCE"),
                "remarks": get_value(row, "REMARKS"),
            })
        
        elif entry_type == "EVENT EXPENDITURE":
            deductions.append({
                "entry_date": get_value(row, "EXPENDITURE DATE"),
                "category": get_value(row, "VENDOR NAME"),
                "description": get_value(row, "EXPENDITURE DETAILS", "DESCRIPTION"),
                "amount": parse_amount(get_value(row, "EXPENDITURE AMOUNT PAID")),
                "payment_mode": get_value(row, "MODE OF PAYMENT__2", "EXPENDITURE MODE OF PAYMENT", "MODE OF PAYMENT 2", "MODE OF PAYMENT"),
                "reference": get_value(row, "PAYMENT REFERENCE__2", "EXPENDITURE PAYMENT REFERENCE", "PAYMENT REFERENCE 2", "PAYMENT REFERENCE"),
                "remarks": "",
                "entered_by": "",
            })
    
    return sponsors, deductions


def extract_wing(value: str) -> str:
    normalized = value.strip().upper()
    match = re.search(r"\b([A-Z])\b", normalized)
    if match:
        return match.group(1)
    return normalized or "Unknown"


def derive_owner_status(paid_amount: float, expected_per_owner: float) -> str:
    if paid_amount <= 0:
        return "Pending"
    if expected_per_owner > 0 and paid_amount >= expected_per_owner:
        return "Paid"
    return "Partial"


def wing_sort_rank(wing: str) -> tuple[int, str]:
    order = {"A": 0, "B": 1, "C": 2}
    normalized = (wing or "Unknown").strip().upper()
    return (order.get(normalized, 99), normalized)


def flat_sort_key(flat: str) -> tuple:
    normalized = (flat or "").strip().upper()
    numbers = tuple(int(value) for value in re.findall(r"\d+", normalized))
    if numbers:
        return (0, numbers, normalized)
    return (1, normalized)


def build_owner_records(owners: list[dict], expected_per_owner: float) -> tuple[list[dict], dict[str, float], list[dict], list[dict], int]:
    block_totals: dict[str, float] = defaultdict(float)
    recent_contributions = []
    owner_records = []

    for owner in owners:
        flat = get_value(owner, "flat", "FLAT NUMBER", "FLAT N UMBER")
        owner_name = get_value(owner, "owner_name", "NAME", "OWNER NAME")
        paid_amount = parse_amount(get_value(owner, "paid_amount", "AMOUNT PAID"))
        wing = extract_wing(get_value(owner, "wing", "BLOCK"))
        last_payment_date = get_value(owner, "last_payment_date", "PAYMENT DATE", "LAST PAYMENT DATE")
        payment_mode = get_value(owner, "payment_mode", "PAYMENT MODE")
        reference = get_value(owner, "reference", "PAYMENT REFERENCE NUMBER", "PAYENT REFERENCE NUMBER", "PAYMENT REFERENCE")
        block_totals[wing] += paid_amount

        owner_records.append(
            {
                "flat": flat,
                "owner_name": owner_name,
                "wing": wing,
                "expected_amount": expected_per_owner,
                "paid_amount": paid_amount,
                "last_payment_date": last_payment_date,
                "payment_mode": payment_mode,
                "reference": reference,
                "status": derive_owner_status(paid_amount, expected_per_owner),
            }
        )

        payment_date = parse_date(last_payment_date)
        if paid_amount > 0 and payment_date:
            recent_contributions.append(
                {
                    "label": flat or owner_name or "Owner",
                    "detail": owner_name or "Owner",
                    "amount": paid_amount,
                    "channel": "Owner",
                    "date": payment_date.strftime("%Y-%m-%d"),
                    "wing": wing,
                }
            )

    owner_records.sort(key=lambda item: (wing_sort_rank(item["wing"]), flat_sort_key(item["flat"])))
    owner_paid_count = sum(1 for item in owner_records if item["paid_amount"] >= expected_per_owner and expected_per_owner > 0)
    pending_owners = [
        {
            "flat": item["flat"],
            "owner_name": item["owner_name"],
            "wing": item["wing"],
            "due_amount": expected_per_owner - item["paid_amount"],
        }
        for item in owner_records
        if item["paid_amount"] < expected_per_owner
    ]
    pending_owners.sort(key=lambda item: (wing_sort_rank(item["wing"]), flat_sort_key(item["flat"])))
    return owner_records, dict(block_totals), pending_owners, recent_contributions, owner_paid_count


def build_sponsor_records(sponsors: list[dict]) -> tuple[list[dict], dict[str, int], list[dict]]:
    sponsor_status: dict[str, int] = defaultdict(int)
    sponsor_records = []
    recent_contributions = []

    for sponsor in sponsors:
        pledged_amount = parse_amount(sponsor.get("pledged_amount"))
        received_amount = parse_amount(sponsor.get("received_amount"))
        status = (sponsor.get("status") or "Unknown").strip() or "Unknown"
        sponsor_status[status] += 1

        sponsor_records.append(
            {
                "sponsor_name": sponsor.get("sponsor_name", ""),
                "category": sponsor.get("category", ""),
                "pledged_amount": pledged_amount,
                "received_amount": received_amount,
                "received_date": sponsor.get("received_date", ""),
                "status": status,
                "contact_person": sponsor.get("contact_person", ""),
                "phone": sponsor.get("phone", ""),
                "reference": sponsor.get("reference", ""),
                "remarks": sponsor.get("remarks", ""),
            }
        )

        received_date = parse_date(sponsor.get("received_date"))
        if received_amount > 0 and received_date:
            recent_contributions.append(
                {
                    "label": sponsor.get("sponsor_name") or "Sponsor",
                    "detail": sponsor.get("category") or "Sponsor",
                    "amount": received_amount,
                    "channel": "Sponsor",
                    "date": received_date.strftime("%Y-%m-%d"),
                    "wing": "Sponsor",
                }
            )

    sponsor_records.sort(key=lambda item: item["received_amount"], reverse=True)
    return sponsor_records, dict(sponsor_status), recent_contributions


def build_deduction_records(deductions: list[dict], currency_symbol: str) -> tuple[list[dict], float]:
    records = []
    for item in deductions:
        amount = parse_amount(item.get("amount"))
        entry_date = (item.get("entry_date") or "").strip()
        records.append(
            {
                "entry_date": entry_date,
                "category": item.get("category", ""),
                "description": item.get("description", ""),
                "amount": amount,
                "formatted_amount": format_currency(amount, currency_symbol),
                "payment_mode": item.get("payment_mode", ""),
                "reference": item.get("reference", ""),
                "remarks": item.get("remarks", ""),
                "entered_by": item.get("entered_by", ""),
            }
        )

    records.sort(key=lambda row: sort_key_by_date(row, "entry_date"), reverse=True)
    total_spent = sum(row["amount"] for row in records)
    return records, total_spent


def build_wing_summary(owner_records: list[dict], currency_symbol: str) -> list[dict]:
    grouped: dict[str, dict[str, float | int]] = defaultdict(lambda: {"expected": 0.0, "paid": 0.0, "count": 0})
    for item in owner_records:
        grouped[item["wing"]]["expected"] += item["expected_amount"]
        grouped[item["wing"]]["paid"] += item["paid_amount"]
        grouped[item["wing"]]["count"] += 1

    wing_summary = []
    for wing, totals in sorted(grouped.items()):
        expected = float(totals["expected"])
        paid = float(totals["paid"])
        wing_summary.append(
            {
                "wing": wing,
                "expected": expected,
                "paid": paid,
                "progress": round((paid / expected) * 100, 1) if expected else 0.0,
                "count": int(totals["count"]),
                "formatted_expected": format_currency(expected, currency_symbol),
                "formatted_paid": format_currency(paid, currency_symbol),
            }
        )
    return wing_summary


def build_payload(settings: dict, owners: list[dict], sponsors: list[dict], deductions: list[dict]) -> dict:
    currency_symbol = settings.get("currency_symbol", "Rs.")
    goal_amount = parse_amount(settings.get("goal_amount", 0))
    expected_per_owner = goal_amount / len(owners) if owners else 0.0

    owner_records, block_totals, pending_owners, owner_recent, owner_paid_count = build_owner_records(owners, expected_per_owner)
    sponsor_records, sponsor_status, sponsor_recent = build_sponsor_records(sponsors)
    deduction_records, total_spent = build_deduction_records(deductions, currency_symbol)
    wing_summary = build_wing_summary(owner_records, currency_symbol)

    owner_total = sum(item["paid_amount"] for item in owner_records)
    sponsor_total = sum(item["received_amount"] for item in sponsor_records)
    total_collected = owner_total + sponsor_total
    net_balance = total_collected - total_spent
    progress_percent = round((total_collected / goal_amount) * 100, 1) if goal_amount else 0.0

    recent_contributions = owner_recent + sponsor_recent
    recent_contributions.sort(key=lambda item: item["date"], reverse=True)

    public_blocks = []
    for wing in ["A", "B", "C"]:
        amount = block_totals.get(wing, 0.0)
        public_blocks.append(
            {
                "wing": wing,
                "amount": amount,
                "formatted_amount": format_currency(amount, currency_symbol),
            }
        )

    return {
        "meta": {
            "title": settings.get("festival_name", "Contribution Dashboard"),
            "subtitle": settings.get("dashboard_subtitle", ""),
            "society_name": settings.get("society_name", ""),
            "year": settings.get("festival_year", ""),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "currency_symbol": currency_symbol,
        },
        "summary": {
            "goal_amount": goal_amount,
            "total_collected": total_collected,
            "owner_total": owner_total,
            "sponsor_total": sponsor_total,
            "total_spent": total_spent,
            "net_balance": net_balance,
            "progress_percent": progress_percent,
            "pending_amount": max(goal_amount - total_collected, 0),
            "owner_paid_count": owner_paid_count,
            "owner_total_count": len(owners),
            "sponsor_total_count": len(sponsors),
            "deduction_total_count": len(deduction_records),
            "formatted_goal": format_currency(goal_amount, currency_symbol),
            "formatted_total": format_currency(total_collected, currency_symbol),
            "formatted_owner_total": format_currency(owner_total, currency_symbol),
            "formatted_sponsor_total": format_currency(sponsor_total, currency_symbol),
            "formatted_total_spent": format_currency(total_spent, currency_symbol),
            "formatted_net_balance": format_currency(net_balance, currency_symbol),
            "formatted_pending_amount": format_currency(max(goal_amount - total_collected, 0), currency_symbol),
        },
        "public_summary": {
            "target_amount": format_currency(goal_amount, currency_symbol),
            "collected_amount": format_currency(total_collected, currency_symbol),
            "external_sponsors_amount": format_currency(sponsor_total, currency_symbol),
            "overall_spent_amount": format_currency(total_spent, currency_symbol),
            "blocks": public_blocks,
        },
        "wing_summary": wing_summary,
        "pending_owners": pending_owners,
        "recent_contributions": recent_contributions[:15],
        "deductions_recent": deduction_records[:20],
        "owners": [
            {
                **item,
                "formatted_expected_amount": format_currency(item["expected_amount"], currency_symbol),
                "formatted_paid_amount": format_currency(item["paid_amount"], currency_symbol),
            }
            for item in owner_records
        ],
        "sponsors": [
            {
                **item,
                "formatted_pledged_amount": format_currency(item["pledged_amount"], currency_symbol),
                "formatted_received_amount": format_currency(item["received_amount"], currency_symbol),
            }
            for item in sponsor_records
        ],
        "deductions": deduction_records,
        "sponsor_status": sponsor_status,
    }


def build_email_summary(payload: dict) -> str:
    lines = [
        f"{payload['meta']['title']} - Nightly Admin Update",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
        "Collection Summary",
        f"- Target amount: {payload['summary']['formatted_goal']}",
        f"- Total collected: {payload['summary']['formatted_total']}",
        f"- External sponsors: {payload['summary']['formatted_sponsor_total']}",
        f"- Overall spent: {payload['summary']['formatted_total_spent']}",
        f"- Net balance: {payload['summary']['formatted_net_balance']}",
        "",
        "Latest 10 Contributions",
    ]

    for row in payload["recent_contributions"][:10]:
        lines.append(
            f"- {row['date']} | {row['channel']} | {row['label']} | {format_currency(row['amount'], payload['meta']['currency_symbol'])}"
        )

    lines.append("")
    lines.append("Latest 10 Deductions")
    for row in payload["deductions_recent"][:10]:
        lines.append(f"- {row['entry_date']} | {row['category']} | {row['description']} | {row['formatted_amount']}")

    lines.append("")
    lines.append("This email is sent by GitHub Actions nightly schedule.")
    return "\n".join(lines)


def render_dashboard(template_name: str, title: str, subtitle: str, payload: dict) -> str:
    template = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    replacements = {
        "{{TITLE}}": title,
        "{{SUBTITLE}}": subtitle,
        "{{SOCIETY_NAME}}": payload["meta"]["society_name"],
        "{{YEAR}}": str(payload["meta"]["year"]),
        "{{GENERATED_AT}}": payload["meta"]["generated_at"],
        "{{PAYLOAD}}": json.dumps(payload),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def write_dist(files: dict[str, str], email_summary: str) -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")
    for filename, html in files.items():
        (DIST_DIR / filename).write_text(html, encoding="utf-8")
    (DIST_DIR / "email-summary.txt").write_text(email_summary, encoding="utf-8")


def main() -> None:
    settings = read_json(DATA_DIR / "settings.json")
    owners = read_csv(DATA_DIR / "owners.csv")
    responses = read_csv(DATA_DIR / "response.csv")
    sponsors, deductions = split_response_records(responses)
    payload = build_payload(settings, owners, sponsors, deductions)
    public_html = render_dashboard(
        "index.html",
        f"{payload['meta']['title']} Public Board",
        "Public collection and expenditure summary from Google Sheets",
        payload,
    )
    admin_html = render_dashboard(
        "admin.html",
        f"{payload['meta']['title']} Admin Board",
        "Detailed admin-only contribution and expenditure tracking from Google Sheets",
        payload,
    )
    email_summary = build_email_summary(payload)
    write_dist({"index.html": public_html, "admin.html": admin_html}, email_summary)
    print(f"Dashboards built at {DIST_DIR / 'index.html'} and {DIST_DIR / 'admin.html'}")


if __name__ == "__main__":
    main()
