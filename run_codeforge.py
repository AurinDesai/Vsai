import subprocess
import time
import requests
import os
import sys
from datetime import datetime
import signal
import socket
import threading

# Configuration
MODEL_PATH = "models/deepseek-coder-6.7b-instruct-Q3_K_S.gguf"
LLAMA_SERVER_EXE = "llama-server.exe"
NODE_SERVER = "codeforge_server.js"

LLAMA_PORT = 8000
NODE_PORT = 5050


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_colored(message, color=""):
    if color:
        print(f"{color}{message}{Colors.ENDC}")
    else:
        print(message)


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         ⚡ CodeForge AI Pro v2.5 - EXPERT EDITION ⚡            ║
║                                                                  ║
║          Production-Grade Code Generation Engine                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.HEADER)


def check_nvidia():
    print_colored("\n[1/6] Checking NVIDIA GPU...", Colors.CYAN)
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0:
            print_colored("  ✅ NVIDIA GPU detected", Colors.GREEN)
            for line in result.stdout.split("\n"):
                if "CUDA Version" in line or "Driver Version" in line:
                    print_colored(f"  📊 {line.strip()}", Colors.BLUE)

            # Check GPU memory
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.free,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    free, total = line.split(",")
                    free_gb = float(free) / 1024
                    total_gb = float(total) / 1024
                    print_colored(
                        f"  📊 GPU Memory: {free_gb:.2f} GB free / {total_gb:.2f} GB total",
                        Colors.BLUE,
                    )

                    if free_gb < 2:
                        print_colored(
                            f"  ⚠️  Low GPU memory! Consider closing other GPU applications",
                            Colors.WARNING,
                        )
            return True
        else:
            print_colored("  ⚠️  GPU not detected - using CPU mode", Colors.WARNING)
            return False
    except Exception as e:
        print_colored("  ⚠️  GPU not detected - using CPU mode", Colors.WARNING)
        return False


def check_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))
            return True
    except:
        return False


def kill_process_on_port(port):
    """Kill any process using the specified port"""
    if os.name == "nt":  # Windows
        try:
            result = subprocess.run(
                f"netstat -ano | findstr :{port}",
                shell=True,
                capture_output=True,
                text=True,
            )
            lines = result.stdout.split("\n")
            for line in lines:
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(
                        f"taskkill /F /PID {pid}", shell=True, capture_output=True
                    )
                    print_colored(
                        f"  🔧 Freed port {port} (killed PID {pid})", Colors.WARNING
                    )
                    time.sleep(2)
                    return True
        except:
            pass
    else:  # Linux/Mac
        try:
            result = subprocess.run(
                f"lsof -ti:{port}", shell=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                pid = result.stdout.strip()
                subprocess.run(f"kill -9 {pid}", shell=True)
                print_colored(
                    f"  🔧 Freed port {port} (killed PID {pid})", Colors.WARNING
                )
                time.sleep(2)
                return True
        except:
            pass
    return False


def check_requirements():
    print_colored("\n[2/6] Checking requirements...", Colors.CYAN)

    required_files = {
        "Model": MODEL_PATH,
        "Llama Server": LLAMA_SERVER_EXE,
        "Node Server": NODE_SERVER,
    }

    missing = []
    for name, path in required_files.items():
        if os.path.exists(path):
            if name == "Model":
                size = os.path.getsize(path) / (1024**3)
                print_colored(f"  ✅ {name}: {size:.2f} GB", Colors.GREEN)
            else:
                print_colored(f"  ✅ {name}: Found", Colors.GREEN)
        else:
            print_colored(f"  ❌ {name}: Missing ({path})", Colors.FAIL)
            missing.append(name)

    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_colored(f"  ✅ Node.js: {version}", Colors.GREEN)
        else:
            print_colored(f"  ❌ Node.js: Not found", Colors.FAIL)
            missing.append("Node.js")
    except:
        print_colored(f"  ❌ Node.js: Not found", Colors.FAIL)
        missing.append("Node.js")

    # Check ports
    print_colored(f"\n  🔍 Checking ports...", Colors.BLUE)
    for port_name, port in [("Llama", LLAMA_PORT), ("Node", NODE_PORT)]:
        if check_port_available(port):
            print_colored(f"  ✅ Port {port} ({port_name}): Available", Colors.GREEN)
        else:
            print_colored(
                f"  ⚠️  Port {port} ({port_name}): In use - freeing...", Colors.WARNING
            )
            if kill_process_on_port(port):
                if check_port_available(port):
                    print_colored(f"  ✅ Port {port}: Now available", Colors.GREEN)
                else:
                    print_colored(f"  ❌ Port {port}: Still in use", Colors.FAIL)
                    missing.append(f"Port {port}")
            else:
                print_colored(f"  ❌ Port {port}: Cannot free", Colors.FAIL)
                missing.append(f"Port {port}")

    if missing:
        print_colored(f"\n  ❌ Missing: {', '.join(missing)}", Colors.FAIL)
        return False
    return True


def start_llama_server_expert(use_gpu=True):
    print_colored(f"\n[3/6] Starting Llama Server - EXPERT MODE...", Colors.CYAN)
    print_colored(
        f"  📊 Mode: {'GPU Accelerated' if use_gpu else 'CPU Only'}", Colors.BLUE
    )
    print_colored(f"  📊 Port: {LLAMA_PORT}", Colors.BLUE)
    print_colored(f"  📊 Model: {MODEL_PATH}", Colors.BLUE)
    print_colored(f"  📊 Max Output: 24000+ tokens", Colors.BLUE)

    # FIXED: Removed incompatible --flash-attn parameter
    # Using only parameters that are compatible with older llama-server versions
    if use_gpu:
        llama_cmd = [
            LLAMA_SERVER_EXE,
            "-m",
            MODEL_PATH,
            "--host",
            "127.0.0.1",
            "--port",
            str(LLAMA_PORT),
            "--ctx-size",
            "8192",
            "--n-predict",
            "-1",
            "--threads",
            "8",
            "--batch-size",
            "1024",
            "--ubatch-size",
            "512",
            "-ngl",
            "16",
        ]

    else:
        llama_cmd = [
            LLAMA_SERVER_EXE,
            "-m",
            MODEL_PATH,
            "--host",
            "127.0.0.1",
            "--port",
            str(LLAMA_PORT),
            "--ctx-size",
            "4096",
            "--threads",
            "8",
            "-ngl",
            "0",
            "--n-predict",
            "-1",
        ]

    print_colored(f"\n  🚀 Launching expert mode...", Colors.CYAN)

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        process = subprocess.Popen(
            llama_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )

        print_colored(f"  ✅ Process started (PID: {process.pid})", Colors.GREEN)
        print_colored(
            f"  ⏳ Waiting for server initialization (max 90 seconds)...",
            Colors.WARNING,
        )

        # Monitor output in background
        output_lines = []

        def monitor_output():
            try:
                for line in process.stdout:
                    if line:
                        output_lines.append(line.strip())
            except:
                pass

        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()

        # Wait for server with progress
        max_wait = 90
        check_interval = 3

        for i in range(0, max_wait, check_interval):
            time.sleep(check_interval)
            elapsed = i + check_interval

            # Check if process crashed
            if process.poll() is not None:
                print_colored(
                    f"\n  ❌ Process exited with code {process.returncode}", Colors.FAIL
                )
                print_colored(f"\n  📋 Last output:", Colors.WARNING)
                for line in output_lines[-10:]:
                    print(f"     {line}")
                return None

            # Check if server is responding
            try:
                response = requests.get(
                    f"http://127.0.0.1:{LLAMA_PORT}/health", timeout=3
                )
                if response.status_code == 200:
                    print_colored(
                        f"\n  ✅ Server ready after {elapsed} seconds!", Colors.GREEN
                    )
                    print_colored(
                        f"  🚀 Expert mode active - maximum performance", Colors.GREEN
                    )
                    return process
            except:
                pass

            print(f"  ⏳ Loading model... {elapsed}/{max_wait}s", end="\r")

        print_colored(
            f"\n\n  ⚠️  Server didn't respond after {max_wait}s", Colors.WARNING
        )
        print_colored(f"  ℹ️  The server is still starting up...", Colors.BLUE)
        print_colored(f"  ℹ️  Continue? (y/n): ", Colors.BLUE, end="")

        user_input = input().lower()
        if user_input == "y":
            print_colored(f"  ✅ Continuing...", Colors.GREEN)
            return process
        else:
            print_colored(f"  ❌ Stopping server...", Colors.FAIL)
            process.terminate()
            return None

    except Exception as e:
        print_colored(f"\n  ❌ Failed to start: {e}", Colors.FAIL)
        return None


def start_node_server():
    print_colored("\n[4/6] Starting Node.js Server - Expert Edition...", Colors.CYAN)

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        process = subprocess.Popen(
            ["node", NODE_SERVER, str(NODE_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )

        print_colored(f"  ✅ Process started (PID: {process.pid})", Colors.GREEN)
        print_colored(f"  ⏳ Waiting for server...", Colors.BLUE)
        time.sleep(3)

        for i in range(10):
            try:
                response = requests.get(
                    f"http://127.0.0.1:{NODE_PORT}/health", timeout=2
                )
                if response.status_code == 200:
                    print_colored(f"  ✅ Server ready!", Colors.GREEN)
                    data = response.json()
                    print_colored(
                        f"  📊 Version: {data.get('version', 'Unknown')}", Colors.BLUE
                    )
                    return process
            except:
                time.sleep(1)

        print_colored(f"  ⚠️  Server starting slowly...", Colors.WARNING)
        return process

    except Exception as e:
        print_colored(f"  ❌ Failed: {e}", Colors.FAIL)
        return None


def show_startup_info():
    print_colored("\n[5/6] System Configuration", Colors.CYAN)
    print_colored(f"  📊 Expert Mode: ACTIVE", Colors.GREEN)
    print_colored(f"  📊 Max Tokens: 24000+", Colors.GREEN)
    print_colored(f"  📊 Context Size: 16384", Colors.GREEN)
    print_colored(f"  📊 Features:", Colors.BLUE)
    print_colored(f"     • Production code generation", Colors.BLUE)
    print_colored(f"     • Advanced debugging", Colors.BLUE)
    print_colored(f"     • Split-view interface", Colors.BLUE)
    print_colored(f"     • High-performance streaming", Colors.BLUE)


def main():
    print_banner()

    print_colored("\n🚀 Launching CodeForge AI Pro - Expert Edition", Colors.HEADER)
    print_colored(
        "Optimized for maximum code generation quality and quantity\n", Colors.BLUE
    )

    # Run checks
    has_gpu = check_nvidia()

    if not check_requirements():
        print_colored("\n❌ Requirements check failed", Colors.FAIL)
        print_colored(
            "\n💡 Please ensure all files are present and ports are available",
            Colors.WARNING,
        )
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Start llama server in expert mode
    llama_process = start_llama_server_expert(has_gpu)

    if not llama_process:
        print_colored("\n❌ Llama server failed to start", Colors.FAIL)
        print_colored("\n💡 Troubleshooting:", Colors.WARNING)
        print_colored("   1. Check if model file is complete", Colors.BLUE)
        print_colored("   2. Ensure CUDA drivers are up to date", Colors.BLUE)
        print_colored("   3. Try running with CPU mode", Colors.BLUE)
        print_colored(
            "   4. Check if antivirus is blocking llama-server.exe", Colors.BLUE
        )
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Start Node server
    node_process = start_node_server()

    if not node_process:
        print_colored("\n❌ Node server failed", Colors.FAIL)
        if llama_process:
            llama_process.terminate()
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Show configuration
    show_startup_info()

    # Success
    print_colored("\n[6/6] STARTUP COMPLETE", Colors.CYAN)
    print_colored("\n" + "=" * 70, Colors.GREEN)
    print_colored("  ✅ CODEFORGE AI PRO - EXPERT MODE ACTIVE", Colors.GREEN)
    print_colored("=" * 70, Colors.GREEN)

    print_colored(f"\n  🌐 Web Interface: http://localhost:{NODE_PORT}", Colors.CYAN)
    print_colored(f"  🧠 AI Engine: http://localhost:{LLAMA_PORT}", Colors.CYAN)
    print_colored(f"\n  📋 CAPABILITIES:", Colors.BLUE)
    print_colored(f"     • Generate 5000+ lines of production code", Colors.BLUE)
    print_colored(f"     • Complete full-stack applications", Colors.BLUE)
    print_colored(f"     • Advanced debugging and optimization", Colors.BLUE)
    print_colored(f"     • Real-time streaming output", Colors.BLUE)
    print_colored(f"     • Split-view code/instructions", Colors.BLUE)

    print_colored(f"\n  💡 TIPS:", Colors.WARNING)
    print_colored(
        f"     • Be specific: 'Build a full e-commerce site with React and Node.js'",
        Colors.BLUE,
    )
    print_colored(
        f"     • Use Expert Mode (PRO button) for maximum output", Colors.BLUE
    )
    print_colored(
        f"     • Switch to Split View to see code and instructions separately",
        Colors.BLUE,
    )
    print_colored(
        f"     • For debugging: Upload your code file and describe the issue",
        Colors.BLUE,
    )

    print_colored(f"\n  ⌨️  Press Ctrl+C to stop all servers", Colors.BLUE)
    print_colored("\n" + "=" * 70 + "\n", Colors.GREEN)

    # Keep running
    try:
        while True:
            time.sleep(30)
            # Check if processes are still alive
            if llama_process.poll() is not None:
                print_colored("\n⚠️  Llama server stopped unexpectedly!", Colors.WARNING)
                break
            if node_process.poll() is not None:
                print_colored("\n⚠️  Node server stopped unexpectedly!", Colors.WARNING)
                break
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Shutting down servers...", Colors.WARNING)
        if llama_process:
            print_colored("  Stopping Llama server...", Colors.BLUE)
            llama_process.terminate()
            try:
                llama_process.wait(timeout=5)
            except:
                llama_process.kill()
        if node_process:
            print_colored("  Stopping Node server...", Colors.BLUE)
            node_process.terminate()
            try:
                node_process.wait(timeout=5)
            except:
                node_process.kill()
        print_colored("✅ Shutdown complete\n", Colors.GREEN)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Interrupted", Colors.WARNING)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Fatal error: {e}", Colors.FAIL)
        import traceback

        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
