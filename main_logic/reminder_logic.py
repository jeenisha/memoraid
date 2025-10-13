import os
import json
import time
from datetime import datetime, date
from threading import Thread
from face_logic import speak_text  # Optional TTS, mostly for local testing

# ----------------- Paths -----------------
REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")

# Ensure reminders file exists
if not os.path.exists(REMINDERS_FILE):
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


# ----------------- Load Reminders -----------------
def load_reminders():
    """
    Load reminders from JSON file.
    Returns a dictionary of users -> reminders list.
    """
    try:
        if os.path.getsize(REMINDERS_FILE) > 0:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        print("Error loading reminders:", e)
    return {}


# ----------------- Save Reminders -----------------
def save_reminders(data):
    """
    Save reminders dictionary to JSON file.
    """
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ----------------- CRUD Operations -----------------
def add_reminder(user, time_str, message):
    """
    Add a reminder for a user.
    """
    data = load_reminders()
    data.setdefault(user, [])
    data[user].append({"time": time_str, "message": message})
    save_reminders(data)
    print(f"Reminder added for {user} at {time_str}: {message}")


def delete_reminder(user, index):
    """
    Delete a specific reminder by user and index.
    """
    data = load_reminders()
    if user in data and 0 <= index < len(data[user]):
        removed = data[user].pop(index)
        save_reminders(data)
        print(f"Deleted reminder: {removed}")
    else:
        print("Invalid user/index")


def edit_reminder(user, index, new_time=None, new_message=None):
    """
    Edit a specific reminder by user and index.
    """
    data = load_reminders()
    if user in data and 0 <= index < len(data[user]):
        if new_time:
            data[user][index]["time"] = new_time
        if new_message:
            data[user][index]["message"] = new_message
        save_reminders(data)
        print(f"Edited reminder: {data[user][index]}")
    else:
        print("Invalid user/index")


# ----------------- Background Checker -----------------
def reminders_checker():
    """
    Background thread that checks every 30 seconds for reminders scheduled for the current time.
    Runs as daemon, prints reminders, and optionally triggers TTS locally.
    For web deployment, send reminder text to frontend for audio playback.
    """
    triggered_today = set()
    last_reset = date.today()
    while True:
        try:
            today = date.today()
            if today != last_reset:
                triggered_today.clear()
                last_reset = today

            now_str = datetime.now().strftime("%H:%M")
            data = load_reminders()

            for user, reminders in data.items():
                for reminder in reminders:
                    sched = reminder.get("time", "").strip()
                    msg = reminder.get("message", "").strip()
                    if sched == now_str and (user, sched) not in triggered_today:
                        print(f"Reminder for {user}: {msg}")
                        # Optional: Local TTS playback
                        Thread(target=speak_text, args=(f"Reminder for {user}: {msg}",)).start()
                        triggered_today.add((user, sched))
            time.sleep(30)
        except Exception as e:
            print("Reminder checker error:", e)
            time.sleep(30)


# Start background checker thread
Thread(target=reminders_checker, daemon=True).start()
