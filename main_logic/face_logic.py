import cv2
import os
import json
import numpy as np
from deepface import DeepFace
from gtts import gTTS
import subprocess
from datetime import datetime
from threading import Thread

# Paths
FACES_FOLDER = os.path.join(os.path.dirname(__file__), "../faces")
DB_FILE = os.path.join(os.path.dirname(__file__), "faces_db.json")

# Ensure folders exist
os.makedirs(FACES_FOLDER, exist_ok=True)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Load face database
with open(DB_FILE, "r", encoding="utf-8") as f:
    face_db = json.load(f)


# ----------------- TTS -----------------
def speak_text(text, lang="en"):
    """
    Text-to-speech for local testing.
    In web deployment, better to send text to frontend for browser playback.
    """
    try:
        tts = gTTS(text=text, lang=lang)
        filename = "temp_audio.mp3"
        tts.save(filename)
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.remove(filename)
    except Exception as e:
        print("TTS Error:", e)


# ----------------- Add Person -----------------
def add_person():
    """
    Add a new person using webcam input.
    GUI only works locally, not on web server.
    """
    person_name = input("Enter person's name: ").strip()
    relation = input("Enter relation: ").strip()
    cap = cv2.VideoCapture(0)
    count = 0
    saved_images = []

    print("Press 'c' to capture a photo, 'q' to stop adding.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera read failed.")
            break

        # Automatic brightness correction
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)

        cv2.imshow("Add Person", frame)
        key = cv2.waitKey(1)
        if key == ord("c"):
            filename = f"{person_name}_{count}.jpg"
            filepath = os.path.join(FACES_FOLDER, filename)
            cv2.imwrite(filepath, frame)
            saved_images.append(filename)
            print(f"Saved: {filename}")
            count += 1
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Update JSON database
    for img in saved_images:
        face_db[img] = {"name": person_name, "relation": relation}

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(face_db, f, indent=4, ensure_ascii=False)

    print(f"{person_name} added successfully!")


# ----------------- Normalize -----------------
def normalize_name(s):
    """Normalize filenames for matching"""
    return os.path.splitext(s)[0].replace(" ", "").replace("_", "").lower()


# ----------------- Recognize Faces -----------------
def recognize_faces(frame, return_info=False):
    """
    Recognize faces from a given frame.
    return_info=True → returns a list of recognized faces.
    """
    results_list = []

    # Brightness correction
    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)

    # Detect faces
    detections = DeepFace.extract_faces(frame, detector_backend="opencv", enforce_detection=False)

    for i, face_obj in enumerate(detections):
        face_img = face_obj["face"]
        temp_path = f"temp_face_{i}.jpg"
        cv2.imwrite(temp_path, (face_img * 255).astype(np.uint8))

        recognized = False
        # Search in face database
        result = DeepFace.find(temp_path, db_path=FACES_FOLDER, enforce_detection=False)
        if isinstance(result, list) and len(result) > 0 and not result[0].empty:
            identity = os.path.basename(result[0].iloc[0]["identity"])
            key_match = next(
                (k for k in face_db.keys() if normalize_name(k) == normalize_name(identity)),
                None
            )
            if key_match:
                details = face_db[key_match]
                name, relation = details["name"], details["relation"]
                recognized = True
                results_list.append({
                    "name": name,
                    "relation": relation,
                    "status": "recognized"
                })

        # If not recognized
        if not recognized:
            results_list.append({"status": "unknown"})

        # Cleanup temporary file
        try:
            os.remove(temp_path)
        except Exception:
            pass

    if return_info:
        return results_list
