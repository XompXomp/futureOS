from localinfo import (
    add_goal, get_goals, complete_goal,
    add_checklist_item, get_checklist_items, complete_checklist_item,
    add_recommendation, get_recommendations, acknowledge_recommendation,
    add_appointment, get_appointments, complete_appointment
)
from datetime import datetime

user_id = 42
today = datetime.utcnow().date().isoformat()

# --- Goals ---
print("Adding goal...")
add_goal("step_goal_10000", "Reach 10000 steps", user_id, today)
print("Goals for today:", get_goals(user_id, today))
print("Completing goal...")
complete_goal("step_goal_10000", user_id, today)
print("Goals after completion:", get_goals(user_id, today))

# --- Daily Checklist ---
print("\nAdding checklist item...")
add_checklist_item("meds_morning", "Take morning medication", user_id, today)
print("Checklist items for today:", get_checklist_items(user_id, today))
print("Completing checklist item...")
complete_checklist_item("meds_morning", user_id, today)
print("Checklist after completion:", get_checklist_items(user_id, today))

# --- Recommendations ---
print("\nAdding recommendation...")
add_recommendation("rec1", "Try meditation", user_id, today)
print("Recommendations for today:", get_recommendations(user_id, today))
print("Acknowledging recommendation...")
acknowledge_recommendation("rec1", user_id, today)
print("Recommendations after acknowledgment:", get_recommendations(user_id, today))

# --- Appointments ---
print("\nAdding appointment...")
add_appointment("appt1", "Doctor visit at 2pm", user_id, today)
print("Appointments for today:", get_appointments(user_id, today))
print("Completing appointment...")
complete_appointment("appt1", user_id, today)
print("Appointments after completion:", get_appointments(user_id, today)) 