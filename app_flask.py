import os
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from app.agents.orchestrator import AIOrchestrator
from app.config import MODELS

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize orchestrator
orchestrator = AIOrchestrator()

@app.route("/")
def index():
    return render_template("index.html", models=MODELS)

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    mode = request.json.get("mode", "auto")
    model_id = request.json.get("model_id", "gpt-4o")
    
    # Get tokens from session
    api_keys = session.get("api_keys", {})
    
    if model_id:
        orchestrator.current_model_id = model_id
        
    response = orchestrator.chat(user_input, mode=mode, api_keys=api_keys)
    return jsonify(response)

@app.route("/set_token", methods=["POST"])
def set_token():
    provider = request.json.get("provider")
    token = request.json.get("token")
    
    if "api_keys" not in session:
        session["api_keys"] = {}
        
    session["api_keys"][provider] = token
    session.modified = True
    return jsonify({"status": "success", "provider": provider})

@app.route("/clear", methods=["POST"])
def clear():
    orchestrator.memory.clear()
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True, port=500)
