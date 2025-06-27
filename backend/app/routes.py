import os
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
import pandas as pd

api_blueprint = Blueprint("api", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
ALLOWED_EXTENSIONS = {'csv', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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