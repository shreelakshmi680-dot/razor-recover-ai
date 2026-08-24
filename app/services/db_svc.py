"""
RazorRecover AI - Persistent Audit & Recovery Store
Thread-safe SQLite storage with backward-compatible column mappings.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/recoveries.db"))

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT UNIQUE,
            order_id TEXT,
            customer_name TEXT,
            failure_type TEXT,
            amount_inr REAL,
            money_at_risk REAL,
            money_recovered REAL,
            status TEXT,
            reason TEXT,
            payment_link TEXT,
            audit_trail TEXT,
            timestamp TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_recovery_record(record: dict) -> bool:
    try:
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        
        amt = float(record.get("money_at_risk", record.get("amount_inr", 0.0)))
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT OR REPLACE INTO recovery_audits (
                record_id, order_id, customer_name, failure_type,
                amount_inr, money_at_risk, money_recovered, status, reason,
                payment_link, audit_trail, timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(record.get("record_id", "REC_UNKNOWN")),
            str(record.get("order_id", "order_unknown")),
            str(record.get("customer_name", "Unknown")),
            str(record.get("failure_type", "UNKNOWN")),
            amt,
            amt,
            float(record.get("money_recovered", 0.0)),
            str(record.get("status", "UNKNOWN")),
            str(record.get("reason", "")),
            str(record.get("payment_link", "")),
            json.dumps(record.get("audit_trail", [])),
            now_ts,
            now_ts
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_all_records() -> list[dict]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id, record_id, order_id, customer_name, failure_type,
            COALESCE(amount_inr, money_at_risk, 0.0) AS amount_inr,
            COALESCE(money_at_risk, amount_inr, 0.0) AS money_at_risk,
            money_recovered, status, reason, payment_link, audit_trail,
            COALESCE(timestamp, created_at) AS timestamp,
            COALESCE(created_at, timestamp) AS created_at
        FROM recovery_audits 
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Backward compatible aliases
save_record = save_recovery_record
fetch_all_records = get_all_records