import os
import subprocess
import json

LINTER_COMMANDS = {
    'Python': lambda f: ['flake8', f],
    'JavaScript': lambda f: ['eslint', '--format', 'json', f],
    'TypeScript': lambda f: ['eslint', '--format', 'json', f],
    'TSX': lambda f: ['eslint', '--format', 'json', f],
    'Java': lambda f: ['java', '-jar', 'checkstyle.jar', '-f', 'xml', f],
    'C': lambda f: ['clang-tidy', f, '--'],
    'C++': lambda f: ['clang-tidy', f, '--'],
}

SUPPORTED_LANGUAGES = set(LINTER_COMMANDS.keys())

def run_linter(file_path, language):
    if language not in LINTER_COMMANDS:
        return []
    cmd = LINTER_COMMANDS[language](file_path)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if result.returncode != 0 and 'eslint' in cmd[0]:
            # If ESLint fails, return the error message
            return [{'error': f'ESLint failed: {output}'}]
        return parse_linter_output(language, output)
    except Exception as e:
        return [{'error': str(e)}]

def parse_linter_output(language, output):
    if language == 'Python':
        # flake8: filename:line:col: error
        issues = []
        for line in output.splitlines():
            parts = line.split(':', 3)
            if len(parts) == 4:
                _, line_no, col, msg = parts
                issues.append({'line': int(line_no), 'col': int(col), 'message': msg.strip()})
        return issues
    elif language == 'JavaScript':
        try:
            data = json.loads(output)
            issues = []
            for file_result in data:
                for msg in file_result.get('messages', []):
                    issues.append({'line': msg.get('line'), 'col': msg.get('column'), 'message': msg.get('message')})
            return issues
        except Exception:
            return [{'error': 'Failed to parse eslint output'}]
    elif language == 'Java':
        # checkstyle XML output parsing can be added here
        return [{'info': 'Java linter output parsing not implemented'}]
    elif language in ('C', 'C++'):
        # clang-tidy output parsing can be added here
        return [{'info': 'C/C++ linter output parsing not implemented'}]
    return []

def run_linters_on_dir(directory, lang_map):
    results = {}
    SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', 'venv', '__pycache__', '.venv', '.mypy_cache', '.pytest_cache'}
    for rel_path, lang in lang_map.items():
        # Skip files in ignored directories
        parts = rel_path.split(os.sep)
        if any(part in SKIP_DIRS for part in parts):
            continue
        if lang in SUPPORTED_LANGUAGES:
            abs_path = os.path.join(directory, rel_path)
            issues = run_linter(abs_path, lang)
            results[rel_path] = issues
    return results

def save_linter_results(directory, results):
    out_path = os.path.join(directory, 'linter_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2) 