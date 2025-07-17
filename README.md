# AI Code Reviewer + Fix Suggestor

## Overview
An AI-powered code review and fix suggestion tool. Supports code submission (paste, ZIP, GitHub), auto language detection, multi-language linting, AI review (Gemini Pro), PR-style comments, patch generation, code quality scoring, and ZIP packaging.

## Features
- Code submission (paste/upload/link)
- Auto language detection
- Multi-language linter support
- LangChain agent + tools
- ChromaDB-based RAG
- Gemini Pro review + suggestions
- PR-style comments
- Patch file generation
- Code quality score
- ZIP download
- MCP-style session tracking
- Input validation + security
- Logging & AI response saving

## Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Frontend
A React or HTML/JS frontend is recommended (not included yet).