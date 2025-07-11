from flask import Flask, request, jsonify, send_file
import os
import uuid
import tempfile
from dotenv import load_dotenv
from flask_cors import CORS
from utils.file_ops import save_uploaded_file, clone_github_repo, extract_zip, create_session_zip
from utils.language_detect import detect_languages_in_dir, save_language_map
from utils.linter import run_linters_on_dir, save_linter_results
from utils.rag import run_rag_on_linter_results, save_rag_context
from utils.ai_review import run_ai_review_on_rag, save_ai_log
from utils.patch import generate_pr_comments, generate_patch_file, calculate_code_quality_score, save_report, save_patch_file
import json
from utils.session import set_session_status, get_session_status

load_dotenv()
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'ai_code_reviewer_sessions')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'.py', '.js', '.java', '.c', '.cpp', '.txt', '.md'}
MAX_ZIP_SIZE_MB = int(os.getenv('MAX_ZIP_SIZE_MB', 5))
MAX_ZIP_SIZE = MAX_ZIP_SIZE_MB * 1024 * 1024

def allowed_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route('/submit', methods=['POST'])
def submit():
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_dir, exist_ok=True)
    set_session_status(session_dir, 'processing')

    # Handle code paste
    if 'code' in request.form:
        code = request.form['code']
        filename = request.form.get('filename', 'pasted_code.py')
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid file type for pasted code.'}), 400
        with open(os.path.join(session_dir, filename), 'w', encoding='utf-8') as f:
            f.write(code)
        # Language detection
        lang_map = detect_languages_in_dir(session_dir)
        save_language_map(session_dir, lang_map)
        # Linter integration
        linter_results = run_linters_on_dir(session_dir, lang_map)
        save_linter_results(session_dir, linter_results)
        # RAG integration
        rag_context = run_rag_on_linter_results(session_dir, lang_map, linter_results)
        save_rag_context(session_dir, rag_context)
        # AI review integration
        ai_results = run_ai_review_on_rag(session_dir, lang_map, rag_context)
        save_ai_log(session_dir, ai_results)
        # Patch/report generation
        with open(os.path.join(session_dir, 'linter_results.json'), 'r', encoding='utf-8') as f:
            linter_results = json.load(f)
        pr_comments = generate_pr_comments(ai_results)
        patch_content = generate_patch_file(ai_results)
        score = calculate_code_quality_score(linter_results, ai_results)
        save_report(session_dir, pr_comments, score)
        save_patch_file(session_dir, patch_content)
        # ZIP packaging
        zip_path = create_session_zip(session_dir)
        set_session_status(session_dir, 'complete', {'download_url': f'/download/{session_id}'})
        return jsonify({'session_id': session_id, 'status': 'submitted', 'type': 'paste'})

    # Handle ZIP upload
    if 'zip' in request.files:
        zip_file = request.files['zip']
        if zip_file.filename == '' or not zip_file.filename.endswith('.zip'):
            return jsonify({'error': 'Invalid ZIP file.'}), 400
        zip_path = os.path.join(session_dir, zip_file.filename)
        zip_file.seek(0, os.SEEK_END)
        size = zip_file.tell()
        zip_file.seek(0)
        if size > MAX_ZIP_SIZE:
            return jsonify({'error': f'ZIP file too large (max {MAX_ZIP_SIZE_MB}MB).'}), 400
        zip_file.save(zip_path)
        extract_zip(zip_path, session_dir)
        # Language detection
        lang_map = detect_languages_in_dir(session_dir)
        save_language_map(session_dir, lang_map)
        # Linter integration
        linter_results = run_linters_on_dir(session_dir, lang_map)
        save_linter_results(session_dir, linter_results)
        # RAG integration
        rag_context = run_rag_on_linter_results(session_dir, lang_map, linter_results)
        save_rag_context(session_dir, rag_context)
        # AI review integration
        ai_results = run_ai_review_on_rag(session_dir, lang_map, rag_context)
        save_ai_log(session_dir, ai_results)
        # Patch/report generation
        with open(os.path.join(session_dir, 'linter_results.json'), 'r', encoding='utf-8') as f:
            linter_results = json.load(f)
        pr_comments = generate_pr_comments(ai_results)
        patch_content = generate_patch_file(ai_results)
        score = calculate_code_quality_score(linter_results, ai_results)
        save_report(session_dir, pr_comments, score)
        save_patch_file(session_dir, patch_content)
        # ZIP packaging
        zip_path = create_session_zip(session_dir)
        set_session_status(session_dir, 'complete', {'download_url': f'/download/{session_id}'})
        return jsonify({'session_id': session_id, 'status': 'submitted', 'type': 'zip'})

    # Handle GitHub repo URL
    if 'github_url' in request.form:
        github_url = request.form['github_url']
        if not github_url.startswith('https://github.com/'):
            return jsonify({'error': 'Only public GitHub repos allowed.'}), 400
        try:
            clone_github_repo(github_url, session_dir)
        except Exception as e:
            return jsonify({'error': f'GitHub clone failed: {str(e)}'}), 400
        # Language detection
        lang_map = detect_languages_in_dir(session_dir)
        save_language_map(session_dir, lang_map)
        # Linter integration
        linter_results = run_linters_on_dir(session_dir, lang_map)
        save_linter_results(session_dir, linter_results)
        # RAG integration
        rag_context = run_rag_on_linter_results(session_dir, lang_map, linter_results)
        save_rag_context(session_dir, rag_context)
        # AI review integration
        ai_results = run_ai_review_on_rag(session_dir, lang_map, rag_context)
        save_ai_log(session_dir, ai_results)
        # Patch/report generation
        with open(os.path.join(session_dir, 'linter_results.json'), 'r', encoding='utf-8') as f:
            linter_results = json.load(f)
        pr_comments = generate_pr_comments(ai_results)
        patch_content = generate_patch_file(ai_results)
        score = calculate_code_quality_score(linter_results, ai_results)
        save_report(session_dir, pr_comments, score)
        save_patch_file(session_dir, patch_content)
        # ZIP packaging
        zip_path = create_session_zip(session_dir)
        set_session_status(session_dir, 'complete', {'download_url': f'/download/{session_id}'})
        return jsonify({'session_id': session_id, 'status': 'submitted', 'type': 'github'})

    return jsonify({'error': 'No valid input provided.'}), 400

@app.route('/status/<session_id>', methods=['GET'])
def status(session_id):
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    status = get_session_status(session_dir)
    return jsonify({'session_id': session_id, **status})

@app.route('/config', methods=['GET'])
def config():
    return jsonify({
        'max_zip_size_mb': MAX_ZIP_SIZE_MB,
        'max_zip_size_bytes': MAX_ZIP_SIZE
    })

@app.route('/download/<session_id>', methods=['GET'])
def download(session_id):
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    zip_path = os.path.join(session_dir, 'session_package.zip')
    if not os.path.exists(zip_path):
        return jsonify({'error': 'ZIP package not found.'}), 404
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 