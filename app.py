import calendar
import hashlib
import sqlite3
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from config import APP_NAME, APP_SUBTITLE, CURRENCY, DEFAULT_ADMIN_PASSWORD_HASH, DEFAULT_ADMIN_USERNAME
from payroll import calculate_payroll, total_deductions
from utils import employee_label, format_currency, month_name, service_duration

st.set_page_config(page_title=APP_NAME, page_icon="💼", layout="wide")
db.initialize_database()

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1450px;}
    [data-testid="stSidebar"] {background: #0f172a;}
    [data-testid="stSidebar"] * {color: #e2e8f0;}
    .brand {font-size:2rem;font-weight:800;color:#1d4ed8;letter-spacing:-1px}
    .subtitle {color:#64748b;margin-top:-8px;margin-bottom:24px}
    .profile {padding:1.3rem;border:1px solid #e2e8f0;border-radius:14px;background:white;}
    div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e2e8f0;
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 2px 8px #0f172a0a;
}

/* عنوان المربع */
div[data-testid="stMetric"] label,
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p {
    color: #475569 !important;
}

/* الرقم داخل المربع */
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
    color: #0f172a !important;
    font-weight: 700 !important;
}
    .net-box {background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:20px;text-align:center;}
    .net-box h2 {color:#1d4ed8;margin:5px 0;}
    .stButton button {border-radius:9px;font-weight:600;}
</style>
""", unsafe_allow_html=True)


def header(title: str, description: str = "") -> None:
    st.markdown(f'<div class="brand">{title}</div>', unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="subtitle">{description}</div>', unsafe_allow_html=True)


def dataframe(data: pd.DataFrame) -> None:
    st.dataframe(data, use_container_width=True, hide_index=True)


def login() -> bool:
    if st.session_state.get("authenticated"):
        return True
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        header("💼 WorkPay", APP_SUBTITLE)
        with st.form("login_form"):
            st.subheader("Admin Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")
        if submitted:
            digest = hashlib.sha256(password.encode()).hexdigest()
            if username == DEFAULT_ADMIN_USERNAME and digest == DEFAULT_ADMIN_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        st.caption("Development login: admin / admin123")
    return False


def dashboard() -> None:
    header("Dashboard", "A clear overview of employees and monthly payroll performance.")
    today = date.today()
    c1, c2 = st.columns(2)
    month = c1.selectbox("Month", range(1, 13), index=today.month - 1, format_func=month_name, key="dash_month")
    year = c2.number_input("Year", 2000, 2100, today.year, key="dash_year")
    records = db.payroll_records("p.payroll_month=? AND p.payroll_year=?", (month, year))
    employees = db.get_employees(active_only=True)
    deductions = sum(total_deductions(r) + float(r["advances"]) for r in records)
    metrics = [
        ("Active Employees", len(employees)),
        ("Monthly Payroll", format_currency(sum(float(r["net_salary"]) for r in records))),
        ("Paid Salaries", sum(r["payment_status"] == "Paid" for r in records)),
        ("Unpaid Salaries", sum(r["payment_status"] == "Unpaid" for r in records)),
        ("Overtime Hours", f"{sum(float(r['overtime_hours']) for r in records):,.1f}"),
        ("Total Deductions", format_currency(deductions)),
    ]
    cols = st.columns(3)
    for i, (label, value) in enumerate(metrics):
        cols[i % 3].metric(label, value)

    st.markdown("### Analytics")
    all_records = db.payroll_records()
    if not all_records:
        st.info("No payroll data yet. Add employees and create the first monthly payroll record.")
        return
    df_all = pd.DataFrame(all_records)
    df_all["Period"] = pd.to_datetime(dict(year=df_all.payroll_year, month=df_all.payroll_month, day=1))
    trend = df_all.groupby("Period", as_index=False)["net_salary"].sum().sort_values("Period")
    left, right = st.columns(2)
    left.plotly_chart(px.line(trend, x="Period", y="net_salary", markers=True,
        labels={"net_salary":f"Payroll ({CURRENCY})"}, template="plotly_white"), use_container_width=True)
    if records:
        current = pd.DataFrame(records)
        dept = current.groupby("department", as_index=False)["net_salary"].sum()
        right.plotly_chart(px.bar(dept, x="department", y="net_salary", color="department",
            labels={"net_salary":f"Payroll ({CURRENCY})","department":"Department"}, template="plotly_white"), use_container_width=True)
        status = current.groupby("payment_status", as_index=False).size()
        st.plotly_chart(px.pie(status, names="payment_status", values="size", hole=.55,
            color="payment_status", color_discrete_map={"Paid":"#2563eb","Unpaid":"#f59e0b"}, template="plotly_white"), use_container_width=True)
    else:
        right.info("No payroll records for the selected period.")


def employee_form(default: dict | None = None, prefix: str = "add") -> dict | None:
    default = default or {}
    with st.form(f"{prefix}_employee_form", clear_on_submit=prefix == "add"):
        a, b = st.columns(2)
        full_name = a.text_input("Full Name *", default.get("full_name", ""))
        job_title = b.text_input("Job Title *", default.get("job_title", ""))
        department = a.text_input("Department *", default.get("department", ""))
        phone = b.text_input("Phone Number", default.get("phone", ""))
        salary = a.number_input("Basic Salary *", min_value=0.0, value=float(default.get("basic_salary", 0)), step=100.0)
        raw_date = default.get("hire_date")
        hire = b.date_input("Hire Date *", value=date.fromisoformat(raw_date) if raw_date else date.today(), max_value=date.today())
        hours = a.number_input("Working Hours Per Day", 1.0, 24.0, float(default.get("working_hours_per_day", db.get_settings()["default_working_hours_per_day"])), .5)
        status = b.selectbox("Employment Status", ["Active", "Inactive"], index=0 if default.get("status", "Active") == "Active" else 1)
        notes = st.text_area("Notes", default.get("notes", ""))
        submit = st.form_submit_button("Save Employee", type="primary", use_container_width=True)
    if not submit:
        return None
    if not full_name.strip() or not job_title.strip() or not department.strip():
        st.error("Full name, job title, and department are required.")
        return None
    if salary <= 0:
        st.error("Basic salary must be greater than zero.")
        return None
    return {"full_name":full_name.strip(),"job_title":job_title.strip(),"department":department.strip(),
        "phone":phone.strip(),"basic_salary":salary,"hire_date":hire.isoformat(),
        "working_hours_per_day":hours,"status":status,"notes":notes.strip()}


def add_employee_page() -> None:
    header("Add Employee", "Create a new employee profile. The employee ID is generated automatically.")
    data = employee_form()
    if data:
        try:
            code = db.add_employee(data)
            st.success(f"Employee added successfully. Employee ID: {code}")
        except sqlite3.DatabaseError as exc:
            st.error(f"Could not add employee: {exc}")


def employees_page() -> None:
    header("Employees", "Browse, filter, edit, and deactivate employee records.")
    employees = db.get_employees()
    if not employees:
        st.info("No employees found. Use Add Employee to create the first record.")
        return
    departments = sorted({e["department"] for e in employees})
    c1, c2, c3 = st.columns(3)
    query = c1.text_input("Search by name")
    dept = c2.selectbox("Department", ["All"] + departments)
    status = c3.selectbox("Status", ["All", "Active", "Inactive"])
    filtered = [e for e in employees if query.lower() in e["full_name"].lower()
                and (dept == "All" or e["department"] == dept)
                and (status == "All" or e["status"] == status)]
    view = pd.DataFrame([{"Employee ID":e["employee_code"],"Name":e["full_name"],"Department":e["department"],
        "Job Title":e["job_title"],"Salary":format_currency(e["basic_salary"]),"Hire Date":e["hire_date"],
        "Years of Service":service_duration(e["hire_date"]),"Status":e["status"]} for e in filtered])
    dataframe(view)
    st.markdown("### View or Edit Employee")
    selected_id = st.selectbox("Select employee", [e["id"] for e in employees],
                               format_func=lambda x: employee_label(next(e for e in employees if e["id"] == x)))
    selected = next(e for e in employees if e["id"] == selected_id)
    with st.expander("Edit employee details"):
        updated = employee_form(selected, "edit")
        if updated:
            db.update_employee(selected_id, updated)
            st.success("Employee updated successfully.")
            st.rerun()


def search_page() -> None:
    header("Employee Search", "Find a profile using a full or partial name or employee ID.")
    term = st.text_input("Search employee", placeholder="Example: Mohamed or EMP-0001")
    if not term:
        st.info("Enter a name or employee ID to begin.")
        return
    matches = db.search_employees(term)
    if not matches:
        st.warning("No matching employee found.")
        return
    employee_id = st.selectbox("Matching employees", [e["id"] for e in matches],
                               format_func=lambda x: employee_label(next(e for e in matches if e["id"] == x)))
    employee = next(e for e in matches if e["id"] == employee_id)
    st.markdown(f"""<div class="profile"><h3>{employee['full_name']}</h3>
    <b>{employee['employee_code']}</b> · {employee['job_title']} · {employee['department']}<br><br>
    <b>Phone:</b> {employee['phone'] or '—'} &nbsp; | &nbsp; <b>Basic Salary:</b> {format_currency(employee['basic_salary'])}<br>
    <b>Hire Date:</b> {employee['hire_date']} &nbsp; | &nbsp; <b>Service:</b> {service_duration(employee['hire_date'])}<br>
    <b>Status:</b> {employee['status']} &nbsp; | &nbsp; <b>Working Hours:</b> {employee['working_hours_per_day']:g} per day<br>
    <b>Notes:</b> {employee['notes'] or '—'}</div>""", unsafe_allow_html=True)
    records = db.payroll_records("p.employee_id=?", (employee_id,))
    st.markdown("### Payroll Summary")
    latest = records[0] if records else None
    cols = st.columns(4)
    stats = [("Payroll Records",len(records)),("Latest Net Salary",format_currency(latest["net_salary"] if latest else 0)),
        ("Overtime Hours",sum(r["overtime_hours"] for r in records)),("Bonuses",format_currency(sum(r["bonuses"] for r in records))),
        ("Deductions",format_currency(sum(total_deductions(r) for r in records))),
        ("Advances",format_currency(sum(r["advances"] for r in records))),
        ("Absence Days",sum(r["absence_days"] for r in records))]
    for i, (label, value) in enumerate(stats): cols[i % 4].metric(label, value)
    if records:
        view = pd.DataFrame(records)
        view["Period"] = view.apply(lambda r: f"{month_name(r.payroll_month)} {r.payroll_year}", axis=1)
        dataframe(view[["Period","basic_salary","overtime_amount","bonuses","net_salary","payment_status"]])
        chart = view.copy()
        chart["Date"] = pd.to_datetime(dict(year=chart.payroll_year, month=chart.payroll_month, day=1))
        st.plotly_chart(px.line(chart.sort_values("Date"), x="Date", y="net_salary", markers=True, template="plotly_white"), use_container_width=True)
    else:
        st.info("No payroll history for this employee.")


def monthly_payroll() -> None:
    header("Monthly Payroll", "Enter attendance and adjustments, review the live calculation, then save.")
    employees = db.get_employees(active_only=True)
    if not employees:
        st.warning("Add at least one active employee before creating payroll.")
        return
    settings = db.get_settings()
    today = date.today()
    a, b, c = st.columns([2,1,1])
    employee_id = a.selectbox("Employee", [e["id"] for e in employees], format_func=lambda x: employee_label(next(e for e in employees if e["id"] == x)))
    month = b.selectbox("Month", range(1,13), index=today.month-1, format_func=month_name)
    year = c.number_input("Year", 2000, 2100, today.year)
    employee = next(e for e in employees if e["id"] == employee_id)
    st.caption(f"{employee['employee_code']} · {employee['department']} · Basic Salary: {format_currency(employee['basic_salary'])} · {employee['working_hours_per_day']:g} hours/day")
    existing = db.payroll_exists(employee_id, month, year)
    if existing:
        st.error("Payroll already exists for this employee for the selected month. Open Payroll History to view or update it.")
        return
    c1, c2, c3 = st.columns(3)
    attendance = c1.number_input("Attendance Days", 0.0, float(settings["working_days_per_month"]), float(settings["working_days_per_month"]), .5)
    absence = c2.number_input("Absence Days", min_value=0.0, step=.5)
    late = c3.number_input("Late Hours", min_value=0.0, step=.5)
    overtime = c1.number_input("Overtime Hours", min_value=0.0, step=.5)
    bonus = c2.number_input("Bonuses", min_value=0.0, step=100.0)
    other = c3.number_input("Other Deductions", min_value=0.0, step=100.0)
    advance = c1.number_input("Advances", min_value=0.0, step=100.0)
    status = c2.selectbox("Payment Status", ["Unpaid", "Paid"])
    notes = st.text_area("Payroll Notes")
    calc = calculate_payroll(employee["basic_salary"], int(settings["working_days_per_month"]),
        employee["working_hours_per_day"], overtime, settings["overtime_multiplier"], absence, late, bonus, other, advance)
    st.markdown("### Live Payroll Preview")
    preview = [("Basic Salary",calc.basic_salary),("Daily Rate",calc.daily_rate),("Hourly Rate",calc.hourly_rate),
        ("Overtime Amount",calc.overtime_amount),("Bonuses",calc.bonuses),("Absence Deduction",calc.absence_deduction),
        ("Late Deduction",calc.late_deduction),("Other Deductions",calc.other_deductions),("Advances",calc.advances)]
    pcols = st.columns(3)
    for i,(label,value) in enumerate(preview): pcols[i%3].metric(label, format_currency(value))
    st.markdown(f'<div class="net-box">NET SALARY<h2>{format_currency(calc.net_salary)}</h2></div>', unsafe_allow_html=True)
    if calc.net_salary < 0:
        st.warning("Net salary is below zero. Please review deductions and advances.")
    if st.button("Save Payroll", type="primary", use_container_width=True):
        payload = calc.to_dict() | {"employee_id":employee_id,"payroll_month":month,"payroll_year":int(year),
            "attendance_days":attendance,"absence_days":absence,"late_hours":late,"overtime_hours":overtime,
            "overtime_multiplier":settings["overtime_multiplier"],"payment_status":status,"notes":notes}
        try:
            db.add_payroll(payload)
            st.success("Payroll saved successfully.")
        except sqlite3.IntegrityError:
            st.error("Payroll already exists for this employee and month.")


def history_page() -> None:
    header("Payroll History", "Filter payroll records and inspect complete salary breakdowns.")
    records = db.payroll_records()
    if not records:
        st.info("No payroll records available.")
        return
    employees = db.get_employees()
    departments = sorted({r["department"] for r in records})
    a,b,c,d = st.columns(4)
    emp = a.selectbox("Employee", ["All"] + [e["id"] for e in employees], format_func=lambda x: "All employees" if x=="All" else employee_label(next(e for e in employees if e["id"]==x)))
    dept = b.selectbox("Department", ["All"] + departments)
    month = c.selectbox("Month", ["All"] + list(range(1,13)), format_func=lambda x:"All months" if x=="All" else month_name(x))
    year = d.selectbox("Year", ["All"] + sorted({r["payroll_year"] for r in records}, reverse=True))
    status = st.selectbox("Payment Status", ["All","Paid","Unpaid"])
    filtered = [r for r in records if (emp=="All" or r["employee_id"]==emp) and (dept=="All" or r["department"]==dept)
        and (month=="All" or r["payroll_month"]==month) and (year=="All" or r["payroll_year"]==year)
        and (status=="All" or r["payment_status"]==status)]
    view = pd.DataFrame([{"Record ID":r["id"],"Employee ID":r["employee_code"],"Employee Name":r["full_name"],"Department":r["department"],
        "Month":f"{month_name(r['payroll_month'])} {r['payroll_year']}","Basic Salary":format_currency(r["basic_salary"]),
        "Overtime":format_currency(r["overtime_amount"]),"Bonuses":format_currency(r["bonuses"]),
        "Deductions":format_currency(total_deductions(r)),"Advances":format_currency(r["advances"]),
        "Net Salary":format_currency(r["net_salary"]),"Payment Status":r["payment_status"]} for r in filtered])
    dataframe(view)
    if not filtered:
        st.info("No records match these filters.")
        return
    record_id = st.selectbox("View record details", [r["id"] for r in filtered],
        format_func=lambda x: next(f"#{r['id']} — {r['employee_code']} — {month_name(r['payroll_month'])} {r['payroll_year']}" for r in filtered if r["id"]==x))
    record = next(r for r in filtered if r["id"] == record_id)
    with st.expander("Complete salary breakdown", expanded=True):
        st.write(f"**{record['full_name']}** · {record['employee_code']} · {record['department']}")
        breakdown = {"Basic Salary":record["basic_salary"],"Overtime Amount":record["overtime_amount"],"Bonuses":record["bonuses"],
            "Absence Deduction":record["absence_deduction"],"Late Deduction":record["late_deduction"],
            "Other Deductions":record["other_deductions"],"Advances":record["advances"],"Net Salary":record["net_salary"]}
        dataframe(pd.DataFrame([{"Item":k,"Amount":format_currency(v)} for k,v in breakdown.items()]))
        with st.form("update_payroll_meta"):
            new_status = st.selectbox("Payment Status", ["Paid","Unpaid"], index=0 if record["payment_status"]=="Paid" else 1)
            new_notes = st.text_area("Notes", record["notes"] or "")
            if st.form_submit_button("Update Status and Notes", type="primary"):
                db.update_payroll_meta(record_id, new_status, new_notes)
                st.success("Payment status updated.")
                st.rerun()


def settings_page() -> None:
    header("Settings", "Update the default payroll calculation rules.")
    settings = db.get_settings()
    with st.form("settings"):
        days = st.number_input("Working Days Per Month", 1, 31, int(settings["working_days_per_month"]))
        hours = st.number_input("Default Working Hours Per Day", 1.0, 24.0, settings["default_working_hours_per_day"], .5)
        multiplier = st.number_input("Overtime Multiplier", 1.0, 5.0, settings["overtime_multiplier"], .1)
        if st.form_submit_button("Save Settings", type="primary"):
            db.update_settings({"working_days_per_month":days,"default_working_hours_per_day":hours,"overtime_multiplier":multiplier})
            st.success("Settings saved successfully.")


def backup_export_page() -> None:
    header("Backup & Export", "Download CSV reports, create safe database copies, or load fictional demo data.")
    employees = db.get_employees()
    employee_csv = pd.DataFrame(employees).to_csv(index=False).encode("utf-8-sig") if employees else b""
    st.download_button("Download Employees CSV", employee_csv, "workpay_employees.csv", "text/csv", disabled=not employees)
    st.markdown("### Monthly Payroll Export")
    today = date.today()
    a,b = st.columns(2)
    month = a.selectbox("Month", range(1,13), index=today.month-1, format_func=month_name, key="export_month")
    year = b.number_input("Year", 2000, 2100, today.year, key="export_year")
    records = db.payroll_records("p.payroll_month=? AND p.payroll_year=?", (month, year))
    payroll_csv = pd.DataFrame(records).to_csv(index=False).encode("utf-8-sig") if records else b""
    st.download_button("Download Monthly Payroll CSV", payroll_csv, f"payroll_{year}_{month:02d}.csv", "text/csv", disabled=not records)
    st.markdown("### Database Backup")
    if st.button("Create Database Backup"):
        try:
            target = db.create_backup()
            st.success(f"Backup created successfully: {target.name}")
        except OSError as exc:
            st.error(f"Could not create backup: {exc}")
    st.markdown("### Demo Data")
    st.caption("Adds five fictional employees once. Existing demo records are not duplicated.")
    if st.button("Insert Demo Data"):
        count = db.insert_demo_data()
        st.success(f"Added {count} demo employee(s)." if count else "Demo data already exists.")


if login():
    st.sidebar.markdown("## 💼 WorkPay")
    st.sidebar.caption(APP_SUBTITLE)
    page = st.sidebar.radio("Navigation", ["Dashboard","Employees","Add Employee","Monthly Payroll",
        "Employee Search","Payroll History","Settings","Backup & Export"], label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
    pages = {"Dashboard":dashboard,"Employees":employees_page,"Add Employee":add_employee_page,
        "Monthly Payroll":monthly_payroll,"Employee Search":search_page,"Payroll History":history_page,
        "Settings":settings_page,"Backup & Export":backup_export_page}
    pages[page]()

