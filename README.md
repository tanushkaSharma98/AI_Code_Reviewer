<<<<<<< HEAD
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
=======
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
>>>>>>> frontend
