from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/agent", methods=["POST"])
def agent_endpoint():
    data = request.get_json()
    print("Received data:", data)  # Logging incoming request

    # Modify each field for testing
    updated_profile = dict(data.get("patientProfile", {}))
    updated_profile["name"] = "Changed Name"
    updated_conversation = dict(data.get("conversation", {}))
    updated_conversation["tags"] = ["test"]
    updated_memory = dict(data.get("memory", {}))
    updated_memory["episodes"] = [{"test": "episode"}]

    return jsonify({
        "updatedPatientProfile": updated_profile,
        "updatedConversation": updated_conversation,
        "updatedMemory": updated_memory,
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5100) 