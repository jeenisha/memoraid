import os
import json
from datetime import datetime

REMINDER_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")

if not os.path.exists(REMINDER_FILE):
    with open(REMINDER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# ----------------- Load / Save -----------------
def load_reminders():
    with open(REMINDER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reminders(reminders):
    with open(REMINDER_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=4)

# ----------------- Add / Delete -----------------
def add_reminder(user, time_str, message):
    reminders = load_reminders()
    if user not in reminders:
        reminders[user] = []

    reminders[user].append({"time": time_str, "message": message})
    save_reminders(reminders)

    # Optional TTS (lazy import to avoid circular import)
    try:
        from .face_logic import speak_text
        speak_text(f"Reminder for {user}: {message}")
    except Exception:
        pass

def delete_reminder(user, index):
    reminders = load_reminders()
    if user in reminders and 0 <= index < len(reminders[user]):
        reminders[user].pop(index)
        if len(reminders[user]) == 0:
            reminders.pop(user)
        save_reminders(reminders)
