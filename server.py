from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import shutil, os, cv2
from main_logic import face_logic, reminder_logic

app = FastAPI(title="Memoraid API")

# ----------------- Static & Templates -----------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Home -----------------
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ----------------- Face Routes -----------------
@app.post("/recognize")
async def recognize(file: UploadFile):
    try:
        # Save uploaded frame temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read frame
        frame = cv2.imread(file_path)
        os.remove(file_path)  # cleanup temp upload

        # Recognize faces
        recognized_faces = face_logic.recognize_faces(frame, return_info=True)
        return JSONResponse({"status": "success", "faces": recognized_faces})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/add_face")
async def add_face(file: UploadFile = None, name: str = Form(...), relation: str = Form(...)):
    try:
        if not file:
            return JSONResponse({"status": "error", "message": "No image uploaded"})

        # Save uploaded image temporarily
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Add face to faces folder and update face_db.json
        result = face_logic.add_person_from_file(file_path, name, relation)

        # Cleanup temp upload
        os.remove(file_path)

        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

# ----------------- Reminder Routes -----------------
@app.get("/get_reminders")
def get_reminders():
    try:
        data = reminder_logic.load_reminders()
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/add_reminder")
async def add_reminder(user: str = Form(...), time: str = Form(...), message: str = Form(...)):
    try:
        reminder_logic.add_reminder(user, time, message)
        return JSONResponse({"status": "success", "message": "Reminder added"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/delete_reminder")
async def delete_reminder(user: str = Form(...), index: int = Form(...)):
    try:
        reminder_logic.delete_reminder(user, index)
        return JSONResponse({"status": "success", "message": "Reminder deleted"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
