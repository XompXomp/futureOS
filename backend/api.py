from flask import Flask, request, jsonify
from flask_cors import CORS
from main import run_agent_workflow

app = Flask(__name__)
CORS(app)

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

def build_default_memory(memory):
    return {
        "id": "memory",
        "episodes": memory.get("episodes", []),
        "procedural": memory.get("procedural", None) if memory.get("procedural", {}) else None,
        "semantic": memory.get("semantic", [])
    }

@app.route("/api/agent", methods=["POST"])
def agent_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received."}), 400

        # --- Input Processing and Validation ---
        user_input = data.get("prompt", "")
        memory = data.get("memory", {})
        updates = data.get("updates", {})

        # Validate and sanitize memory structure
        if not isinstance(memory, dict):
            memory = {} # Default to empty dict if memory is not a dict
        memory.setdefault("episodes", [])
        memory.setdefault("procedural", {})
        memory.setdefault("semantic", [])
        if memory.get("episodes") is None:
            memory["episodes"] = []
        if memory.get("procedural") is None:
            memory["procedural"] = {}
        if memory.get("semantic") is None:
            memory["semantic"] = []

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
            updates=updates
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

        # --- Memory Transformation ---
        mem = result.get("memory", memory)
        transformed_memory = build_default_memory(mem)

        # Prepare response with transformed data
        
        response = {
            "updatedPatientProfile": transformed_profile,
            "updatedMemory": transformed_memory,
            "updatedUpdates": result.get("updates", updates),
        }
        if "final_answer" in result and result["final_answer"]:
            response["extraInfo"] = result["final_answer"]
        elif "response" in result:
            response["extraInfo"] = result["response"]
        print("Response:-\n",jsonify(response))
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5100)