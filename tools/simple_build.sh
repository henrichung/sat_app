#!/bin/bash
echo "=== Simple SAT App Build Process with PyQt6 ==="
echo

echo "Step 1: Cleaning environment and installing dependencies..."
python -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5_sip PySide6 shiboken6
python -m pip install PyQt6==6.8.1 PyQt6-Qt6==6.8.2 PyQt6_sip==13.10.0
python -m pip install -r requirements.txt
echo

echo "Step 2: Verifying critical dependencies for new features..."
python -c "import fuzzywuzzy; print('✓ fuzzywuzzy installed')" || { echo "✗ fuzzywuzzy missing"; exit 1; }
python -c "import Levenshtein; print('✓ python-Levenshtein installed')" || { echo "✗ python-Levenshtein missing"; exit 1; }
echo

echo "Step 3: Testing database schema migration..."
python -c "from sat_app.dal.database_manager import DatabaseManager; print('✓ Database manager ready')" || { echo "✗ Database migration issues"; exit 1; }
echo

echo "Step 4: Creating spec file..."
python tools/simple_pyqt6_spec.py
echo

echo "Step 5: Building application with PyInstaller..."
python -m PyInstaller tools/simple_pyqt6.spec
echo

echo "Step 6: Verifying build artifacts..."
if [ -f "dist/SAT App" ]; then
    echo "✓ Executable created successfully"
else
    echo "✗ Build failed - executable not found"
    exit 1
fi

echo
echo "Build completed successfully!"
echo "The executable is located at: dist/SAT App"
echo
echo "New features included in this build:"
echo "- Free response question support"
echo "- Enhanced duplicate detection with fuzzy matching"
echo "- Question type system (multiple_choice/free_response)"
echo