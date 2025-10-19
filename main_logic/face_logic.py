import os
import json
import cv2
import numpy as np
import uuid
import time
from deepface import DeepFace
from numpy.linalg import norm

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


def _generate_unique_filename(original_name: str):
    base, ext = os.path.splitext(original_name)
    safe = base.replace(" ", "_")
    return f"{safe}_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext or '.jpg'}"


def _compute_embedding(img_path: str):
    """
    Use DeepFace.represent to compute embedding for a single face image.
    Returns a 1-D list of floats (embedding) or None on failure.
    """
    try:
        # Facenet or Facenet512 works well; keep enforce_detection False so headless works
        vec = DeepFace.represent(img_path=img_path, model_name="Facenet", enforce_detection=False)
        # DeepFace.represent returns list of lists sometimes; coerce to 1D
        if isinstance(vec, list) and len(vec) > 0:
            # If nested list
            if isinstance(vec[0], (list, np.ndarray)):
                emb = np.array(vec[0]).astype(float)
            else:
                emb = np.array(vec).astype(float)
        else:
            emb = np.array(vec).astype(float)
        return emb.tolist()
    except Exception:
        return None


def add_person_from_file(file_path: str, name: str, relation: str):
    """
    Move uploaded file into faces folder, compute embedding, and add entry to faces_db.json.
    file_path: temporary uploaded path (server uploads/)
    """
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": "Uploaded file not found"}

        filename = os.path.basename(file_path)
        unique_name = _generate_unique_filename(filename)
        dest = os.path.join(FACES_FOLDER, unique_name)

        # move file to faces folder
        os.replace(file_path, dest)

        # compute embedding
        embedding = _compute_embedding(dest)

        # store in db (embedding as list)
        face_db[unique_name] = {"name": name, "relation": relation, "embedding": embedding}
        _save_db()

        return {"status": "success", "message": f"{name} added as {unique_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _cosine_similarity(a: np.ndarray, b: np.ndarray):
    if a is None or b is None:
        return -1.0
    denom = (norm(a) * norm(b))
    if denom == 0:
        return -1.0
    return float(np.dot(a, b) / denom)


def recognize_faces(frame, return_info=False):
    """
    Input: OpenCV frame (BGR)
    Output: list of {name, relation, confidence, status}
    Uses DeepFace.extract_faces to get face crops, then compares embeddings to stored DB.
    """
    results = []
    try:
        # adjust brightness/contrast slightly to help detection
        frame_adj = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

        # extract faces (returns list of dicts with 'face' key as the face array RGB)
        detections = DeepFace.extract_faces(img_path=frame_adj, detector_backend="opencv", enforce_detection=False)

        if not detections:
            return [] if return_info else {"faces": []}

        # Prepare stored embeddings
        stored_items = []
        for fname, rec in face_db.items():
            emb = rec.get("embedding")
            if emb is not None:
                try:
                    emb_arr = np.array(emb, dtype=float)
                    stored_items.append((fname, rec, emb_arr))
                except Exception:
                    continue

        for i, face_obj in enumerate(detections):
            face_img = face_obj.get("face")
            if face_img is None:
                results.append({"status": "unknown", "name": "Unknown", "relation": "", "confidence": 0.0})
                continue

            # save temp face image
            temp_path = f"temp_face_{uuid.uuid4().hex[:8]}.jpg"
            arr = (face_img * 255).astype(np.uint8) if (face_img.dtype == np.float32 or face_img.max() <= 1.0) else face_img
            cv2.imwrite(temp_path, arr)

            try:
                # compute embedding for this face crop
                emb = _compute_embedding(temp_path)
                emb_arr = np.array(emb, dtype=float) if emb is not None else None

                # find best match by cosine similarity
                best = None
                best_score = -1.0
                for fname, rec, stored_emb in stored_items:
                    score = _cosine_similarity(emb_arr, stored_emb)
                    if score > best_score:
                        best_score = score
                        best = (fname, rec, score)

                # interpret best match with threshold
                # Cosine similarity ranges -1..1. Typical good match > 0.6-0.75 for facenet depending on preprocessing.
                threshold = 0.6
                if best and best_score >= threshold:
                    fname, rec, score = best
                    confidence = float(best_score)
                    results.append({
                        "status": "recognized",
                        "name": rec.get("name", os.path.splitext(fname)[0]),
                        "relation": rec.get("relation", ""),
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
