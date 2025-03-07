#!/usr/bin/env python3
"""
Clean PyQt environment to ensure no conflicts between PyQt5 and PyQt6
"""
import subprocess
import sys

def main():
    """Uninstall PyQt5 and reinstall PyQt6 with specific versions"""
    packages_to_uninstall = [
        "PyQt5", "PyQt5-Qt5", "PyQt5_sip", 
        "PySide6", "shiboken6"
    ]
    
    # Uninstall PyQt5 and PySide6 packages
    print("Uninstalling potentially conflicting packages...")
    for package in packages_to_uninstall:
        print(f"Uninstalling {package}...")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package],
                      capture_output=True, text=True)
    
    # Reinstall PyQt6 with specific versions
    print("\nReinstalling PyQt6 packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", 
                   "PyQt6==6.8.1", "PyQt6-Qt6==6.8.2", "PyQt6_sip==13.10.0"],
                  capture_output=False)  # Show pip output for installation
    
    # Print installed Qt packages
    print("\nInstalled Qt packages:")
    subprocess.run([sys.executable, "-m", "pip", "list"], 
                  capture_output=False)
    
    print("\nPyQt environment cleaned successfully.")

if __name__ == "__main__":
    main()