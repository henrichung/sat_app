"""
PyQt6.QtCore hook for PyInstaller
"""
# Add QtCore dependencies explicitly
hiddenimports = ['PyQt6.sip', 'PyQt6.QtGui']