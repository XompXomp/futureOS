from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from main import run_agent_workflow
import json
import queue
import threading
import time

app = Flask(__name__)
CORS(app)

# Global streaming queue
streaming_queue = queue.Queue()

def send_streaming_chunk(chunk_type: str, data: dict):
    """Send a chunk to the frontend via the streaming queue"""
    chunk = {
        "type": chunk_type,
        "data": data,
        "timestamp": time.time()
    }
    streaming_queue.put(chunk)
    print(f"DEBUG - Sent streaming chunk: {chunk_type} (queue size: {streaming_queue.qsize()})")

def build_default_profile(profile):
    # Fill with defaults if missing
    return {
        "uid": profile.get("uid", ""),
        "name": profile.get("name", ""),
        "age": profile.get("age", 0),
        "bloodType": profile.get("bloodType", ""),
        "allergies": profile.get("allergies", []),
        "treatment": {
            "medicationList": profile.get("treatment", {}).get("medicationList", []),
            "dailyChecklist": profile.get("treatment", {}).get("dailyChecklist", []),
            "appointment": profile.get("treatment", {}).get("appointment", ""),
            "recommendations": profile.get("treatment", {}).get("recommendations", []),
            "sleepHours": profile.get("treatment", {}).get("sleepHours", 0),
            "sleepQuality": profile.get("treatment", {}).get("sleepQuality", "")
        }
    }

@app.route("/api/agent", methods=["POST"])
def agent_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received."}), 400

        # --- Input Processing and Validation ---
        user_input = data.get("prompt", "")
        memory = data.get("memory", [])
        updates = data.get("updates", [])
        conversation = data.get("conversation", {})

        # Validate and sanitize memory structure
        if not isinstance(memory, list):
            memory = [] # Default to empty list if memory is not a list

        # Validate conversation structure
        if not isinstance(conversation, dict):
            conversation = {"cid": "conv-001", "tags": [], "conversation": []}

        # Flatten incoming patient profile
        patient_profile = data.get("patientProfile", {})
        if "treatment" in patient_profile and isinstance(patient_profile["treatment"], dict):
            treatment_data = patient_profile.pop("treatment")
            patient_profile.update(treatment_data)

        if not user_input:
            return jsonify({"error": "Missing 'prompt' in request."}), 400

        # --- Call backend.main.run_agent_workflow ---
        result = run_agent_workflow(
            user_input, memory, patient_profile,
            updates=updates, conversation=conversation
        )

        # --- Patient Profile Transformation ---
        profile = result.get("patientProfile", patient_profile)
        # Dynamically collect all treatment fields
        treatment_data = {}
        for k in list(profile.keys()):
            if k not in ("uid", "name", "age", "bloodType", "allergies", "treatment"):
                treatment_data[k] = profile.pop(k)
        # Compose the nested treatment dict
        transformed_profile = profile.copy()
        transformed_profile["treatment"] = treatment_data
        # Ensure all required fields are present
        transformed_profile = build_default_profile(transformed_profile)

        # --- Memory ---
        memory = result.get("memory", memory)

        # Prepare response with transformed data
        
        response = {
            "updatedPatientProfile": transformed_profile,
            "updatedMemory": memory,
            "Updates": result.get("updates", updates),
        }
        if "final_answer" in result and result["final_answer"]:
            response["extraInfo"] = result["final_answer"]
        elif "response" in result:
            response["extraInfo"] = result["response"]
        print("Response:-\n",jsonify(response))
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# New streaming endpoint
@app.route("/api/agent/stream", methods=["POST", "OPTIONS"])
def agent_stream_endpoint():
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Cache-Control',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
    
    # Handle actual POST request
    """Streaming endpoint that sends chunks in real-time"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received."}), 400

        # --- Input Processing and Validation ---
        user_input = data.get("prompt", "")
        memory = data.get("memory", [])
        updates = data.get("updates", [])
        conversation = data.get("conversation", {})

        # Validate and sanitize memory structure
        if not isinstance(memory, list):
            memory = []

        # Validate conversation structure
        if not isinstance(conversation, dict):
            conversation = {"cid": "conv-001", "tags": [], "conversation": []}

        # Flatten incoming patient profile
        patient_profile = data.get("patientProfile", {})
        if "treatment" in patient_profile and isinstance(patient_profile["treatment"], dict):
            treatment_data = patient_profile.pop("treatment")
            patient_profile.update(treatment_data)

        if not user_input:
            return jsonify({"error": "Missing 'prompt' in request."}), 400

        def generate_stream():
            """Generator function for Server-Sent Events"""
            try:
                # Create a new queue for this specific request
                request_queue = queue.Queue()
                
                # Override the global send_streaming_chunk function for this request
                def send_streaming_chunk_local(chunk_type: str, data: dict):
                    """Send a chunk to the frontend via the request-specific queue"""
                    chunk = {
                        "type": chunk_type,
                        "data": data,
                        "timestamp": time.time()
                    }
                    request_queue.put(chunk)
                    print(f"DEBUG - Sent streaming chunk: {chunk_type} (queue size: {request_queue.qsize()})")
                
                # Start workflow in background thread FIRST
                def run_workflow():
                    try:
                        # Temporarily replace the global send_streaming_chunk
                        import main
                        original_send_chunk = main.send_streaming_chunk
                        main.send_streaming_chunk = send_streaming_chunk_local
                        
                        try:
                            result = run_agent_workflow(
                                user_input, memory, patient_profile,
                                updates=updates, conversation=conversation
                            )
                            
                            # Send final result
                            # Add defensive type checking for result
                            if isinstance(result, dict):
                                patient_profile_result = result.get("patientProfile", patient_profile)
                                memory_result = result.get("memory", memory)
                                updates_result = result.get("updates", updates)
                                final_answer_result = result.get("final_answer", "")
                                function_result = result.get("function", "")
                            else:
                                print(f"WARNING: result is not a dict, it's {type(result)}: {result}")
                                # Fallback to original values if result is not a dict
                                patient_profile_result = patient_profile
                                memory_result = memory
                                updates_result = updates
                                final_answer_result = ""
                                function_result = ""
                            
                            final_response = {
                                "type": "final_result",
                                "data": {
                                    "updatedPatientProfile": patient_profile_result, #build_default_profile(patient_profile_result),
                                    "updatedMemory": memory_result,
                                    "Updates": updates_result,
                                    "extraInfo": final_answer_result,
                                    "function": function_result
                                }
                            }
                            request_queue.put(final_response)
                            
                        finally:
                            # Restore the original function
                            main.send_streaming_chunk = original_send_chunk
                        
                    except Exception as e:
                        error_response = {
                            "type": "error",
                            "data": {"error from here": str(e)}
                        }
                        request_queue.put(error_response)
                
                # Start workflow thread BEFORE starting streaming loop
                workflow_thread = threading.Thread(target=run_workflow)
                workflow_thread.daemon = True
                workflow_thread.start()
                
                # Give workflow a moment to start and send first chunk
                #import time
                #time.sleep(0.5)
                
                # Stream chunks as they arrive
                print(f"DEBUG - Streaming endpoint: Starting to read chunks from queue")
                keepalive_count = 0
                while True:
                    try:
                        # Wait for chunk with timeout - use shorter timeout for real-time streaming
                        print(f"DEBUG - Streaming endpoint: Waiting for chunk (queue size: {request_queue.qsize()})")
                        chunk = request_queue.get(timeout=0.5)  # 0.005 second timeout for real-time
                        print(f"DEBUG - Streaming endpoint: Sending chunk {chunk['type']} to frontend")
                        
                        if chunk["type"] == "final_result":
                            # Send final result and end stream
                            yield f"data: {json.dumps(chunk)}\n\n"
                            print(f"DEBUG - Streaming endpoint: Sent final_result, ending stream")
                            break
                        elif chunk["type"] == "error":
                            # Send error and end stream
                            yield f"data: {json.dumps(chunk)}\n\n"
                            print(f"DEBUG - Streaming endpoint: Sent error, ending stream")
                            break
                        else:
                            # Send streaming chunk immediately
                            yield f"data: {json.dumps(chunk)}\n\n"
                            print(f"DEBUG - Streaming endpoint: Sent {chunk['type']} chunk")
                            
                    except queue.Empty:
                        # Send keepalive less frequently
                        keepalive_count += 1
                        if keepalive_count % 10 == 0:  # Only log every 10th keepalive
                            print(f"DEBUG - Streaming endpoint: Sent keepalive (count: {keepalive_count})")
                        yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                        
            except Exception as e:
                error_response = {
                    "type": "error",
                    "data": {"error": f"Streaming error: {str(e)}"}
                }
                yield f"data: {json.dumps(error_response)}\n\n"

        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Cache-Control',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5100)