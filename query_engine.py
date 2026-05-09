import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# create connection to your DB
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/payroll_db")
engine = create_engine(DATABASE_URL)

def get_salary(employee_id, month=None):
    if month is None:
        query = text("""
            SELECT total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id
        """)
        params = {"emp_id": employee_id}
    else:
        query = text("""
            SELECT total_netpay, gross_earning, gross_deduction
            FROM pay_register
            WHERE employee_id = :emp_id AND month = :month
        """)
        params = {"emp_id": employee_id, "month": month}

    with engine.connect() as conn:
        result = conn.execute(query, params).fetchone()

    return result