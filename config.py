from pathlib import Path

APP_NAME = "WorkPay"
APP_SUBTITLE = "Local Payroll & Employee Management System"
CURRENCY = "EGP"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "workpay.db"
DEFAULT_SETTINGS = {
    "working_days_per_month": "30",
    "default_working_hours_per_day": "8",
    "overtime_multiplier": "1.5",
}
DEFAULT_ADMIN_USERNAME = "admin"
# SHA-256 for admin123. Change this value as described in README.md.
DEFAULT_ADMIN_PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
