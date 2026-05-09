SEMANTIC_INTENT_MAP = {
    "salary_query": "net_pay",
    "payroll_breakdown": "net_pay",
    "deduction_reason": "deduction_reason",
    "salary_comparison": "deduction_reason",
    "tax_query": "tax_query",
    "ot_query": "ot_query",
    "reimbursement_query": "get_ot_reimbursement",
    "lop_query": "lop_query",
    "allowance_query": "allowance_query",
    "component_query": "get_field_value",
    "faq": "faq",
    "unknown": "unknown"
}

def classify_intent(query: str, semantic_result: dict = None) -> str:
    # -------------------------
    # 1. SEMANTIC HYBRID ROUTING (High Confidence)
    # -------------------------
    if semantic_result and semantic_result.get("confidence", 0) >= 0.75:
        s_intent = semantic_result.get("intent")
        mapped_intent = SEMANTIC_INTENT_MAP.get(s_intent)
        if mapped_intent and mapped_intent != "unknown":
            print(f"DEBUG: Using semantic intent: {mapped_intent} (confidence: {semantic_result['confidence']})")
            return mapped_intent

    q = str(query).lower().strip()

    # -------------------------
    # 0. SALARY SUM (Basic, HRA, LTA) - ABSOLUTE TOP PRIORITY
    # -------------------------
    if all(kw in q for kw in ["basic", "hra", "lta"]):
        return "get_salary_sum"

    # 🔥 HIGH PRIORITY RULES
    if "allowance type" in q:
        return "get_ot_allowance_type"
    if "reimbursement" in q or "period" in q:
        return "get_ot_reimbursement"
    if "taxable earning" in q:
        return "get_taxable_income"
    if "tax per month" in q or "pay tax" in q:
        return "get_income_tax"
    if "lta" in q:
        return "get_lta"
    if "tax paid" in q or "tax till date" in q:
        return "get_income_tax_till_date"
    if any(kw in q for kw in ["working days", "total days", "paid days"]):
        return "get_working_days"
    import re
    if "overtime" in q or re.search(r"\bot\b", q):
        return "get_ot_data"
    if "pf code" in q or "epf code" in q:
        return "security_block"

    # -------------------------
    # 1. SECURITY BLOCK (highest priority)
    # -------------------------
    PERSONAL_DATA_KEYWORDS = [
        "bank details", "bank account", "account number", "ifsc",
        "employee name", "other employee", "swapnil", "rahul", "riya",
        "details of", "details for", "payroll details of", "payroll details for",
        "payslip of", "payslip for",
        "share my bank", "personal data", "personal information",
        "my role", "my designation", "company name",
    ]
    if any(kw in q for kw in PERSONAL_DATA_KEYWORDS):
        # Only block if NOT about the user's own data (e.g. 'my payroll details for Jan 2026')
        is_self_query = bool(re.search(r"\bmy (?:payroll )?details\b", q)) or "my jan" in q or "my feb" in q or "my mar" in q
        is_specific_month_query = bool(re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b", q))
        # Only block if the query references other employees
        if not is_self_query and not (is_specific_month_query and "my" in q):
            return "security_block"

    # -------------------------
    # 2. SALARY SUM (Basic, HRA, LTA)
    # -------------------------
    if all(kw in q for kw in ["basic", "hra", "lta"]):
        return "get_salary_sum"

    # -------------------------
    # 3. COMPARISON / REASONING QUERIES
    # -------------------------
    REASONING_KEYWORDS = [
        "why salary", "salary reduced", "salary dropped", "salary decreased",
        "salary less", "why is my salary", "why my salary",
        "compare last 2", "compare last two", "last 2 months", "last two months",
        "compare", "difference between",
    ]
    if any(kw in q for kw in REASONING_KEYWORDS):
        if any(w in q for w in ["every month", "each month", "month on month", "changing month"]):
            return "get_salary_history"
        return "deduction_reason"
    # shift allowance → OT reimbursement (check ot_data table)
    if "shift allowance" in q:
        return "get_ot_reimbursement"

    # -------------------------
    # 3. OT / OVERTIME / REIMBURSEMENT
    # -------------------------
    OT_KEYWORDS = [
        "overtime", "night shift allowance", "shift allowance",
        "reimbursement", "reimb", "what was paid along",
        "allowance type", "allowance received", "saot",
    ]
    if any(kw in q for kw in OT_KEYWORDS):
        return "ot_query"

    # -------------------------
    # 4. TAX QUERIES
    # -------------------------
    TAX_KEYWORDS = [
        "tax", "tds", "regime", "old regime", "new regime",
        "taxable income", "net taxable", "tax liability",
        "income tax", "total tax", "how much tax",
        "total deduction from salary", "tax deduction from salary",
        "how much should i pay tax",
    ]
    if "tax" in q and ("till date" in q or "deduction from salary" in q or "deductions from salary" in q):
        return "tax_paid_till_date"
    
    # FY tax deduction → tax_paid_till_date from tax_data
    if "tax" in q and ("fy" in q or "financial year" in q or "2025-26" in q or "2025 26" in q):
        return "tax_paid_till_date"

    if "bank name" in q or "bank account" in q or "bank details" in q:
        return "get_field_value"

    if any(kw in q for kw in TAX_KEYWORDS):
        return "tax_query"

    # -------------------------
    # 5. LOP QUERIES
    # -------------------------
    LOP_KEYWORDS = [
        "lop", "loss of pay", "lop days", "lop deducted", "lop entries",
        "lop impact", "lop in", "my lop",
    ]
    if any(kw in q for kw in LOP_KEYWORDS):
        # LOP date query → lop_query for detailed dates
        if any(w in q for w in ["which date", "what date", "date of lop", "lop date", "when was lop"]):
            return "lop_query"
        # LOP impact on salary → analyze_salary for reasoning
        if any(w in q for w in ["less salary", "salary less", "is there any lop", "any lop", "deduction"]):
            return "deduction_reason"
        return "lop_query"

    # -------------------------
    # 6. FULL PAYROLL / BREAKDOWN
    # -------------------------
    PAYROLL_KEYWORDS = [
        "payroll", "payslip", "pay slip", "salary details",
        "components", "all components", "full breakdown",
        "share my payroll", "my payroll details",
        "annual salary structure", "annual structure",
        "list of all components",
    ]
    if any(kw in q for kw in PAYROLL_KEYWORDS):
        return "net_pay"

    # -------------------------
    # 7. ALLOWANCE / EARNINGS
    # -------------------------
    ALLOWANCE_KEYWORDS = [
        "allowance", "earnings", "earning components", "what allowance",
        "total allowance", "all earnings",
    ]
    if any(kw in q for kw in ALLOWANCE_KEYWORDS):
        return "allowance_query"

    # -------------------------
    # 8. DEDUCTION QUERIES
    # -------------------------
    DEDUCTION_KEYWORDS = [
        "deduction", "deductions", "what are all the deductions",
    ]
    if any(kw in q for kw in DEDUCTION_KEYWORDS):
        return "deduction_query"

    # -------------------------
    # 9. NET PAY / SALARY QUERIES
    # -------------------------
    SALARY_KEYWORDS = [
        "net pay", "take home", "in hand", "my salary", "net salary",
        "total salary", "gross salary", "latest payroll", "latest pay",
        "working days", "paid days", "total days",
        "total pay", "what is my pay",
    ]
    if any(kw in q for kw in SALARY_KEYWORDS):
        return "net_pay"

    # -------------------------
    # 11. FAQ FALLBACK
    # -------------------------
    FAQ_KEYWORDS = [
        "how do i", "how can i", "whom should i", "who should i contact",
        "process", "policy", "portal", "form", "login", "password",
        "pf portal", "pan update", "nps", "sodexo", "fbp", "documents",
    ]
    if any(kw in q for kw in FAQ_KEYWORDS):
        return "faq"

    # -------------------------
    # 11. DEFAULT
    # -------------------------
    if "my" in q or any(char.isdigit() for char in q):
        return "net_pay"

    return "unknown"