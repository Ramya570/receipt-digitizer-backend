from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_cors import CORS
import bcrypt
import os

from database.db import (
    init_db,
    create_user,
    get_user_by_username,
    save_receipt,
    get_receipts_by_user,
    delete_receipt_by_id,
    get_total_spending_by_user,
)

from services.ocr_service import extract_receipt_data


app = Flask(__name__)
CORS(app)

# =========================
# JWT Configuration
# =========================
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-this"
jwt = JWTManager(app)

# =========================
# Initialize Database
# =========================
init_db()


# =====================================================
# AUTH ROUTES
# =====================================================

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Missing username or password"
        }), 400

    hashed_pw = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    result = create_user(
        username,
        hashed_pw.decode("utf-8")
    )

    if not result:
        return jsonify({
            "success": False,
            "message": "User already exists"
        }), 409

    return jsonify({
        "success": True,
        "message": "User registered successfully"
    }), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = get_user_by_username(username)

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    stored_password = user["password"]

    if not bcrypt.checkpw(
        password.encode("utf-8"),
        stored_password.encode("utf-8")
    ):
        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    # 🔥 FIX: Identity must be STRING
    access_token = create_access_token(
        identity=str(user["id"])
    )

    return jsonify({
        "success": True,
        "access_token": access_token
    }), 200


# =====================================================
# RECEIPT ROUTES (Protected)
# =====================================================

@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_receipt():
    # 🔥 Convert back to int
    current_user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file uploaded"
        }), 400

    file = request.files["file"]

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)
    file.save(file_path)

    extracted_data = extract_receipt_data(file_path)

    total = extracted_data.get(
        "structured_data", {}
    ).get("total")

    if total:
        save_receipt(
            current_user_id,
            file.filename,
            float(total)
        )

    return jsonify(extracted_data), 200


@app.route("/receipts", methods=["GET"])
@jwt_required()
def get_receipts():
    current_user_id = int(get_jwt_identity())

    receipts = get_receipts_by_user(current_user_id)

    return jsonify({
        "success": True,
        "receipts": receipts
    }), 200


@app.route("/receipt/<int:receipt_id>", methods=["DELETE"])
@jwt_required()
def delete_receipt(receipt_id):
    current_user_id = int(get_jwt_identity())

    result = delete_receipt_by_id(
        receipt_id,
        current_user_id
    )

    if not result:
        return jsonify({
            "success": False,
            "message": "Receipt not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Receipt deleted"
    }), 200


# =====================================================
# ANALYTICS ROUTE
# =====================================================

@app.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    current_user_id = int(get_jwt_identity())

    total_spent = get_total_spending_by_user(current_user_id)

    return jsonify({
        "success": True,
        "total_spent": total_spent
    }), 200


# =====================================================
# HEALTH CHECK ROUTE
# =====================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Receipt Digitizer API is running"
    }), 200


# =====================================================
# RUN APP (Render Compatible)
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
