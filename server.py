from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from main_logic.face_logic import recognize_face, add_face
from main_logic.reminder_logic import add_reminder, get_reminders

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "🚀 Memoraid FastAPI server running!"}

@app.post("/api/recognize")
async def recognize(req: Request):
    data = await req.json()
    return recognize_face(data["image"])

@app.post("/api/add_face")
async def add_face_api(req: Request):
    data = await req.json()
    return add_face(data["name"], data["relation"], data["image"])

@app.post("/api/reminder")
async def add_reminder_api(req: Request):
    data = await req.json()
    return add_reminder(data["person"], data["message"], data["time"])

@app.get("/api/reminders")
def get_reminders_api():
    return get_reminders()
