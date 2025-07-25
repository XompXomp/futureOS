import time
import requests
from datetime import datetime
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

FRONTEND_API_ENDPOINT = "http://172.22.225.49:8002/api/llama-bridge"  # Example frontend API endpoint
MEDICAL_LLM_ENDPOINT = "http://172.22.225.49:8000/endpoint"  # Example medical LLM endpoint

# --- Data Builders (placeholders for real data gathering) ---
def build_daily_updates_payload():
    # Placeholder: fetch or construct the real updates payload from your data source
    return {}

def build_daily_links_payload():
    # Placeholder: fetch or construct the real memory+links payload from your data source
    return {}

def build_weekly_payload():
    # Placeholder: fetch or construct the real weekly payload from your data source
    return {}

# --- Communication Logic ---
def request_from_frontend(request_type):
    # This function should request the required data from the frontend
    try:
        response = requests.post(FRONTEND_API_ENDPOINT, json={"request_type": request_type}, timeout=10)
        response.raise_for_status()
        logging.info(f"Requested {request_type} from frontend. Response: {response.json()}")
        return response.json()
    except Exception as e:
        logging.error(f"Failed to request {request_type} from frontend: {e}")
        return None

def send_to_medical_llm(payload, payload_type):
    # Always send a 'payload_type' key along with the payload to the medical LLM
    payload_with_type = dict(payload)
    payload_with_type['payload_type'] = payload_type
    try:
        response = requests.post(MEDICAL_LLM_ENDPOINT, json=payload_with_type, timeout=10)
        response.raise_for_status()
        logging.info(f"Sent {payload_type} payload to medical LLM. Response: {response.json()}")
        return response.json()
    except Exception as e:
        logging.error(f"Failed to send {payload_type} payload to medical LLM: {e}")
        return None

def send_to_frontend_api(payload, update_type):
    # Add a 'tag' to indicate the type of info being updated
    tagged_payload = {"tag": update_type, "data": payload}
    try:
        response = requests.post(FRONTEND_API_ENDPOINT, json=tagged_payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Sent {update_type} update to frontend. Response: {response.json()}")
        return response.json()
    except Exception as e:
        logging.error(f"Failed to send {update_type} update to frontend: {e}")
        return None

# --- Orchestration Logic ---
def handle_daily_cycle():
    # Step 1: Request updates from frontend
    updates_payload = request_from_frontend("updates")
    if updates_payload:
        # Step 2: Send updates to medical LLM (with payload_type)
        medical_response = send_to_medical_llm(updates_payload, "daily-updates")
        if medical_response:
            # Step 3: Send medical LLM's response back to frontend with tag
            send_to_frontend_api(medical_response, "recommendations_and_treatment_insights")
    # Step 4: Wait 10 seconds
    time.sleep(10)
    # Step 5: Request memory+links from frontend
    links_payload = request_from_frontend("memory_links")
    if links_payload:
        # Step 6: Send memory+links to medical LLM (with payload_type)
        medical_links_response = send_to_medical_llm(links_payload, "daily-links")
        if medical_links_response:
            # Step 7: Send medical LLM's response back to frontend with tag
            send_to_frontend_api(medical_links_response, "links_and_function_call")

def handle_weekly_cycle():
    # Step 1: Request weekly data (conversations and general insights) from frontend
    weekly_payload = request_from_frontend("convo_general_insights")
    if weekly_payload:
        # Step 2: Send to medical LLM with payload_type 'weekly'
        medical_response = send_to_medical_llm(weekly_payload, "weekly")
        if medical_response:
            # Step 3: Send updated general insights from medical LLM back to frontend
            send_to_frontend_api(medical_response, "updated_general_insights")

# --- Main Loop ---
def main_loop():
    now = datetime.now()
    DAILY_HOUR = now.hour      # Set to current hour for testing
    WEEKLY_HOUR = now.hour     # Set to current hour for testing
    WEEKLY_DAY = now.isoweekday()  # Set to today for testing
    last_daily_date = None
    last_weekly_date = None
    while True:
        now = datetime.now()
        # Daily at DAILY_HOUR
        if now.hour == DAILY_HOUR and (last_daily_date is None or now.date() != last_daily_date):
            handle_daily_cycle()
            last_daily_date = now.date()
        # Weekly at WEEKLY_HOUR on WEEKLY_DAY (Monday)
        if now.isoweekday() == WEEKLY_DAY and now.hour == WEEKLY_HOUR and (last_weekly_date is None or now.date() != last_weekly_date):
            handle_weekly_cycle()
            last_weekly_date = now.date()
        time.sleep(3600)  # Check every hour

if __name__ == "__main__":
    main_loop() 