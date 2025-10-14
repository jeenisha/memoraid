import os
import json
from deepface import DeepFace
import shutil # For deleting directories

# Path to the face database JSON file
FACE_DB_PATH = os.path.join(os.path.dirname(__file__), "face_db.json")
# This FACES_DIR should be the actual directory containing face images, relative to server.py
# Or an absolute path if DeepFace.find needs it. Keeping it relative to the project root.
FACES_DIR = "faces" 

def load_face_db(face_db_path: str):
    """Loads the face database from face_db.json."""
    if os.path.exists(face_db_path):
        with open(face_db_path, 'r') as f:
            return json.load(f)
    return {}

def save_face_db(db, face_db_path: str):
    """Saves the face database to face_db.json."""
    with open(face_db_path, 'w') as f:
        json.dump(db, f, indent=4)

def recognize_face(captured_image_path: str, face_db_path: str, faces_dir: str):
    """
    Recognizes a face in the captured image against the known faces database.
    Args:
        captured_image_path (str): Path to the image captured from the webcam.
        face_db_path (str): Path to the face_db.json file.
        faces_dir (str): Directory containing the known face images. This is passed to DeepFace.
    Returns:
        dict: A dictionary containing 'name' and 'relation' of the recognized person,
              or None if no face is recognized or found.
    """
    try:
        # DeepFace.find expects db_path to be the directory where images are stored
        # It will build/use its .deepface cache there.
        dfs = DeepFace.find(img_path=captured_image_path, db_path=faces_dir, enforce_detection=False, model_name="VGG-Face")

        if dfs and len(dfs[0]) > 0:
            # Assuming the first result is the most confident match
            # The 'identity' column in DeepFace results gives the full path to the matched image
            matched_img_full_path = dfs[0].iloc[0]['identity']
            matched_filename = os.path.basename(matched_img_full_path)

            face_db = load_face_db(face_db_path)
            
            # Find the entry in face_db.json that matches the filename
            if matched_filename in face_db:
                data = face_db[matched_filename]
                return {"name": data["name"], "relation": data["relation"]}
            else:
                # This warning indicates a discrepancy between DeepFace's index and your JSON
                print(f"Warning: DeepFace matched {matched_filename} but it was not found as a key in {face_db_path}")
                return None
        else:
            return None # No face recognized
    except ValueError as e:
        # DeepFace raises ValueError if no face is detected in the input image
        print(f"No face detected in the captured image: {e}")
        return None
    except Exception as e:
        print(f"Error during face recognition: {e}")
        return None


def add_person_logic(filename: str, name: str, relation: str, face_db_path: str):
    """
    Adds a new person's face data to the database.
    Args:
        filename (str): The filename of the saved image file (e.g., "Alice_0.jpg").
        name (str): Name of the person.
        relation (str): Relation of the person to the patient.
        face_db_path (str): Path to the face_db.json file.
    """
    face_db = load_face_db(face_db_path)
    face_db[filename] = {"name": name, "relation": relation}
    save_face_db(face_db, face_db_path)
    
    # After adding a new image, it's a good idea to clear DeepFace's cache
    # so it rebuilds its database to include the new face on the next recognition.
    deepface_cache_path = os.path.join(FACES_DIR, ".deepface")
    if os.path.exists(deepface_cache_path):
        print(f"Deleting DeepFace cache for rebuild: {deepface_cache_path}")
        shutil.rmtree(deepface_cache_path)


def get_all_people_names(face_db_path: str):
    """
    Returns a list of unique names of all people stored in face_db.json.
    """
    face_db = load_face_db(face_db_path)
    unique_names = set()
    for data in face_db.values():
        unique_names.add(data["name"])
    return sorted(list(unique_names))