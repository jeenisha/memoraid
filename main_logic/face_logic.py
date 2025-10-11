import cv2, os, json, base64
import numpy as np
from deepface import DeepFace

faces_folder = "faces/"
json_file = "faces_db.json"

def recognize_face(image_b64: str):
    image_bytes = base64.b64decode(image_b64.split(',')[-1])
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # Recognition logic here...
    return {"recognized": "John Doe"}

def add_face(name: str, relation: str, image_b64: str):
    image_bytes = base64.b64decode(image_b64.split(',')[-1])
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    filepath = os.path.join(faces_folder, f"{name}.jpg")
    cv2.imwrite(filepath, frame)
    return {"message": f"{name} added successfully"}
