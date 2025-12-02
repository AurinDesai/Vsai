#!/usr/bin/env python3
"""
CodeForge Studio - Complete IDE with AI
Starts: Llama Server (port 8000) + Node.js Backend (port 5050) + Browser UI
"""

import os
import sys
import subprocess
import time
import platform
import json
import shutil
from pathlib import Path

# ============= CONFIG =============
LLAMA_PORT = 8000
NODE_PORT = 5050
MODEL_PATH = './models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf'
LLAMA_SERVER = './python/server'  # llama-cpp-python server
NODE_SERVER = 'node codeforge_studio_server.js'

print("""
=================================================================
 CodeForge Studio - VS Code Clone with AI
 Professional IDE with Collaborative Coding Features
=================================================================
""")

# ============= VALIDATION =============
def check_requirements():
    """Validate all dependencies"""
    print('\n[1/4] Checking requirements...')
    
    # Python
    print(f'  [OK] Python {sys.version.split()[0]}')
    
    # Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f'  [OK] Node.js {result.stdout.strip()}')
    except:
        print('  [ERROR] Node.js not found. Install from nodejs.org')
        sys.exit(1)
    
    # Model
    if os.path.exists(MODEL_PATH):
        size_gb = os.path.getsize(MODEL_PATH) / (1024**3)
        print(f'  ✅ Model: {size_gb:.2f}GB')
    else:
        print(f'  ⚠️  Model not found at {MODEL_PATH}')
    
    # Llama server
    if os.path.exists(LLAMA_SERVER):
        print(f'  ✅ Llama server found')
    else:
        print(f'  ⚠️  Llama server not found at {LLAMA_SERVER}')
    
    return True

def check_gpu():
    """Check for NVIDIA GPU"""
    print('\n[2/4] Checking GPU acceleration...')
    
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version,compute_cap', '--format=csv,noheader'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  ✅ NVIDIA GPU detected')
            print(f'     {result.stdout.strip()}')
            return True
    except:
        pass
    
    print('  ℹ️  No NVIDIA GPU found. Using CPU (slower)')
    return False

def start_llama_server():
    """Start Llama server using run_codeforge.py"""
    print('\n[3/4] Starting Llama Server...')
    
    if not os.path.exists(MODEL_PATH):
        print('  ❌ Model file not found. Skipping Llama server.')
        return None
    
    try:
        print(f'  🚀 Launching at http://localhost:{LLAMA_PORT}')
        print(f'     Model: {MODEL_PATH}')
        print(f'     Using: python run_codeforge.py')
        
        # Use the existing run_codeforge.py which handles all the setup
        proc = subprocess.Popen([sys.executable, 'run_codeforge.py'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to be ready with longer timeout
        print('  ⏳ Waiting for server initialization (max 120s)...')
        for i in range(120):
            try:
                import urllib.request
                urllib.request.urlopen(f'http://localhost:{LLAMA_PORT}/health', timeout=2)
                print(f'  ✅ Llama server ready!')
                return proc
            except:
                if i % 15 == 0 and i > 0:
                    print(f'     {i}s...')
                time.sleep(1)
        
        print('  ⚠️  Llama server still loading (continuing anyway)')
        return proc
        
    except Exception as e:
        print(f'  ⚠️  Could not start Llama server: {e}')
        print('     Continuing with Node backend...')
        return None

def start_node_server():
    """Start Node.js backend"""
    print('\n[4/4] Starting Node.js Backend...')
    
    try:
        print(f'  🚀 Launching at http://localhost:{NODE_PORT}')
        
        env = os.environ.copy()
        env['ADMIN_TOKEN'] = 'localdev'
        env['NODE_ENV'] = 'production'
        
        proc = subprocess.Popen(NODE_SERVER.split(), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for startup
        time.sleep(2)
        
        if proc.poll() is not None:
            print('  ❌ Node server failed to start')
            return None
        
        print(f'  ✅ Node.js backend ready!')
        return proc
        
    except Exception as e:
        print(f'  ❌ Failed to start Node server: {e}')
        return None

def open_browser():
    """Open UI in default browser"""
    print(f'\n🌐 Opening UI at http://localhost:{NODE_PORT}/vscode_clone.html')
    
    url = f'http://localhost:{NODE_PORT}/vscode_clone.html'
    
    system = platform.system()
    try:
        if system == 'Darwin':  # macOS
            subprocess.Popen(['open', url])
        elif system == 'Windows':
            import webbrowser
            webbrowser.open(url)
        elif system == 'Linux':
            subprocess.Popen(['xdg-open', url])
    except:
        print(f'  Please open manually: {url}')

def main():
    check_requirements()
    check_gpu()
    
    llama_proc = start_llama_server()
    node_proc = start_node_server()
    
    if not node_proc:
        print('\n❌ Failed to start backend services')
        sys.exit(1)
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                     🎉 All systems ready!                         ║
║                                                                   ║
║  Open your browser to: http://localhost:5050/vscode_clone.html    ║
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
║  Admin Token: localdev                                           ║
║  Llama Server: http://localhost:8000                             ║
║  Backend Server: http://localhost:5050                           ║
║                                                                   ║
║  Default admin token (if prompted): localdev                     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    open_browser()
    
    print('\n📝 Press Ctrl+C to shutdown all services...\n')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n\n🛑 Shutting down gracefully...')
        
        if llama_proc:
            try:
                llama_proc.terminate()
                llama_proc.wait(timeout=5)
            except:
                llama_proc.kill()
        
        if node_proc:
            try:
                node_proc.terminate()
                node_proc.wait(timeout=5)
            except:
                node_proc.kill()
        
        print('✅ All services stopped')
        sys.exit(0)

if __name__ == '__main__':
    main()
