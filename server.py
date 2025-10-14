import os
import json
import base64
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any

# Correct import paths for your logic modules
from main_logic.face_logic import recognize_face, add_person_logic, get_all_people_names
from main_logic.reminder_logic import get_all_reminders, add_reminder, edit_reminder, delete_reminder

app = FastAPI()

# Mount Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/faces", StaticFiles(directory="faces"), name="faces") # To serve face images

# Initialize Jinja2Templates
templates = Jinja2Templates(directory="templates")

# Define paths for data files
FACES_DIR = "faces"
FACE_DB_PATH = os.path.join("main_logic", "face_db.json")
REMINDERS_DB_PATH = os.path.join("main_logic", "reminders.json")

# Ensure the 'faces' directory exists
os.makedirs(FACES_DIR, exist_ok=True)

# Ensure face_db.json and reminders.json exist with initial empty structure if not present
if not os.path.exists(FACE_DB_PATH):
    with open(FACE_DB_PATH, 'w') as f:
        json.dump({}, f, indent=4)
if not os.path.exists(REMINDERS_DB_PATH):
    with open(REMINDERS_DB_PATH, 'w') as f:
        json.dump({}, f, indent=4)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# --- Section 1: Recognize Person ---

@app.post("/recognize_face")
async def recognize_face_api(image_data: Dict[str, str]):
    """
    Receives an image frame (base64) from the frontend, recognizes the face,
    and returns the recognized person's details.
    """
    encoded_image = image_data.get("image")
    if not encoded_image:
        return JSONResponse(content={"error": "No image data provided"}, status_code=400)

    # The frontend usually sends data:image/png;base64,...., so we split it
    header, encoded_image = encoded_image.split(",", 1)
    image_bytes = base64.b64decode(encoded_image)

    # Save the image temporarily for DeepFace
    temp_img_path = "temp_capture.jpg"
    with open(temp_img_path, "wb") as f:
        f.write(image_bytes)

    recognized_person = recognize_face(temp_img_path, FACE_DB_PATH, FACES_DIR)

    # Clean up the temporary image
    os.remove(temp_img_path)

    if recognized_person:
        return JSONResponse(content={"success": True, "person": recognized_person})
    else:
        return JSONResponse(content={"success": False, "message": "No face recognized or found in database"})

# --- Section 2: Add Person ---

@app.post("/add_person")
async def add_person_api(
    name: str = Form(...),
    relation: str = Form(...),
    file: UploadFile = File(None), # Optional: for file upload
    image_data_url: str = Form(None) # Optional: for webcam capture
):
    """
    Adds a new person to the database either by uploading an image file
    or by receiving a base64 image from the webcam.
    """
    image_path = None
    if file and file.filename:
        # Save the uploaded file
        # Ensure filenames are unique and valid for DeepFace/file system
        existing_files = os.listdir(FACES_DIR)
        base_name = name.replace(' ', '_')
        i = 0
        while True:
            filename = f"{base_name}_{i}{os.path.splitext(file.filename)[1]}"
            image_path = os.path.join(FACES_DIR, filename)
            if not os.path.exists(image_path):
                break
            i += 1
        
        with open(image_path, "wb") as f:
            f.write(await file.read())
    elif image_data_url:
        # Decode base64 image from webcam
        header, encoded_image = image_data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded_image)
        
        # Ensure filenames are unique and valid
        existing_files = os.listdir(FACES_DIR)
        base_name = name.replace(' ', '_')
        i = 0
        while True:
            filename = f"{base_name}_{i}.png" # Assuming PNG from webcam canvas
            image_path = os.path.join(FACES_DIR, filename)
            if not os.path.exists(image_path):
                break
            i += 1

        with open(image_path, "wb") as f:
            f.write(image_bytes)
    else:
        return JSONResponse(content={"success": False, "message": "No image provided."}, status_code=400)

    if image_path:
        # Pass only the filename relative to FACES_DIR to face_db.json
        add_person_logic(os.path.basename(image_path), name, relation, FACE_DB_PATH)
        return JSONResponse(content={"success": True, "message": f"Person {name} added successfully."})
    else:
        return JSONResponse(content={"success": False, "message": "Failed to process image."}, status_code=500)

@app.get("/get_all_people_names")
async def get_all_people_names_api():
    """
    Returns unique names of all people stored in face_db.json for dropdowns.
    """
    people_names = get_all_people_names(FACE_DB_PATH)
    return JSONResponse(content={"success": True, "people_names": people_names})


# --- Section 3: Reminders ---

@app.get("/get_reminders")
async def get_reminders_api():
    """
    Returns all reminders.
    """
    reminders = get_all_reminders(REMINDERS_DB_PATH)
    return JSONResponse(content={"success": True, "reminders": reminders})

@app.post("/add_reminder")
async def add_reminder_api(
    person_name: str = Form(...),
    time: str = Form(...),
    message: str = Form(...)
):
    """
    Adds a new reminder for a specific person.
    """
    add_reminder(person_name, time, message, REMINDERS_DB_PATH)
    return JSONResponse(content={"success": True, "message": "Reminder added successfully."})

@app.post("/edit_reminder")
async def edit_reminder_api(
    person_name: str = Form(...),
    old_time: str = Form(...),
    old_message: str = Form(...),
    new_time: str = Form(...),
    new_message: str = Form(...)
):
    """
    Edits an existing reminder.
    """
    success = edit_reminder(person_name, old_time, old_message, new_time, new_message, REMINDERS_DB_PATH)
    if success:
        return JSONResponse(content={"success": True, "message": "Reminder updated successfully."})
    else:
        return JSONResponse(content={"success": False, "message": "Reminder not found."}, status_code=404)

@app.post("/delete_reminder")
async def delete_reminder_api(
    person_name: str = Form(...),
    time: str = Form(...),
    message: str = Form(...)
):
    """
    Deletes a reminder.
    """
    success = delete_reminder(person_name, time, message, REMINDERS_DB_PATH)
    if success:
        return JSONResponse(content={"success": True, "message": "Reminder deleted successfully."})
    else:
        return JSONResponse(content={"success": False, "message": "Reminder not found."}, status_code=404)