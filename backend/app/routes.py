import os
import json
import pandas as pd
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename



api_blueprint = Blueprint("api", __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../file_log.json'))
ALLOWED_EXTENSIONS = {'csv', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def log_file_metadata(filename, filepath):
    metadata = {
        "filename": filename,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "size_kb": round(os.path.getsize(filepath) / 1024, 2)
    }

    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'r') as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(metadata)

        with open(LOG_PATH, 'w') as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print(f"Logging failed: {e}")



@api_blueprint.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "DriveAware backend is running!"})

@api_blueprint.route("/upload", methods=["POST"])
def upload_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({"message": f"File '{filename}' uploaded successfully"}), 200

    return jsonify({"error": "Invalid file type"}), 400

@api_blueprint.route("/upload/preview", methods=["POST"])
def preview_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            df = pd.read_csv(file, on_bad_lines='skip', engine='python')

            preview = df.head(5).to_dict(orient='records')
            summary = {
                "filename": secure_filename(file.filename),
                "rows": df.shape[0],
                "columns": df.shape[1],
                "column_names": list(df.columns),
                "preview": preview
            }

            return jsonify(summary), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400

@api_blueprint.route("/preview/<filename>", methods=["GET"])
def preview_uploaded_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python')
        preview = df.head(5).to_dict(orient='records')

        summary = {
            "filename": filename,
            "rows": df.shape[0],
            "columns": df.shape[1],
            "column_names": list(df.columns),
            "preview": preview
        }

        return jsonify(summary), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/uploads", methods=["GET"])
def list_uploaded_files():
    try:
        if not os.path.exists(LOG_PATH):
            return jsonify([])

        with open(LOG_PATH, 'r') as f:
            logs = json.load(f)

        return jsonify(logs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
