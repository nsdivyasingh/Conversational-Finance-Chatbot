from __future__ import annotations

from typing import Any

from sqlalchemy import text

from query_engine import engine
from metadata.field_registry import FieldRegistry

ALLOWED_TOOLS = {
    "get_salary",
    "get_lop",
    "get_tax",
    "get_ot",
    "get_ot_reimbursement",
    "analyze_salary",
    "get_full_salary_breakdown",
    "get_allowance_breakdown",
    "get_field_value",
    "get_salary_sum",
    "analyze_salary_reason",
    "get_salary_history",
}


def _normalize_month_year(month: str | None, year: int | None) -> tuple[str | None, int | None]:
    if month is None:
        return None, year
    clean_month = month.strip().title()
    if not clean_month:
        return None, year
    if "-" in clean_month and year is None:
        month_part, year_part = clean_month.split("-", 1)
        try:
            return month_part.strip().title(), int(year_part.strip())
        except ValueError:
            return clean_month.title(), None
    return clean_month, year


def _validate_inputs(employee_id: int, month: str | None, year: int | None) -> dict[str, Any] | None:
    if employee_id is None:
        return {"status": "error", "message": "employee_id is required", "data": []}
    try:
        employee_id = int(employee_id)
    except (TypeError, ValueError):
        return {"status": "error", "message": "employee_id must be an integer", "data": []}
    if employee_id <= 0:
        return {"status": "error", "message": "employee_id must be positive", "data": []}
    if month is not None and not str(month).strip():
        return {"status": "error", "message": "month cannot be empty", "data": []}
    if year is not None:
        try:
            int(year)
        except (TypeError, ValueError):
            return {"status": "error", "message": "year must be an integer", "data": []}
    return None


def employee_exists(employee_id: int) -> bool:
    query = text("SELECT 1 FROM employee_master WHERE employee_id = :emp_id LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_id": employee_id}).fetchone()
    return row is not None

def get_employee_id_by_code(employee_code: str) -> int | None:
    query = text("SELECT employee_id FROM employee_master WHERE employee_code = :emp_code LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_code": str(employee_code).strip()}).fetchone()
    return row[0] if row else None


def get_salary(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_salary", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_salary", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded, pt_ded, pf_ded, lopd
            FROM pay_register
            WHERE employee_id = :emp_id
            AND month = :month
            AND eyear = :year
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded, pt_ded, pf_ded, lopd
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded, pt_ded, pf_ded, lopd
            FROM pay_register
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] salary -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows and month and year is not None:
        # Auto-fallback: fetch latest available month
        month_case = _month_sort_case("month")
        fallback_query = text(
            f"""
            SELECT month, eyear, total_netpay, gross_earning, gross_deduction, income_tax_ded, pt_ded, pf_ded, lopd
            FROM pay_register
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, {month_case} DESC
            LIMIT 1
            """
        )
        with engine.connect() as conn:
            rows = [dict(row._mapping) for row in conn.execute(fallback_query, {"emp_id": employee_id}).fetchall()]
        if rows:
            return {
                "tool": "get_salary",
                "status": "success_fallback",
                "data": rows,
                "message": ""
            }
    if not rows:
        return {"tool": "get_salary", "status": "no_data", "message": "No salary data found", "data": []}
    return {"tool": "get_salary", "status": "success", "data": rows}


def get_lop(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_lop", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_lop", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        month_year = f"{month}-{year}"
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id 
            AND (month = :month OR month = :month_year)
            AND EXTRACT(YEAR FROM lop_date) = :year
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id, "month": month, "month_year": month_year, "year": year}
    elif month:
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id 
            AND (month = :month OR month LIKE :month_pattern)
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id, "month": month, "month_pattern": f"{month}-%"}
    else:
        query = text(
            """
            SELECT month, lop_date, lop_days
            FROM lop_data
            WHERE employee_id = :emp_id
            ORDER BY lop_date DESC
            LIMIT 15
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] lop -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_lop", "status": "no_data", "message": "No LOP data found", "data": []}
    return {"tool": "get_lop", "status": "success", "data": rows}


def get_tax(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_tax", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_tax", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id AND month = :month AND eyear = :year
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, eyear, total_tax_liability
            FROM tax_data
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, month DESC
            LIMIT 3
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] tax -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_tax", "status": "no_data", "message": "No tax data found", "data": []}
    return {"tool": "get_tax", "status": "success", "data": rows}


def get_ot(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_ot", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_ot", "status": "no_data", "message": "Employee not found", "data": []}

    if month and year is not None:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id AND month = :month
            AND EXTRACT(YEAR FROM from_date) = :year
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id, "month": month, "year": year}
    elif month:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id AND month = :month
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id, "month": month}
    else:
        query = text(
            """
            SELECT month, allowance_type, from_date, to_date, component_in_pay_slip, paid_amount
            FROM ot_data
            WHERE employee_id = :emp_id
            ORDER BY from_date DESC
            LIMIT 20
            """
        )
        params = {"emp_id": employee_id}

    print(f"[QUERY] ot -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, params).fetchall()]
    if not rows:
        return {"tool": "get_ot", "status": "no_data", "message": "No OT/allowance data found", "data": []}
    return {"tool": "get_ot", "status": "success", "data": rows}

def get_ot_reimbursement(employee_id: int, month: str | None = None, year: int | None = None, from_date: str | None = None, to_date: str | None = None, amount: float | None = None) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_ot_reimbursement", **validation_error}
    if not employee_exists(employee_id):
        return {"tool": "get_ot_reimbursement", "status": "no_data", "message": "Employee not found", "data": []}

    query_str = """
        SELECT month, allowance_type, from_date, to_date, paid_amount, component_in_pay_slip
        FROM ot_data
        WHERE employee_id = :emp_id
    """
    params = {"emp_id": employee_id}
    
    # Amount filtering
    if amount is not None:
        query_str += " AND (paid_amount BETWEEN :amt_min AND :amt_max) "
        params.update({"amt_min": amount - 1, "amt_max": amount + 1})

    # Prioritize specific period if available
    if from_date and to_date:
        query_str += " AND ((from_date >= :from_date AND from_date <= :to_date) OR (to_date >= :from_date AND to_date <= :to_date)) "
        params.update({"from_date": from_date, "to_date": to_date})
    elif month and year is not None:
        month_year = f"{month}-{year}"
        query_str += " AND month = :month_year "
        params.update({"month_year": month_year})
    elif month:
        query_str += " AND month LIKE :month_pattern "
        params.update({"month_pattern": f"{month}-%"})
    
    query_str += " ORDER BY from_date DESC LIMIT 20 "

    print(f"DEBUG: OT Query: {query_str}")
    print(f"DEBUG: OT Params: {params}")

    with engine.connect() as conn:
        res = conn.execute(text(query_str), params)
        rows = [dict(row._mapping) for row in res.fetchall()]
        print(f"DEBUG: OT Row Count: {len(rows)}")
    
    if not rows and (month or year):
        fallback_query = """
            SELECT month, allowance_type, from_date, to_date, paid_amount, component_in_pay_slip
            FROM ot_data
            WHERE employee_id = :emp_id
            ORDER BY from_date DESC
            LIMIT 5
        """
        with engine.connect() as conn:
            res = conn.execute(text(fallback_query), {"emp_id": employee_id})
            rows = [dict(row._mapping) for row in res.fetchall()]
        if rows:
            return {"tool": "get_ot_reimbursement", "status": "success_fallback", "message": f"No records found for {month}-{year}.", "data": rows}

    if not rows:
        return {"tool": "get_ot_reimbursement", "status": "no_data", "message": "No reimbursement data found", "data": []}

    return {"tool": "get_ot_reimbursement", "status": "success", "data": rows}

def _first_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    return rows[0] if rows else None


def analyze_salary(employee_id, month, year, previous_month, previous_year):

    current = get_full_salary_breakdown(employee_id, month, year)
    previous = get_full_salary_breakdown(employee_id, previous_month, previous_year) if previous_month and previous_year else {}

    if current.get("status") != "success":
        reasons = []
        reasons.append(f"We could not find any salary records for {month} {year}.")
            
        return {
            "tool": "analyze_salary",
            "status": "success",
            "data": {
                "current": None,
                "previous": None,
                "reasons": reasons,
                "primary_reason": "missing_current_data"
            }
        }

    curr = current.get("data", {})
    prev = previous.get("data", {}) if previous.get("status") == "success" else None

    return {
        "tool": "analyze_salary",
        "status": "success",
        "data": {
            "current": curr,
            "previous": prev
        }
    }

def analyze_salary_reason(employee_id, month, year, previous_month=None, previous_year=None):
    # Fetch current and previous breakdowns
    current = get_full_salary_breakdown(employee_id, month, year)
    previous = get_full_salary_breakdown(employee_id, previous_month, previous_year) if previous_month and previous_year else {}
    
    # Also fetch OT/allowance data for context
    allowances = get_ot_reimbursement(employee_id, month, year)
    
    return {
        "current": current.get("data") if current.get("status") == "success" else {},
        "previous": previous.get("data") if previous.get("status") == "success" else {},
        "allowance": allowances.get("data") if allowances.get("status") == "success" else []
    }


def execute_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    tool = str(tool_name).strip().lower()
    if tool not in ALLOWED_TOOLS:
        return {
            "tool": tool_name,
            "status": "error",
            "message": f"Unsupported tool '{tool_name}'",
            "data": [],
        }

    employee_id = params.get("employee_id")
    month = params.get("month")
    year = params.get("year")
    try:
        if tool == "get_salary":
            return get_salary(employee_id=employee_id, month=month, year=year)
        if tool == "get_lop":
            return get_lop(employee_id=employee_id, month=month, year=year)
        if tool == "get_tax":
            return get_tax(employee_id=employee_id, month=month, year=year)
        if tool == "get_ot":
            return get_ot(employee_id=employee_id, month=month, year=year)
        if tool == "get_ot_reimbursement":
            return get_ot_reimbursement(
                employee_id=employee_id, 
                month=month, 
                year=year,
                from_date=params.get("from_date"),
                to_date=params.get("to_date")
            )
        if tool == "get_allowance_breakdown":
            return get_allowance_breakdown(employee_id=employee_id, month=month, year=year)
        if tool == "get_field_value":
            return get_field_value(
                employee_id=employee_id,
                field_key=params.get("field_key"),
                table=params.get("table"),
                column=params.get("column"),
                month=month,
                year=year,
            )
        if tool == "get_salary_sum":
            return get_salary_sum(employee_id=employee_id, month=month, year=year)
        if tool == "analyze_salary_reason":
            return analyze_salary_reason(employee_id=employee_id, month=month, year=year, previous_month=params.get("previous_month"), previous_year=params.get("previous_year"))
        
        if tool == "get_salary_history":
            return get_salary_history(employee_id=employee_id)
        
        if tool == "get_full_salary_breakdown":
            return get_full_salary_breakdown(employee_id=employee_id, month=month, year=year)
        return analyze_salary(
            employee_id=employee_id,
            month=month,
            year=year,
            previous_month=params.get("previous_month"),
            previous_year=params.get("previous_year"),
        )
    except Exception as exc:
        return {
            "tool": tool_name,
            "status": "error",
            "message": str(exc),
            "data": [],
        }


def get_full_salary_breakdown(
    employee_id: int, month: str | None = None, year: int | None = None
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_full_salary_breakdown", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_full_salary_breakdown",
            "status": "no_data",
            "message": "Employee not found",
            "data": {},
        }
    if month is None or year is None:
        # Auto-fetch the latest available month
        month_case = _month_sort_case("month")
        latest_q = text(f"SELECT * FROM pay_register_raw WHERE employee_id = :emp_id ORDER BY eyear DESC, {month_case} DESC LIMIT 1")
        with engine.connect() as conn:
            latest_row = conn.execute(latest_q, {"emp_id": employee_id}).mappings().fetchone()
        if not latest_row:
            return {"tool": "get_full_salary_breakdown", "status": "no_data", "message": "No breakdown data found", "data": {}}
        # Extract month/year from latest row and recurse
        raw = dict(latest_row)
        raw_m = str(raw.get("month", ""))
        if "-" in raw_m:
            parts = raw_m.split("-", 1)
            month = parts[0].strip()
            year = int(parts[1].strip())
        else:
            month = raw_m
            year = raw.get("eyear")

    month_year = f"{month}-{year}"
    query = """
    SELECT *
    FROM pay_register_raw
    WHERE employee_id = :emp_id
      AND month = :month_year
    """

    print(f"[QUERY] full_breakdown -> emp={employee_id}, month={month}, year={year}")
    with engine.connect() as conn:
        result = (
            conn.execute(
                text(query),
                {
                    "emp_id": employee_id,
                    "month_year": month_year,
                },
            )
            .mappings()
            .fetchone()
        )
    print("DEBUG PARAMS:", employee_id, month, year)
    print("DEBUG RESULT:", result)

    if not result:
        # Fallback to latest
        month_case = _month_sort_case("month")
        fallback_query = text(f"SELECT * FROM pay_register_raw WHERE employee_id = :emp_id ORDER BY eyear DESC, {month_case} DESC LIMIT 1")
        with engine.connect() as conn:
            result = conn.execute(fallback_query, {"emp_id": employee_id}).mappings().fetchone()
            
        if result:
            status = "success_fallback"
            fallback_msg = ""
        else:
            return {
                "tool": "get_full_salary_breakdown",
                "status": "no_data",
                "message": "No breakdown data found",
                "data": {
                    "month": month,
                    "eyear": year,
                    "earnings": {},
                    "deductions": {},
                    "total_netpay": 0
                },
            }
    else:
        status = "success"
        fallback_msg = ""

    EARNING_MAPPING = {
        "basic": "Basic Pay",
        "h_r_a": "House Rent Allowance (HRA)",
        "lta": "Leave Travel Allowance (LTA)",
        "gratuity": "Gratuity",
        "leave_encash": "Leave Encashment",
        "mange_allow": "Management Allowance",
        "other_allowance": "Other Allowance",
        "yearly_bonus": "Yearly Bonus",
        "incentive": "Incentive",
        "night_shift_all": "Night Shift Allowance",
        "nontax": "Non-Tax Amount",
        "referal_bonus": "Referral Bonus",
        "joibon": "Joining Bonus",
        "relocation": "Relocation Allowance",
        "salary_advance": "Salary Advance Earnings",
        "sign_tenure_bon": "Sign-on/Tenure Bonus",
        "notice_per_pay": "Notice Period Pay",
        "misc_earn": "Miscellaneous Earnings",
        "tele_reimb": "Telephone Reimbursement",
        "serweigh": "Service Weightage",
        "prof_developmnt": "Professional Development",
        "maternity_bonus": "Maternity Bonus"
    }

    DEDUCTION_MAPPING = {
        "pt_ded": "Professional Tax (PT)",
        "pf_ded": "Provident Fund (PF)",
        "esi_employee_ded": "ESI (Employee)",
        "vpf_ded": "VPF Deduction",
        "l_w_f_ded": "Labour Welfare Fund",
        "sal_adv_ded": "Salary Advance Deduction",
        "notice_per_ded_ded": "Notice Period Deduction",
        "medical_ins_par_ded": "Medical Insurance (Parent)",
        "oth_dedu_ded": "Other Deduction 1",
        "other_ded_2_ded": "Other Deduction 2",
        "income_tax_ded": "Income Tax"
    }

    data = dict(result)
    earnings = {}
    for db_col, label in EARNING_MAPPING.items():
        val = data.get(db_col)
        if val is not None and float(val) != 0:
            earnings[label] = float(val)

    deductions = {}
    for db_col, label in DEDUCTION_MAPPING.items():
        val = data.get(db_col)
        if val is not None and float(val) != 0:
            deductions[label] = float(val)
    return {
        "tool": "get_full_salary_breakdown",
        "status": status,
        "message": fallback_msg,
        "data": {
            "month": data.get("month", month),
            "eyear": data.get("eyear", year),
            "earnings": earnings,
            "deductions": deductions,
            "total_netpay": float(data.get("total_netpay") or 0),
            "gross_earning": float(data.get("gross_earning") or 0),
            "gross_deduction": float(data.get("gross_deduction") or 0),
            "lop_days": float(data.get("lopd") or 0)
        },
    }

def get_allowance_breakdown(
    employee_id: int, month: str | None = None, year: int | None = None
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_allowance_breakdown", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_allowance_breakdown",
            "status": "no_data",
            "message": "Employee not found",
            "data": {},
        }
    if month is None or year is None:
        return {
            "tool": "get_allowance_breakdown",
            "status": "error",
            "message": "month and year are required for allowance breakdown",
            "data": {},
        }

    month_year = f"{month}-{year}"

    query = """
    SELECT 
        other_allowance,
        bonus,
        incentive,
        night_shift_all
    FROM pay_register_raw
    WHERE employee_id = :emp_id
      AND month = :month_year
    """
    print(f"[QUERY] allowance_breakdown -> emp={employee_id}, month={month}, year={year}")

    with engine.connect() as conn:
        result = conn.execute(
            text(query),
            {"emp_id": employee_id, "month_year": month_year}
        ).mappings().fetchone()

    if not result:
        return {
            "tool": "get_allowance_breakdown",
            "status": "no_data",
            "message": "No allowance breakdown data found",
            "data": {},
        }

    data = dict(result)
    
    total = sum([
        float(data.get("bonus") or 0),
        float(data.get("incentive") or 0),
        float(data.get("other_allowance") or 0),
        float(data.get("night_shift_all") or 0),
    ])

    return {
        "tool": "get_allowance_breakdown",
        "status": "success",
        "data": {
            "total_allowance": total,
            "components": data
        }
    }


def _month_sort_case(alias: str = "month") -> str:
    return (
        f"CASE SUBSTRING({alias}, 1, 3) "
        "WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3 WHEN 'Apr' THEN 4 "
        "WHEN 'May' THEN 5 WHEN 'Jun' THEN 6 WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 "
        "WHEN 'Sep' THEN 9 WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12 "
        "ELSE 0 END"
    )


def get_field_value(
    employee_id: int,
    field_key: str,
    table: str,
    column: str,
    month: str | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    month, year = _normalize_month_year(month, year)
    validation_error = _validate_inputs(employee_id, month, year)
    if validation_error:
        return {"tool": "get_field_value", **validation_error}
    if not employee_exists(employee_id):
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": "Employee not found",
            "data": None,
        }

    field_meta = FieldRegistry.get_field(str(field_key or ""))
    if not field_meta:
        return {
            "tool": "get_field_value",
            "status": "error",
            "message": f"Unknown field '{field_key}'",
            "data": None,
        }
    if table != field_meta["table"] or column != field_meta["column"]:
        return {
            "tool": "get_field_value",
            "status": "error",
            "message": "Field/table/column mismatch",
            "data": None,
        }

    month_case = _month_sort_case("month")

    # Check if eyear/month exists in table
    with engine.connect() as conn:
        has_eyear = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'eyear'")).fetchone()
        has_month = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'month'")).fetchone()
        
    month_year = f"{month}-{year}" if month and year is not None else None
    
    if month and year is not None:
        if has_month:
            if has_eyear:
                query = text(
                    f"""
                    SELECT {column} AS value, month, eyear
                    FROM {table}
                    WHERE employee_id = :emp_id
                      AND (month = :month OR month = :month_year)
                      AND eyear = :year
                    LIMIT 1
                    """
                )
                params = {"emp_id": employee_id, "month": month, "month_year": month_year, "year": year}
            else:
                query = text(
                    f"""
                    SELECT {column} AS value, month
                    FROM {table}
                    WHERE employee_id = :emp_id
                      AND (month = :month OR month = :month_year)
                    LIMIT 1
                    """
                )
                params = {"emp_id": employee_id, "month": month, "month_year": month_year}
        else:
            # Table has no month column (e.g. tax_data_raw)
            if has_eyear:
                query = text(f"SELECT {column} AS value, eyear FROM {table} WHERE employee_id = :emp_id AND eyear = :year LIMIT 1")
                params = {"emp_id": employee_id, "year": year}
            else:
                query = text(f"SELECT {column} AS value FROM {table} WHERE employee_id = :emp_id LIMIT 1")
                params = {"emp_id": employee_id}
    else:
        if has_eyear:
            query = text(
                f"""
                SELECT {column} AS value, month, eyear
                FROM {table}
                WHERE employee_id = :emp_id
                ORDER BY eyear DESC, {month_case} DESC
                LIMIT 1
                """
            )
        else:
            query = text(
                f"""
                SELECT {column} AS value, month
                FROM {table}
                WHERE employee_id = :emp_id
                ORDER BY month DESC
                LIMIT 1
                """
            )
        params = {"emp_id": employee_id}

    print(
        f"[QUERY] field_value -> field={field_key}, table={table}, column={column}, "
        f"emp={employee_id}, month={month}, year={year}"
    )
    with engine.connect() as conn:
        row = conn.execute(query, params).mappings().fetchone()

    if not row and month and year is not None:
        fallback_query = text(
            f"""
            SELECT {column} AS value, month, eyear
            FROM {table}
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, {month_case} DESC
            LIMIT 1
            """
        )
        with engine.connect() as conn:
            row = conn.execute(fallback_query, {"emp_id": employee_id}).mappings().fetchone()
        if row:
            data = dict(row)
            fallback_month = str(data.get("month") or "")
            fallback_year = data.get("eyear")
            if "-" in fallback_month:
                fallback_to = fallback_month
            else:
                fallback_to = f"{fallback_month}-{fallback_year}"
            fallback_m = data.get("month")
            fallback_y = data.get("eyear")
            return {
                "tool": "get_field_value",
                "status": "success_fallback",
                "field_key": field_key,
                "value": data.get("value"),
                "month": fallback_m,
                "year": fallback_y,
                "fallback_to": fallback_to,
                "original_request": f"{month}-{year}",
                "message": "",
                "data": data,
            }

    if not row:
        return {
            "tool": "get_field_value",
            "status": "no_data",
            "message": f"No data found for {field_key}",
            "data": None,
        }

    data = dict(row)
    return {
        "tool": "get_field_value",
        "status": "success",
        "field_key": field_key,
        "value": data.get("value"),
        "month": data.get("month") if "month" in data else None,
        "year": data.get("eyear") or data.get("year"),
        "data": {**data, "year": data.get("eyear") or data.get("year")},
    }


def get_salary_sum(employee_id: int, month: str | None = None, year: int | None = None) -> dict[str, Any]:
    """Calculates the sum of Basic Pay, HRA and LTA."""
    month, year = _normalize_month_year(month, year)
    
    query = text("""
        SELECT basic, h_r_a, lta, month, eyear
        FROM pay_register
        WHERE employee_id = :emp_id
          AND (month = :month OR month = :month_year)
          AND eyear = :year
    """)
    month_year = f"{month}-{year}" if month and year is not None else None
    
    with engine.connect() as conn:
        row = conn.execute(query, {"emp_id": employee_id, "month": month, "month_year": month_year, "year": year}).mappings().fetchone()
        
    if not row:
        # Fallback to latest
        fallback_query = text(f"""
            SELECT basic, h_r_a, lta, month, eyear
            FROM pay_register
            WHERE employee_id = :emp_id
            ORDER BY eyear DESC, {_month_sort_case()} DESC
            LIMIT 1
        """)
        with engine.connect() as conn:
            row = conn.execute(fallback_query, {"emp_id": employee_id}).mappings().fetchone()
            
    if not row:
        return {"tool": "get_salary_sum", "status": "no_data", "message": "No salary data found"}
        
    data = dict(row)
    total = float(data.get("basic") or 0) + float(data.get("h_r_a") or 0) + float(data.get("lta") or 0)
    
    return {
        "tool": "get_salary_sum",
        "status": "success",
        "total": total,
        "data": {
            "basic": float(data.get("basic") or 0),
            "hra": float(data.get("h_r_a") or 0),
            "lta": float(data.get("lta") or 0),
            "total": total,
            "month": data.get("month"),
            "year": data.get("eyear")
        }
    }


def get_salary_history(employee_id: int) -> dict[str, Any]:
    """Fetches salary records for the latest 3 months."""
    if not employee_exists(employee_id):
        return {"tool": "get_salary_history", "status": "no_data", "message": "Employee not found"}

    month_case = _month_sort_case("month")
    query = text(f"""
        SELECT month, eyear, total_netpay, gross_earning, gross_deduction, lopd
        FROM pay_register
        WHERE employee_id = :emp_id
        ORDER BY eyear DESC, {month_case} DESC
        LIMIT 3
    """)

    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(query, {"emp_id": employee_id}).fetchall()]

    if not rows:
        return {"tool": "get_salary_history", "status": "no_data", "message": "No salary data found"}

    return {"tool": "get_salary_history", "status": "success", "data": rows}


