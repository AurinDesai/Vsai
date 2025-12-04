#!/usr/bin/env python3
"""
CodeForge Studio Launcher - Improved Version
Keeps server running and handles errors properly
"""

import os
import sys
import subprocess
import time
import platform
import webbrowser
import signal
import atexit
from pathlib import Path

# Configuration
NODE_PORT = 5050
LLAMA_PORT = 8000
MODEL_PATH = './models/deepseek-coder-6.7b-instruct.Q3_K_S.gguf'

# Global process handlers
node_proc = None
llama_proc = None

def cleanup():
    """Cleanup function called on exit"""
    print('\n\n🛑 Cleaning up...')
    
    if node_proc:
        try:
            node_proc.terminate()
            node_proc.wait(timeout=5)
            print('✅ Node server stopped')
        except:
            try:
                node_proc.kill()
            except:
                pass
    
    if llama_proc:
        try:
            llama_proc.terminate()
            llama_proc.wait(timeout=5)
            print('✅ Llama server stopped')
        except:
            try:
                llama_proc.kill()
            except:
                pass

# Register cleanup
atexit.register(cleanup)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\n🛑 Shutting down...')
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, None

def check_port(port):
    """Check if port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def wait_for_server(port, timeout=30):
    """Wait for server to become available"""
    import socket
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('localhost', port)) == 0:
                    return True
        except:
            pass
        time.sleep(0.5)
    
    return False

def main():
    global node_proc, llama_proc
    
    print(r"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║          🚀 CodeForge Studio - VS Code Clone with AI 🚀          ║
║                        Improved Launcher v3.0                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    # Check requirements
    print('[1/4] Checking requirements...')
    
    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f'  ✅ Python {py_version}')
    
    # Node.js
    node_ok, node_version = check_node()
    if not node_ok:
        print('  ❌ Node.js not found!')
        print('\n  Install Node.js from: https://nodejs.org/')
        input('\nPress Enter to exit...')
        sys.exit(1)
    print(f'  ✅ Node.js {node_version}')
    
    # Check if workspace exists
    workspace = Path('./workspace')
    if not workspace.exists():
        print(f'  📁 Creating workspace folder...')
        workspace.mkdir(parents=True, exist_ok=True)
        print(f'  ✅ Workspace created')
    else:
        print(f'  ✅ Workspace exists')
    
    # Model (optional)
    if os.path.exists(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        print(f'  ✅ AI Model: {size_mb:.1f}MB')
    else:
        print(f'  ⚠️  AI Model not found (optional)')
    
    # Check port availability
    print('\n[2/4] Checking ports...')
    
    if not check_port(NODE_PORT):
        print(f'  ⚠️  Port {NODE_PORT} is in use!')
        print(f'     Trying to kill existing process...')
        
        if platform.system() == 'Windows':
            os.system(f'taskkill /F /FI "IMAGENAME eq node.exe" >nul 2>&1')
        else:
            os.system(f'pkill -f "node.*codeforge"')
        
        time.sleep(2)
        
        if not check_port(NODE_PORT):
            print(f'  ❌ Port {NODE_PORT} still in use!')
            print(f'     Please close the existing process')
            input('\nPress Enter to exit...')
            sys.exit(1)
    
    print(f'  ✅ Port {NODE_PORT} available')
    
    # Start Node.js server
    print('\n[3/4] Starting Node.js server...')
    
    try:
        # Use CREATE_NO_WINDOW on Windows to prevent console spam
        creation_flags = 0
        if platform.system() == 'Windows':
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        node_proc = subprocess.Popen(
            ['node', 'codeforge_studio_server.js'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
            cwd=os.getcwd()
        )
        
        print(f'  🚀 Node server starting (PID: {node_proc.pid})')
        
        # Wait for server to be ready
        if wait_for_server(NODE_PORT, timeout=30):
            print(f'  ✅ Server ready on port {NODE_PORT}')
        else:
            print(f'  ❌ Server failed to start!')
            
            # Show error output
            stdout, stderr = node_proc.communicate(timeout=1)
            if stderr:
                print(f'\n  Error output:')
                print(f'  {stderr.decode()[:500]}')
            
            sys.exit(1)
    
    except Exception as e:
        print(f'  ❌ Failed to start Node server: {e}')
        input('\nPress Enter to exit...')
        sys.exit(1)
    
    # Try to start Llama (optional)
    print('\n[4/4] Starting AI engine (optional)...')
    
    if os.path.exists(MODEL_PATH):
        try:
            llama_cmd = [
                sys.executable, '-m', 'llama_cpp.server',
                '--model', MODEL_PATH,
                '--port', str(LLAMA_PORT),
                '--n_gpu_layers', '99',
                '--n_ctx', '4096'
            ]
            
            creation_flags = 0
            if platform.system() == 'Windows':
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            llama_proc = subprocess.Popen(
                llama_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
            
            print(f'  🧠 Llama starting (this may take a minute)...')
            
            # Wait up to 60 seconds for Llama
            if wait_for_server(LLAMA_PORT, timeout=60):
                print(f'  ✅ AI engine ready')
            else:
                print(f'  ⚠️  AI engine not responding (continuing anyway)')
        
        except Exception as e:
            print(f'  ⚠️  Could not start AI: {e}')
            print(f'  💡 AI features will be unavailable')
    else:
        print(f'  ⚠️  Model not found - AI features disabled')
    
    # Success!
    print(r"""
╔═══════════════════════════════════════════════════════════════════╗
║                     🎉 CodeForge Studio Ready!                   ║
╚═══════════════════════════════════════════════════════════════════╝

  📋 Quick Start:
     1. Click "Set Auth Token" → enter "localdev"
     2. Files will be saved to: workspace/
     3. Use File menu to create/import files
     4. Press Ctrl+S to save
     5. Press Ctrl+P for file search

  🌐 Opening browser...
""")
    
    # Open browser
    try:
        url = f'http://localhost:{NODE_PORT}/vscode_clone.html'
        webbrowser.open(url)
        print(f'  ✅ Browser opened: {url}')
    except:
        print(f'  ⚠️  Could not open browser automatically')
        print(f'  📌 Please open: http://localhost:{NODE_PORT}/vscode_clone.html')
    
    print('\n' + '=' * 70)
    print('  Press Ctrl+C to stop all services')
    print('=' * 70 + '\n')
    
    # Keep running until interrupted
    try:
        while True:
            # Check if Node process is still running
            if node_proc.poll() is not None:
                print('\n❌ Node server stopped unexpectedly!')
                
                # Show error output
                stdout, stderr = node_proc.communicate()
                if stderr:
                    print(f'\nError output:\n{stderr.decode()[:1000]}')
                
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        pass
    
    finally:
        cleanup()
        print('\n✅ Shutdown complete')
        print('Thank you for using CodeForge Studio!\n')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'\n❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
        input('\nPress Enter to exit...')
        sys.exit(1)