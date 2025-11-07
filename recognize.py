import face_recognition
import cv2
import numpy as np
import pickle

ENCODINGS_FILE = "data/encodings.pkl"

def recognize_faces(image_path):
    print("Recognizing faces in:", image_path)
    try:
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        print("⚠️ No encodings found. Please run encode_all_faces() first.")
        return []

    known_encodings = data["encodings"]
    known_names = data["names"]

    img = cv2.imread(image_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_img)
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    recognized_names = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]
                recognized_names.append(name)
            else:
                recognized_names.append("Unknown")
        else:
            recognized_names.append("Unknown")

    print("✅ Recognized:", recognized_names)
    return recognized_names
