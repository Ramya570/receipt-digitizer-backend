import sqlite3
from datetime import datetime
import bcrypt

DB_NAME = "receipts.db"


# ====================================
# Initialize Database
# ====================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password BLOB
        )
    """)

    # Receipts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            store TEXT,
            phone TEXT,
            total REAL,
            calculated_subtotal REAL,
            total_matches BOOLEAN,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER,
            name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(receipt_id) REFERENCES receipts(id)
        )
    """)

    conn.commit()
    conn.close()


# ====================================
# Create User
# ====================================
def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return None

    conn.close()
    return user_id


# ====================================
# Authenticate User
# ====================================
def authenticate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, password FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user[1]):
        return user[0]

    return None


# ====================================
# Save Receipt (CREATE)
# ====================================
def save_receipt(user_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO receipts 
        (user_id, store, phone, total, calculated_subtotal, total_matches, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("store"),
        data.get("phone"),
        float(data.get("total")) if data.get("total") else 0,
        data.get("calculated_subtotal"),
        data.get("total_matches"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    receipt_id = cursor.lastrowid

    for item in data.get("items", []):
        cursor.execute("""
            INSERT INTO items (receipt_id, name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (
            receipt_id,
            item["name"],
            item["quantity"],
            item["price"]
        ))

    conn.commit()
    conn.close()

    return receipt_id


# ====================================
# Get All Receipts (READ + Pagination)
# ====================================
def get_all_receipts(user_id, page=1, limit=10, store=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    offset = (page - 1) * limit

    if store:
        cursor.execute("""
            SELECT * FROM receipts
            WHERE user_id = ? AND store LIKE ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (user_id, f"%{store}%", limit, offset))
    else:
        cursor.execute("""
            SELECT * FROM receipts
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))

    receipts = cursor.fetchall()
    conn.close()

    return receipts


# ====================================
# Get Receipt By ID (READ ONE)
# ====================================
def get_receipt_by_id(user_id, receipt_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM receipts
        WHERE id = ? AND user_id = ?
    """, (receipt_id, user_id))

    receipt = cursor.fetchone()

    if not receipt:
        conn.close()
        return None

    cursor.execute("""
        SELECT name, quantity, price
        FROM items
        WHERE receipt_id = ?
    """, (receipt_id,))

    items = cursor.fetchall()
    conn.close()

    return receipt, items


# ====================================
# Update Receipt (UPDATE)
# ====================================
def update_receipt(user_id, receipt_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM receipts
        WHERE id = ? AND user_id = ?
    """, (receipt_id, user_id))

    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return False

    cursor.execute("""
        UPDATE receipts
        SET store = ?, phone = ?, total = ?, 
            calculated_subtotal = ?, total_matches = ?
        WHERE id = ? AND user_id = ?
    """, (
        data.get("store"),
        data.get("phone"),
        data.get("total"),
        data.get("calculated_subtotal"),
        data.get("total_matches"),
        receipt_id,
        user_id
    ))

    # Delete old items
    cursor.execute("DELETE FROM items WHERE receipt_id = ?", (receipt_id,))

    # Insert updated items
    for item in data.get("items", []):
        cursor.execute("""
            INSERT INTO items (receipt_id, name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (
            receipt_id,
            item["name"],
            item["quantity"],
            item["price"]
        ))

    conn.commit()
    conn.close()

    return True


# ====================================
# Delete Receipt (DELETE)
# ====================================
def delete_receipt(user_id, receipt_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM receipts
        WHERE id = ? AND user_id = ?
    """, (receipt_id, user_id))

    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return 0

    cursor.execute("DELETE FROM items WHERE receipt_id = ?", (receipt_id,))
    cursor.execute("""
        DELETE FROM receipts
        WHERE id = ? AND user_id = ?
    """, (receipt_id, user_id))

    conn.commit()
    conn.close()

    return 1


# ====================================
# Analytics Summary
# ====================================
def get_analytics_summary(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Total receipts
    cursor.execute("""
        SELECT COUNT(*)
        FROM receipts
        WHERE user_id = ?
    """, (user_id,))
    total_receipts = cursor.fetchone()[0]

    # Total spent
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM receipts
        WHERE user_id = ?
    """, (user_id,))
    total_spent = cursor.fetchone()[0]

    # Average receipt value
    cursor.execute("""
        SELECT COALESCE(AVG(total), 0)
        FROM receipts
        WHERE user_id = ?
    """, (user_id,))
    average_spent = cursor.fetchone()[0]

    # Spending per store
    cursor.execute("""
        SELECT store, COALESCE(SUM(total), 0)
        FROM receipts
        WHERE user_id = ?
        GROUP BY store
        ORDER BY SUM(total) DESC
    """, (user_id,))

    store_data = cursor.fetchall()
    conn.close()

    store_summary = [
        {"store": row[0], "total_spent": round(row[1], 2)}
        for row in store_data
    ]

    return {
        "total_receipts": total_receipts,
        "total_spent": round(total_spent, 2),
        "average_receipt_value": round(average_spent, 2),
        "spending_per_store": store_summary
    }
