# WorkPay

**WorkPay** is a polished, lightweight payroll and employee management application for small businesses. It runs entirely on the local computer and stores its data in SQLite—no cloud account, paid API, or internet connection is required.

## Features

- Employee management, editing, filtering, and deactivation
- Automatic monthly payroll calculation
- Attendance, overtime, lateness, bonuses, advances, and deductions
- Live payroll preview and duplicate-record protection
- Partial employee name and ID search
- Employee profiles, service duration, and payroll summaries
- Dashboard KPIs and Plotly charts
- Payroll history, record details, and payment-status updates
- CSV exports and timestamped SQLite backups
- Optional fictional demo data and a simple local admin login

## Tech Stack

Python · Streamlit · SQLite · Pandas · Plotly

## Installation

```bash
git clone <repository-url>
cd WorkPay
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Default Login

- Username: `admin`
- Password: `admin123`

For local development, the SHA-256 password hash is stored in `config.py`. To change it, generate a new hash:

```bash
python -c "import hashlib; print(hashlib.sha256(b'YOUR_NEW_PASSWORD').hexdigest())"
```

Replace `DEFAULT_ADMIN_PASSWORD_HASH` in `config.py`. For a shared or internet-facing deployment, use environment-based secrets and stronger authentication.

## Project Structure

```text
WorkPay/
├── app.py             # Streamlit interface and pages
├── database.py        # SQLite schema and data operations
├── payroll.py         # Reusable payroll calculations
├── utils.py           # Formatting and service-duration helpers
├── config.py          # Paths, currency, defaults, and local login
├── requirements.txt
├── data/              # Created automatically; contains workpay.db
└── backups/           # Timestamped local database backups
```

## Payroll Formula

```text
Daily Rate = Basic Salary / Working Days
Hourly Rate = Daily Rate / Working Hours Per Day
Overtime = Overtime Hours × Hourly Rate × Overtime Multiplier
Net Salary = Basic Salary + Overtime + Bonuses
             - Absence Deduction - Late Deduction
             - Other Deductions - Advances
```

All monetary values are rounded to two decimal places. Default settings are 30 working days, 8 hours per day, and a 1.5 overtime multiplier. They can be changed inside the app.

## Screenshots

Add dashboard, employee search, and payroll preview screenshots here after running the application.

