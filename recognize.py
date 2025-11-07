import face_recognition
import cv2
import numpy as np
import pickle
import os

ENCODINGS_FILE = "data/encodings.pkl"

def recognize_faces(image_path):
    print(f"🔍 Recognizing faces in: {image_path}")

    # --- Load encodings safely ---
    if not os.path.exists(ENCODINGS_FILE):
        print("⚠️ No encodings found. Please run encode_all_faces() first.")
        return []

    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)

    known_encodings = data.get("encodings", [])
    known_names = data.get("names", [])

    if not known_encodings or not known_names:
        print("⚠️ No data found in encodings file.")
        return []

    # --- Read input image ---
    img = cv2.imread(image_path)
    if img is None:
        print("⚠️ Failed to read image:", image_path)
        return []

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # --- Detect & encode faces ---
    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    recognized_names = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                # Clean and normalize name
                raw_name = known_names[best_match_index]
                name = os.path.splitext(raw_name)[0].replace("_", " ").title()
                recognized_names.append(name)
            else:
                recognized_names.append("Unknown")
        else:
            recognized_names.append("Unknown")

    print("✅ Recognized:", recognized_names)
    return recognized_names
