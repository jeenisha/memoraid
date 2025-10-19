import os
import json
import cv2
from deepface import DeepFace
import numpy as np

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FACES_FOLDER = os.path.join(BASE_DIR, "faces")
JSON_FILE = os.path.join(BASE_DIR, "main_logic", "faces_db.json")

os.makedirs(FACES_FOLDER, exist_ok=True)

# ------------------ Load & Save Helpers ------------------
def load_faces_db():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f:
            json.dump({}, f)
    with open(JSON_FILE, "r") as f:
        return json.load(f)

def save_faces_db(db):
    with open(JSON_FILE, "w") as f:
        json.dump(db, f, indent=4)

# ------------------ Add New Person ------------------
def save_face(image_path, name, relation):
    db = load_faces_db()

    # count how many existing images of same person
    existing = [f for f in db.keys() if f.startswith(name)]
    index = len(existing)

    new_filename = f"{name}_{index}.jpg"
    save_path = os.path.join(FACES_FOLDER, new_filename)

    # Save image to faces folder
    img = cv2.imread(image_path)
    if img is not None:
        cv2.imwrite(save_path, img)

    # store metadata (no embedding yet)
    db[new_filename] = {"name": name, "relation": relation}
    save_faces_db(db)

    return new_filename

# ------------------ Recognition ------------------
# ------------------ Recognition ------------------
def recognize_face(image):
    """
    Compares uploaded image (path or numpy array) against all known faces and returns best matches.
    """
    db = load_faces_db()
    if not db:
        return [{"face": "No registered faces found"}]

    try:
        results = []
        for filename, info in db.items():
            known_img_path = os.path.join(FACES_FOLDER, filename)
            if not os.path.exists(known_img_path):
                continue

            try:
                verification = DeepFace.verify(
                    img1_path=image,           # <-- can be path or np.array
                    img2_path=known_img_path,
                    model_name="Facenet",
                    distance_metric="cosine",
                    enforce_detection=False
                )

                if verification["verified"]:
                    results.append({
                        "name": info["name"],
                        "relation": info["relation"],
                        "match": filename,
                        "distance": round(float(verification["distance"]), 4)
                    })
            except Exception as e:
                print(f"Error verifying with {filename}: {e}")
                continue

        if not results:
            return [{"face": "Unknown"}]
        else:
            results = sorted(results, key=lambda x: x["distance"])
            return results[:3]  # top 3 matches

    except Exception as e:
        print("Recognition error:", e)
        return [{"face": "Error", "message": str(e)}]

