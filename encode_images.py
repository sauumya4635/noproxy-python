import os
import face_recognition
import numpy as np

STUDENTS_DIR = "students"
ENCODINGS_DIR = "encodings"

os.makedirs(ENCODINGS_DIR, exist_ok=True)

def encode_all_faces():
    for filename in os.listdir(STUDENTS_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(STUDENTS_DIR, filename)
            print(f"Encoding {filename}...")
            image = face_recognition.load_image_file(path)

            encodings = face_recognition.face_encodings(image)
            if len(encodings) > 0:
                encoding = encodings[0]
                name = os.path.splitext(filename)[0]
                np.save(os.path.join(ENCODINGS_DIR, f"{name}.npy"), encoding)
                print(f"✅ Saved encoding for {name}")
            else:
                print(f"⚠️ No face found in {filename}")

if __name__ == "__main__":
    encode_all_faces()
    print("✅ All student faces encoded successfully.")
