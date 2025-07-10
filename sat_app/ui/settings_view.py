"""
Settings view for the SAT Question Bank application.
Provides a UI for configuring application settings.
"""
import os
import logging
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QFormLayout, QFileDialog,
    QMessageBox, QGroupBox, QScrollArea, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from sat_app.business.settings_manager import SettingsManager


class SettingsView(QWidget):
    """
    Settings view widget.
    
    Provides a UI for viewing and modifying application settings.
    """
    
    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()
    
    def __init__(self, settings_manager: SettingsManager):
        """
        Initialize the settings view.
        
        Args:
            settings_manager: The application settings manager
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different settings categories
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs for different setting categories
        self._create_ui_settings_tab()
        self._create_directories_settings_tab()
        
        # Buttons for saving or resetting settings
        button_layout = QHBoxLayout()
        
        # Reset button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        # Spacer
        button_layout.addStretch()
        
        # Apply button
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self._apply_changes)
        button_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(button_layout)
    
    def _create_ui_settings_tab(self):
        """Create the UI settings tab."""
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # Get current UI settings
        ui_settings = self.settings_manager.get_ui_settings()
        
        # UI settings form
        form_layout = QFormLayout()
        
        # Theme selector
        self.theme_combo = QComboBox()
        for theme in self.settings_manager.get_available_themes():
            self.theme_combo.addItem(theme.capitalize())
        
        # Set current theme
        current_theme = ui_settings.get("theme", "light")
        self.theme_combo.setCurrentText(current_theme.capitalize())
        
        form_layout.addRow("Theme:", self.theme_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSingleStep(1)
        
        # Set current font size
        current_font_size = ui_settings.get("font_size", 12)
        self.font_size_spin.setValue(current_font_size)
        
        form_layout.addRow("Font Size:", self.font_size_spin)
        
        # Window size settings - Remember and restore window size
        self.remember_window_size = QCheckBox("Remember window size and position")
        self.remember_window_size.setChecked(ui_settings.get("remember_window_size", False))
        form_layout.addRow("", self.remember_window_size)
        
        # Add form to layout
        ui_layout.addLayout(form_layout)
        
        # Add optional UI settings for future expansion
        ui_layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(ui_tab, "User Interface")
    
    def _create_directories_settings_tab(self):
        """Create the directories settings tab."""
        directories_tab = QWidget()
        directories_layout = QVBoxLayout(directories_tab)
        
        # Get current directory settings
        database_settings = self.settings_manager.get_database_settings()
        image_settings = self.settings_manager.get_image_settings()
        output_settings = self.settings_manager.get_output_settings()
        
        # Create a scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Database settings group
        db_group = QGroupBox("Database")
        db_layout = QFormLayout(db_group)
        
        # Database path
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(database_settings.get("path", ""))
        self.db_path_edit.setReadOnly(True)  # Read-only to prevent typos
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        
        db_browse_button = QPushButton("Browse...")
        db_browse_button.clicked.connect(lambda: self._browse_file_path(self.db_path_edit, "Database File (*.db)"))
        db_path_layout.addWidget(db_browse_button)
        
        db_layout.addRow("Database Path:", db_path_layout)
        
        scroll_layout.addWidget(db_group)
        
        # Image directories group
        img_group = QGroupBox("Images")
        img_layout = QFormLayout(img_group)
        
        # Question images directory
        self.question_img_dir_edit = QLineEdit()
        self.question_img_dir_edit.setText(image_settings.get("question_images_dir", ""))
        self.question_img_dir_edit.setReadOnly(True)
        
        q_img_dir_layout = QHBoxLayout()
        q_img_dir_layout.addWidget(self.question_img_dir_edit)
        
        q_img_browse_button = QPushButton("Browse...")
        q_img_browse_button.clicked.connect(lambda: self._browse_directory_path(self.question_img_dir_edit, "Question Images Directory"))
        q_img_dir_layout.addWidget(q_img_browse_button)
        
        img_layout.addRow("Question Images:", q_img_dir_layout)
        
        # Answer images directory
        self.answer_img_dir_edit = QLineEdit()
        self.answer_img_dir_edit.setText(image_settings.get("answer_images_dir", ""))
        self.answer_img_dir_edit.setReadOnly(True)
        
        a_img_dir_layout = QHBoxLayout()
        a_img_dir_layout.addWidget(self.answer_img_dir_edit)
        
        a_img_browse_button = QPushButton("Browse...")
        a_img_browse_button.clicked.connect(lambda: self._browse_directory_path(self.answer_img_dir_edit, "Answer Images Directory"))
        a_img_dir_layout.addWidget(a_img_browse_button)
        
        img_layout.addRow("Answer Images:", a_img_dir_layout)
        
        scroll_layout.addWidget(img_group)
        
        # Output directories group
        output_group = QGroupBox("Output")
        output_layout = QFormLayout(output_group)
        
        # Worksheets directory
        self.worksheets_dir_edit = QLineEdit()
        self.worksheets_dir_edit.setText(output_settings.get("worksheets_dir", ""))
        self.worksheets_dir_edit.setReadOnly(True)
        
        ws_dir_layout = QHBoxLayout()
        ws_dir_layout.addWidget(self.worksheets_dir_edit)
        
        ws_browse_button = QPushButton("Browse...")
        ws_browse_button.clicked.connect(lambda: self._browse_directory_path(self.worksheets_dir_edit, "Worksheets Directory"))
        ws_dir_layout.addWidget(ws_browse_button)
        
        output_layout.addRow("Worksheets:", ws_dir_layout)
        
        scroll_layout.addWidget(output_group)
        
        # Add spacer
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        directories_layout.addWidget(scroll_area)
        
        # Add tab
        self.tab_widget.addTab(directories_tab, "Directories")
    
    def _browse_directory_path(self, line_edit: QLineEdit, title: str):
        """
        Open a directory browser dialog and update a line edit with the selected path.
        
        Args:
            line_edit: The line edit to update
            title: Dialog title
        """
        current_path = line_edit.text()
        initial_dir = current_path if os.path.exists(current_path) else ""
        
        directory = QFileDialog.getExistingDirectory(
            self, title, initial_dir, 
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if directory:
            line_edit.setText(directory)
    
    def _browse_file_path(self, line_edit: QLineEdit, filter_str: str):
        """
        Open a file browser dialog and update a line edit with the selected path.
        
        Args:
            line_edit: The line edit to update
            filter_str: File filter string
        """
        current_path = line_edit.text()
        initial_dir = os.path.dirname(current_path) if os.path.exists(os.path.dirname(current_path)) else ""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Database File", initial_dir, filter_str
        )
        
        if file_path:
            line_edit.setText(file_path)
    
    def _apply_changes(self):
        """Apply the settings changes."""
        try:
            # UI settings
            theme = self.theme_combo.currentText().lower()
            font_size = self.font_size_spin.value()
            remember_window_size = self.remember_window_size.isChecked()
            
            self.settings_manager.update_setting("ui", "theme", theme)
            self.settings_manager.update_setting("ui", "font_size", font_size)
            self.settings_manager.update_setting("ui", "remember_window_size", remember_window_size)
            
            # Database settings
            db_path = self.db_path_edit.text()
            if db_path:
                self.settings_manager.update_setting("database", "path", db_path)
            
            # Image directory settings
            q_img_dir = self.question_img_dir_edit.text()
            if q_img_dir:
                self.settings_manager.update_setting("images", "question_images_dir", q_img_dir)
                
            a_img_dir = self.answer_img_dir_edit.text()
            if a_img_dir:
                self.settings_manager.update_setting("images", "answer_images_dir", a_img_dir)
            
            # Output directory settings
            ws_dir = self.worksheets_dir_edit.text()
            if ws_dir:
                self.settings_manager.update_setting("output", "worksheets_dir", ws_dir)
            
            # Emit settings updated signal
            self.settings_updated.emit()
            
            # Show success message
            QMessageBox.information(self, "Settings Updated", 
                                   "Settings have been updated successfully.\n\n"
                                   "Some changes may require a restart to take effect.")
            
            self.logger.info("Settings updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying settings changes: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error applying settings: {str(e)}")
    
    def _reset_to_defaults(self):
        """Reset settings to defaults."""
        # Confirm with user
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to default values?\n\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Reset settings
                if self.settings_manager.reset_to_defaults():
                    # Reload the UI with default values
                    self._reload_settings()
                    
                    # Emit settings updated signal
                    self.settings_updated.emit()
                    
                    # Show success message
                    QMessageBox.information(self, "Settings Reset", 
                                          "Settings have been reset to default values.")
                    
                    self.logger.info("Settings reset to defaults")
                else:
                    QMessageBox.warning(self, "Warning", 
                                      "Failed to reset settings to defaults.")
            except Exception as e:
                self.logger.error(f"Error resetting settings: {str(e)}")
                QMessageBox.critical(self, "Error", f"Error resetting settings: {str(e)}")
    
    def _reload_settings(self):
        """Reload settings values in the UI."""
        # Get current settings
        ui_settings = self.settings_manager.get_ui_settings()
        database_settings = self.settings_manager.get_database_settings()
        image_settings = self.settings_manager.get_image_settings()
        output_settings = self.settings_manager.get_output_settings()
        
        # Update UI settings controls
        current_theme = ui_settings.get("theme", "light")
        self.theme_combo.setCurrentText(current_theme.capitalize())
        
        current_font_size = ui_settings.get("font_size", 12)
        self.font_size_spin.setValue(current_font_size)
        
        # Update directory settings controls
        self.db_path_edit.setText(database_settings.get("path", ""))
        self.question_img_dir_edit.setText(image_settings.get("question_images_dir", ""))
        self.answer_img_dir_edit.setText(image_settings.get("answer_images_dir", ""))
        self.worksheets_dir_edit.setText(output_settings.get("worksheets_dir", ""))
        
    def showEvent(self, event):
        """
        Handle show event.
        
        Reload settings when the view becomes visible.
        
        Args:
            event: Show event
        """
        self._reload_settings()
        super().showEvent(event)