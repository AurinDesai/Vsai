#!/usr/bin/env python3
"""Quick test to verify launcher.py imports without encoding errors"""
import sys
import traceback

try:
    print("Attempting to import launcher...")
    import launcher
    print("SUCCESS: launcher.py imported without encoding errors!")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)
