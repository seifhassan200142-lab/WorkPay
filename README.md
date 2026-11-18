# WorkPay
**Payroll & Employee Management System | Python · Streamlit · SQLite**

WorkPay is a lightweight payroll and employee management application designed to simplify salary calculations, employee records, and monthly payroll operations for small businesses.

The application provides a centralized interface for managing employee information, tracking payroll adjustments, calculating net salaries, and reviewing payment history.

Built with Python and Streamlit, WorkPay operates locally using SQLite, without requiring cloud infrastructure, paid APIs, or an internet connection.

## Overview

Managing payroll manually through spreadsheets can become time-consuming and prone to calculation errors, especially when accounting for attendance, overtime, lateness, bonuses, and salary deductions.

WorkPay simplifies this process by bringing employee management, payroll calculations, and reporting into a single application.

The system is designed to support straightforward payroll workflows while keeping business data stored locally.

## Key Features

### Employee Management
- Create, edit, search, and deactivate employee records.
- Search employees using partial names or employee IDs.
- View employee profiles, employment duration, and payroll summaries.
- Filter employee records for easier administration.

### Payroll Automation
- Automatically calculate monthly employee salaries.
- Process overtime, absences, lateness, bonuses, advances, and deductions.
- Preview payroll calculations before saving.
- Prevent duplicate payroll records for the same period.
- Configure working days, working hours, and overtime multipliers.

### Dashboard & Reporting
- Monitor payroll and employee KPIs.
- Explore interactive charts using Plotly.
- Review payroll history and individual salary records.
- Track and update payment statuses.
- Export payroll data to CSV.

### Data Management
- Store employee and payroll information locally in SQLite.
- Create timestamped database backups.
- Generate fictional demonstration data for testing.
- Access the application through a basic local administrator login.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Application Framework | Streamlit |
| Database | SQLite |
| Data Processing | Pandas |
| Data Visualization | Plotly |
| Interface | Streamlit Web UI |
| Data Export | CSV |

## Application Workflow

```text
Employee Management
        |
        v
Employee Salary Information
        |
        v
Monthly Payroll Inputs
        |
        v
Payroll Calculation Engine
        |
        v
Payroll Preview & Validation
        |
        v
Save Payroll Records
        |
        v
Payment Status & History
        |
        v
Dashboard / CSV Export
```

## Payroll Calculation

WorkPay uses configurable payroll parameters to calculate employee compensation and deductions.

```text
Daily Rate = Basic Salary / Working Days

Hourly Rate = Daily Rate / Working Hours Per Day

Overtime Pay = Overtime Hours × Hourly Rate
               × Overtime Multiplier

Net Salary = Basic Salary
             + Overtime Pay
             + Bonuses
             - Absence Deductions
             - Late Deductions
             - Other Deductions
             - Advances
```

The default configuration uses 30 working days per month, 8 working hours per day, and a 1.5 overtime multiplier.

These values can be adjusted through the application settings to match business requirements.

## Project Structure

```text
WorkPay/
├── app.py
├── database.py
├── payroll.py
├── utils.py
├── config.py
├── requirements.txt
├── data/
└── backups/
```

**Core Components**

- `app.py` — Application interface and navigation.
- `database.py` — Database schema and operations.
- `payroll.py` — Payroll calculation logic.
- `utils.py` — Shared formatting and date utilities.
- `config.py` — Configuration and local authentication settings.
- `data/` — Local SQLite database storage.
- `backups/` — Database backup files.

## Installation

**Requirements:** Python 3.10+ and pip.

```bash
git clone <repository-url>
cd WorkPay

python -m venv .venv
```

Activate the virtual environment:

**Windows**
```powershell
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and start the application:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Access the application at:

`http://localhost:8501`

## Security & Data Storage

WorkPay operates as a local application, with employee records and payroll history stored in SQLite.

A basic administrator login is provided for local development and demonstration purposes.

The default authentication mechanism uses a SHA-256 password hash defined in the application configuration. It is not intended to provide production-grade authentication.

For shared or production deployments, stronger password hashing, proper access controls, secure credential management, and data protection measures should be implemented.

## Screenshots

Application screenshots can be added to demonstrate the main workflows:

- Dashboard and payroll analytics.
- Employee management and search.
- Monthly payroll calculation and preview.
- Payroll history and payment tracking.

## Intended Use

WorkPay is suitable as a lightweight payroll management solution or customizable foundation for small-business administrative workflows.

It demonstrates practical implementation of business logic, relational data storage, data processing, interactive dashboards, and payroll automation using Python.

The application is designed primarily for local use. Business-specific payroll policies, statutory deductions, and compliance requirements should be reviewed before operational adoption.

---

**Project:** WorkPay  
**Category:** Business Automation / Payroll Management  
**Developer:** Seif Eldeen Hassan
