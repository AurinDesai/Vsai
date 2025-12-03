<!-- Copilot instructions for CodeForge Studio (Vsai) -->
# Quick AI-Agent Guide — CodeForge Studio (Vsai)

This file gives concise, actionable guidance for AI coding agents working in this repository.

**Purpose**: Help an automated assistant become productive quickly by documenting architecture, run/debug commands, repository-specific conventions, and examples taken from this codebase.

**Big Picture**:
- **Frontend served by**: `codeforge_studio_server.js` (Node) — serves `vscode_clone.html` on port `5050`.
- **AI engine**: local Llama server launched via `llama_cpp.server` on port `8000` (see `launcher.py`).
- **Orchestration**: Python scripts (`start.py`, `start_codeforge.py`, `launcher.py`, `run_codeforge.py`) coordinate startup: launch Llama, then Node, then open browser.
- **Model storage**: `models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf` — large file; agent should not attempt to modify or re-distribute it.

**Key run / dev commands (discovered in repo)**
- Start everything (recommended):
  - `python start_codeforge.py` or double-click `start.py` / `start_codeforge.bat` (Windows).
- Start Node backend manually: `node codeforge_studio_server.js` (runs on port `5050`).
- Start Llama server the same way `launcher.py` does:
  - `python -m llama_cpp.server --model ./models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf --port 8000 ...`
- Ports: **Llama** `8000`, **Backend** `5050`. Frontend URL: `http://localhost:5050/vscode_clone.html`.

**Project-specific conventions & patterns**
- `launcher.py` is the authoritative Windows launcher: it
  - creates a lock file: `codeforge.lock` to enforce a single instance,
  - writes logs to `codeforge_launcher.log`,
  - supports an emergency kill file `codeforge.kill` which forces a shutdown,
  - uses `psutil` to detect/kill processes on ports.
- Health checks: services are waited-for using `wait_for_port(port, timeout=...)` before proceeding.
- Avoid changing `package.json` blindly: the current `package.json` content appears to be a generic/placeholder Node module and may not reflect this project's build steps.

**Files to inspect when making changes**
- Startup and orchestration: `launcher.py`, `start_codeforge.py`, `start.py`, `run_codeforge.py`.
- Backend: `codeforge_studio_server.js` (Node server). Use it to understand API routes and static serving.
- Frontend: `vscode_clone.html` (served by Node).
- Model and AI: `models/` folder — large model files live here; do not modify without caution.
- Requirements: `requirements.txt` lists Python dependencies (FastAPI, uvicorn, sentence-transformers, etc.).

**Safety, debug, and emergency patterns (important)**
- To force-stop everything: create a file named `codeforge.kill` in the repo root — `launcher.py` watches for this and will force shutdown.
- To debug startup failures, inspect `codeforge_launcher.log` and the console output from starting Node (`node codeforge_studio_server.js`).
- Use `psutil`-based cleanup helpers in `launcher.py` when writing fixes that involve process management.

**Editing guidance & examples**
- When modifying `launcher.py`:
  - Preserve the `codeforge.lock` single-instance semantics and the emergency kill behavior.
  - Respect `wait_for_port` timeouts — increasing timeouts is preferable to removing them.
  - If you add new subprocesses, follow existing patterns (hide window on Windows, capture/redirect stdout/stderr appropriately).
- When changing ports or URLs, update `QUICKSTART.md` and `START_HERE.md` examples used by users.

**Tests, CI, and build notes**
- There are no project-specific unit tests discovered; `package.json` contains generic npm test scripts that likely do not apply — verify before running `npm test`.
- Development installs: use Python v3.10+ and Node v18+/v20+ per `QUICKSTART.md` recommendations.

**Do NOT assume**
- That `package.json` represents project build steps — inspect `codeforge_studio_server.js` and Python startup scripts instead.
- That models are small — `models/*.gguf` are large; avoid loading or transferring them unnecessarily.

If anything in this guidance is unclear or you want additional examples (e.g., sample `python -m llama_cpp.server` command-line or a minimal Node dev command), tell me which area to expand and I will update this file.
