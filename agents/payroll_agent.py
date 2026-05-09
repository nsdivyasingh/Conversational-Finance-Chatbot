from tools.tools import execute_tool
from services.tool_planner import plan_tool
from services.query_parser import extract_query_params, normalize_time

from metadata.field_registry import FieldRegistry
from metadata.query_context import QueryContext


def handle_payroll_query(user_query: str, intent: str, employee_id: int):
    parsed = extract_query_params(user_query)
    parsed["intent"] = intent
    normalized = normalize_time(parsed)

    field = FieldRegistry.find_field(user_query)

    query_type = QueryContext.determine_query_type(
        user_query,
        intent,
        field
    )

    print(f"DEBUG: intent={intent}, field={field}, query_type={query_type}")
    
    high_priority_intents = [
        "get_ot_allowance_type", "get_ot_reimbursement", "get_taxable_income",
        "get_income_tax", "get_lta", "get_working_days", "get_ot_data", "get_net_pay",
        "get_salary_history", "tax_paid_till_date", "lop_query", "deduction_reason",
    ]
    
    if intent in high_priority_intents:
        tool_name = QueryContext.TOOL_ROUTING.get(intent)
    else:
        tool_name = QueryContext.get_tool_for_type(query_type)

    print(f"DEBUG: selected tool_name={tool_name}")

    if not tool_name:
        tool_name = QueryContext.TOOL_ROUTING.get(intent)

    if not tool_name:
        plan = plan_tool(normalized, employee_id, user_query)

        if not plan:
            return None

        tool_name = plan.get("tool")
        params = plan.get("params", {})
    else:

        params = {
            "employee_id": employee_id,
            **normalized
        }

        intent_to_field = {
            "get_taxable_income": "net_taxable_income",
            "get_income_tax": "income_tax_deduction",
            "get_income_tax": "income_tax_per_month",
            "get_lta": "lta",
            "get_working_days": "total_paid_days",
            "get_net_pay": "total_netpay",
            "tax_paid_till_date": "tax_paid_till_date"
        }
        
        target_field = field or intent_to_field.get(intent)
        
        if target_field:
            field_meta = FieldRegistry.get_field(target_field)
            if field_meta:
                params["field_key"] = target_field
                params["table"] = field_meta["table"]
                params["column"] = field_meta["column"]
        

        if "amount" in parsed:
            params["amount"] = parsed["amount"]

    # -------------------------
    # EXECUTE TOOL
    # -------------------------
    result = execute_tool(tool_name, params)

    return {
        "tool": tool_name,
        "data": result,
        "params": params,
        "field": field,
        "query_type": query_type,
        "raw_query": user_query
    }