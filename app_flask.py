import os
from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from flask_session import Session
from app.agents.orchestrator import AIOrchestrator
from app.config import MODELS, AppConfig
from app.utils.file_parser import parse_file
from app.utils.logger import logger
from app.utils.env_manager import env_manager

app = Flask(__name__)
app.config["SECRET_KEY"] = AppConfig.SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
Session(app)

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize orchestrator
orchestrator = AIOrchestrator()

@app.route("/")
def index():
    return render_template("index.html", models=MODELS)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message")
        mode = data.get("mode", "auto")
        model_id = data.get("model_id")
        attachment = data.get("attachment")
        web_search = data.get("web_search", False)
        
        api_keys = session.get("api_keys", {})
        if model_id: orchestrator.current_model_id = model_id
            
        response = orchestrator.chat(message, mode=mode, api_keys=api_keys, attachment=attachment, web_search=web_search)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500

@app.route("/chat_stream")
def chat_stream():
    message = request.args.get("message")
    mode = request.args.get("mode", "auto")
    model_id = request.args.get("model_id")
    attachment = request.args.get("attachment")
    web_search = request.args.get("web_search") == "true"
    
    api_keys = session.get("api_keys", {})
    if model_id: orchestrator.current_model_id = model_id

    def generate():
        try:
            for chunk in orchestrator.chat_stream(message, mode=mode, api_keys=api_keys, attachment=attachment, web_search=web_search):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "version": "1.1.0"})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

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

@app.route("/setup_status")
def setup_status():
    return jsonify({
        "is_complete": env_manager.is_setup_complete(),
        "configured_keys": [k for k, v in env_manager.get_keys().items() if v]
    })

@app.route("/update_persistent_keys", methods=["POST"])
def update_persistent_keys():
    try:
        data = request.json
        keys = data.get("keys", {})
        for key, value in keys.items():
            if value:
                env_manager.update_key(key, value)
        return jsonify({"status": "success", "message": "API keys saved to .env"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stats")
def stats():
    from app.utils.cost_tracker import cost_tracker
    return jsonify(cost_tracker.get_detailed_stats())

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        
        content = parse_file(file_path)
        
        # Clean up file after parsing (optional, but good for privacy)
        # os.remove(file_path)
        
        if content.startswith("Error"):
            return jsonify({"error": content}), 500
            
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "content": content
        })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
