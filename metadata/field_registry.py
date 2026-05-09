from __future__ import annotations

from typing import Any

class FieldRegistry:
    """Field-to-column registry for deterministic query mapping."""

    @staticmethod
    def get_fields_by_category(category: str):
        return [
            key for key, val in FieldRegistry.FIELDS.items()
            if val.get("category") == category
        ]

    FIELDS: dict[str, dict[str, Any]] = {
        # Earnings and pay-register components
        "basic": {
            "table": "pay_register",
            "column": "basic",
            "category": "earning",
            "unit": "amount",
            "aliases": ["basic", "basic salary", "base salary"],
            "response_template": "Your Basic Pay for {month} {year} is {value}.",
        },
        "hra": {
            "table": "pay_register",
            "column": "h_r_a",
            "category": "earning",
            "unit": "amount",
            "aliases": ["hra", "house rent", "house rent allowance"],
            "response_template": "Your House Rent Allowance (HRA) for {month} {year} is {value}.",
        },
        "lta": {
            "table": "pay_register",
            "column": "lta",
            "category": "earning",
            "unit": "amount",
            "aliases": ["lta", "leave travel", "leave travel allowance"],
            "response_template": "Your Leave Travel Allowance (LTA) for {month} {year} is {value}.",
        },
        "bonus": {
            "table": "pay_register",
            "column": "bonus",
            "category": "earning",
            "unit": "amount",
            "aliases": ["bonus"],
            "response_template": "Your Bonus for {month} {year} is {value}.",
        },
        "incentive": {
            "table": "pay_register",
            "column": "incentive",
            "category": "earning",
            "unit": "amount",
            "aliases": ["incentive"],
            "response_template": "Your Incentive for {month} {year} is {value}.",
        },
        "night_shift_allowance": {
            "table": "pay_register",
            "column": "night_shift_all",
            "category": "earning",
            "unit": "amount",
            "aliases": ["night shift allowance", "night shift", "nsa"],
            "response_template": "Your Night Shift Allowance for {month} {year} is {value}.",
        },
        "other_allowance": {
            "table": "pay_register",
            "column": "other_allowance",
            "category": "earning",
            "unit": "amount",
            "aliases": ["other allowance", "allowance"],
            "response_template": "Your Other Allowance for {month} {year} is {value}.",
        },
        "non_tax_amount": {
            "table": "pay_register",
            "column": "nontax",
            "category": "earning",
            "unit": "amount",
            "aliases": ["non tax", "non-tax", "non taxable", "non taxable earnings"],
            "response_template": "Your Non-Tax amount for {month} {year} is {value}.",
        },
        # Deductions
        "pf": {
            "table": "pay_register",
            "column": "pf_ded",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["pf", "provident fund", "pf deduction"],
            "response_template": "Your Provident Fund (PF) deduction for {month} {year} is {value}.",
        },
        "pt": {
            "table": "pay_register",
            "column": "pt_ded",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["pt", "professional tax", "pt deduction"],
            "response_template": "Your Professional Tax (PT) deduction for {month} {year} is {value}.",
        },
        "income_tax_deduction": {
            "table": "pay_register",
            "column": "income_tax_ded",
            "category": "deduction",
            "unit": "amount",
            "aliases": ["income tax deduction", "income tax ded", "tds"],
            "response_template": "Your Income Tax deduction for {month} {year} is {value}.",
        },
        # Totals
        "gross_earning": {
            "table": "pay_register",
            "column": "gross_earning",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross earning", "gross earnings", "total earning", "total earnings", "gross salary"],
            "response_template": "Your Gross Earnings for {month} {year} is {value}.",
        },
        "gross_deduction": {
            "table": "pay_register",
            "column": "gross_deduction",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross deduction", "total deductions", "deductions"],
            "response_template": "Your Total Deductions for {month} {year} is {value}.",
        },
        "total_netpay": {
            "table": "pay_register",
            "column": "total_netpay",
            "category": "total",
            "unit": "amount",
            "aliases": ["net pay", "net salary", "take home", "total netpay", "salary", "pay"],
            "response_template": "Your Net Pay for {month} {year} is {value}.",
        },
        "total_paid_days": {
            "table": "pay_register",
            "column": "total_paid_days",
            "category": "total",
            "unit": "days",
            "aliases": ["paid days", "total paid days", "number of paid days", "total number of paid days", "total number of paid day", "no of paid days"],
            "response_template": "Your total paid days for {month} {year} were {value}.",
        },
        "tax_paid_till_date": {
            "table": "tax_data_raw",
            "column": "total_income_tax_paid_from_salary_till_date",
            "category": "tax",
            "unit": "amount",
            "aliases": ["tax paid till date", "total income tax paid from salary till date", "tax paid from salary", "income tax paid from salary till date", "total income tax paid from salary", "total tax deductions from salary", "tax deductions from salary", "total tax deduction from salary"],
            "response_template": "Your total income tax paid from salary till {month} {year} is {value}.",
        },
        "actdays": {
            "table": "pay_register",
            "column": "actdays",
            "category": "total",
            "unit": "days",
            "aliases": ["act days", "actual days", "actdays", "actual working days"],
            "response_template": "Your actual working days for {month} {year} were {value}.",
        },
        "wday": {
            "table": "pay_register_raw",
            "column": "wday",
            "category": "total",
            "unit": "days",
            "aliases": ["wday", "w day", "total days", "total days pay", "days worked", "working day", "working days", "wod"],
            "response_template": "Your total working days for {month} {year} were {value}.",
        },
        "management_allowance": {
            "table": "pay_register",
            "column": "mange_allow",
            "category": "earning",
            "unit": "amount",
            "aliases": ["management allowance", "management allow", "mange allow"],
            "response_template": "Your Management Allowance for {month} {year} is {value}.",
        },
        "arrdays": {
            "table": "pay_register",
            "column": "arrdays",
            "category": "total",
            "unit": "days",
            "aliases": ["arrear days", "arr days", "arrdays"],
            "response_template": "Your arrear days for {month} {year} were {value}.",
        },
        "leavenchdays": {
            "table": "pay_register",
            "column": "leavenchdays",
            "category": "total",
            "unit": "days",
            "aliases": ["leave encashment days", "leave encash days", "leavenchdays"],
            "response_template": "Your leave encashment days for {month} {year} were {value}.",
        },
        "notpaydays": {
            "table": "pay_register",
            "column": "notpaydays",
            "category": "total",
            "unit": "days",
            "aliases": ["not pay days", "unpaid days", "notpaydays", "not paid days"],
            "response_template": "Your unpaid days for {month} {year} were {value}.",
        },
        "lopd": {
            "table": "pay_register",
            "column": "lopd",
            "category": "total",
            "unit": "days",
            "aliases": ["lop", "lop days", "loss of pay", "loss of pay days", "lopd"],
            "response_template": "Your LOP (Loss of Pay) days for {month} {year} were {value}.",
        },
        # Tax reconciliation fields (from tax_data_raw)
        "net_taxable_income": {
            "table": "tax_data_raw",
            "column": "net_taxable_income",
            "category": "tax",
            "unit": "amount",
            "aliases": ["net taxable income", "taxable income", "taxable earning", "taxable earnings"],
            "response_template": "Your net taxable income is Rs {value}.",
        },
        "income_tax_per_month": {
            "table": "tax_data_raw",
            "column": "income_tax_per_month",
            "category": "tax",
            "unit": "amount",
            "aliases": ["income tax per month", "tax per month", "pay tax"],
            "response_template": "Your income tax per month is Rs {value}.",
        },
        "surcharge": {
            "table": "tax_data_raw",
            "column": "surcharge_on_income_tax",
            "category": "tax",
            "unit": "amount",
            "aliases": ["surcharge", "surcharge on income tax"],
            "response_template": "Your surcharge on income tax for {month} {year} is {value}.",
        },
        "tax_due": {
            "table": "tax_data_raw",
            "column": "income_tax_due",
            "category": "tax",
            "unit": "amount",
            "aliases": ["tax due", "income tax due", "tax owed"],
            "response_template": "Your remaining income tax due for {month} {year} is {value}.",
        },
        "total_tax_liability": {
            "table": "tax_data_raw",
            "column": "total_tax_liability",
            "category": "tax",
            "unit": "amount",
            "aliases": ["total tax liability", "tax liability", "total tax"],
            "response_template": "Your total tax liability for {month} {year} is {value}.",
        },
        "tax_paid_till_date": {
            "table": "tax_data_raw",
            "column": "total_income_tax_paid_from_salary_till_date",
            "category": "tax",
            "unit": "amount",
            "aliases": ["tax paid till date", "total income tax paid from salary till date", "tax paid from salary", "income tax paid from salary till date", "total income tax paid from salary", "tax deductions from salary", "total tax deduction from salary"],
            "response_template": "Your total income tax paid from salary till {month} {year} is {value}.",
        },
        "tax_regime": {
            "table": "tax_data_raw",
            "column": "tax_regime",
            "category": "tax",
            "unit": "text",
            "aliases": ["tax regime", "which regime", "old regime", "new regime", "regime"],
            "response_template": "You are under the {value} tax regime for {month} {year}.",
        },
        "total_gross_salary": {
            "table": "tax_data_raw",
            "column": "total_gross_salary",
            "category": "tax",
            "unit": "amount",
            "aliases": ["total gross salary", "gross total income", "total gross"],
            "response_template": "Your total gross salary for {month} {year} is {value}.",
        },
        "gross_salary": {
            "table": "pay_register",
            "column": "gross_earning",
            "category": "total",
            "unit": "amount",
            "aliases": ["gross salary", "gross pay"],
            "response_template": "Your gross salary for {month} {year} is Rs {value}.",
        },
        "gross_total_income": {
            "table": "tax_data_raw",
            "column": "gross_total_income",
            "category": "tax",
            "unit": "amount",
            "aliases": ["gross total income", "total income", "gross income"],
            "response_template": "Your gross total income for {month} {year} is {value}.",
        },
        "bank_name": {
            "table": "pay_register_raw",
            "column": "bank_name",
            "category": "personal",
            "unit": "text",
            "aliases": ["bank name", "bank name of salary credited", "bank details", "bank account", "bank account no"],
            "response_template": "I cannot access or share personal employee details.",
        },
    }

    @staticmethod
    def find_field(query: str) -> str | None:
        q = str(query).lower().strip()
        matches = []
        for field_key, field_data in FieldRegistry.FIELDS.items():
            for alias in field_data.get("aliases", []):
                if alias in q:
                    matches.append((len(alias), field_key))
        
        if matches:
            # Sort by length descending and return the field_key of the longest alias
            matches.sort(key=lambda x: x[0], reverse=True)
            return matches[0][1]
        
        return None

    @staticmethod
    def get_field(field_key: str) -> dict[str, Any] | None:
        return FieldRegistry.FIELDS.get(field_key)

