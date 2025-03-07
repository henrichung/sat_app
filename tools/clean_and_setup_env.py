#!/usr/bin/env python3
"""
Script to clean up the environment by removing PyQt5 and setting up PyQt6 correctly
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and print output"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def main():
    """Clean up environment and set up PyQt6"""
    # Uninstall PyQt5 packages
    print("Uninstalling PyQt5 packages...")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "PyQt5", "PyQt5-Qt5", "PyQt5_sip"])
    
    # Uninstall PySide6 to avoid conflicts
    print("Uninstalling PySide6 packages...")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "PySide6", "shiboken6"])
    
    # Uninstall PyQt6 to reinstall cleanly
    print("Uninstalling PyQt6 packages to reinstall cleanly...")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "PyQt6", "PyQt6-Qt6", "PyQt6_sip"])
    
    # Install PyQt6 with specific versions
    print("Installing PyQt6 packages...")
    run_command([sys.executable, "-m", "pip", "install", "PyQt6==6.8.1", "PyQt6-Qt6==6.8.2", "PyQt6_sip==13.10.0"])
    
    # Check and print the installed packages
    print("\nInstalled Qt packages:")
    run_command([sys.executable, "-m", "pip", "list", "|", "grep", "-i", "qt"])
    
    print("\nEnvironment setup complete. Now you can build the application.")

if __name__ == "__main__":
    main()