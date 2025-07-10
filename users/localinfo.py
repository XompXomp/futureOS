import sqlite3
import json
from datetime import datetime
from typing import Optional, List

DB_PATH = 'instance/localinfo.db'

# Ensure the database and tables exist
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Table for storing the full EMR as a JSON blob
c.execute('''
CREATE TABLE IF NOT EXISTS patient_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    record_json TEXT NOT NULL,
    last_updated TEXT NOT NULL
)
''')

# Table for storing CareAITreatments (user-updatable fields)
c.execute('''
CREATE TABLE IF NOT EXISTS care_ai_treatments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    sleep_quality INTEGER,  -- Now integer, rated on 10
    medication_adherence TEXT,
    sleep_hours REAL,
    last_updated TEXT NOT NULL
)
''')

# Table for goals
c.execute('''
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL
)
''')

# Table for daily checklist items
c.execute('''
CREATE TABLE IF NOT EXISTS daily_checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL
)
''')

# Table for recommendations
c.execute('''
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL
)
''')

# Table for appointments
c.execute('''
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appt_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    last_updated TEXT NOT NULL
)
''')

conn.commit()
conn.close()

def set_patient_record(user_id: int, record: dict):
    """Set or update the EMR for a user."""
    now = datetime.utcnow().isoformat()
    record_json = json.dumps(record)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM patient_record WHERE user_id = ?', (user_id,))
    if c.fetchone():
        c.execute('UPDATE patient_record SET record_json = ?, last_updated = ? WHERE user_id = ?', (record_json, now, user_id))
    else:
        c.execute('INSERT INTO patient_record (user_id, record_json, last_updated) VALUES (?, ?, ?)', (user_id, record_json, now))
    conn.commit()
    conn.close()

def get_patient_record(user_id: int) -> Optional[dict]:
    """Get the EMR for a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT record_json FROM patient_record WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

# Update table creation for care_ai_treatments
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS care_ai_treatments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    sleep_quality INTEGER,  -- Now integer, rated on 10
    medication_adherence TEXT,
    sleep_hours REAL,
    last_updated TEXT NOT NULL
)
''')
conn.commit()
conn.close()

def add_or_update_care_ai_treatment(user_id: int, date: str, sleep_quality: Optional[int] = None, medication_adherence: Optional[str] = None, sleep_hours: Optional[float] = None):
    """Add or update a CareAITreatments entry for a user and date. sleep_quality is int (0-10)."""
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM care_ai_treatments WHERE user_id = ? AND date = ?', (user_id, date))
    if c.fetchone():
        c.execute('''
            UPDATE care_ai_treatments SET sleep_quality = ?, medication_adherence = ?, sleep_hours = ?, last_updated = ?
            WHERE user_id = ? AND date = ?
        ''', (sleep_quality, medication_adherence, sleep_hours, now, user_id, date))
    else:
        c.execute('''
            INSERT INTO care_ai_treatments (user_id, date, sleep_quality, medication_adherence, sleep_hours, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, date, sleep_quality, medication_adherence, sleep_hours, now))
    conn.commit()
    conn.close()

def get_care_ai_treatment(user_id: int, date: str) -> Optional[dict]:
    """Get a CareAITreatments entry for a user and date. sleep_quality is int (0-10)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT sleep_quality, medication_adherence, sleep_hours, last_updated
        FROM care_ai_treatments WHERE user_id = ? AND date = ?
    ''', (user_id, date))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'sleep_quality': row[0],
            'medication_adherence': row[1],
            'sleep_hours': row[2],
            'last_updated': row[3]
        }
    return None

def get_all_care_ai_treatments(user_id: int) -> List[dict]:
    """Get all CareAITreatments entries for a user. sleep_quality is int (0-10)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT date, sleep_quality, medication_adherence, sleep_hours, last_updated
        FROM care_ai_treatments WHERE user_id = ? ORDER BY date DESC
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            'date': row[0],
            'sleep_quality': row[1],
            'medication_adherence': row[2],
            'sleep_hours': row[3],
            'last_updated': row[4]
        } for row in rows
    ]

# --- Goals Functions ---
def add_goal(goal_id: str, description: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO goals (goal_id, user_id, date, description, completed, last_updated)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (goal_id, user_id, date, description, now))
    conn.commit()
    conn.close()

def get_goals(user_id: int, date: Optional[str] = None) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if date:
        c.execute('SELECT goal_id, description, completed, last_updated FROM goals WHERE user_id = ? AND date = ?', (user_id, date))
    else:
        c.execute('SELECT goal_id, description, completed, last_updated FROM goals WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {"goal_id": row[0], "description": row[1], "completed": bool(row[2]), "last_updated": row[3]}
        for row in rows
    ]

def complete_goal(goal_id: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE goals SET completed = 1, last_updated = ? WHERE goal_id = ? AND user_id = ? AND date = ?', (now, goal_id, user_id, date))
    conn.commit()
    conn.close()

# --- Daily Checklist Functions ---
def add_checklist_item(item_id: str, description: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO daily_checklist_items (item_id, user_id, date, description, completed, last_updated)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (item_id, user_id, date, description, now))
    conn.commit()
    conn.close()

def get_checklist_items(user_id: int, date: Optional[str] = None) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if date:
        c.execute('SELECT item_id, description, completed, last_updated FROM daily_checklist_items WHERE user_id = ? AND date = ?', (user_id, date))
    else:
        c.execute('SELECT item_id, description, completed, last_updated FROM daily_checklist_items WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {"item_id": row[0], "description": row[1], "completed": bool(row[2]), "last_updated": row[3]}
        for row in rows
    ]

def complete_checklist_item(item_id: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE daily_checklist_items SET completed = 1, last_updated = ? WHERE item_id = ? AND user_id = ? AND date = ?', (now, item_id, user_id, date))
    conn.commit()
    conn.close()

# --- Recommendations Functions ---
def add_recommendation(rec_id: str, description: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO recommendations (rec_id, user_id, date, description, acknowledged, last_updated)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (rec_id, user_id, date, description, now))
    conn.commit()
    conn.close()

def get_recommendations(user_id: int, date: Optional[str] = None) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if date:
        c.execute('SELECT rec_id, description, acknowledged, last_updated FROM recommendations WHERE user_id = ? AND date = ?', (user_id, date))
    else:
        c.execute('SELECT rec_id, description, acknowledged, last_updated FROM recommendations WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {"rec_id": row[0], "description": row[1], "acknowledged": bool(row[2]), "last_updated": row[3]}
        for row in rows
    ]

def acknowledge_recommendation(rec_id: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE recommendations SET acknowledged = 1, last_updated = ? WHERE rec_id = ? AND user_id = ? AND date = ?', (now, rec_id, user_id, date))
    conn.commit()
    conn.close()

# --- Appointments Functions ---
def add_appointment(appt_id: str, description: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO appointments (appt_id, user_id, date, description, completed, last_updated)
        VALUES (?, ?, ?, ?, 0, ?)
    ''', (appt_id, user_id, date, description, now))
    conn.commit()
    conn.close()

def get_appointments(user_id: int, date: Optional[str] = None) -> List[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if date:
        c.execute('SELECT appt_id, description, completed, last_updated FROM appointments WHERE user_id = ? AND date = ?', (user_id, date))
    else:
        c.execute('SELECT appt_id, description, completed, last_updated FROM appointments WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {"appt_id": row[0], "description": row[1], "completed": bool(row[2]), "last_updated": row[3]}
        for row in rows
    ]

def complete_appointment(appt_id: str, user_id: int, date: str):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE appointments SET completed = 1, last_updated = ? WHERE appt_id = ? AND user_id = ? AND date = ?', (now, appt_id, user_id, date))
    conn.commit()
    conn.close()

# --- Remove Functions ---
def remove_goal(goal_id: str, user_id: int, date: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM goals WHERE goal_id = ? AND user_id = ? AND date = ?', (goal_id, user_id, date))
    conn.commit()
    conn.close()

def remove_checklist_item(item_id: str, user_id: int, date: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM daily_checklist_items WHERE item_id = ? AND user_id = ? AND date = ?', (item_id, user_id, date))
    conn.commit()
    conn.close()

def remove_recommendation(rec_id: str, user_id: int, date: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM recommendations WHERE rec_id = ? AND user_id = ? AND date = ?', (rec_id, user_id, date))
    conn.commit()
    conn.close()

def remove_appointment(appt_id: str, user_id: int, date: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM appointments WHERE appt_id = ? AND user_id = ? AND date = ?', (appt_id, user_id, date))
    conn.commit()
    conn.close() 