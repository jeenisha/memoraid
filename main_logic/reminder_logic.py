# In main_logic/reminder_logic.py
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMINDERS_FILE = os.path.join(BASE_DIR, 'reminders.json')

def get_all_reminders():
    try:
        if os.path.exists(REMINDERS_FILE) and os.path.getsize(REMINDERS_FILE) > 0:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []

def save_all_reminders(reminders):
    with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reminders, f, indent=2, ensure_ascii=False)

def add_reminder(new_reminder_object):
    reminders = get_all_reminders()
    reminders.append(new_reminder_object)
    save_all_reminders(reminders)

def delete_reminder_by_id(id_to_delete):
    reminders = get_all_reminders()
    original_count = len(reminders)
    filtered_reminders = [rem for rem in reminders if rem.get('id') != id_to_delete]
    if len(filtered_reminders) < original_count:
        save_all_reminders(filtered_reminders)
        return True
    return False