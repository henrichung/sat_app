"""
User interface for importing and exporting questions.

This module contains the ImportExportView class for importing and exporting
questions in JSON format.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QProgressBar, QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
    QComboBox, QLineEdit, QScrollArea, QFormLayout, QGridLayout,
    QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from sat_app.business.import_export_manager import ImportExportManager
from sat_app.business.question_manager import QuestionManager
from sat_app.utils.logger import get_logger


class ImportExportView(QWidget):
    """
    User interface for importing and exporting questions.
    
    Provides a tabbed interface for:
    - Importing questions from a JSON file
    - Exporting questions to a JSON file
    """
    
    # Define signals
    import_completed = pyqtSignal(bool, str, dict)
    export_completed = pyqtSignal(bool, str)
    
    def __init__(self, import_export_manager: ImportExportManager, 
                 question_manager: QuestionManager):
        """
        Initialize the ImportExportView.
        
        Args:
            import_export_manager: Manager for import/export operations
            question_manager: Manager for question operations
        """
        super().__init__()
        
        self.logger = get_logger(__name__)
        self.import_export_manager = import_export_manager
        self.question_manager = question_manager
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._setup_import_tab()
        self._setup_export_tab()
    
    def _setup_import_tab(self):
        """Set up the Import tab."""
        import_tab = QWidget()
        layout = QVBoxLayout(import_tab)
        
        # File selection group
        file_group = QGroupBox("Select JSON File to Import")
        file_layout = QHBoxLayout(file_group)
        
        self.import_path_edit = QLineEdit()
        self.import_path_edit.setReadOnly(True)
        self.import_path_edit.setPlaceholderText("Select a JSON file...")
        file_layout.addWidget(self.import_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_import_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # Options group
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout(options_group)
        
        self.import_images_check = QCheckBox("Import associated images")
        self.import_images_check.setChecked(True)
        options_layout.addWidget(self.import_images_check)
        
        layout.addWidget(options_group)
        
        # Progress group
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.import_progress_bar = QProgressBar()
        self.import_progress_bar.setRange(0, 100)
        self.import_progress_bar.setValue(0)
        progress_layout.addWidget(self.import_progress_bar)
        
        self.import_status_label = QLabel("Ready to import")
        progress_layout.addWidget(self.import_status_label)
        
        layout.addWidget(progress_group)
        
        # Results area
        results_group = QGroupBox("Import Results")
        results_layout = QVBoxLayout(results_group)
        
        self.import_results_table = QTableWidget(0, 2)
        self.import_results_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.import_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.import_results_table)
        
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.import_button = QPushButton("Import Questions")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self._import_questions)
        button_layout.addWidget(self.import_button)
        
        layout.addLayout(button_layout)
        
        # Add the tab
        self.tab_widget.addTab(import_tab, "Import")
    
    def _setup_export_tab(self):
        """Set up the Export tab."""
        export_tab = QWidget()
        layout = QVBoxLayout(export_tab)
        
        # Export selection group
        selection_group = QGroupBox("Select Questions to Export")
        selection_layout = QVBoxLayout(selection_group)
        
        # Radio buttons for selection mode
        self.export_all_radio = QRadioButton("Export all questions")
        self.export_all_radio.setChecked(True)
        selection_layout.addWidget(self.export_all_radio)
        
        self.export_filtered_radio = QRadioButton("Export filtered questions")
        selection_layout.addWidget(self.export_filtered_radio)
        
        # Button group for radio buttons
        self.export_selection_group = QButtonGroup()
        self.export_selection_group.addButton(self.export_all_radio)
        self.export_selection_group.addButton(self.export_filtered_radio)
        
        # Filter options (initially disabled)
        filter_layout = QGridLayout()
        
        filter_layout.addWidget(QLabel("Subject:"), 0, 0)
        self.subject_filter = QComboBox()
        self.subject_filter.setEnabled(False)
        self.subject_filter.addItems(["Any", "Math", "Reading", "Writing"])
        filter_layout.addWidget(self.subject_filter, 0, 1)
        
        filter_layout.addWidget(QLabel("Difficulty:"), 1, 0)
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.setEnabled(False)
        self.difficulty_filter.addItems(["Any", "Easy", "Medium", "Hard"])
        filter_layout.addWidget(self.difficulty_filter, 1, 1)
        
        selection_layout.addLayout(filter_layout)
        
        # Connect radio buttons to filter controls
        self.export_all_radio.toggled.connect(self._update_filter_controls)
        
        layout.addWidget(selection_group)
        
        # File selection group
        file_group = QGroupBox("Export Destination")
        file_layout = QHBoxLayout(file_group)
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setReadOnly(True)
        self.export_path_edit.setPlaceholderText("Select destination file...")
        file_layout.addWidget(self.export_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_export_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # Options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.export_images_check = QCheckBox("Include images in export")
        self.export_images_check.setChecked(True)
        options_layout.addWidget(self.export_images_check)
        
        layout.addWidget(options_group)
        
        # Status
        self.export_status_label = QLabel("Ready to export")
        layout.addWidget(self.export_status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.export_button = QPushButton("Export Questions")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._export_questions)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Add the tab
        self.tab_widget.addTab(export_tab, "Export")
    
    def _browse_import_file(self):
        """Open a file dialog to select a JSON file for import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.import_path_edit.setText(file_path)
            self.import_button.setEnabled(True)
    
    def _browse_export_file(self):
        """Open a file dialog to select a destination for export."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Ensure it has .json extension
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            
            self.export_path_edit.setText(file_path)
            self.export_button.setEnabled(True)
    
    def _update_filter_controls(self):
        """Update filter control enabled states based on selection mode."""
        filter_enabled = self.export_filtered_radio.isChecked()
        self.subject_filter.setEnabled(filter_enabled)
        self.difficulty_filter.setEnabled(filter_enabled)
    
    def _import_questions(self):
        """Import questions from the selected file."""
        import_path = self.import_path_edit.text()
        if not import_path or not os.path.exists(import_path):
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select a valid JSON file to import."
            )
            return
        
        # Update UI for import in progress
        self.import_status_label.setText("Importing questions...")
        self.import_progress_bar.setValue(25)
        self.import_button.setEnabled(False)
        
        # Import questions
        import_images = self.import_images_check.isChecked()
        success, message, stats = self.import_export_manager.import_questions(
            import_path, import_images
        )
        
        # Update progress
        self.import_progress_bar.setValue(100)
        
        # Update status
        if success:
            self.import_status_label.setText(message)
            self._show_import_results(stats)
        else:
            self.import_status_label.setText(f"Error: {message}")
        
        # Re-enable import button
        self.import_button.setEnabled(True)
        
        # Emit completion signal
        self.import_completed.emit(success, message, stats)
    
    def _show_import_results(self, stats: Dict[str, int]):
        """
        Display import results in the table.
        
        Args:
            stats: Dictionary of import statistics
        """
        # Clear existing data
        self.import_results_table.clearContents()
        self.import_results_table.setRowCount(0)
        
        # Add stats to the table
        for i, (key, value) in enumerate(stats.items()):
            self.import_results_table.insertRow(i)
            self.import_results_table.setItem(i, 0, QTableWidgetItem(key.capitalize()))
            self.import_results_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def _export_questions(self):
        """Export questions to the selected file."""
        export_path = self.export_path_edit.text()
        if not export_path:
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select a destination file for export."
            )
            return
        
        # Update UI for export in progress
        self.export_status_label.setText("Exporting questions...")
        self.export_button.setEnabled(False)
        
        # Determine export mode
        export_all = self.export_all_radio.isChecked()
        include_images = self.export_images_check.isChecked()
        
        try:
            if export_all:
                # Export all questions
                success, message = self.import_export_manager.export_all_questions(
                    export_path, include_images
                )
            else:
                # Export filtered questions
                filters = {}
                
                # Add subject filter if not "Any"
                subject = self.subject_filter.currentText()
                if subject != "Any":
                    filters["subject_tags"] = subject
                
                # Add difficulty filter if not "Any"
                difficulty = self.difficulty_filter.currentText()
                if difficulty != "Any":
                    filters["difficulty_label"] = difficulty
                
                success, message = self.import_export_manager.export_filtered_questions(
                    filters, export_path, include_images
                )
            
            # Update status
            self.export_status_label.setText(message)
            
            # Show success or error message
            if success:
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Questions have been exported successfully.\n{message}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    f"Error during export: {message}"
                )
        
        except Exception as e:
            error_msg = f"Error during export: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.export_status_label.setText(error_msg)
            
            QMessageBox.critical(
                self,
                "Export Error",
                error_msg
            )
        
        # Re-enable export button
        self.export_button.setEnabled(True)
        
        # Emit completion signal
        self.export_completed.emit(success if 'success' in locals() else False, 
                                   message if 'message' in locals() else str(e))
    
    def populate_subject_tags(self):
        """Populate the subject tags combo box with available tags."""
        try:
            # Get all questions to extract unique tags
            questions = self.question_manager.get_all_questions()
            
            # Extract unique tags
            all_tags = set()
            for question in questions:
                for tag in question.subject_tags:
                    all_tags.add(tag)
            
            # Sort tags alphabetically
            sorted_tags = sorted(list(all_tags))
            
            # Clear and populate combo box
            self.subject_filter.clear()
            self.subject_filter.addItem("Any")
            self.subject_filter.addItems(sorted_tags)
            
        except Exception as e:
            self.logger.error(f"Error populating subject tags: {str(e)}")
    
    def populate_difficulty_levels(self):
        """Populate the difficulty combo box with available levels."""
        try:
            # Get all questions to extract unique difficulty levels
            questions = self.question_manager.get_all_questions()
            
            # Extract unique difficulty levels
            difficulty_levels = set()
            for question in questions:
                if question.difficulty_label:
                    difficulty_levels.add(question.difficulty_label)
            
            # Sort difficulty levels
            sorted_levels = sorted(list(difficulty_levels))
            
            # Clear and populate combo box
            self.difficulty_filter.clear()
            self.difficulty_filter.addItem("Any")
            self.difficulty_filter.addItems(sorted_levels)
            
        except Exception as e:
            self.logger.error(f"Error populating difficulty levels: {str(e)}")