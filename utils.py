import calendar
from datetime import date, datetime
from typing import Any

from config import CURRENCY


def format_currency(value: Any) -> str:
    try:
        return f"{float(value or 0):,.2f} {CURRENCY}"
    except (TypeError, ValueError):
        return f"0.00 {CURRENCY}"


def service_duration(hire_date: str | date, today: date | None = None) -> str:
    if isinstance(hire_date, str):
        hire = datetime.strptime(hire_date, "%Y-%m-%d").date()
    else:
        hire = hire_date
    current = today or date.today()
    if hire > current:
        return "Not started"
    months = (current.year - hire.year) * 12 + current.month - hire.month
    if current.day < hire.day:
        months -= 1
    years, remaining = divmod(max(months, 0), 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if remaining:
        parts.append(f"{remaining} month{'s' if remaining != 1 else ''}")
    return " and ".join(parts) if parts else "Less than 1 month"


def month_name(month: int) -> str:
    return calendar.month_name[int(month)]


def employee_label(employee: dict) -> str:
    return f"{employee['employee_code']} — {employee['full_name']}"

