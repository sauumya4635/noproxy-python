from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
from encode_images import encode_all_faces
from recognize import recognize_faces
import csv
from flask_cors import CORS  # ✅ allow frontend to connect

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5502"])  # ✅ frontend running on 5502

# --- Folders ---
UPLOAD_FOLDER = "uploads"
STUDENT_FOLDER = "students"
ATTENDANCE_FILE = "attendance.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STUDENT_FOLDER, exist_ok=True)

# --- Initialize attendance file ---
if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Timestamp"])

# -------------------------------------------------
# 🏠 Home Page (upload interface)
# -------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------------------------------
# 👤 Register a new student
# -------------------------------------------------
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

    encode_all_faces()

    return jsonify({"message": f"Student {filename} registered and encoded successfully!"})

# -------------------------------------------------
# 🧠 Recognize faces and mark attendance
# -------------------------------------------------
@app.route("/recognize", methods=["POST"])
def recognize_class():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    recognized_names = recognize_faces(save_path)

    recognized_cleaned = []
    for name in recognized_names:
        if name.lower() != "unknown":
            recognized_cleaned.append(name)
            # Mark attendance
            with open(ATTENDANCE_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    if not recognized_cleaned:
        return jsonify({"message": "No known faces recognized.", "recognized": recognized_names})

    return jsonify({"message": "Attendance recorded.", "recognized": recognized_cleaned})

# -------------------------------------------------
# 🧩 Optional: Test route for connection
# -------------------------------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "Python backend running!", "port": 5500})

# -------------------------------------------------
# 🚀 Run the app
# -------------------------------------------------
if __name__ == "__main__":
    # Run Flask on port 5500 so frontend (5502) can connect easily
    app.run(host="127.0.0.1", port=5500, debug=True)
