#!/usr/bin/env python3
"""
CodeForge Studio - Complete VS Code Clone with AI
Single startup file that launches everything at once
"""

import os
import sys
import subprocess
import time
import platform
import webbrowser
from pathlib import Path

# ============= CONFIG =============
LLAMA_PORT = 8000
NODE_PORT = 5050
MODEL_PATH = './models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf'

print(r"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║          🚀 CodeForge Studio - VS Code Clone with AI 🚀          ║
║                                                                   ║
║     Professional IDE with Collaborative Coding Features          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")

# ============= STARTUP =============
def main():
    print('\n[1/3] Checking environment...')
    
    # Python version
    print(f'  ✅ Python {sys.version.split()[0]}')
    
    # Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        print(f'  ✅ Node.js {result.stdout.strip()}')
    except:
        print('  ❌ Node.js not found. Install from nodejs.org')
        input('\nPress Enter to exit...')
        sys.exit(1)
    
    # Model
    if os.path.exists(MODEL_PATH):
        size_gb = os.path.getsize(MODEL_PATH) / (1024**3)
        print(f'  ✅ Model: {size_gb:.2f}GB')
    else:
        print(f'  ⚠️  Model not found at {MODEL_PATH}')
    
    print('\n[2/3] Starting Llama Server...')
    try:
        llama_cmd = [
            sys.executable, '-m', 'llama_cpp.server',
            '--model', MODEL_PATH,
            '--port', str(LLAMA_PORT),
            '--n_gpu_layers', '99',
            '-ngl', '99',
            '--n_ctx', '4096'
        ]
        
        llama_proc = subprocess.Popen(
            llama_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        print(f'  🚀 Llama Server starting on port {LLAMA_PORT}')
        print('  ⏳ Loading model (this may take a minute)...')
        
        # Wait for Llama to be ready
        for i in range(120):
            try:
                import urllib.request
                urllib.request.urlopen(f'http://localhost:{LLAMA_PORT}/health', timeout=2)
                print(f'  ✅ Llama Server ready!')
                break
            except:
                if i % 15 == 0 and i > 0:
                    print(f'     Still loading... ({i}s)')
                time.sleep(1)
    except Exception as e:
        print(f'  ⚠️  Could not start Llama: {e}')
        print('     Continuing with Node backend...')
        llama_proc = None
    
    print('\n[3/3] Starting Node.js Backend...')
    try:
        node_proc = subprocess.Popen(
            ['node', 'codeforge_studio_server.js'],
            cwd=os.getcwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        print(f'  🚀 Node.js Backend starting on port {NODE_PORT}')
        
        # Wait for Node to be ready
        time.sleep(3)
        for i in range(30):
            try:
                import urllib.request
                urllib.request.urlopen(f'http://localhost:{NODE_PORT}', timeout=2)
                print(f'  ✅ Backend ready!')
                break
            except:
                time.sleep(0.5)
    except Exception as e:
        print(f'  ❌ Failed to start Node server: {e}')
        if llama_proc:
            llama_proc.terminate()
        input('\nPress Enter to exit...')
        sys.exit(1)
    
    # ============= STARTUP COMPLETE =============
    print(r"""
╔═══════════════════════════════════════════════════════════════════╗
║                     🎉 All systems ready!                        ║
║                                                                   ║
║              CodeForge Studio is starting in your browser         ║
║                                                                   ║
║  Features:                                                        ║
║    ✅ VS Code-like editor with syntax highlighting               ║
║    ✅ Multi-tab support for multiple files                       ║
║    ✅ AI assistant on right side (powered by Llama)              ║
║    ✅ File explorer with folder structure                        ║
║    ✅ Source control (Git) integration                           ║
║    ✅ Terminal commands support                                  ║
║    ✅ Real-time code analysis                                    ║
║    ✅ Collaborative file sharing                                 ║
║                                                                   ║
║  Default Settings:                                                ║
║    Admin Token: localdev                                         ║
║    Backend: http://localhost:5050                                ║
║    Llama Server: http://localhost:8000                           ║
║                                                                   ║
║  Click "Set Auth Token" in the right panel and enter: localdev   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    # Open browser
    try:
        print('\n🌐 Opening CodeForge Studio in your browser...\n')
        webbrowser.open(f'http://localhost:{NODE_PORT}/vscode_clone.html')
    except:
        print(f'Please open manually: http://localhost:{NODE_PORT}/vscode_clone.html\n')
    
    print('=' * 70)
    print('Press Ctrl+C to shutdown all services')
    print('=' * 70)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n\n🛑 Shutting down gracefully...')
        
        try:
            if llama_proc:
                llama_proc.terminate()
                llama_proc.wait(timeout=5)
        except:
            try:
                llama_proc.kill()
            except:
                pass
        
        try:
            if node_proc:
                node_proc.terminate()
                node_proc.wait(timeout=5)
        except:
            try:
                node_proc.kill()
            except:
                pass
        
        print('✅ All services stopped')
        print('\nThank you for using CodeForge Studio!')
        sys.exit(0)

if __name__ == '__main__':
    main()
