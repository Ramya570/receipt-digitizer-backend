from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from services.ocr_service import extract_text_from_image, parse_receipt

from database.db import (
    init_db,
    create_user,
    authenticate_user,
    save_receipt,
    get_all_receipts,
    get_receipt_by_id,
    update_receipt,
    delete_receipt,
    get_analytics_summary
)

app = Flask(__name__)
CORS(app)

# ===============================
# JWT Configuration
# ===============================
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-this"
jwt = JWTManager(app)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ===============================
# Home
# ===============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Receipt Digitizer Backend Running 🚀"
    })


# ===============================
# Register
# ===============================
@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password required"
        }), 400

    user_id = create_user(username, password)

    if not user_id:
        return jsonify({
            "success": False,
            "message": "User already exists"
        }), 400

    return jsonify({
        "success": True,
        "message": "User registered successfully"
    })


# ===============================
# Login
# ===============================
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user_id = authenticate_user(username, password)

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Invalid credentials"
        }), 401

    access_token = create_access_token(identity=user_id)

    return jsonify({
        "success": True,
        "access_token": access_token
    })


# ===============================
# Upload Receipt (CREATE)
# ===============================
@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_receipt():

    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        extracted_text = extract_text_from_image(filepath)
        structured_data = parse_receipt(extracted_text)

        receipt_id = save_receipt(user_id, structured_data)

        os.remove(filepath)

        return jsonify({
            "success": True,
            "receipt_id": receipt_id,
            "structured_data": structured_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===============================
# Get All Receipts (READ)
# ===============================
@app.route("/receipts", methods=["GET"])
@jwt_required()
def fetch_receipts():

    user_id = get_jwt_identity()

    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=10, type=int)
    store = request.args.get("store", default=None, type=str)

    receipts = get_all_receipts(user_id, page, limit, store)

    formatted = []
    for r in receipts:
        formatted.append({
            "id": r[0],
            "store": r[2],
            "phone": r[3],
            "total": r[4],
            "calculated_subtotal": r[5],
            "total_matches": bool(r[6]),
            "created_at": r[7]
        })

    return jsonify({
        "success": True,
        "page": page,
        "limit": limit,
        "count": len(formatted),
        "receipts": formatted
    })


# ===============================
# Get Single Receipt (READ ONE)
# ===============================
@app.route("/receipt/<int:receipt_id>", methods=["GET"])
@jwt_required()
def fetch_receipt(receipt_id):

    user_id = get_jwt_identity()

    result = get_receipt_by_id(user_id, receipt_id)

    if not result:
        return jsonify({
            "success": False,
            "message": "Receipt not found"
        }), 404

    receipt, items = result

    formatted_items = []
    for item in items:
        formatted_items.append({
            "name": item[0],
            "quantity": item[1],
            "price": item[2]
        })

    return jsonify({
        "success": True,
        "receipt": {
            "id": receipt[0],
            "store": receipt[2],
            "phone": receipt[3],
            "total": receipt[4],
            "calculated_subtotal": receipt[5],
            "total_matches": bool(receipt[6]),
            "created_at": receipt[7],
            "items": formatted_items
        }
    })


# ===============================
# Update Receipt (UPDATE)
# ===============================
@app.route("/receipt/<int:receipt_id>", methods=["PUT"])
@jwt_required()
def edit_receipt(receipt_id):

    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided"
        }), 400

    updated = update_receipt(user_id, receipt_id, data)

    if not updated:
        return jsonify({
            "success": False,
            "message": "Receipt not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Receipt updated successfully"
    })


# ===============================
# Delete Receipt (DELETE)
# ===============================
@app.route("/receipt/<int:receipt_id>", methods=["DELETE"])
@jwt_required()
def remove_receipt(receipt_id):

    user_id = get_jwt_identity()

    deleted = delete_receipt(user_id, receipt_id)

    if deleted == 0:
        return jsonify({
            "success": False,
            "message": "Receipt not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Receipt deleted successfully"
    })


# ===============================
# Analytics Summary
# ===============================
@app.route("/analytics/summary", methods=["GET"])
@jwt_required()
def analytics_summary():

    user_id = get_jwt_identity()

    summary = get_analytics_summary(user_id)

    return jsonify({
        "success": True,
        "analytics": summary
    })


# ===============================
# Run App
# ===============================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
