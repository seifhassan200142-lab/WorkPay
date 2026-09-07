import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from config import BACKUP_DIR, DATA_DIR, DB_PATH, DEFAULT_SETTINGS


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            full_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            department TEXT NOT NULL,
            phone TEXT DEFAULT '',
            basic_salary REAL NOT NULL CHECK(basic_salary > 0),
            hire_date TEXT NOT NULL,
            working_hours_per_day REAL NOT NULL CHECK(working_hours_per_day > 0),
            status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Inactive')),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payroll_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            payroll_month INTEGER NOT NULL CHECK(payroll_month BETWEEN 1 AND 12),
            payroll_year INTEGER NOT NULL,
            basic_salary REAL NOT NULL,
            attendance_days REAL NOT NULL DEFAULT 0,
            absence_days REAL NOT NULL DEFAULT 0,
            late_hours REAL NOT NULL DEFAULT 0,
            overtime_hours REAL NOT NULL DEFAULT 0,
            overtime_multiplier REAL NOT NULL,
            overtime_amount REAL NOT NULL DEFAULT 0,
            bonuses REAL NOT NULL DEFAULT 0,
            absence_deduction REAL NOT NULL DEFAULT 0,
            late_deduction REAL NOT NULL DEFAULT 0,
            other_deductions REAL NOT NULL DEFAULT 0,
            advances REAL NOT NULL DEFAULT 0,
            net_salary REAL NOT NULL,
            payment_status TEXT NOT NULL CHECK(payment_status IN ('Paid','Unpaid')),
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(employee_id) REFERENCES employees(id),
            UNIQUE(employee_id, payroll_month, payroll_year)
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))


def rows(query: str, params: Iterable[Any] = ()) -> list[dict]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]


def row(query: str, params: Iterable[Any] = ()) -> dict | None:
    result = rows(query, params)
    return result[0] if result else None


def get_settings() -> dict[str, float]:
    return {item["key"]: float(item["value"]) for item in rows("SELECT key,value FROM settings")}


def update_settings(values: dict[str, float]) -> None:
    with connect() as conn:
        for key, value in values.items():
            conn.execute("UPDATE settings SET value=?, updated_at=CURRENT_TIMESTAMP WHERE key=?", (str(value), key))


def add_employee(data: dict) -> str:
    with connect() as conn:
        cur = conn.execute("""INSERT INTO employees
            (full_name,job_title,department,phone,basic_salary,hire_date,working_hours_per_day,status,notes)
            VALUES(?,?,?,?,?,?,?,?,?)""", tuple(data[k] for k in
            ("full_name","job_title","department","phone","basic_salary","hire_date","working_hours_per_day","status","notes")))
        code = f"EMP-{cur.lastrowid:04d}"
        conn.execute("UPDATE employees SET employee_code=? WHERE id=?", (code, cur.lastrowid))
        return code


def update_employee(employee_id: int, data: dict) -> None:
    with connect() as conn:
        conn.execute("""UPDATE employees SET full_name=?,job_title=?,department=?,phone=?,
            basic_salary=?,hire_date=?,working_hours_per_day=?,status=?,notes=?,updated_at=CURRENT_TIMESTAMP
            WHERE id=?""", tuple(data[k] for k in ("full_name","job_title","department","phone",
            "basic_salary","hire_date","working_hours_per_day","status","notes")) + (employee_id,))


def get_employees(active_only: bool = False) -> list[dict]:
    query = "SELECT * FROM employees"
    if active_only:
        query += " WHERE status='Active'"
    return rows(query + " ORDER BY full_name")


def search_employees(term: str) -> list[dict]:
    like = f"%{term.strip()}%"
    return rows("SELECT * FROM employees WHERE full_name LIKE ? COLLATE NOCASE OR employee_code LIKE ? COLLATE NOCASE ORDER BY full_name", (like, like))


def add_payroll(data: dict) -> None:
    columns = ("employee_id","payroll_month","payroll_year","basic_salary","attendance_days",
        "absence_days","late_hours","overtime_hours","overtime_multiplier","overtime_amount",
        "bonuses","absence_deduction","late_deduction","other_deductions","advances",
        "net_salary","payment_status","notes")
    with connect() as conn:
        conn.execute(f"INSERT INTO payroll_records ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                     tuple(data[c] for c in columns))


def payroll_exists(employee_id: int, month: int, year: int) -> dict | None:
    return row("SELECT * FROM payroll_records WHERE employee_id=? AND payroll_month=? AND payroll_year=?", (employee_id, month, year))


def payroll_records(where: str = "", params: Iterable[Any] = ()) -> list[dict]:
    query = """SELECT p.*, e.employee_code,e.full_name,e.department,e.job_title
        FROM payroll_records p JOIN employees e ON e.id=p.employee_id"""
    if where:
        query += " WHERE " + where
    return rows(query + " ORDER BY p.payroll_year DESC,p.payroll_month DESC,e.full_name", params)


def update_payroll_meta(record_id: int, status: str, notes: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE payroll_records SET payment_status=?, notes=? WHERE id=?", (status, notes, record_id))


def create_backup() -> Path:
    if not DB_PATH.exists():
        raise FileNotFoundError("Database has not been created yet.")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"workpay_backup_{datetime.now():%Y_%m_%d_%H%M%S}.db"
    shutil.copy2(DB_PATH, target)
    return target


def insert_demo_data() -> int:
    demo = [
        ("Ahmed Hassan","Software Engineer","Technology","01000000001",12000,"2024-01-15",8),
        ("Sara Mohamed","Accountant","Finance","01000000002",9500,"2022-06-01",8),
        ("Omar Ali","Sales Executive","Sales","01000000003",8500,"2025-02-10",8),
        ("Mariam Adel","HR Specialist","Human Resources","01000000004",10000,"2023-09-20",8),
        ("Youssef Khaled","Operations Coordinator","Operations","01000000005",9000,"2021-11-05",8),
    ]
    count = 0
    for name, title, dept, phone, salary, hire, hours in demo:
        if not row("SELECT id FROM employees WHERE full_name=? AND phone=?", (name, phone)):
            add_employee({"full_name":name,"job_title":title,"department":dept,"phone":phone,
                "basic_salary":salary,"hire_date":hire,"working_hours_per_day":hours,
                "status":"Active","notes":"Fictional demo employee"})
            count += 1
    return count

