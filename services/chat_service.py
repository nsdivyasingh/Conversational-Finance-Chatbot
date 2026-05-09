from router.intent_router import classify_intent
from guardrails.security import violates_security, BLOCK_RESPONSE
from agents.faq_agent import answer_faq
from agents.payroll_agent import handle_payroll_query
from agents.reasoning_agent import generate_response
from tools.tools import employee_exists 
from services.query_parser import semantic_parse_query


import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") 
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-flash-latest")

TOOLS = [
    {
        "name": "get_full_salary_breakdown",
        "description": """
        Use when user asks about:
        - payroll details
        - salary breakdown
        - components of salary
        - earnings + deductions together

        Returns:
        - earnings (all earning components)
        - deductions (all deduction components)
        - net pay
        - gross earnings
        - gross deductions
        """
    },

    {
        "name": "get_salary",
        "description": """
        Use when user asks:
        - net salary
        - take home pay
        - salary for a month

        Returns:
        - total_netpay
        - gross earnings
        - gross deductions
        """
    },

    {
        "name": "get_field_value",
        "description": """
        Use when user asks about a specific component:
        - HRA, LTA, Basic Pay
        - PF, PT, tax
        - any single field

        Required:
        - field_key (example: hra, lta, pf_ded)

        Returns:
        - value of that field
        """
    },

    {
        "name": "get_allowance_breakdown",
        "description": """
        Use when user asks:
        - allowances received
        - bonus, incentive, night shift allowance

        Returns:
        - total allowance
        - allowance components
        """
    },

    {
        "name": "get_ot_reimbursement",
        "description": """
        Use when user asks:
        - reimbursement
        - overtime
        - shift allowance period

        Returns:
        - allowance type
        - amount
        - period (from_date to to_date)
        """
    },

    {
        "name": "get_lop",
        "description": """
        Use when user asks:
        - loss of pay
        - salary reduction
        - unpaid leaves

        Returns:
        - lop dates
        - lop days
        """
    },

    {
        "name": "get_tax",
        "description": """
        Use when user asks:
        - tax liability
        - income tax
        - tax paid

        Returns:
        - tax values
        """
    },

    {
        "name": "analyze_salary",
        "description": """
        Use when user asks:
        - compare salary between months
        - why salary changed
        - salary increase/decrease

        Returns:
        - comparison between current and previous month
        """
    },

    {
        "name": "get_salary_sum",
        "description": """
        Use when user asks:
        - sum of salary components
        - total of basic + hra + lta

        Returns:
        - total sum of selected fields
        """
    }
]



USE_GEMINI = True

REASONING_PROMPT = """
You are a payroll analysis assistant.

You are given:
- A user query
- Structured payroll data (current month, previous month, and/or allowance/reimbursement data)

Your job is to ANALYZE and EXPLAIN the answer clearly.

🚨 STRICT RULES:
1. Use ONLY the provided data. Do NOT guess or invent values.
2. Do NOT say "I think", "maybe", or "it seems".
3. Be precise, structured, and factual.
4. Always mention numbers when explaining differences.
5. If data is missing, say so clearly.
6. Do NOT include unnecessary explanations or generic text.

🎯 TASK TYPES:
1. Salary Change / Reduction Queries
   - Compare current vs previous month: Net Pay, Total Deductions, Gross Earnings, LOP (Loss of Pay).
   - Identify exact reasons: Increase in deductions, Salary advance deductions, Change in allowances, LOP impact.

2. Comparison Queries
   - Return Net Pay difference (with amount) and key changes in deductions, earnings, allowances.

3. Reimbursement / Allowance Period Queries
   - Use allowance/reimbursement data. Mention: allowance type, amount, period (from_date to to_date), and which salary month it was paid in.
   - For "Non Taxable" queries: If it's in allowance data, use that timeline. If NOT in allowance data but present in salary earnings as "Non-Tax Amount", say the period was the "entire month".
   - If no data exists: "No reimbursement was recorded for the requested period."

4. Deductions Breakdown
   - ALWAYS list ALL deduction components found in the data (PT, PF, Salary Advance Deduction, etc.). Do NOT summarize or skip any.

5. Full Breakdown (Earnings & Deductions)
   - When asked for "payroll details", "salary breakdown", or "earnings and deductions", ALWAYS list ALL earnings components and ALL deduction components.

📊 OUTPUT FORMAT RULES:
- Use bullet points for comparisons
- Keep sentences short and clear
- Always include currency values (Rs X)
- Do NOT include JSON or code

USER QUERY:
{user_query}

DATA:
{data}

Now generate the final answer.
"""

def plan_with_gemini(user_query):
    prompt = f"""
    You are a payroll assistant.

    User query: {user_query}

    Available tools:
    {TOOLS}

    Choose the BEST tool based on these RULES:
    - If query contains: "why", "reason", "compare", "change", "difference", "changing", "period" -> ALWAYS use analyze_salary_reason
    - If query contains "every month", "month-on-month", or "3 months", use get_salary_history
    - If query contains "payroll details", "salary structure", "breakdown", "tabular", use get_full_salary_breakdown
    - If query contains "bank name" or "personal details", use get_field_value
    - If query contains a specific field (HRA, PF, LTA, Basic, working days, total days, Wod, PT, tax paid), use get_field_value
    - If query contains "reimbursement" or "overtime", use get_ot_reimbursement
    - If query contains "allowance", use get_allowance_breakdown
    - If query contains "tax", use get_tax

    Return ONLY JSON:
    {{
        "tool": "tool_name",
        "reason": "why this tool"
    }}
    """

    response = model.generate_content(prompt)
    print(f"DEBUG: Gemini response: {response.text}")

    import json
    text = response.text.replace("```json", "").replace("```", "").replace("```JSON", "").strip()
    return json.loads(text)

def execute_tool(tool_name, user_query, employee_id):
    # Use existing handle_payroll_query but treat Gemini's choice as the 'intent'
    return handle_payroll_query(user_query, tool_name, employee_id)

def process_user_query(user_query, employee_id, history=None):
    global USE_GEMINI
    print(f"DEBUG: Entering process_user_query with query: {user_query}")
    
    # -------------------------
    # 1. SECURITY FIRST
    # -------------------------
    if violates_security(user_query, employee_id):
        return {
            "status": "blocked",
            "answer": "I do not have access to records for other employees. I can only assist with your own payroll, tax, and FAQ queries."
        }

    # -------------------------
    # 2. HYBRID INTENT CLASSIFICATION
    # -------------------------
    # a. Deterministic check
    det_intent = classify_intent(user_query)
    
    # b. Semantic parse (Gemini)
    semantic_result = None
    if USE_GEMINI:
        semantic_result = semantic_parse_query(user_query)
        
    confidence = semantic_result.get("confidence", 0) if semantic_result else 0
    
    # c. Hybrid Routing Strategy
    if det_intent == "unknown" or confidence >= 0.75:
        intent = classify_intent(user_query, semantic_result)
        effective_query = semantic_result.get("rewritten_query", user_query) if semantic_result else user_query
        routing_source = "semantic"
    else:
        intent = det_intent
        effective_query = user_query
        routing_source = "deterministic"
        
    print(f"DEBUG: Routing Decision -> Intent: {intent}, Source: {routing_source}, Confidence: {confidence}")

    # Intent-level security block
    if intent == "security_block":
        return {
            "status": "blocked",
            "answer": "I do not have access to records for other employees. I can only assist with your own payroll, tax, and FAQ queries."
        }

    # -------------------------
    # 3. FAQ CHECK
    # -------------------------
    if intent == "faq":
        faq_answer = answer_faq(user_query)
        if faq_answer:
            return {"status": "ok", "answer": faq_answer, "source": "faq"}

    # -------------------------
    # 4. EXECUTION (Deterministic Tools)
    # -------------------------
    try:
        # Use handle_payroll_query as the single source of truth for tool execution
        tool_result = handle_payroll_query(effective_query, intent, employee_id)
        
        if not tool_result or tool_result.get("status") != "success":
            # Fallback to original query if rewritten query failed
            if effective_query != user_query:
                tool_result = handle_payroll_query(user_query, intent, employee_id)

        # -------------------------
        # 5. RESPONSE GENERATION
        # -------------------------
        # For complex reasoning (deductions, comparisons), use Gemini for a natural explanation if enabled
        if intent in ["deduction_reason", "salary_comparison"] and USE_GEMINI:
            clean_data = {
                "current": tool_result.get("data", {}).get("current", {}),
                "previous": tool_result.get("data", {}).get("previous", {}),
                "allowance": tool_result.get("data", {}).get("allowance", {})
            }
            
            import json
            resp = model.generate_content(
                REASONING_PROMPT.format(
                    user_query=user_query,
                    data=json.dumps(clean_data, indent=2)
                )
            )
            final_answer = resp.text
        else:
            # Standard deterministic response
            final_answer = generate_response(intent, tool_result)

        return {
            "status": "ok",
            "answer": final_answer,
            "intent": intent,
            "source": f"hybrid-{routing_source}"
        }

    except Exception as e:
        print(f"DEBUG: Execution error: {e}")
        # Final deterministic fallback
        try:
            tool_data = handle_payroll_query(user_query, det_intent, employee_id)
            return {
                "status": "ok",
                "answer": generate_response(det_intent, tool_data),
                "source": "emergency-fallback"
            }
        except:
            return {
                "status": "error",
                "answer": "I encountered an issue processing your request. Please try again later."
            }