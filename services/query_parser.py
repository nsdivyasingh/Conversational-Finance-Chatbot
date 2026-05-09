from __future__ import annotations

import re
from datetime import datetime
from typing import Any
import os
import json
import google.generativeai as genai

from metadata.field_registry import FieldRegistry

MONTH_ALIASES = {
    "jan": "Jan",
    "january": "Jan",
    "feb": "Feb",
    "february": "Feb",
    "mar": "Mar",
    "march": "Mar",
    "apr": "Apr",
    "april": "Apr",
    "may": "May",
    "jun": "Jun",
    "june": "Jun",
    "jul": "Jul",
    "july": "Jul",
    "aug": "Aug",
    "august": "Aug",
    "sep": "Sep",
    "sept": "Sep",
    "september": "Sep",
    "oct": "Oct",
    "october": "Oct",
    "nov": "Nov",
    "november": "Nov",
    "dec": "Dec",
    "december": "Dec",
}

MONTH_TO_NUMBER = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def extract_query_params(query: str) -> dict[str, Any]:
    q = str(query).lower().strip()
    parsed: dict[str, Any] = {
        "intent": "unknown",
        "field_request": None,
        "month": None,
        "year": None,
        "compare_prev": False,
        "relative_time": None,
        "fy_start": None,
        "query_type": None,
        "raw": query,
    }

    field_request = FieldRegistry.find_field(q)
    if field_request:
        parsed["field_request"] = field_request
        field_meta = FieldRegistry.get_field(field_request) or {}
        category = field_meta.get("category")

    # The actual intent will be passed in from intent_router in chat_service
    # We remove the custom keyword logic here to ensure single source of truth.
    
    if "net taxable" in q or "taxable income" in q:
        parsed["field_request"] = "net_taxable_income"

    if any(
        kw in q
        for kw in [
            "less than last month",
            "less than previous month",
            "why salary less",
            "why is my salary less",
            "salary less than",
            "my salary is less",
            "salary decreased",
            "salary dropped",
            "salary reduced",
        ]
    ):
        parsed["compare_prev"] = True

    if "last month" in q or "previous month" in q:
        parsed["relative_time"] = "last_month"
    elif "this month" in q or "current month" in q:
        parsed["relative_time"] = "this_month"
    elif "this year" in q or "current year" in q or "this financial year" in q:
        parsed["relative_time"] = "this_year"
    elif "last year" in q or "previous year" in q or "last financial year" in q:
        parsed["relative_time"] = "last_year"

    # Period extraction: "period of Oct 1, 2025 to Oct 31, 2025"
    period_match = re.search(
        r"period of\s+([a-zA-Z]{3,})\s+(\d{1,2}),?\s+(\d{4})\s+to\s+([a-zA-Z]{3,})\s+(\d{1,2}),?\s+(\d{4})",
        q
    )
    if period_match:
        m1, d1, y1, m2, d2, y2 = period_match.groups()
        try:
            from_date = datetime.strptime(f"{m1[:3].title()} {int(d1)} {y1}", "%b %d %Y")
            to_date = datetime.strptime(f"{m2[:3].title()} {int(d2)} {y2}", "%b %d %Y")
            parsed["from_date"] = from_date.strftime("%Y-%m-%d")
            parsed["to_date"] = to_date.strftime("%Y-%m-%d")
        except:
            pass

    fy_match = re.search(r"\bfy\s*(20\d{2}|\d{2})(?:-(20\d{2}|\d{2}))?\b", q)
    if fy_match:
        fy = int(fy_match.group(1))
        if fy < 100:
            fy += 2000
        parsed["fy_start"] = fy

    def normalize_month_year(text):
        # 1. Try "Month Day, Year" or "Month Year" (prefer 4-digit year)
        my_match = re.search(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\b(?:[^0-9]*(\d{1,2}))?[^0-9]*(\d{4})\b",
            text,
        )
        if my_match:
            month = MONTH_ALIASES[my_match.group(1).lower()]
            year = int(my_match.group(3))
            return month, year

        # 2. Try "Month YY"
        my_match_2 = re.search(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\s*,?\s*(\d{2})\b",
            text,
        )
        if my_match_2:
            month = MONTH_ALIASES[my_match_2.group(1).lower()]
            year = int(my_match_2.group(2))
            if year < 100:
                year += 2000
            return month, year
        
        # Explicit formats: "2026 Jan", "26 January"
        ym_match = re.search(
            r"\b(\d{4})\s*,?\s*(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
            r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\b",
            text,
        )
        if ym_match:
            year = int(ym_match.group(1))
            month = MONTH_ALIASES[ym_match.group(2).lower()]
            return month, year
            
        return None, None

    month, year = normalize_month_year(q)
    if month and year:
        parsed["month"] = month
        parsed["year"] = year
    else:
        year_match = re.search(r"\b(20\d{2})\b", q)
        if year_match:
            parsed["year"] = int(year_match.group(1))
        month_match = re.search(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\b",
            q,
        )
        if month_match:
            parsed["month"] = MONTH_ALIASES[month_match.group(1).lower()]

    # Extract amount if present
    amount_match = re.search(r"(?:rs\.?|inr|amount of|of)\s*([\d,]+)", q)
    if amount_match:
        try:
            amt_str = amount_match.group(1).replace(",", "")
            parsed["amount"] = float(amt_str)
        except:
            pass

    return parsed


def normalize_time(parsed: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    normalized = dict(parsed)
    normalized["time_valid"] = True
    normalized["time_error"] = None

    month = normalized.get("month")
    year = normalized.get("year")
    relative_time = normalized.get("relative_time")

    if relative_time == "this_month":
        normalized["month"] = now.strftime("%b")
        normalized["year"] = now.year
    elif relative_time == "last_month":
        if now.month == 1:
            normalized["month"] = "Dec"
            normalized["year"] = now.year - 1
        else:
            prev_date = datetime(now.year, now.month - 1, 1)
            normalized["month"] = prev_date.strftime("%b")
            normalized["year"] = prev_date.year
    elif relative_time == "this_year":
        normalized["fy_start"] = now.year if now.month >= 4 else now.year - 1
    elif relative_time == "last_year":
        normalized["fy_start"] = now.year - 1 if now.month >= 4 else now.year - 2
        
        if "last year" in parsed.get("raw", "").lower():
            normalized["year"] = now.year - 1
    else:
        normalized["fy_start"] = parsed.get("fy_start")
        
        if month and year is None and not normalized.get("fy_start"):
            normalized["year"] = now.year
        elif not month and not year and not normalized.get("fy_start"):
            # Default to current month/year for fallback detection
            normalized["month"] = now.strftime("%b")
            normalized["year"] = now.year
            
    # For tax queries, fy_start 2026 means FY 2026-27 which ends in 2027
    if normalized.get("fy_start") and not normalized.get("year"):
        normalized["year"] = normalized["fy_start"] + 1

    from metadata.query_context import QueryContext
    qt = QueryContext.determine_query_type(
        query=parsed["raw"], 
        parsed_intent=parsed["intent"], 
        field_request=parsed.get("field_request")
    )
    normalized["query_type"] = qt.value if hasattr(qt, "value") else qt

    if normalized.get("month") and normalized.get("year"):
        normalized["month_year"] = f"{normalized['month']}-{normalized['year']}"
    else:
        normalized["month_year"] = None

    # Future-period rejection to avoid impossible payroll lookups.
    if normalized.get("month") and normalized.get("year"):
        query_month_num = MONTH_TO_NUMBER[normalized["month"]]
        if normalized["year"] > now.year or (
            normalized["year"] == now.year and query_month_num > now.month
        ):
            normalized["time_valid"] = False
            normalized["time_error"] = (
                f"Salary data is not available for future dates ({normalized['month']}-{normalized['year']})."
            )
    elif normalized.get("year") and normalized["year"] > now.year:
        normalized["time_valid"] = False
        normalized["time_error"] = (
            f"Salary data is not available for future dates ({normalized['year']})."
        )

    if normalized.get("compare_prev") and normalized.get("month") and normalized.get("year"):
        month_num = MONTH_TO_NUMBER[normalized["month"]]
        if month_num == 1:
            normalized["previous_month"] = "Dec"
            normalized["previous_year"] = normalized["year"] - 1
        else:
            prev = datetime(normalized["year"], month_num - 1, 1)
            normalized["previous_month"] = prev.strftime("%b")
            normalized["previous_year"] = prev.year
    else:
        normalized["previous_month"] = None
        normalized["previous_year"] = None

    # STEP 1 — ADD PREVIOUS MONTH LOGIC
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    intent = parsed.get("intent")

    # ONLY for reasoning queries
    if intent == "deduction_reason" or normalized.get("compare_prev"):
        if not normalized.get("previous_month"):
            m = normalized.get("month") or now.strftime("%b")
            y = normalized.get("year") or now.year
            try:
                idx = MONTHS.index(m)
                if idx == 0:
                    prev_month = "Dec"
                    prev_year = y - 1
                else:
                    prev_month = MONTHS[idx - 1]
                    prev_year = y
                
                normalized["previous_month"] = prev_month
                normalized["previous_year"] = prev_year
                
                if not normalized.get("month"):
                    normalized["month"] = m
                if not normalized.get("year"):
                    normalized["year"] = y
            except ValueError:
                pass

    normalized["field_request"] = parsed.get("field_request")

    return normalized


def semantic_parse_query(query: str) -> dict[str, Any] | None:
    """
    Uses Gemini to perform semantic analysis of the payroll query.
    Returns a dict with intent, confidence, rewritten_query, and entities.
    """
    api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyBXvpNdQiwkE8_Zs0a6Py6ctGXI2eQXtcw"
    if not api_key:
        print("DEBUG: No GEMINI_API_KEY found for semantic parse.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")

        system_prompt = """
        You are a semantic payroll intelligence layer. Your goal is to understand human phrasing and translate it into structured payroll intents and entities.
        
        INTENTS:
        - salary_query: Basic salary questions (net pay, take home).
        - payroll_breakdown: Full earnings and deductions breakdown.
        - deduction_reason: Why salary is less, what was deducted.
        - salary_comparison: Comparing two months or periods.
        - tax_query: Income tax, TDS, tax liability.
        - ot_query: Overtime, night shift allowance, shift allowance.
        - reimbursement_query: Specific reimbursements (fuel, driver, etc).
        - lop_query: Loss of pay, unpaid leaves, LOP dates.
        - allowance_query: Specific allowances (HRA, LTA, Bonus).
        - component_query: Single component lookup (PF, PT, Basic).
        - faq: General policy or process questions.
        - unknown: Query not related to payroll.

        ENTITIES to extract:
        - month: (Jan, Feb, etc)
        - year: (2025, 2026, etc)
        - financial_year: (2025-26, etc)
        - component: (PF, Basic, HRA, etc)
        - allowance_type: (Night shift, Bonus, etc)
        - reimbursement_type: (Fuel, etc)
        - comparison: (previous_month, last_year, etc)

        REWRITING RULES:
        - Normalize vague phrasing: "payout was less" -> "Analyze salary reduction reasons compared to previous month"
        - "what all came in" -> "Provide full payroll earnings and deductions breakdown"
        - "did I get shift allowance" -> "Check if shift allowance was paid in Mar 2026"

        RETURN ONLY VALID JSON.
        Format:
        {
            "intent": "intent_name",
            "confidence": 0.95,
            "rewritten_query": "Rewritten version",
            "entities": {
                "month": "Month",
                "year": 2026,
                "financial_year": null,
                "component": null,
                "allowance_type": null,
                "reimbursement_type": null,
                "comparison": null
            }
        }
        """

        prompt = f"{system_prompt}\n\nQuery: \"{query}\"\n\nJSON Output:"
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        parsed = json.loads(text)
        if "intent" in parsed and "confidence" in parsed:
            return parsed
        return None
        
    except Exception as e:
        print(f"DEBUG: semantic_parse_query error: {e}")
        return None
