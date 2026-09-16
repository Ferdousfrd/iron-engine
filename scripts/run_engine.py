#!/usr/bin/env python3
"""
Module: run_engine.py
Description: Master pipeline runner for Iron North Dispatch.
             Executes dispatch generation, image retrieval, and card rendering in sequence.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "bin", "python3")
PYTHON_EXEC = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

SCRIPTS = [
    os.path.join(SCRIPTS_DIR, "generate_dispatch.py"),
    os.path.join(SCRIPTS_DIR, "fetch_image.py"),
    os.path.join(SCRIPTS_DIR, "render_card.py")
]

def run_pipeline():
    print(f"[ENGINE] Working Directory: {BASE_DIR}")
    print(f"[ENGINE] Python Executable: {PYTHON_EXEC}\n")

    for script_path in SCRIPTS:
        script_name = os.path.basename(script_path)
        print(f"[ENGINE] Running {script_name}...")
        
        result = subprocess.run([PYTHON_EXEC, script_path], cwd=BASE_DIR)
        if result.returncode != 0:
            print(f"\n[ENGINE ERROR] Pipeline failed at {script_name} (Exit code: {result.returncode})")
            sys.exit(result.returncode)
            
    print("\n[ENGINE SUCCESS] Complete pipeline executed successfully.")

if __name__ == "__main__":
    run_pipeline()
