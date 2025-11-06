import os
import face_recognition
import numpy as np
import cv2

ENCODINGS_DIR = "encodings"
UPLOADS_DIR = "uploads"

def load_known_faces():
    known_encodings = []
    known_names = []
    for filename in os.listdir(ENCODINGS_DIR):
        if filename.endswith(".npy"):
            name = os.path.splitext(filename)[0]
            encoding = np.load(os.path.join(ENCODINGS_DIR, filename))
            known_encodings.append(encoding)
            known_names.append(name)
    return known_encodings, known_names

def recognize_faces(image_path):
    known_encodings, known_names = load_known_faces()

    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    recognized = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = known_names[match_index]

        recognized.append(name)

    return recognized

if __name__ == "__main__":
    for filename in os.listdir(UPLOADS_DIR):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            image_path = os.path.join(UPLOADS_DIR, filename)
            print(f"\n📸 Checking {filename}...")
            result = recognize_faces(image_path)
            print("Recognized:", result)
