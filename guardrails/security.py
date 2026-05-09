def violates_security(query: str, employee_id: int) -> bool:
    q = query.lower()

    # ONLY block if asking about OTHER employees
    if "employee code" in q and str(employee_id) not in q:
        return True

    # ONLY block sensitive personal info
    sensitive = [
        "pan number",
        "uan number",
        "bank account number",
        "ifsc code"
    ]

    if any(s in q for s in sensitive):
        return True

    return False


BLOCK_RESPONSE = {
    "status": "blocked",
    "answer": "I cannot access personal or other employees' data."
}