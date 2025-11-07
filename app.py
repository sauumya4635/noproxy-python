from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
import mysql.connector
import csv
from flask_cors import CORS
from encode_images import encode_all_faces
from recognize import recognize_faces

# ===============================
# Flask Initialization
# ===============================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all for local testing

# ===============================
# Folder Setup
# ===============================
UPLOAD_FOLDER = "uploads"
STUDENT_FOLDER = "students"
ATTENDANCE_FILE = "data/attendance.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STUDENT_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ===============================
# Database Connection Helper
# ===============================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="cpgisHD@21",   # your MySQL password
        database="noproxy"
    )

# ===============================
# Initialize attendance CSV
# ===============================
if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Timestamp"])

# ===============================
# 🏠 Home Page (optional)
# ===============================
@app.route("/")
def home():
    return jsonify({"message": "Flask backend running!", "port": 5500})

# ===============================
# 👤 Register a new student
# ===============================
@app.route("/register", methods=["POST"])
def register_student():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename
    save_path = os.path.join(STUDENT_FOLDER, filename)
    file.save(save_path)

    # ✅ Extract student name (remove extension)
    student_name = os.path.splitext(filename)[0]

    # ✅ Update the image_path in MySQL for that student
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET image_path = %s WHERE name = %s",
            (save_path, student_name)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("MySQL update error:", e)

    # ✅ Encode all known faces again
    try:
        encode_all_faces()
    except Exception as e:
        print("Encoding error:", e)

    return jsonify({
        "message": f"Student '{student_name}' registered and encoded successfully!",
        "file_saved": save_path
    })

# ===============================
# 🧠 Recognize faces and mark attendance
# ===============================
@app.route("/recognize", methods=["POST"])
def recognize_class():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    # ✅ Recognize faces from uploaded image
    recognized_files = recognize_faces(save_path)
    recognized_names = []

    # ✅ Match filenames with real names from MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for file_name in recognized_files:
            name_no_ext = os.path.splitext(file_name)[0]
            cursor.execute("SELECT name FROM users WHERE name = %s", (name_no_ext,))
            result = cursor.fetchone()
            if result:
                recognized_names.append(result[0])
            elif name_no_ext.lower() != "unknown":
                recognized_names.append(name_no_ext)

        cursor.close()
        conn.close()
    except Exception as e:
        print("MySQL lookup error:", e)
        recognized_names = recognized_files

    # ✅ Write attendance to CSV
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for name in recognized_names:
            if name.lower() != "unknown":
                writer.writerow([name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    if not recognized_names:
        return jsonify({"message": "No known faces recognized.", "recognized": []})

    return jsonify({
        "message": "Attendance recorded.",
        "recognized": recognized_names
    })

# ===============================
# 🧩 Ping Route (for testing)
# ===============================
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "Python backend running!", "port": 5500})

# ===============================
# 🚀 Run Flask Server
# ===============================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5500, debug=True)
