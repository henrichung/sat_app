@echo off
echo === Simple SAT App Build Process with PyQt6 ===
echo.

echo Step 1: Cleaning environment and installing dependencies...
python -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5_sip PySide6 shiboken6
python -m pip install PyQt6==6.8.1 PyQt6-Qt6==6.8.2 PyQt6_sip==13.10.0
python -m pip install -r requirements.txt
echo.

echo Step 2: Verifying critical dependencies for new features...
python -c "import fuzzywuzzy; print('✓ fuzzywuzzy installed')" || (echo "✗ fuzzywuzzy missing" && exit /b 1)
python -c "import Levenshtein; print('✓ python-Levenshtein installed')" || (echo "✗ python-Levenshtein missing" && exit /b 1)
echo.

echo Step 3: Testing database schema and new models...
python -c "from sat_app.dal.database_manager import DatabaseManager; print('✓ Database manager ready')" || (echo "✗ Database migration issues" && exit /b 1)
python -c "from sat_app.dal.models import StudentResponse; print('✓ StudentResponse model ready')" || (echo "✗ StudentResponse model issues" && exit /b 1)
python -c "from sat_app.business.import_export_manager import ImportExportManager; print('✓ Import/Export manager ready')" || (echo "✗ Import/Export issues" && exit /b 1)
echo.

echo Step 4: Testing UI components...
python -c "from sat_app.ui.components.response_grid import ResponseGrid, ResponseGridCell; print('✓ Response grid components ready')" || (echo "✗ Response grid issues" && exit /b 1)
python -c "from sat_app.ui.question_editor import QuestionEditor; print('✓ Question editor ready')" || (echo "✗ Question editor issues" && exit /b 1)
echo.

echo Step 5: Creating spec file...
python tools\simple_pyqt6_spec.py
echo.

echo Step 6: Building application with PyInstaller...
python -m PyInstaller tools\simple_pyqt6.spec
echo.

echo Step 7: Verifying build artifacts...
if exist "dist\SAT App.exe" (
    echo ✓ Executable created successfully
) else (
    echo ✗ Build failed - executable not found
    exit /b 1
)

echo.
echo Build completed successfully!
echo The executable is located at: dist\SAT App.exe
echo.
echo Features included in this build:
echo - Free response question support with text input
echo - Mixed question type worksheets (multiple choice + free response)
echo - Enhanced response grid with adaptive UI
echo - Question type auto-detection during import
echo - Enhanced duplicate detection with fuzzy matching
echo - Improved Unicode support in logging
echo - Database schema migration for answer field flexibility
echo - StudentResponse model for detailed answer tracking
echo - Complex answer data structure normalization
echo.