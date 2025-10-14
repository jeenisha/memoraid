import os
import json

# Path to the reminders database JSON file (relative to where reminder_logic.py is run from)
REMINDERS_DB_PATH = os.path.join(os.path.dirname(__file__), "reminders.json")

def load_reminders_db():
    """Loads the reminders database from reminders.json."""
    if os.path.exists(REMINDERS_DB_PATH):
        with open(REMINDERS_DB_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_reminders_db(db):
    """Saves the reminders database to reminders.json."""
    with open(REMINDERS_DB_PATH, 'w') as f:
        json.dump(db, f, indent=4)

def get_all_reminders(reminders_db_path: str):
    """
    Returns all reminders from the reminders.json.
    """
    if os.path.exists(reminders_db_path):
        with open(reminders_db_path, 'r') as f:
            return json.load(f)
    return {}

def add_reminder(person_name: str, time: str, message: str, reminders_db_path: str):
    """
    Adds a new reminder for a specific person.
    Args:
        person_name (str): The name of the person associated with the reminder.
        time (str): The time of the reminder (e.g., "HH:MM").
        message (str): The reminder message.
        reminders_db_path (str): Path to the reminders.json file.
    """
    reminders_db = load_reminders_db()
    if person_name not in reminders_db:
        reminders_db[person_name] = []
    
    reminders_db[person_name].append({"time": time, "message": message})
    save_reminders_db(reminders_db)

def edit_reminder(person_name: str, old_time: str, old_message: str, new_time: str, new_message: str, reminders_db_path: str):
    """
    Edits an existing reminder for a specific person.
    Args:
        person_name (str): The name of the person.
        old_time (str): The original time of the reminder to be edited.
        old_message (str): The original message of the reminder to be edited.
        new_time (str): The new time for the reminder.
        new_message (str): The new message for the reminder.
        reminders_db_path (str): Path to the reminders.json file.
    Returns:
        bool: True if the reminder was found and edited, False otherwise.
    """
    reminders_db = load_reminders_db()
    if person_name in reminders_db:
        for reminder in reminders_db[person_name]:
            if reminder["time"] == old_time and reminder["message"] == old_message:
                reminder["time"] = new_time
                reminder["message"] = new_message
                save_reminders_db(reminders_db)
                return True
    return False

def delete_reminder(person_name: str, time: str, message: str, reminders_db_path: str):
    """
    Deletes a reminder for a specific person.
    Args:
        person_name (str): The name of the person.
        time (str): The time of the reminder to be deleted.
        message (str): The message of the reminder to be deleted.
        reminders_db_path (str): Path to the reminders.json file.
    Returns:
        bool: True if the reminder was found and deleted, False otherwise.
    """
    reminders_db = load_reminders_db()
    if person_name in reminders_db:
        initial_len = len(reminders_db[person_name])
        reminders_db[person_name] = [
            r for r in reminders_db[person_name]
            if not (r["time"] == time and r["message"] == message)
        ]
        if len(reminders_db[person_name]) < initial_len:
            save_reminders_db(reminders_db)
            return True
    return False