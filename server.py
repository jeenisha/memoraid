from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil, os, cv2, pathlib

from main_logic import face_logic, reminder_logic

app = FastAPI(title="Memoraid API")

# static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CAREGIVER_PASSWORD = "@dmin123"   # password provided by you

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/login")
async def login(password: str = Form(...)):
    try:
        if password == CAREGIVER_PASSWORD:
            # Successful: respond with JSON (client will redirect)
            return JSONResponse({"status": "success"})
        else:
            return JSONResponse({"status": "error", "message": "Invalid password"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.get("/dashboard")
def dashboard(request: Request):
    # For simplicity we just render the dashboard template — the client is responsible
    # for asking password before redirecting here.
    return templates.TemplateResponse("dashboard.html", {"request": request})


# Recognize: receives a single image file (from webcam capture or upload)
@app.post("/recognize")
async def recognize(file: UploadFile):
    try:
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        frame = cv2.imread(temp_path)
        os.remove(temp_path)

        faces = face_logic.recognize_faces(frame, return_info=True)
        return JSONResponse({"status": "success", "faces": faces})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# Add person: accepts a file (blob from camera or uploaded image) plus name & relation
@app.post("/add_person")
async def add_person(file: UploadFile = None, name: str = Form(...), relation: str = Form(...)):
    try:
        if not name or not relation:
            return JSONResponse({"status": "error", "message": "Name and relation required"})

        if not file:
            return JSONResponse({"status": "error", "message": "Image file required"})

        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = face_logic.add_person_from_file(temp_path, name, relation)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


# Reminders: keep same CRUD behavior (load/add/edit/delete)
@app.get("/get_reminders")
def get_reminders():
    return reminder_logic.load_reminders()


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
