from fastapi import FastAPI, UploadFile, Form, File, Request# type: ignore
from fastapi.responses import JSONResponse, HTMLResponse# type: ignore
from fastapi.staticfiles import StaticFiles# type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
import os
import shutil
import cv2# type: ignore
import numpy as np
from deepface import DeepFace# type: ignore

from main_logic import face_logic, reminder_logic

app = FastAPI(title="Memoraid AI System")

# ------------------ PATH SETUP ------------------
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Static + templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CAREGIVER_PASSWORD = "@dmin123"


# ------------------ HOME PAGE ------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ------------------ LOGIN ------------------
@app.post("/login")
async def login(password: str = Form(...)):
    if password == CAREGIVER_PASSWORD:
        return JSONResponse({"status": "success"})
    else:
        return JSONResponse({"status": "error", "message": "Invalid password"})


# ------------------ DASHBOARD ------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ------------------ RECOGNITION ------------------

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    try:
        # Read uploaded file directly into numpy array
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Run recognition
        faces = face_logic.recognize_face(img)

        # Wrap in nested structure for frontend
        return JSONResponse({"status": "success", "faces": {"faces": faces}})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})




# ------------------ ADD PERSON ------------------
@app.post("/add_person")
async def add_person(
    file: UploadFile = File(...),
    name: str = Form(...),
    relation: str = Form(...)
):
    try:
        if not name or not relation:
            return JSONResponse({"status": "error", "message": "Name and relation required"})

        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        filename = face_logic.save_face(temp_path, name, relation)
        os.remove(temp_path)

        return JSONResponse({"status": "success", "message": f"Person '{name}' added as {relation}", "filename": filename})

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ------------------ REMINDERS ------------------
@app.get("/get_reminders")
def get_reminders():
    """Fetch all reminders."""
    try:
        return reminder_logic.load_reminders()
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/add_reminder")
def add_reminder(user: str = Form(...), time: str = Form(...), message: str = Form(...)):
    try:
        reminder_logic.add_reminder(user, time, message)
        return JSONResponse({"status": "success", "message": "Reminder added"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/edit_reminder")
def edit_reminder(user: str = Form(...), index: int = Form(...), new_time: str = Form(None), new_message: str = Form(None)):
    try:
        reminder_logic.edit_reminder(user, index, new_time, new_message)
        return JSONResponse({"status": "success", "message": "Reminder edited"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/delete_reminder")
def delete_reminder(user: str = Form(...), index: int = Form(...)):
    try:
        reminder_logic.delete_reminder(user, index)
        return JSONResponse({"status": "success", "message": "Reminder deleted"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# ------------------ RUN ------------------
if __name__ == "__main__":
    import uvicorn# type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)
