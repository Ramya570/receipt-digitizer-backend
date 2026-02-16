import sqlite3
import os

DB_NAME = "receipts.db"


# =========================
# DATABASE INITIALIZATION
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            total REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USER FUNCTIONS
# =========================

def create_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        return False


def get_user_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    conn.close()

    return dict(user) if user else None


# =========================
# RECEIPT FUNCTIONS
# =========================

def save_receipt(user_id, filename, total):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO receipts (user_id, filename, total) VALUES (?, ?, ?)",
        (user_id, filename, total)
    )

    conn.commit()
    conn.close()


def get_receipts_by_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM receipts WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )

    receipts = cursor.fetchall()
    conn.close()

    return [dict(r) for r in receipts]


def delete_receipt_by_id(receipt_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM receipts WHERE id = ? AND user_id = ?",
        (receipt_id, user_id)
    )

    affected = cursor.rowcount

    conn.commit()
    conn.close()

    return affected > 0


def get_total_spending_by_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(total) FROM receipts WHERE user_id = ?",
        (user_id,)
    )

    total = cursor.fetchone()[0]
    conn.close()

    return total if total else 0.0
