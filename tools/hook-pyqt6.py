"""
PyQt6 hook for PyInstaller to collect all necessary Qt files
"""
# List all PyQt6 modules needed by the application
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtSvg',
    'PyQt6.QtNetwork'
]