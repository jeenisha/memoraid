
import os
import json
import time
from datetime import datetime, date
from threading import Thread

BASE_DIR = os.path.dirname(__file__)
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")

if not os.path.exists(REMINDERS_FILE):
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4, ensure_ascii=False)


def load_reminders():
    try:
        if os.path.getsize(REMINDERS_FILE) > 0:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        print("Error loading reminders:", e)
    return {}


def save_reminders(data):
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def add_reminder(user, time_str, message):
    data = load_reminders()
    data.setdefault(user, [])
    data[user].append({"time": time_str, "message": message})
    save_reminders(data)
    print(f"Reminder added for {user} at {time_str}: {message}")


def delete_reminder(user, index):
    data = load_reminders()
    if user in data and 0 <= index < len(data[user]):
        removed = data[user].pop(index)
        save_reminders(data)
        print(f"Deleted reminder: {removed}")
        return True
    return False


def edit_reminder(user, index, new_time=None, new_message=None):
    data = load_reminders()
    if user in data and 0 <= index < len(data[user]):
        if new_time:
            data[user][index]["time"] = new_time
        if new_message:
            data[user][index]["message"] = new_message
        save_reminders(data)
        print(f"Edited reminder: {data[user][index]}")
        return True
    return False


# Background checker to speak reminder (keeps same)
def reminders_checker():
    triggered_today = set()
    last_reset = date.today()

    while True:
        try:
            today = date.today()
            if today != last_reset:
                triggered_today.clear()
                last_reset = today

            current_reminders = load_reminders()
            now_str = datetime.now().strftime("%H:%M")

            if current_reminders:
                for user, reminders in current_reminders.items():
                    if not isinstance(reminders, list):
                        continue
                    for reminder in reminders:
                        sched_raw = str(reminder.get("time", "")).strip()
                        msg = str(reminder.get("message", "")).strip()

                        if sched_raw == "" or msg == "" or len(sched_raw) != 5:
                            continue

                        key = (user, sched_raw)
                        if sched_raw == now_str and key not in triggered_today:
                            print(f"Reminder for {user}: {msg} (scheduled {sched_raw}, now {now_str})")
                            # optionally TTS here (but may fail on headless)
                            triggered_today.add(key)

            time.sleep(30)
        except Exception as ex:
            print("Error in reminders_checker:", ex)
            time.sleep(30)


# Start background checker thread (daemon)
Thread(target=reminders_checker, daemon=True).start()
