import os
import json

def mock_gemini_review(file, line, issue, code, linter_output, best_practices):
    # This is a mock. Replace with real Gemini Pro API call.
    suggestion = f"[AI] Suggestion for: {issue.get('message', issue)}"
    recommended_code = code  # For demo, just echo code
    patch = f"--- {file}\n+++ {file}\n@@ -{line} +{line} @@\n-{code}\n+{recommended_code}\n"
    return {
        "file": file,
        "line": line,
        "issue": issue,
        "suggestion": suggestion,
        "current_code": code,
        "recommended_code": recommended_code,
        "patch": patch
    }

def run_ai_review_on_rag(directory, lang_map, rag_context):
    ai_results = []
    for rel_path, issues in rag_context.items():
        abs_path = os.path.join(directory, rel_path)
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            lines = []
        for entry in issues:
            issue = entry.get('issue', {})
            context = entry.get('context', [])
            line = issue.get('line', 1) if isinstance(issue, dict) else 1
            code = lines[line-1].strip() if 0 < line <= len(lines) else ''
            linter_output = issue.get('message', str(issue))
            best_practices = context
            ai_result = mock_gemini_review(
                file=rel_path,
                line=line,
                issue=issue,
                code=code,
                linter_output=linter_output,
                best_practices=best_practices
            )
            ai_results.append(ai_result)
    return ai_results

def save_ai_log(directory, ai_results):
    out_path = os.path.join(directory, 'ai_log.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(ai_results, f, indent=2)
