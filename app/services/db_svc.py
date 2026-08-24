import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/recoveries.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_records (
                record_id TEXT PRIMARY KEY,
                order_id TEXT,
                customer_name TEXT,
                customer_email TEXT,
                failure_type TEXT,
                amount_inr REAL,
                money_recovered REAL,
                status TEXT,
                reason TEXT,
                payment_link TEXT,
                audit_trail TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_record(record: dict):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO recovery_records 
            (record_id, order_id, customer_name, customer_email, failure_type, amount_inr, money_recovered, status, reason, payment_link, audit_trail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("record_id"),
            record.get("order_id"),
            record.get("customer_name"),
            record.get("customer_email"),
            record.get("failure_type"),
            record.get("money_at_risk", record.get("amount_inr", 0.0)),
            record.get("money_recovered", 0.0),
            record.get("status"),
            record.get("reason"),
            record.get("payment_link"),
            json.dumps(record.get("audit_trail", []))
        ))
        conn.commit()

def fetch_all_records():
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recovery_records ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]