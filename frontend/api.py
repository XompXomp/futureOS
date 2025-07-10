from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import AIAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the AI agent
try:
    agent = AIAgent()
    print("AI Agent initialized successfully")
except Exception as e:
    print(f"Error initializing AI Agent: {e}")
    agent = None

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests from the frontend."""
    try:
        if agent is None:
            return jsonify({'error': 'AI Agent is not initialized'}), 500
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get response from AI agent
        response = agent.run(user_message)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'agent_initialized': agent is not None
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 