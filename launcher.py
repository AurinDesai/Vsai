#!/usr/bin/env python3
"""
CodeForge Studio - Windows Desktop Application
FIXED: Prevents infinite loops, proper cleanup, kill switch
"""

import sys
import time
import webbrowser
import socket
import subprocess
import atexit
import signal
import threading
import os

# `psutil` is required at runtime. Try to import early but allow
# the script to attempt an automatic install later in `__main__`.
try:
    import psutil
except ImportError:
    psutil = None

# Provide safe aliases for psutil exception types so `except (..)` tuples
# don't attempt to access attributes on `None` (which would raise while
# handling another exception). When psutil is missing we alias to
# `Exception` so the except block still catches runtime errors.
if psutil is None:
    PSUTIL_NoSuchProcess = Exception
    PSUTIL_AccessDenied = Exception
    PSUTIL_ZombieProcess = Exception
else:
    PSUTIL_NoSuchProcess = psutil.NoSuchProcess
    PSUTIL_AccessDenied = psutil.AccessDenied
    # Some psutil versions export ZombieProcess; fallback if missing
    PSUTIL_ZombieProcess = getattr(psutil, 'ZombieProcess', Exception)

def ensure_psutil():
    """Ensure `psutil` is importable. If missing, attempt to install it.

    This updates the global `psutil` and PSUTIL_* aliases.
    """
    global psutil, PSUTIL_NoSuchProcess, PSUTIL_AccessDenied, PSUTIL_ZombieProcess

    if psutil is not None:
        return

    try:
        import psutil as _p
        psutil = _p
    except Exception:
        try:
            print_log("psutil not found — attempting to install via pip")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psutil'])
            import importlib
            psutil = importlib.import_module('psutil')
        except Exception as e:
            log(f"Could not install/import psutil: {e}")
            psutil = None

    # Update aliases
    if psutil is None:
        PSUTIL_NoSuchProcess = Exception
        PSUTIL_AccessDenied = Exception
        PSUTIL_ZombieProcess = Exception
    else:
        PSUTIL_NoSuchProcess = psutil.NoSuchProcess
        PSUTIL_AccessDenied = psutil.AccessDenied
        PSUTIL_ZombieProcess = getattr(psutil, 'ZombieProcess', Exception)

# ============= CONFIGURATION =============
LLAMA_PORT = 8000
NODE_PORT = 5050
MODEL_PATH = './models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf'
LOCK_FILE = 'codeforge.lock'
LOG_FILE = 'codeforge_launcher.log'
KILL_FILE = 'codeforge.kill'  # NEW: Emergency kill file

# ============= PROCESS TRACKING =============
llama_process = None
node_process = None
startup_complete = False
shutdown_initiated = False

def log(msg):
    """Write to log file with timestamp"""
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {msg}\n")
            f.flush()
    except:
        pass

def print_log(msg):
    """Print and log simultaneously (prints are ASCII-only)"""
    try:
        print(msg)
    except Exception:
        pass
    log(msg)

def emergency_kill_check():
    """Check for emergency kill file every second"""
    while not shutdown_initiated:
        if os.path.exists(KILL_FILE):
            print_log("[EMERGENCY] EMERGENCY KILL FILE DETECTED - FORCE SHUTDOWN")
            force_shutdown()
            sys.exit(1)
        time.sleep(1)

def force_shutdown():
    """Force kill all processes immediately"""
    global shutdown_initiated
    shutdown_initiated = True
    
    print_log("[WARN] FORCE SHUTDOWN INITIATED")
    
    # Kill all Python processes named llama (if psutil available)
    if psutil is None:
        log("psutil not available: skipping process-kill for llama")
    else:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'llama' in proc.name().lower() or \
                       (proc.cmdline() and any('llama' in str(cmd).lower() for cmd in proc.cmdline())):
                        print_log(f"Killing llama process: {proc.pid}")
                        proc.kill()
                except (PSUTIL_NoSuchProcess, PSUTIL_AccessDenied):
                    pass
        except Exception as e:
            log(f"Error killing llama processes: {e}")
    
    # Kill all node processes on our port
    if psutil is None:
        log("psutil not available: skipping process-kill for node")
    else:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    if proc.name().lower() in ['node.exe', 'node']:
                        for conn in proc.connections():
                            if conn.laddr.port == NODE_PORT:
                                print_log(f"Killing node process: {proc.pid}")
                                proc.kill()
                except (PSUTIL_NoSuchProcess, PSUTIL_AccessDenied, PSUTIL_ZombieProcess):
                    pass
        except Exception as e:
            log(f"Error killing node processes: {e}")
    
    # Remove lock files
    remove_lock()
    try:
        if os.path.exists(KILL_FILE):
            os.remove(KILL_FILE)
    except:
        pass
    
    print_log("[OK] Force shutdown complete")

def check_single_instance():
    """Ensure only one instance is running - WITH TIMEOUT"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process still exists (best-effort with psutil)
            try:
                if psutil is None:
                    # Fallback: if lock file is recent, assume running; otherwise remove
                    lock_age = time.time() - os.path.getmtime(LOCK_FILE)
                    if lock_age > 300:  # 5 minutes
                        print_log(f"[WARN] Stale lock file detected (age: {lock_age:.0f}s)")
                        print_log("Removing stale lock and continuing...")
                        os.remove(LOCK_FILE)
                    else:
                        print_log(f"Lock file present (PID: {old_pid}) — psutil not installed to verify process")
                        sys.exit(0)
                else:
                    process = psutil.Process(old_pid)
                    if process.is_running():
                        # Check how old the lock file is
                        lock_age = time.time() - os.path.getmtime(LOCK_FILE)
                        if lock_age > 300:  # 5 minutes
                            print_log(f"[WARN] Stale lock file detected (age: {lock_age:.0f}s)")
                            print_log("Removing stale lock and continuing...")
                            os.remove(LOCK_FILE)
                        else:
                            print_log(f"Another instance is running (PID: {old_pid})")
                            # Non-interactive exit
                            sys.exit(0)
            except Exception as e:
                # If psutil raised NoSuchProcess or other errors, remove stale lock
                try:
                    os.remove(LOCK_FILE)
                except:
                    pass
                log("Removed stale lock file (process dead or unknown error)")
        except Exception as e:
            log(f"Lock check error: {e}")
            # Remove corrupted lock file
            try:
                os.remove(LOCK_FILE)
            except:
                pass
    
    # Create new lock file with timestamp
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        log(f"Lock acquired (PID: {os.getpid()})")
    except Exception as e:
        log(f"Failed to create lock: {e}")

def remove_lock():
    """Remove lock file on exit"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            log("Lock removed")
    except:
        pass

def is_port_in_use(port):
    """Check if a port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    killed = False
    if psutil is None:
        log(f"psutil not available: cannot kill processes on port {port}")
        return False

    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        print_log(f"Killing process {proc.pid} ({proc.name()}) on port {port}")
                        proc.kill()
                        proc.wait(timeout=3)
                        killed = True
            except (PSUTIL_AccessDenied, PSUTIL_NoSuchProcess, PSUTIL_ZombieProcess):
                continue
            except Exception as e:
                log(f"Error killing process: {e}")
    except Exception as e:
        log(f"Error scanning processes on port {port}: {e}")
    
    if killed:
        time.sleep(2)
    return killed

def wait_for_port(port, timeout=120, service_name="Service"):
    """Wait for a service to be ready on specified port - WITH PROGRESS"""
    print_log(f"Waiting for {service_name} on port {port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for emergency kill
        if os.path.exists(KILL_FILE):
            print_log("Emergency kill detected during startup")
            return False
            
            print_log(f"[OK] {service_name} ready on port {port}")
        
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"   Still loading... {elapsed}s elapsed", end='\r')
        
        time.sleep(1)
    
    print_log(f"[WARN] {service_name} timeout after {timeout}s")
    return False

def cleanup_processes():
    """Clean up all spawned processes"""
    global llama_process, node_process, shutdown_initiated
    
    if shutdown_initiated:
        return
        
    shutdown_initiated = True
    print_log("[SHUTDOWN] Shutting down services...")
    
    # Terminate Node server
    if node_process:
        try:
            print_log("Stopping Node server...")
            node_process.terminate()
            print_log("[OK] Node server stopped")
        except subprocess.TimeoutExpired:
            node_process.kill()
            log("Node server killed (timeout)")
        except Exception as e:
            log(f"Error stopping Node: {e}")
    
    # Terminate Llama server
    if llama_process:
        try:
            print_log("Stopping Llama server...")
            llama_process.terminate()
            print_log("[OK] Llama server stopped")
        except subprocess.TimeoutExpired:
            llama_process.kill()
            log("Llama server killed (timeout)")
        except Exception as e:
            log(f"Error stopping Llama: {e}")
    
    # Kill any remaining processes on our ports
    for port, name in [(LLAMA_PORT, "Llama"), (NODE_PORT, "Node")]:
        if is_port_in_use(port):
            print_log(f"Cleaning up port {port} ({name})...")
            kill_process_on_port(port)
    
    print_log("[OK] Cleanup complete")

def start_llama_server():
    """Start Llama server with timeout protection"""
    global llama_process
    
    print_log("\n[1/3] Starting AI Engine...")
    
    # Check if llama-cpp-python is installed
    try:
        import llama_cpp
    except ImportError:
        print_log("[WARN] llama-cpp-python not installed")
        print("\nWarning: llama-cpp-python not found")
        print("   AI features will be limited")
        return None
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print_log(f"[WARN] Model not found: {MODEL_PATH}")
        print("Warning: AI model not found. AI features will be limited.")
        return None
    
    # Kill any existing process on port
    if is_port_in_use(LLAMA_PORT):
        print_log(f"Port {LLAMA_PORT} in use, cleaning up...")
        kill_process_on_port(LLAMA_PORT)
        time.sleep(3)
    
    try:
        # Build command
        cmd = [
            sys.executable, '-m', 'llama_cpp.server',
            '--model', MODEL_PATH,
            '--port', str(LLAMA_PORT),
            '--n_gpu_layers', '99',
            '--n_threads', '8',
            '--chat_format', 'chatml'
        ]
        
        # Create process with proper flags to hide window
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        llama_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            cwd=os.getcwd()
        )
        
        log(f"Llama server started (PID: {llama_process.pid})")
        
        # Wait for server to be ready WITH TIMEOUT
        if wait_for_port(LLAMA_PORT, timeout=90, service_name="AI Engine"):
            return llama_process
        else:
            print_log("[WARN] AI Engine timeout - continuing anyway")
            return llama_process
            
    except Exception as e:
        print_log(f"[ERROR] Failed to start AI Engine: {e}")
        return None

def start_node_server():
    """Start Node.js backend with timeout protection"""
    global node_process
    
    print_log("\n[2/3] Starting Backend Server...")
    
    # Check if Node is available
    try:
        subprocess.run(['node', '--version'], capture_output=True, timeout=5)
    except:
        print_log("[ERROR] Node.js not found. Please install Node.js from nodejs.org")
        return None
    
    # Kill any existing process on port
    if is_port_in_use(NODE_PORT):
        print_log(f"Port {NODE_PORT} in use, cleaning up...")
        kill_process_on_port(NODE_PORT)
        time.sleep(3)
    
    try:
        # Build command
        cmd = ['node', 'codeforge_studio_server.js']
        
        # Create process with proper flags to hide window
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        node_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            cwd=os.getcwd()
        )
        
        log(f"Node server started (PID: {node_process.pid})")
        
        # Give Node a moment to start binding to the port
        time.sleep(3)
        
        # Wait for server to be ready (with longer timeout for slower systems)
        if wait_for_port(NODE_PORT, timeout=60, service_name="Backend Server"):
            return node_process
        else:
            print_log("[WARN] Backend server timeout - but continuing anyway")
            # Return the process even if timeout, it may still work
            return node_process
            
    except Exception as e:
        print_log(f"[ERROR] Failed to start backend: {e}")
        return None

def open_browser():
    """Open the application in browser"""
    print_log("\n[3/3] Opening browser...")
    url = f'http://localhost:{NODE_PORT}/vscode_clone.html'
    
    time.sleep(2)
    
    try:
        webbrowser.open(url)
        print_log("[OK] Browser opened")
        print(f"\nApplication URL: {url}")
    except Exception as e:
        print_log(f"[WARN] Could not open browser: {e}")
        print(f"\nPlease open manually: {url}")

def monitor_health():
    """Monitor process health and restart if needed"""
    global llama_process, node_process, startup_complete
    
    while not shutdown_initiated:
        time.sleep(10)
        
        if not startup_complete:
            continue
        
        # Check if Node process died
        if node_process and node_process.poll() is not None:
            print_log("[WARN] Node server died unexpectedly")
            break
        
        # Check if Llama process died (non-critical)
        if llama_process and llama_process.poll() is not None:
            print_log("[WARN] Llama server died (AI features disabled)")
            llama_process = None

def main():
    """Main startup orchestration"""
    global startup_complete
    
    # Clear old log on startup
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except:
        pass
    
    # Remove old kill file
    try:
        if os.path.exists(KILL_FILE):
            os.remove(KILL_FILE)
    except:
        pass
    
    print("\n" + "="*70)
    print("  CodeForge Studio - Professional IDE with AI")
    print("="*70 + "\n")
    
    log("\n=== CodeForge Studio Launcher Started ===\n")
    
    # Register cleanup handler
    atexit.register(cleanup_processes)
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    
    # Start emergency kill checker thread
    kill_thread = threading.Thread(target=emergency_kill_check, daemon=True)
    kill_thread.start()
    
    try:
        # Check for existing instance
        # Ensure psutil available (try to auto-install if missing)
        ensure_psutil()
        check_single_instance()
        
        # Start services
        llama_proc = start_llama_server()
        node_proc = start_node_server()
        
        if not node_proc:
            print_log("\n[ERROR] Failed to start backend server")
            print("\nStartup failed. Check the log file for details.")
            print("\n[INFO] To force kill any stuck processes:")
            print("   1. Create a file named 'codeforge.kill'")
            print("   2. Wait a few seconds")
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        # Open browser
        open_browser()
        
        startup_complete = True
        
        # Success message
        print("\n" + "="*70)
        print("  CodeForge Studio is running!")
        print("="*70)
        print("\n  Features:")
        print("    - VS Code-like editor with AI assistance")
        print("    - File explorer and source control")
        print("    - Real-time code analysis")
        print("    - Collaborative file sharing")
        print("\n  Default admin token: localdev")
        print("\n  EMERGENCY SHUTDOWN: create 'codeforge.kill' in this folder")
        print("\n  To stop: Close this window or press Ctrl+C")
        print("="*70 + "\n")
        
        log("Startup complete - entering main loop")
        
        # Start health monitor thread
        health_thread = threading.Thread(target=monitor_health, daemon=True)
        health_thread.start()
        
        # Keep running
        while not shutdown_initiated:
            time.sleep(5)

            # Check for manual stop
            if node_proc and node_proc.poll() is not None:
                print_log("[WARN] Backend server stopped")
                break
        
    except KeyboardInterrupt:
        print_log("\nInterrupted by user")
    except Exception as e:
        print_log(f"\nFATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        print("\nAn error occurred. Check codeforge_launcher.log for details.")
        print("\nCreate a file named 'codeforge.kill' to force shutdown")
    finally:
        cleanup_processes()
        sys.exit(0)

if __name__ == '__main__':
    main()