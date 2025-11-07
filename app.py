import os
import csv
import mysql.connector
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from encode_images import encode_all_faces
from recognize import recognize_faces

# ===============================
# Flask Initialization
# ===============================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
# Database Connection
# ===============================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="cpgisHD@21",  # update if needed
        database="noproxy"
    )

# ===============================
# Initialize attendance CSV (backup)
# ===============================
if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Timestamp"])

# ===============================
# 🏠 Home
# ===============================
@app.route("/")
def home():
    return jsonify({"message": "Flask backend running!", "port": 5500})

# ===============================
# 👤 Register new student (photo upload)
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

    student_name = os.path.splitext(filename)[0]

    # ✅ Update student’s image_path in users table
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

    # ✅ Encode student’s face
    try:
        encode_all_faces()
    except Exception as e:
        print("Encoding error:", e)

    return jsonify({
        "message": f"Student '{student_name}' registered and encoded successfully!",
        "file_saved": save_path
    })

# ===============================
# 🧠 Recognize faces → Save attendance properly
# ===============================
@app.route("/recognize", methods=["POST"])
def recognize_class():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    lecture_name = request.form.get("session", "Default Lecture")
    marked_by = request.form.get("marked_by", None)  # Optional faculty ID

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    recognized_files = recognize_faces(save_path)
    recognized_names = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for file_name in recognized_files:
            name_no_ext = os.path.splitext(file_name)[0]

            cursor.execute("SELECT id, name FROM users WHERE name = %s", (name_no_ext,))
            result = cursor.fetchone()

            if result:
                user_id, real_name = result
                recognized_names.append(real_name)

                # ✅ Insert attendance record properly
                cursor.execute("""
                    INSERT INTO attendance_records (date, lecture_name, status, user_id, marked_by)
                    VALUES (CURDATE(), %s, 'PRESENT', %s, %s)
                """, (lecture_name, user_id, marked_by))
                conn.commit()
            elif name_no_ext.lower() != "unknown":
                recognized_names.append(name_no_ext)

        cursor.close()
        conn.close()
    except Exception as e:
        print("MySQL insert error:", e)
        recognized_names = recognized_files

    # ✅ Optional CSV backup
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
# 📋 Get student attendance (by user_id)
# ===============================
@app.route("/attendance/<int:user_id>", methods=["GET"])
def get_attendance(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, lecture_name, status
            FROM attendance_records
            WHERE user_id = %s
            ORDER BY date DESC
        """, (user_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()

        data = [{"date": str(r[0]), "lecture_name": r[1], "status": r[2]} for r in records]

        return jsonify({
            "user_id": user_id,
            "count": len(data),
            "attendance": data
        })
    except Exception as e:
        print("MySQL fetch error:", e)
        return jsonify({"error": str(e)}), 500

# ===============================
# 🧩 Ping
# ===============================
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "Python backend running!", "port": 5500})

# ===============================
# 🚀 Run Server
# ===============================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5500, debug=True)
