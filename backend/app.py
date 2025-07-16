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

# ALLOWED_EXTENSIONS = {'.py', '.js', '.java', '.c', '.cpp', '.txt', '.md'}
MAX_ZIP_SIZE_MB = int(os.getenv('MAX_ZIP_SIZE_MB', 5))
MAX_ZIP_SIZE = MAX_ZIP_SIZE_MB * 1024 * 1024

print("MAX_ZIP_SIZE_MB =", MAX_ZIP_SIZE_MB)

def allowed_file(filename):
    return True  # Accept any file extension

@app.route('/submit', methods=['POST'])
def submit():
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_dir, exist_ok=True)
    set_session_status(session_dir, 'processing')

    MAX_SAFE_ZIP_SIZE = 900 * 1024 * 1024  # 900MB

    try:
        # Handle code paste
        if 'code' in request.form:
            code = request.form['code']
            filename = request.form.get('filename', 'pasted_code.py')
            if not allowed_file(filename):
                set_session_status(session_dir, 'error', {'error': 'Invalid file type for pasted code.'})
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
                set_session_status(session_dir, 'error', {'error': 'Invalid ZIP file.'})
                return jsonify({'error': 'Invalid ZIP file.'}), 400
            zip_file.seek(0, os.SEEK_END)
            size = zip_file.tell()
            zip_file.seek(0)
            if size > MAX_SAFE_ZIP_SIZE:
                set_session_status(session_dir, 'error', {'error': f'ZIP file too large (max 900MB).'})
                return jsonify({'error': 'ZIP file too large (max 900MB).'}), 400
            if size > MAX_ZIP_SIZE:
                set_session_status(session_dir, 'error', {'error': f'ZIP file too large (max {MAX_ZIP_SIZE_MB}MB).'})
                return jsonify({'error': f'ZIP file too large (max {MAX_ZIP_SIZE_MB}MB).'}), 400
            zip_path = os.path.join(session_dir, zip_file.filename)
            zip_file.save(zip_path)
            extracted, skipped = extract_zip(zip_path, session_dir)
            if not extracted:
                set_session_status(session_dir, 'error', {'error': 'No files could be extracted from the ZIP. The archive may be empty, corrupted, or all files were skipped due to errors.'})
                return jsonify({'error': 'No files could be extracted from the ZIP. The archive may be empty, corrupted, or all files were skipped due to errors.'}), 400
            # Language detection
            lang_map = detect_languages_in_dir(session_dir)
            import logging
            logging.warning(f"Detected files and languages: {lang_map}")
            from utils.linter import SUPPORTED_LANGUAGES
            SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', 'venv', '__pycache__', '.venv', '.mypy_cache', '.pytest_cache'}
            def is_supported_code_file(rel_path, lang):
                parts = rel_path.split(os.sep)
                if any(part in SKIP_DIRS for part in parts):
                    return False
                return lang in SUPPORTED_LANGUAGES
            code_files = [f for f, lang in lang_map.items() if is_supported_code_file(f, lang)]
            if not code_files:
                set_session_status(session_dir, 'error', {'error': 'No supported code files found in the ZIP. The archive may only contain dependencies or unsupported files.'})
                return jsonify({'error': 'No supported code files found in the ZIP. The archive may only contain dependencies or unsupported files.'}), 400
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
                set_session_status(session_dir, 'error', {'error': 'Only public GitHub repos allowed.'})
                return jsonify({'error': 'Only public GitHub repos allowed.'}), 400
            try:
                clone_github_repo(github_url, session_dir)
            except Exception as e:
                set_session_status(session_dir, 'error', {'error': f'GitHub clone failed: {str(e)}'})
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

        set_session_status(session_dir, 'error', {'error': 'No valid input provided.'})
        return jsonify({'error': 'No valid input provided.'}), 400

    except Exception as e:
        import traceback
        set_session_status(session_dir, 'error', {'error': str(e), 'traceback': traceback.format_exc()})
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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

@app.route('/review/<session_id>', methods=['GET'])
def review(session_id):
    session_dir = os.path.join(UPLOAD_FOLDER, session_id)
    ai_log_path = os.path.join(session_dir, 'ai_log.json')
    linter_path = os.path.join(session_dir, 'linter_results.json')
    patch_path = os.path.join(session_dir, 'patch.diff')
    report_path = os.path.join(session_dir, 'review_report.md')
    download_url = f'/download/{session_id}'
    # Load files if they exist
    ai_log = []
    linter_results = {}
    code_quality_score = None
    patch = ''
    pr_comments = ''
    if os.path.exists(ai_log_path):
        with open(ai_log_path, 'r', encoding='utf-8') as f:
            ai_log = json.load(f)
    if os.path.exists(linter_path):
        with open(linter_path, 'r', encoding='utf-8') as f:
            linter_results = json.load(f)
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith('## Code Quality Score:'):
                    try:
                        code_quality_score = int(line.split(':')[1].split('/')[0].strip())
                    except Exception:
                        code_quality_score = None
                # Collect PR-style comments (after '## PR-Style Comments')
            pr_section = False
            pr_lines = []
            for line in lines:
                if line.strip().startswith('## PR-Style Comments'):
                    pr_section = True
                    continue
                if pr_section:
                    pr_lines.append(line)
            pr_comments = ''.join(pr_lines).strip()
    if os.path.exists(patch_path):
        with open(patch_path, 'r', encoding='utf-8') as f:
            patch = f.read()
    return jsonify({
        'ai_log': ai_log,
        'linter_results': linter_results,
        'code_quality_score': code_quality_score,
        'patch': patch,
        'download_url': download_url,
        'pr_comments': pr_comments
    })

if __name__ == '__main__':
    app.run(debug=True) 