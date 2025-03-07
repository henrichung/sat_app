#!/usr/bin/env python3
"""
SAT Question Bank & Worksheet Generator
Main Application Entry Point
"""
import sys
import os
import logging
import site
import importlib.machinery
import importlib.util

# Get the application directory
if getattr(sys, 'frozen', False):
    # Running as bundle (frozen)
    bundle_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, bundle_dir)
    
    # Add PyQt6 path specifically if we're frozen
    # Look for PyQt6 in potential locations
    potential_pyqt_paths = [
        os.path.join(bundle_dir, 'PyQt6'),
        os.path.join(bundle_dir, 'lib', 'PyQt6'),
        os.path.join(bundle_dir, 'lib', 'site-packages', 'PyQt6'),
        os.path.join(bundle_dir, 'pkgs', 'PyQt6'),
    ]
    
    for path in potential_pyqt_paths:
        if os.path.exists(path):
            if path not in sys.path:
                sys.path.insert(0, path)
                print(f"Added PyQt6 path: {path}")
                break
else:
    # Running in normal Python environment
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Try importing PyQt6 with detailed error reporting
try:
    # Try to import sip through PyQt6
    try:
        import PyQt6.sip
        print(f"Successfully imported PyQt6.sip")
    except ImportError as e:
        print(f"Warning: Could not import PyQt6.sip: {e}")
        # Only warn, don't fail, as some versions have different structure
        
    # Import the widgets module
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    print("Successfully imported PyQt6.QtWidgets and PyQt6.QtCore")
except ImportError as e:
    print(f"Error importing PyQt6: {e}")
    print(f"Current sys.path: {sys.path}")
    if getattr(sys, 'frozen', False):
        print(f"Frozen application directory: {bundle_dir}")
        # List contents to help debugging
        print("Directory contents:")
        # os.walk doesn't support maxdepth parameter
        level = 0
        max_level = 2
        for root, dirs, files in os.walk(bundle_dir, topdown=True):
            level = root.count(os.sep) - bundle_dir.count(os.sep)
            if level > max_level:
                del dirs[:]  # Don't go deeper
                continue
                
            print(f"Directory: {root}")
            for d in dirs:
                print(f"  Dir: {d}")
            for f in files:
                if 'pyqt' in f.lower() or 'sip' in f.lower():
                    print(f"  File: {f}")
    sys.exit(1)

# Import application modules
from sat_app.config.config_manager import ConfigManager
from sat_app.dal.database_manager import DatabaseManager
from sat_app.business.manager_factory import ManagerFactory
from sat_app.ui.main_window import MainWindow
from sat_app.utils.logger import setup_logger


def main():
    """Initialize and run the SAT Question Bank application."""
    # Set up logging
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting SAT Question Bank Application")

    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("SAT Question Bank")
    
    # Load configuration
    config = ConfigManager()
    if not config.load_config():
        logger.error("Failed to load configuration. Exiting.")
        return 1
    
    # Initialize database
    db_manager = DatabaseManager(config.get_db_path())
    if not db_manager.initialize():
        logger.error("Failed to initialize database. Exiting.")
        return 1
    
    # Initialize manager factory with config and config_manager
    manager_factory = ManagerFactory(db_manager, config.get_config_dict(), config)
    
    # Start UI
    main_window = MainWindow(config, db_manager, manager_factory)
    main_window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())