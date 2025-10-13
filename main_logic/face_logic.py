import cv2
import os
import json
import numpy as np
from deepface import DeepFace
from gtts import gTTS
import subprocess

# ----------------- Paths -----------------
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


# ----------------- TTS (Optional) -----------------
def speak_text(text, lang="en"):
    """Text-to-speech for local testing"""
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


# ----------------- Normalize -----------------
def normalize_name(s):
    """Normalize filenames for matching"""
    return os.path.splitext(s)[0].replace(" ", "").replace("_", "").lower()


# ----------------- Add Person from File -----------------
def add_person_from_file(file_path, name, relation):
    """
    Add a person from a given image file.
    Saves image to faces folder and updates JSON database.
    """
    try:
        filename = os.path.basename(file_path)
        save_path = os.path.join(FACES_FOLDER, filename)
        # Copy the uploaded file to faces folder
        os.replace(file_path, save_path)

        # Update database
        face_db[filename] = {"name": name, "relation": relation}
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(face_db, f, indent=4, ensure_ascii=False)

        return {"status": "success", "message": f"{name} added successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------- Recognize Faces -----------------
def recognize_faces(frame, return_info=False):
    """
    Recognize faces from a given frame.
    Returns a list of recognized face details with confidence.
    """
    results_list = []

    # Adjust brightness slightly
    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=30)

    # Detect faces
    detections = DeepFace.extract_faces(frame, detector_backend="opencv", enforce_detection=False)

    for i, face_obj in enumerate(detections):
        face_img = face_obj["face"]
        temp_path = f"temp_face_{i}.jpg"
        cv2.imwrite(temp_path, (face_img * 255).astype(np.uint8))

        recognized = False
        best_confidence = 0.0
        name = relation = "Unknown"

        try:
            # Match with face database
            result = DeepFace.find(temp_path, db_path=FACES_FOLDER, enforce_detection=False)
            if isinstance(result, list) and len(result) > 0 and not result[0].empty:
                top_row = result[0].iloc[0]
                identity_filename = os.path.basename(top_row["identity"])
                best_confidence = float(1 - top_row["distance"])  # Convert distance → confidence approx.

                # Exact filename match
                if identity_filename in face_db:
                    details = face_db[identity_filename]
                    name = details.get("name", "Unknown")
                    relation = details.get("relation", "Unknown")
                    recognized = True
                else:
                    # Fallback: normalize and match
                    key_match = next(
                        (k for k in face_db.keys() if normalize_name(k) == normalize_name(identity_filename)),
                        None
                    )
                    if key_match:
                        details = face_db[key_match]
                        name = details.get("name", "Unknown")
                        relation = details.get("relation", "Unknown")
                        recognized = True
        except Exception as e:
            print("Recognition error:", e)

        results_list.append({
            "name": name,
            "relation": relation,
            "confidence": best_confidence,
            "status": "recognized" if recognized else "unknown"
        })

        # Cleanup temporary file
        try:
            os.remove(temp_path)
        except Exception:
            pass

    if return_info:
        return results_list
    else:
        return {"faces": results_list}
