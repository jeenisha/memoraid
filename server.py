from fastapi import FastAPI, UploadFile, Form, File, Request# type: ignore
from fastapi.responses import JSONResponse, HTMLResponse# type: ignore
from fastapi.staticfiles import StaticFiles# type: ignore
from fastapi.templating import Jinja2Templates # type: ignore
import os
import shutil
import cv2# type: ignore
import numpy as np
from deepface import DeepFace# type: ignore
import time 
from main_logic import face_logic, reminder_logic
import traceback
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

# ------------------ REMINDERS (FINAL CORRECTED VERSION) ------------------

@app.get("/get_reminders")
def get_reminders_route():
    return reminder_logic.get_all_reminders()

@app.post("/add_reminder")
def add_reminder_route(
    user: str = Form(...),
    datetime: str = Form(...),
    message: str = Form(...)
):
    try:
        if not all([user, datetime, message]):
            return JSONResponse(status_code=400, content={"status": "error", "message": "Missing required fields"})
        
        reminder_id = int(time.time())
        new_reminder = {
            "id": reminder_id,
            "user": user,
            "datetime": datetime,
            "message": message
        }
        
        reminder_logic.add_reminder(new_reminder)
        return JSONResponse({"status": "success", "message": "Reminder added"})
    except Exception as e:
        # vvvvv THIS IS THE NEW DEBUGGING CODE vvvvv
        print("--- A CRITICAL ERROR OCCURRED IN /add_reminder ---")
        traceback.print_exc() # This will print the full error traceback
        # ^^^^^ THIS IS THE NEW DEBUGGING CODE ^^^^^
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    
@app.post("/delete_reminder")
def delete_reminder_route(id: int = Form(...)):
    try:
        if reminder_logic.delete_reminder_by_id(id):
            return JSONResponse({"status": "success", "message": "Reminder deleted"})
        else:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Reminder not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ------------------ RUN ------------------
if __name__ == "__main__":
    import uvicorn# type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)
