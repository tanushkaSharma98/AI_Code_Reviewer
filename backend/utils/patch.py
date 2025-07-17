import os
import json

def generate_pr_comments(ai_log):
    comments = []
    for entry in ai_log:
        comments.append(f"""File: {entry['file']}\nLine: {entry['line']}\n Issue: {entry['issue']}\n Suggestion: {entry['suggestion']}\n Current:\n    {entry['current_code']}\n Fix:\n    {entry['recommended_code']}\n""")
    return '\n---\n'.join(comments)

def generate_patch_file(ai_log):
    patches = [entry['patch'] for entry in ai_log if 'patch' in entry]
    return '\n'.join(patches)

def calculate_code_quality_score(linter_results, ai_log):
    # Simple scoring: 100 - (# linter issues * 2) - (# AI issues * 3)
    linter_issues = sum(len(v) for v in linter_results.values())
    ai_issues = len(ai_log)
    score = 100 - (linter_issues * 2) - (ai_issues * 3)
    return max(score, 0)

def save_report(directory, pr_comments, score):
    report_path = os.path.join(directory, 'review_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Code Review Report\n\n## Code Quality Score: {score}/100\n\n## PR-Style Comments\n\n{pr_comments}\n")

def save_patch_file(directory, patch_content):
    patch_path = os.path.join(directory, 'patch.diff')
    with open(patch_path, 'w', encoding='utf-8') as f:
        f.write(patch_content) 