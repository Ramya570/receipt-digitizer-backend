# 🧾 Receipt Digitizer Backend API

A Flask-based backend API that extracts receipt data using OCR, stores structured receipt data in a database, and provides analytics per user.

---

## 🚀 Features

- 🔐 JWT Authentication (Register/Login)
- 🧾 OCR Receipt Processing
- 📦 Store Structured Receipt Data
- 📊 Analytics (Total spending, item breakdown)
- 👤 User-specific data isolation
- 🗄 SQLite Database
- 🌐 RESTful API

---

## 🛠 Tech Stack

- Python
- Flask
- Flask-JWT-Extended
- SQLite
- Bcrypt
- Flask-CORS

---

## 📂 Project Structure


---

## 🔐 Authentication

### Register
POST `/register`

Body:
```json
{
  "username": "testuser",
  "password": "123456"
}
Login

POST /login

Returns:

{
  "access_token": "JWT_TOKEN"
}

📦 Receipt Endpoints
Upload Receipt

POST /upload

Requires JWT Token

Get Receipts

GET /receipts

Requires JWT Token

Delete Receipt

DELETE /receipt/<id>

Requires JWT Token

📊 Analytics
Get Total Spending

GET /analytics

Returns total spending per user.

▶️ Run Locally
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py


Server runs at:

http://127.0.0.1:5000

🎯 Future Improvements

PostgreSQL instead of SQLite

Docker containerization

Cloud deployment

Frontend integration

👨‍💻 Author

Your Name


---

# 🚀 After Updating README

Your project will now look complete and professional.

---

