import face_recognition
import cv2
import numpy as np
import os
import pickle

STUDENTS_DIR = "students"
ENCODINGS_FILE = "data/encodings.pkl"

def encode_all_faces():
    print("Encoding all student faces...")
    known_encodings = []
    known_names = []

    for filename in os.listdir(STUDENTS_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(STUDENTS_DIR, filename)

            # Extract student's actual name from filename
            name = os.path.splitext(filename)[0]
            name = name.replace("_", " ").title()  # e.g. saumya_bhatia → Saumya Bhatia

            img = cv2.imread(filepath)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            faces = face_recognition.face_encodings(rgb_img)
            if len(faces) > 0:
                known_encodings.append(faces[0])
                known_names.append(name)
                print(f"✅ Encoded: {name}")
            else:
                print(f"⚠️ No face found in {filename}")

    os.makedirs("data", exist_ok=True)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump({"encodings": known_encodings, "names": known_names}, f)

    print(f"Saved encodings for {len(known_names)} students.")
