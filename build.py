import os
import subprocess
import sys

def build():
    separator = ";" if sys.platform == "win32" else ":"
    
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", 
        "--name", "NetPulse",
        "main.py"
    ]
    
    print("Starting compilation of NetPulse...")
    subprocess.run(command)
    print("Build complete! Check the 'dist' folder for your executable.")

if __name__ == "__main__":
    build()
