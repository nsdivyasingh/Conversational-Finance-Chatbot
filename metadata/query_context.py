from enum import Enum
from typing import Dict, Any

class QueryType(Enum):
    FIELD_VALUE = "field_value"
    SINGLE_FIELD = "single_field"
    AGGREGATE = "aggregate"
    COMPARISON = "comparison"
    BREAKDOWN = "breakdown"
    FY_OVERVIEW = "fy_overview"
    OT_REIMBURSEMENT = "ot_reimbursement"
    SALARY_SUM = "salary_sum"

class QueryContext:
    """Manages the contextual routing and type matching for queries."""
    
    TOOL_ROUTING = {
        QueryType.BREAKDOWN: "get_full_salary_breakdown",
        QueryType.COMPARISON: "analyze_salary",
        QueryType.OT_REIMBURSEMENT: "get_ot_reimbursement", 
        QueryType.FY_OVERVIEW: "get_salary",
        QueryType.FIELD_VALUE: "get_field_value",
        QueryType.SALARY_SUM: "get_salary_sum",
        # Intent-based routing
        "payroll_full": "get_full_salary_breakdown",
        "earning_full": "get_full_salary_breakdown",
        "deduction_full": "get_full_salary_breakdown",
        "payroll_impact": "get_full_salary_breakdown",
        "allowance_query": "get_full_salary_breakdown",  # Allowances = full earnings breakdown
        "tax_query": "get_tax",
        "net_pay": "get_salary",
        "lop_query": "get_lop",
        "deduction_reason": "analyze_salary",
        "deduction_query": "get_full_salary_breakdown",
        "ot_query": "get_ot_reimbursement",
        "get_ot_allowance_type": "get_ot_reimbursement",
        "get_ot_reimbursement": "get_ot_reimbursement",
        "get_taxable_income": "get_field_value",
        "get_income_tax": "get_field_value",
        "get_lta": "get_field_value",
        "get_working_days": "get_field_value",
        "get_income_tax_till_date": "get_field_value",
        "get_ot_data": "get_ot_reimbursement",
        "get_net_pay": "get_salary",
        "tax_paid_till_date": "get_field_value",
        # Semantic intents
        "salary_query": "get_salary",
        "payroll_breakdown": "get_full_salary_breakdown",
        "salary_comparison": "analyze_salary",
        "reimbursement_query": "get_ot_reimbursement",
        "component_query": "get_field_value",
        "allowance_query": "get_full_salary_breakdown",
        # Gemini agent tool name pass-through
        "get_full_salary_breakdown": "get_full_salary_breakdown",
        "get_salary": "get_salary",
        "get_field_value": "get_field_value",
        "get_ot_reimbursement": "get_ot_reimbursement",
        "get_allowance_breakdown": "get_full_salary_breakdown",  # Redirect to full breakdown
        "get_tax": "get_tax",
        "analyze_salary_reason": "analyze_salary_reason",
        "analyze_salary": "analyze_salary",
        "get_salary_history": "get_salary_history",
    }

    @staticmethod
    def determine_query_type(query: str, parsed_intent: str, field_request: str | None = None) -> QueryType | str:
        q = str(query).lower()

        # 🔥 PRIORITY BLOCK: sum of components
        if "basic" in q and "hra" in q and "lta" in q and ("total" in q or "sum" in q):
            return QueryType.SALARY_SUM

        if "tax" in q and ("till date" in q or "fy" in q or "financial year" in q):
            return QueryType.FIELD_VALUE

        if "allowance" in q and ("receive" in q or "received" in q or "did i get" in q):
            return QueryType.BREAKDOWN

        if field_request:
            if field_request in ["gross_deduction", "gross_earning", "total_netpay"]:
                return QueryType.BREAKDOWN
            return QueryType.FIELD_VALUE

        # Annual salary structure → full earning breakdown
        if "annual salary structure" in q or "annual structure" in q or "salary structure" in q:
            return QueryType.BREAKDOWN

        # OT / Night shift / Reimbursement
        if "reimbursement" in q or "overtime" in q or "night shift" in q or "shift allowance" in q or "allowance type" in q:
            return QueryType.OT_REIMBURSEMENT

        # Payroll/components → full breakdown
        if "payroll" in q or "components" in q or "all components" in q:
            return QueryType.BREAKDOWN

        # Earnings are the same as allowances
        if "earning components" in q or "all earnings" in q or "total earnings" in q:
            return QueryType.BREAKDOWN

        # Deduction components → full breakdown
        if "deduction components" in q or "all deductions" in q or "total deductions" in q:
            return QueryType.BREAKDOWN

        if "affect" in q or "impact" in q:
            return "payroll_impact"

        # Comparison / Reason queries → analyze
        if "compare" in q or "difference" in q or "why" in q or "reason" in q or "less" in q or "increase" in q or "decrease" in q:
            return QueryType.COMPARISON

        if "financial year" in q or "fy" in q or "this year" in q or "last year" in q:
            return QueryType.FY_OVERVIEW

        if "breakdown" in q:
            return QueryType.BREAKDOWN

        # Allowances = full earnings breakdown
        if parsed_intent == "allowance_query":
            return QueryType.BREAKDOWN

        if parsed_intent in ["deduction_reason"]:
            return QueryType.COMPARISON

        if parsed_intent in ["deduction_query"]:
            return QueryType.BREAKDOWN

        if parsed_intent in ["tax_query", "net_pay", "lop_query", "ot_query"]:
            return parsed_intent
                
        return QueryType.SINGLE_FIELD
        
    @staticmethod
    def get_tool_for_type(query_type: QueryType | str) -> str | None:
        return QueryContext.TOOL_ROUTING.get(query_type)
