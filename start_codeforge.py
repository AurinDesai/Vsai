#!/usr/bin/env python3
"""
CodeForge Studio - All-in-One Starter
Launches Node backend and opens the web UI in your default browser.
No dependencies required (uses subprocess only).
"""

import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent
NODE_SERVER = PROJECT_ROOT / "codeforge_studio_server.js"
BROWSER_URL = "http://localhost:5050/vscode_clone.html"
PORT = 5050

def check_port_available(port=5050):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def kill_node_process():
    """Kill any existing node processes on port 5050"""
    try:
        if sys.platform == 'win32':
            os.system('taskkill /F /IM node.exe >nul 2>&1')
        else:
            os.system('pkill -f "node.*codeforge_studio_server.js" 2>/dev/null')
        time.sleep(1)
    except:
        pass

def start_node_server():
    """Start the Node.js backend server"""
    print("\n" + "="*60)
    print("Starting CodeForge Studio Backend...")
    print("="*60)
    
    if not NODE_SERVER.exists():
        print(f"ERROR: {NODE_SERVER} not found!")
        return None
    
    try:
        # Start Node server in background
        if sys.platform == 'win32':
            # Windows: start detached process
            process = subprocess.Popen(
                ["node", str(NODE_SERVER)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
        else:
            # Unix: start detached process
            process = subprocess.Popen(
                ["node", str(NODE_SERVER)],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        
        print(f"✓ Node server started (PID: {process.pid})")
        return process
    except FileNotFoundError:
        print("ERROR: Node.js not found. Please install Node.js from https://nodejs.org")
        return None
    except Exception as e:
        print(f"ERROR: Failed to start Node server: {e}")
        return None

def wait_for_server(timeout=10):
    """Wait for server to be ready"""
    print("\nWaiting for server to start...", end=" ", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            import urllib.request
            response = urllib.request.urlopen(BROWSER_URL, timeout=1)
            if response.status == 200:
                print("✓ Ready!")
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(0.5)
    
    print("\nWARNING: Server may still be starting...")
    return True

def open_browser():
    """Open the web UI in default browser"""
    print(f"\nOpening browser at {BROWSER_URL}...")
    try:
        webbrowser.open(BROWSER_URL)
        print("✓ Browser opened!")
        return True
    except:
        print(f"Could not open browser automatically.")
        print(f"Please open manually: {BROWSER_URL}")
        return False

def show_instructions():
    """Show user instructions"""
    print("\n" + "="*60)
    print("CodeForge Studio is Ready!")
    print("="*60)
    print(f"\nWeb UI: {BROWSER_URL}")
    print("\nQuick Start:")
    print("  1. Click 'Set Auth Token' → enter 'localdev'")
    print("  2. Create a file: File → New File")
    print("  3. Fuzzy search: Press Ctrl+P")
    print("  4. Upload folder: File → Add Existing Folder (Upload)")
    print("  5. Split editor: Click 'Split Right' button")
    print("\nFeatures:")
    print("  • File explorer & multi-tab editor")
    print("  • Git integration (Source Control panel)")
    print("  • Terminal (View → Toggle Terminal)")
    print("  • AI chat (optional, requires Llama server)")
    print("  • Syntax highlighting (20+ languages)")
    print("  • Auto-save & backups")
    print("\nPress Ctrl+C to stop the server.\n")
    print("="*60 + "\n")

def main():
    """Main entry point"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█  CodeForge Studio - VS Code Clone with AI             █")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    # Kill any existing processes
    print("\nChecking for existing processes...")
    kill_node_process()
    
    # Check if port is available
    if not check_port_available(PORT):
        print(f"ERROR: Port {PORT} is already in use.")
        print("Please close other applications using port 5050.")
        sys.exit(1)
    
    # Start Node server
    process = start_node_server()
    if not process:
        sys.exit(1)
    
    # Wait for server to be ready
    wait_for_server()
    
    # Open browser
    open_browser()
    
    # Show instructions
    show_instructions()
    
    # Keep process alive
    try:
        while True:
            time.sleep(1)
            # Check if process is still running
            if process.poll() is not None:
                print("\nERROR: Server process exited unexpectedly!")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nShutting down CodeForge Studio...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        print("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
