from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PayrollCalculation:
    basic_salary: float
    daily_rate: float
    hourly_rate: float
    overtime_amount: float
    bonuses: float
    absence_deduction: float
    late_deduction: float
    other_deductions: float
    advances: float
    net_salary: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def calculate_payroll(
    basic_salary: float,
    working_days: int,
    working_hours: float,
    overtime_hours: float = 0,
    overtime_multiplier: float = 1.5,
    absence_days: float = 0,
    late_hours: float = 0,
    bonuses: float = 0,
    other_deductions: float = 0,
    advances: float = 0,
) -> PayrollCalculation:
    values = [basic_salary, working_days, working_hours, overtime_hours,
              overtime_multiplier, absence_days, late_hours, bonuses,
              other_deductions, advances]
    if any(value < 0 for value in values):
        raise ValueError("Payroll values cannot be negative.")
    if basic_salary <= 0 or working_days <= 0 or working_hours <= 0:
        raise ValueError("Salary, working days, and working hours must be greater than zero.")

    daily_rate = basic_salary / working_days
    hourly_rate = daily_rate / working_hours
    overtime_amount = overtime_hours * hourly_rate * overtime_multiplier
    absence_deduction = absence_days * daily_rate
    late_deduction = late_hours * hourly_rate
    net_salary = (basic_salary + overtime_amount + bonuses - absence_deduction
                  - late_deduction - other_deductions - advances)
    rounded = [round(v, 2) for v in (basic_salary, daily_rate, hourly_rate,
                overtime_amount, bonuses, absence_deduction, late_deduction,
                other_deductions, advances, net_salary)]
    return PayrollCalculation(*rounded)


def total_deductions(record: dict) -> float:
    return round(sum(float(record.get(key, 0) or 0) for key in
                     ("absence_deduction", "late_deduction", "other_deductions")), 2)

