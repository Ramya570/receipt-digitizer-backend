import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.utils import secure_filename
from datetime import timedelta

app = Flask(__name__)

# =========================
# CONFIGURATION
# =========================

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///receipt.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    "super-secret-key"
)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)
jwt = JWTManager(app)

# =========================
# DATABASE MODEL
# =========================

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return jsonify({
        "message": "Receipt Digitizer API is running"
    })


# -------------------------
# LOGIN (Demo Login)
# -------------------------
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data or "email" not in data:
        return jsonify({
            "success": False,
            "message": "Email required"
        }), 400

    email = data["email"]

    access_token = create_access_token(identity=email)

    return jsonify({
        "success": True,
        "access_token": access_token
    })


# -------------------------
# UPLOAD RECEIPT
# -------------------------
@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_receipt():

    # Check file exists
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "No selected file"
        }), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    current_user = get_jwt_identity()

    new_receipt = Receipt(
        user_email=current_user,
        filename=filename
    )

    db.session.add(new_receipt)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "filename": filename
    })


# -------------------------
# GET RECEIPTS
# -------------------------
@app.route("/receipts", methods=["GET"])
@jwt_required()
def get_receipts():

    current_user = get_jwt_identity()

    receipts = Receipt.query.filter_by(
        user_email=current_user
    ).all()

    receipt_list = [
        {
            "id": r.id,
            "filename": r.filename
        }
        for r in receipts
    ]

    return jsonify({
        "success": True,
        "receipts": receipt_list
    })


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
