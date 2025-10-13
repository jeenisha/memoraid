from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil
import os
import cv2
import json

# Import main logic
from main_logic import face_logic
from main_logic import reminder_logic

# ----------------- FastAPI App -----------------
app = FastAPI(title="Memoraid API")

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Temporary folder to save uploaded images
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Routes -----------------

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------- Reminders -----------------
@app.get("/get_reminders")
def get_reminders():
    return reminder_logic.load_reminders()


@app.post("/add_reminder")
async def add_reminder(user: str = Form(...), time: str = Form(...), message: str = Form(...)):
    try:
        reminder_logic.add_reminder(user, time, message)
        return JSONResponse({"status": "success", "message": "Reminder added"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/edit_reminder")
async def edit_reminder(user: str = Form(...), index: int = Form(...), new_time: str = Form(None), new_message: str = Form(None)):
    try:
        reminder_logic.edit_reminder(user, index, new_time, new_message)
        return JSONResponse({"status": "success", "message": "Reminder edited"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/delete_reminder")
async def delete_reminder(user: str = Form(...), index: int = Form(...)):
    try:
        reminder_logic.delete_reminder(user, index)
        return JSONResponse({"status": "success", "message": "Reminder deleted"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ----------------- Face Recognition -----------------
@app.post("/recognize")
async def recognize(file: UploadFile):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        frame = cv2.imread(file_path)
        os.remove(file_path)

        # Return recognized faces info instead of showing OpenCV window
        recognized_faces = face_logic.recognize_faces(frame, return_info=True)
        return JSONResponse({"status": "success", "faces": recognized_faces})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ----------------- Add Face -----------------
@app.post("/add_face")
async def add_face(name: str = Form(...), relation: str = Form(...), file: UploadFile = None):
    try:
        filenames = []

        if file:
            file_path = os.path.join(face_logic.FACES_FOLDER, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            filenames.append(file.filename)

        # Update face database
        for img in filenames:
            face_logic.face_db[img] = {"name": name, "relation": relation}

        with open(face_logic.DB_FILE, "w", encoding="utf-8") as f:
            json.dump(face_logic.face_db, f, indent=4, ensure_ascii=False)

        return JSONResponse({"status": "success", "message": f"{name} added successfully"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
