#!/usr/bin/env python3
"""
project_generator.py

Generates either a 'website' or full 'software' (React frontend + Express backend)
scaffold. Guarantees a minimum number of total source lines by creating meaningful
files and, if necessary, a controlled filler file.

Usage:
    python project_generator.py website MyHotel --min-lines 5000
    python project_generator.py software MyApp --min-lines 7000
"""
import os
from pathlib import Path
import argparse
import textwrap

# ---------- Helpers ----------
def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

def count_lines_in_dir(root: Path):
    total = 0
    for p in root.rglob('*'):
        if p.is_file() and p.suffix not in ('.png', '.jpg', '.jpeg', '.bin', '.exe'):
            try:
                with p.open('r', encoding='utf-8', errors='ignore') as f:
                    total += sum(1 for _ in f)
            except Exception:
                pass
    return total

def make_filler(path: Path, lines_needed: int):
    # Create a controlled filler JS/MD file with readable comment blocks.
    block = "// ----- auto-generated filler block -----\n"
    lines = []
    per_block = 20
    blocks = (lines_needed // per_block) + 1
    for i in range(blocks):
        lines.append(block)
        lines.append(f"// filler block #{i+1}\n")
        for j in range(per_block - 2):
            lines.append(f"// filler line {i+1}-{j+1}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(lines), encoding='utf-8')

# ---------- Boilerplate content ----------
def website_files(project_root: Path, project_name: str):
    # Basic website assets: index, about, contact, CSS, JS
    write_file(project_root / 'templates' / 'index.html', textwrap.dedent(f"""\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width,initial-scale=1" />
          <title>{project_name} — Home</title>
          <link rel="stylesheet" href="/assets/css/style.css" />
        </head>
        <body>
          <header>
            <h1>{project_name}</h1>
            <nav><a href="/about.html">About</a> • <a href="/contact.html">Contact</a></nav>
          </header>
          <main id="app">
            <section>
              <h2>Welcome</h2>
              <p>Production-grade landing content goes here.</p>
            </section>
          </main>
          <script src="/assets/js/main.js"></script>
        </body>
        </html>
    """))

    write_file(project_root / 'templates' / 'about.html', "<!doctype html>\n<html><body><h1>About</h1></body></html>")
    write_file(project_root / 'templates' / 'contact.html', "<!doctype html>\n<html><body><h1>Contact</h1></body></html>")
    write_file(project_root / 'assets' / 'css' / 'style.css', textwrap.dedent("""\
        :root{--bg:#0b1220;--fg:#e6eef8}
        body{background:var(--bg);color:var(--fg);font-family:Inter,system-ui,Segoe UI,Roboto,Arial;}
        header{padding:28px;background:linear-gradient(90deg,#667eea,#764ba2);color:white}
    """))
    write_file(project_root / 'assets' / 'js' / 'main.js', "// main JS entry - add interactivity here\nconsole.log('Site loaded');")

    # Add README and simple build notes
    write_file(project_root / 'README.md', f"# {project_name}\n\nGenerated website scaffold.\n")

def software_files(project_root: Path, project_name: str):
    # Frontend (React) minimal but nontrivial scaffold
    frontend = project_root / 'client'
    write_file(frontend / 'package.json', textwrap.dedent(f"""\
        {{
          "name": "{project_name}-client",
          "version": "1.0.0",
          "private": true,
          "scripts": {{
            "start": "vite",
            "build": "vite build",
            "dev": "vite"
          }},
          "dependencies": {{
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.14.0"
          }},
          "devDependencies": {{
            "vite": "^5.0.0",
            "@vitejs/plugin-react": "^4.0.0"
          }}
        }}
    """))

    write_file(frontend / 'index.html', textwrap.dedent("""\
        <!doctype html>
        <html>
          <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>App</title></head>
          <body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>
        </html>
    """))

    write_file(frontend / 'src' / 'main.jsx', textwrap.dedent("""\
        import React from 'react';
        import { createRoot } from 'react-dom/client';
        import App from './App';
        const root = createRoot(document.getElementById('root'));
        root.render(<App />);
    """))

    # Create a sizeable App with many components to be non-trivial
    app_lines = []
    app_lines.append("import React from 'react';\n")
    app_lines.append("import './styles.css';\n\n")
    app_lines.append("const LargeComponent = () => {\n")
    app_lines.append("  return (\n")
    app_lines.append("    <div className='large'>\n")
    for i in range(1, 101):
        app_lines.append(f"      <section key={i}>\n        <h3>Section {i}</h3>\n        <p>This is placeholder content for section {i}.</p>\n      </section>\n")
    app_lines.append("    </div>\n  );\n}\n\n")
    app_lines.append("export default function App(){\n  return (\n    <main>\n      <header><h1>Welcome</h1></header>\n      <LargeComponent />\n    </main>\n  )\n}\n")
    write_file(frontend / 'src' / 'App.jsx', ''.join(app_lines))

    write_file(frontend / 'src' / 'styles.css', "body{font-family:Inter,system-ui;line-height:1.6}\n.large{padding:24px}")

    # Backend (Express)
    backend = project_root / 'server'
    write_file(backend / 'package.json', textwrap.dedent(f"""\
        {{
          "name": "{project_name}-server",
          "version": "1.0.0",
          "main": "index.js",
          "scripts": {{
            "start": "node index.js"
          }},
          "dependencies": {{
            "express": "^5.1.0",
            "cors": "^2.8.5"
          }}
        }}
    """))

    write_file(backend / 'index.js', textwrap.dedent("""\
        const express = require('express');
        const cors = require('cors');
        const app = express();
        app.use(cors());
        app.use(express.json());

        // Example API endpoints
        app.get('/health', (req, res) => res.json({status: 'ok'}));

        app.get('/api/items', (req, res) => {
          const items = Array.from({length: 50}, (_, i) => ({ id: i+1, name: `Item ${i+1}` }));
          res.json(items);
        });

        const PORT = process.env.PORT || 4000;
        app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
    """))

    write_file(project_root / 'README.md', f"# {project_name}\n\nFullstack scaffold (client + server).")

    # Root package to start both in dev (optional)
    write_file(project_root / 'package.json', textwrap.dedent(f"""\
        {{
          "name": "{project_name}-fullstack",
          "version": "1.0.0",
          "private": true,
          "scripts": {{
            "start:client": "cd client && npm run dev",
            "start:server": "cd server && npm start"
          }}
        }}
    """))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('type', choices=['website', 'software'], help='Type to generate')
    parser.add_argument('name', help='Project folder name')
    parser.add_argument('--min-lines', type=int, default=1000, help='Minimum total source lines to produce')
    args = parser.parse_args()

    project_root = Path(args.name).resolve()
    print(f"Generating {args.type} in {project_root} (min lines: {args.min_lines})")

    if args.type == 'website':
        website_files(project_root, args.name)
    else:
        software_files(project_root, args.name)

    # After generating initial files, ensure line count
    total_lines = count_lines_in_dir(project_root)
    print(f"Current total source lines: {total_lines}")

    if total_lines < args.min_lines:
        needed = args.min_lines - total_lines
        filler_path = project_root / 'generated_filler' / 'FILLER.js'
        print(f"Adding filler of ~{needed} lines at {filler_path}")
        make_filler(filler_path, needed)
        total_lines = count_lines_in_dir(project_root)
        print(f"New total lines: {total_lines}")

    print("Generation complete. Run `cd {}` and follow README.".format(project_root.name))

if __name__ == '__main__':
    main()
