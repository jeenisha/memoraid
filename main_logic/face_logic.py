
import os
import json
import cv2
import numpy as np
from deepface import DeepFace

# Paths (adjust to absolute)
BASE_DIR = os.path.dirname(__file__)
FACES_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "faces"))
DB_FILE = os.path.join(BASE_DIR, "faces_db.json")

os.makedirs(FACES_FOLDER, exist_ok=True)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

# load db
with open(DB_FILE, "r", encoding="utf-8") as f:
    face_db = json.load(f)


def _save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(face_db, f, indent=4, ensure_ascii=False)


def normalize_name(s: str):
    return os.path.splitext(s)[0].replace(" ", "").replace("_", "").lower()


def add_person_from_file(file_path: str, name: str, relation: str):
    """
    Move uploaded file into faces folder and add entry to faces_db.json
    file_path: temporary uploaded path (server uploads/)
    """
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": "Uploaded file not found"}

        filename = os.path.basename(file_path)
        # avoid name collisions: if exists, append timestamp
        dest = os.path.join(FACES_FOLDER, filename)
        if os.path.exists(dest):
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{int(__import__('time').time())}{ext}"
            dest = os.path.join(FACES_FOLDER, filename)

        # move file
        os.replace(file_path, dest)

        # update db
        face_db[filename] = {"name": name, "relation": relation}
        _save_db()

        return {"status": "success", "message": f"{name} added as {filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def recognize_faces(frame, return_info=False):
    """
    Input: OpenCV frame (BGR)
    Output: list of {name, relation, confidence, status}
    """
    results = []
    try:
        # small brightness adjust (optional)
        frame_adj = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

        # DeepFace.extract_faces expects RGB or array; passing frame_adj works
        detections = DeepFace.extract_faces(img_path=frame_adj, detector_backend="opencv", enforce_detection=False)

        if not detections:
            return [] if return_info else {"faces": []}

        for i, face_obj in enumerate(detections):
            face_img = face_obj.get("face")
            if face_img is None:
                results.append({"status": "unknown", "name": "Unknown", "relation": "", "confidence": 0.0})
                continue

            # save temp face (face_img may be floats 0..1)
            temp_path = f"temp_face_{i}.jpg"
            arr = (face_img * 255).astype(np.uint8) if (face_img.dtype == np.float32 or face_img.max() <= 1.0) else face_img
            cv2.imwrite(temp_path, arr)

            # search DB
            try:
                res = DeepFace.find(img_path=temp_path, db_path=FACES_FOLDER, enforce_detection=False)
                if isinstance(res, list) and len(res) > 0 and not res[0].empty:
                    top = res[0].iloc[0]
                    matched_file = os.path.basename(top["identity"])
                    distance = float(top.get("distance", 0.0))
                    confidence = max(0.0, 1.0 - distance) if distance >= 0 else 0.0

                    # find matching record in face_db
                    matched_key = None
                    if matched_file in face_db:
                        matched_key = matched_file
                    else:
                        # try normalized match
                        matched_key = next((k for k in face_db.keys() if normalize_name(k) == normalize_name(matched_file)), None)

                    if matched_key:
                        details = face_db[matched_key]
                        results.append({
                            "status": "recognized",
                            "name": details.get("name", "Unknown"),
                            "relation": details.get("relation", ""),
                            "confidence": confidence
                        })
                    else:
                        results.append({
                            "status": "recognized",
                            "name": os.path.splitext(matched_file)[0],
                            "relation": "",
                            "confidence": confidence
                        })
                else:
                    results.append({"status": "unknown", "name": "Unknown", "relation": "", "confidence": 0.0})
            except Exception as e:
                results.append({"status": "error", "message": str(e), "name": "Unknown", "relation": "", "confidence": 0.0})
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    except Exception as e:
        return [] if return_info else {"faces": []}

    return results if return_info else {"faces": results}
