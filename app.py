import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import PyPDF2

from services.ai_analyzer import AIAnalyzer

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)
# This line sets the configuration for where to save uploaded files.
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

try:
    analyzer = AIAnalyzer()
except ValueError as e:
    print(f"CRITICAL ERROR ON STARTUP: {e}")
    analyzer = None

def extract_text_from_pdf(filepath: str) -> str:
    text = ""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading PDF file {filepath}: {e}")
        return None
    return text

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

@app.route('/analyze', methods=['POST'])
def analyze():
    if analyzer is None:
        return jsonify({"error": "AI Analyzer is not initialized. Check server logs for API key issues."}), 500

    if 'resume' not in request.files:
        return jsonify({"error": "No resume file part"}), 400
    if 'job_description' not in request.form:
        return jsonify({"error": "No job description part"}), 400

    resume_file = request.files['resume']
    job_description = request.form['job_description']

    if resume_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if resume_file:
        # This line was causing the error, which is now fixed.
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        resume_file.save(filepath)

        resume_text = extract_text_from_pdf(filepath)
        if resume_text is None:
            return jsonify({"error": "Could not extract text from the PDF. It might be corrupted or image-based."}), 500

        try:
            analysis_result = analyzer.analyze_resume_match(resume_text, job_description)
            return jsonify(analysis_result)
        except Exception as e:
            print(f"An error occurred during analysis: {e}")
            return jsonify({"error": "An internal error occurred during analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)