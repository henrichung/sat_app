"""
Theme manager for the SAT Question Bank application.
Provides styles and theme management for the application.
"""
import logging
import os
from enum import Enum
from typing import Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


class Theme(Enum):
    """Enum for available themes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeManager:
    """
    Manages application theming.
    
    Provides functions for setting application-wide themes,
    creating stylesheets, and maintaining consistent styling.
    """
    
    # Color definitions for difficulty levels
    DIFFICULTY_COLORS = {
        "Easy": {"light": "#4CAF50", "dark": "#388E3C"},       # Green
        "Medium": {"light": "#FFC107", "dark": "#FFA000"},     # Amber
        "Hard": {"light": "#FF9800", "dark": "#F57C00"},       # Orange
        "Very Hard": {"light": "#F44336", "dark": "#D32F2F"}   # Red
    }
    
    # Color definitions for status indicators
    STATUS_COLORS = {
        "correct": {"light": "#4CAF50", "dark": "#388E3C"},       # Green
        "incorrect": {"light": "#F44336", "dark": "#D32F2F"},     # Red
        "unanswered": {"light": "#9E9E9E", "dark": "#757575"},    # Gray
        "in_progress": {"light": "#2196F3", "dark": "#1976D2"},   # Blue
        "completed": {"light": "#9C27B0", "dark": "#7B1FA2"}      # Purple
    }
    
    # Color definitions for action buttons
    ACTION_BUTTON_COLORS = {
        "view": {"light": "#2196F3", "dark": "#1976D2"},       # Blue
        "edit": {"light": "#FF9800", "dark": "#F57C00"},       # Orange
        "delete": {"light": "#F44336", "dark": "#D32F2F"},     # Red
        "add": {"light": "#4CAF50", "dark": "#388E3C"},        # Green
        "remove": {"light": "#F44336", "dark": "#D32F2F"}      # Red
    }
    
    def __init__(self):
        """Initialize the theme manager."""
        self.logger = logging.getLogger(__name__)
        self._current_theme = Theme.LIGHT
        self._current_font_size = 12
    
    def apply_theme(self, theme_name: str, font_size: int = 12) -> bool:
        """
        Apply a theme to the application.
        
        Args:
            theme_name: Name of the theme to apply ("light", "dark", or "system")
            font_size: Base font size for the application
            
        Returns:
            True if the theme was applied successfully, False otherwise
        """
        try:
            # Convert string to enum
            theme = None
            if theme_name.lower() == "light":
                theme = Theme.LIGHT
            elif theme_name.lower() == "dark":
                theme = Theme.DARK
            elif theme_name.lower() == "system":
                theme = Theme.SYSTEM
            else:
                self.logger.error(f"Unknown theme: {theme_name}")
                return False
            
            # Store current settings
            self._current_theme = theme
            self._current_font_size = font_size
            
            # Apply the selected theme
            if theme == Theme.LIGHT:
                self._apply_light_theme(font_size)
            elif theme == Theme.DARK:
                self._apply_dark_theme(font_size)
            elif theme == Theme.SYSTEM:
                # Use system preference if available, fallback to light
                self._apply_light_theme(font_size)  # System preference not implemented yet
            
            self.logger.info(f"Applied {theme_name} theme with font size {font_size}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying theme: {str(e)}")
            return False
    
    def _apply_light_theme(self, font_size: int) -> None:
        """
        Apply the light theme to the application.
        
        Args:
            font_size: Base font size for the application
        """
        app = QApplication.instance()
        if not app:
            self.logger.error("No QApplication instance available")
            return
        
        # Set palette
        palette = QPalette()
        # Background (window) color
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        # Window text color
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        # Base color (for text entry fields, lists etc.)
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        # Text color
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        # Button color
        palette.setColor(QPalette.ColorRole.Button, QColor(225, 225, 225))
        # Button text color
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        # Highlight color
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        # Highlighted text color
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        # Link color
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        # Link visited color
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(128, 0, 128))
        
        app.setPalette(palette)
        
        # Create and apply the stylesheet
        stylesheet = self._create_light_stylesheet(font_size)
        app.setStyleSheet(stylesheet)
    
    def _apply_dark_theme(self, font_size: int) -> None:
        """
        Apply the dark theme to the application.
        
        Args:
            font_size: Base font size for the application
        """
        app = QApplication.instance()
        if not app:
            self.logger.error("No QApplication instance available")
            return
        
        # Set palette
        palette = QPalette()
        # Background (window) color - dark gray
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        # Window text color - light gray
        palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
        # Base color (for text entry fields, lists etc.) - darker gray
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        # Text color - light gray
        palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
        # Button color - medium gray
        palette.setColor(QPalette.ColorRole.Button, QColor(70, 70, 70))
        # Button text color - light gray
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))
        # Highlight color - blue
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        # Highlighted text color - white
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        # Link color - light blue
        palette.setColor(QPalette.ColorRole.Link, QColor(102, 178, 255))
        # Link visited color - light purple
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(193, 147, 240))
        
        app.setPalette(palette)
        
        # Create and apply the stylesheet
        stylesheet = self._create_dark_stylesheet(font_size)
        app.setStyleSheet(stylesheet)
    
    def _create_light_stylesheet(self, font_size: int) -> str:
        """
        Create the light theme stylesheet.
        
        Args:
            font_size: Base font size for the application
            
        Returns:
            CSS stylesheet for the light theme
        """
        return f"""
            QWidget {{
                font-size: {font_size}px;
            }}
            
            QPushButton {{
                background-color: #e6e6e6;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px 15px;
            }}
            
            QPushButton:hover {{
                background-color: #d4d4d4;
            }}
            
            QPushButton:pressed {{
                background-color: #c0c0c0;
            }}
            
            /* Action button styling */
            QPushButton[class="view-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["view"]["light"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["view"]["light"]};
            }}
            
            QPushButton[class="edit-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["edit"]["light"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["edit"]["light"]};
            }}
            
            QPushButton[class="delete-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["delete"]["light"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["delete"]["light"]};
            }}
            
            QPushButton[class="add-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["add"]["light"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["add"]["light"]};
            }}
            
            QPushButton[class="remove-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["remove"]["light"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["remove"]["light"]};
            }}
            
            /* Status indicator styling */
            QLabel[class="status-correct"] {{
                color: {self.STATUS_COLORS["correct"]["light"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-incorrect"] {{
                color: {self.STATUS_COLORS["incorrect"]["light"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-unanswered"] {{
                color: {self.STATUS_COLORS["unanswered"]["light"]};
            }}
            
            QLabel[class="status-in-progress"] {{
                color: {self.STATUS_COLORS["in_progress"]["light"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-completed"] {{
                color: {self.STATUS_COLORS["completed"]["light"]};
                font-weight: bold;
            }}
            
            /* Difficulty label styling */
            QLabel[class="difficulty-easy"] {{
                color: {self.DIFFICULTY_COLORS["Easy"]["light"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Easy"]["light"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-medium"] {{
                color: {self.DIFFICULTY_COLORS["Medium"]["light"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Medium"]["light"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-hard"] {{
                color: {self.DIFFICULTY_COLORS["Hard"]["light"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Hard"]["light"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-very-hard"] {{
                color: {self.DIFFICULTY_COLORS["Very Hard"]["light"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Very Hard"]["light"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid #c0c0c0;
                border-top: 0px;
            }}
            
            QTabBar::tab {{
                background-color: #e6e6e6;
                border: 1px solid #c0c0c0;
                border-bottom: 0px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #d4d4d4;
            }}
            
            QTableView, QTreeView, QListView {{
                border: 1px solid #c0c0c0;
                background-color: #ffffff;
                alternate-background-color: #f6f6f6;
            }}
            
            QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
                background-color: #2a82da;
                color: #ffffff;
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 3px;
                background-color: #ffffff;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid #2a82da;
            }}
            
            QGroupBox {{
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 14px;
                height: 14px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: #2a82da;
                border: 1px solid #2a82da;
            }}
            
            QRadioButton::indicator:checked {{
                background-color: #2a82da;
                border: 1px solid #2a82da;
            }}
            
            QMenuBar {{
                background-color: #f0f0f0;
                border-bottom: 1px solid #c0c0c0;
            }}
            
            QMenuBar::item {{
                padding: 5px 10px;
                background: transparent;
            }}
            
            QMenuBar::item:selected {{
                background-color: #d4d4d4;
            }}
            
            QMenu {{
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
            }}
            
            QMenu::item {{
                padding: 5px 30px 5px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: #2a82da;
                color: #ffffff;
            }}
            
            QScrollBar:vertical {{
                background-color: #f0f0f0;
                width: 12px;
                margin: 10px 0px 10px 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: #f0f0f0;
                height: 12px;
                margin: 0px 10px 0px 10px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: #c0c0c0;
                min-width: 20px;
                border-radius: 3px;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            
            QStatusBar {{
                background-color: #f0f0f0;
                border-top: 1px solid #c0c0c0;
            }}
            
            /* Special styling for ResponseGridCell */
            QFrame[class="ResponseGridCell"] {{
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
            }}
            
            QFrame[class="ResponseGridCell-correct"] {{
                background-color: {self.STATUS_COLORS["correct"]["light"] + "20"};
                border: 1px solid {self.STATUS_COLORS["correct"]["light"]};
                border-radius: 5px;
                padding: 8px;
            }}
            
            QFrame[class="ResponseGridCell-incorrect"] {{
                background-color: {self.STATUS_COLORS["incorrect"]["light"] + "20"};
                border: 1px solid {self.STATUS_COLORS["incorrect"]["light"]};
                border-radius: 5px;
                padding: 8px;
            }}
            
            /* Question label styling */
            QLabel[class="question-label"] {{
                font-weight: bold;
                color: #333333;
            }}
        """
    
    def _create_dark_stylesheet(self, font_size: int) -> str:
        """
        Create the dark theme stylesheet.
        
        Args:
            font_size: Base font size for the application
            
        Returns:
            CSS stylesheet for the dark theme
        """
        return f"""
            QWidget {{
                font-size: {font_size}px;
                background-color: #353535;
                color: #e6e6e6;
            }}
            
            QPushButton {{
                background-color: #464646;
                border: 1px solid #222222;
                border-radius: 4px;
                padding: 5px 15px;
                color: #e6e6e6;
            }}
            
            QPushButton:hover {{
                background-color: #555555;
            }}
            
            QPushButton:pressed {{
                background-color: #666666;
            }}
            
            /* Action button styling */
            QPushButton[class="view-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["view"]["dark"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["view"]["dark"]};
            }}
            
            QPushButton[class="edit-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["edit"]["dark"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["edit"]["dark"]};
            }}
            
            QPushButton[class="delete-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["delete"]["dark"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["delete"]["dark"]};
            }}
            
            QPushButton[class="add-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["add"]["dark"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["add"]["dark"]};
            }}
            
            QPushButton[class="remove-button"] {{
                background-color: {self.ACTION_BUTTON_COLORS["remove"]["dark"]};
                color: white;
                border: 1px solid {self.ACTION_BUTTON_COLORS["remove"]["dark"]};
            }}
            
            /* Status indicator styling */
            QLabel[class="status-correct"] {{
                color: {self.STATUS_COLORS["correct"]["dark"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-incorrect"] {{
                color: {self.STATUS_COLORS["incorrect"]["dark"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-unanswered"] {{
                color: {self.STATUS_COLORS["unanswered"]["dark"]};
            }}
            
            QLabel[class="status-in-progress"] {{
                color: {self.STATUS_COLORS["in_progress"]["dark"]};
                font-weight: bold;
            }}
            
            QLabel[class="status-completed"] {{
                color: {self.STATUS_COLORS["completed"]["dark"]};
                font-weight: bold;
            }}
            
            /* Difficulty label styling */
            QLabel[class="difficulty-easy"] {{
                color: {self.DIFFICULTY_COLORS["Easy"]["dark"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Easy"]["dark"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-medium"] {{
                color: {self.DIFFICULTY_COLORS["Medium"]["dark"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Medium"]["dark"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-hard"] {{
                color: {self.DIFFICULTY_COLORS["Hard"]["dark"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Hard"]["dark"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QLabel[class="difficulty-very-hard"] {{
                color: {self.DIFFICULTY_COLORS["Very Hard"]["dark"]};
                font-weight: bold;
                background-color: {self.DIFFICULTY_COLORS["Very Hard"]["dark"] + "30"};
                border-radius: 4px;
                padding: 2px 5px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid #222222;
                border-top: 0px;
            }}
            
            QTabBar::tab {{
                background-color: #464646;
                border: 1px solid #222222;
                border-bottom: 0px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: #353535;
                border-bottom: 1px solid #353535;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #555555;
            }}
            
            QTableView, QTreeView, QListView {{
                border: 1px solid #222222;
                background-color: #232323;
                alternate-background-color: #2b2b2b;
            }}
            
            QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
                background-color: #2a82da;
                color: #ffffff;
            }}
            
            QHeaderView::section {{
                background-color: #464646;
                color: #e6e6e6;
                border: 1px solid #222222;
                padding: 4px;
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                border: 1px solid #222222;
                border-radius: 4px;
                padding: 3px;
                background-color: #232323;
                color: #e6e6e6;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid #2a82da;
            }}
            
            QGroupBox {{
                border: 1px solid #222222;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
            
            QCheckBox, QRadioButton {{
                color: #e6e6e6;
            }}
            
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 14px;
                height: 14px;
                background-color: #232323;
                border: 1px solid #222222;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: #2a82da;
                border: 1px solid #2a82da;
            }}
            
            QRadioButton::indicator:checked {{
                background-color: #2a82da;
                border: 1px solid #2a82da;
            }}
            
            QMenuBar {{
                background-color: #353535;
                border-bottom: 1px solid #222222;
            }}
            
            QMenuBar::item {{
                padding: 5px 10px;
                background: transparent;
            }}
            
            QMenuBar::item:selected {{
                background-color: #555555;
            }}
            
            QMenu {{
                background-color: #353535;
                border: 1px solid #222222;
            }}
            
            QMenu::item {{
                padding: 5px 30px 5px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: #2a82da;
                color: #ffffff;
            }}
            
            QScrollBar:vertical {{
                background-color: #353535;
                width: 12px;
                margin: 10px 0px 10px 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #555555;
                min-height: 20px;
                border-radius: 3px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: #353535;
                height: 12px;
                margin: 0px 10px 0px 10px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: #555555;
                min-width: 20px;
                border-radius: 3px;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
            
            QStatusBar {{
                background-color: #353535;
                border-top: 1px solid #222222;
            }}
            
            QComboBox {{
                background-color: #464646;
                border: 1px solid #222222;
                border-radius: 4px;
                padding: 3px;
                color: #e6e6e6;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #222222;
                border-left-style: solid;
            }}
            
            QComboBox QAbstractItemView {{
                border: 1px solid #222222;
                background-color: #353535;
                selection-background-color: #2a82da;
            }}
            
            /* Special styling for ResponseGridCell */
            QFrame[class="ResponseGridCell"] {{
                background-color: #2b2b2b;
                border: 1px solid #222222;
                border-radius: 5px;
                padding: 8px;
            }}
            
            QFrame[class="ResponseGridCell-correct"] {{
                background-color: {self.STATUS_COLORS["correct"]["dark"] + "20"};
                border: 1px solid {self.STATUS_COLORS["correct"]["dark"]};
                border-radius: 5px;
                padding: 8px;
            }}
            
            QFrame[class="ResponseGridCell-incorrect"] {{
                background-color: {self.STATUS_COLORS["incorrect"]["dark"] + "20"};
                border: 1px solid {self.STATUS_COLORS["incorrect"]["dark"]};
                border-radius: 5px;
                padding: 8px;
            }}
            
            /* Question label styling */
            QLabel[class="question-label"] {{
                font-weight: bold;
                color: #e0e0e0;
            }}
        """
    
    def get_current_theme(self) -> Theme:
        """
        Get the currently applied theme.
        
        Returns:
            The current theme enum value
        """
        return self._current_theme
    
    def get_current_font_size(self) -> int:
        """
        Get the currently applied font size.
        
        Returns:
            The current font size
        """
        return self._current_font_size