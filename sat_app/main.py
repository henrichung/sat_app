#!/usr/bin/env python3
"""
SAT Question Bank & Worksheet Generator
Main Application Entry Point
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication

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