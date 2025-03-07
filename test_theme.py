#!/usr/bin/env python3
"""
Test script for the theme implementation.
This allows for easily seeing theme changes without running the full application.
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit,
    QTextEdit, QCheckBox, QRadioButton, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QListWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from sat_app.ui.theme_manager import ThemeManager

class ThemeTestWindow(QMainWindow):
    """Test window for theme demonstration."""
    
    def __init__(self):
        """Initialize the test window."""
        super().__init__()
        
        self.setWindowTitle("Theme Test")
        self.resize(800, 600)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create theme selection controls
        self._create_theme_controls()
        
        # Create UI components for testing
        self._create_test_components()
        
        # Apply initial light theme
        self.theme_manager.apply_theme("light", 12)
        
    def _create_theme_controls(self):
        """Create controls for switching themes."""
        controls_layout = QVBoxLayout()
        
        # Theme selection
        theme_group = QGroupBox("Theme Selection")
        theme_form = QFormLayout()
        
        # Theme combo
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        self.theme_combo.setCurrentText("Light")
        theme_form.addRow("Theme:", self.theme_combo)
        
        # Font size spinner
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        theme_form.addRow("Font Size:", self.font_size_spin)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Theme")
        self.apply_btn.clicked.connect(self._apply_selected_theme)
        theme_form.addRow("", self.apply_btn)
        
        theme_group.setLayout(theme_form)
        controls_layout.addWidget(theme_group)
        self.main_layout.addLayout(controls_layout)
        
    def _create_test_components(self):
        """Create various UI components to showcase the theme."""
        # Create a tab widget
        self.tab_widget = QTabWidget()
        
        # Basic controls tab
        controls_tab = QWidget()
        controls_layout = QVBoxLayout(controls_tab)
        
        # Add various controls
        controls_layout.addWidget(QLabel("Standard Label"))
        
        bold_label = QLabel("Bold Label")
        font = bold_label.font()
        font.setBold(True)
        bold_label.setFont(font)
        controls_layout.addWidget(bold_label)
        
        controls_layout.addWidget(QPushButton("Standard Button"))
        controls_layout.addWidget(QLineEdit("Line Edit Text"))
        controls_layout.addWidget(QTextEdit("Text Edit\nMultiple lines\nof text"))
        
        checkbox_group = QGroupBox("Checkboxes")
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(QCheckBox("Checkbox 1"))
        checkbox_layout.addWidget(QCheckBox("Checkbox 2"))
        checkbox_group.setLayout(checkbox_layout)
        controls_layout.addWidget(checkbox_group)
        
        radio_group = QGroupBox("Radio Buttons")
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(QRadioButton("Option 1"))
        radio_layout.addWidget(QRadioButton("Option 2"))
        radio_group.setLayout(radio_layout)
        controls_layout.addWidget(radio_group)
        
        # Add tab
        self.tab_widget.addTab(controls_tab, "Controls")
        
        # Data view tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        # Create a table
        table = QTableWidget(5, 3)
        table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        
        # Add some data
        for row in range(5):
            for col in range(3):
                table.setItem(row, col, QTableWidgetItem(f"Item {row},{col}"))
        
        data_layout.addWidget(table)
        
        # Create a list
        list_widget = QListWidget()
        list_widget.addItems([f"List Item {i}" for i in range(1, 11)])
        data_layout.addWidget(list_widget)
        
        # Add tab
        self.tab_widget.addTab(data_tab, "Data Views")
        
        # Special components tab
        special_tab = QWidget()
        special_layout = QVBoxLayout(special_tab)
        
        # Create a component that mimics ResponseGridCell
        cell_frame = QWidget()
        cell_frame.setProperty("class", "ResponseGridCell")
        cell_layout = QVBoxLayout(cell_frame)
        
        # Add question label
        question_label = QLabel("This is a sample question with styling applied through the theme system?")
        question_label.setWordWrap(True)
        question_label.setProperty("class", "question-label")
        cell_layout.addWidget(question_label)
        
        # Add radio buttons
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(QRadioButton("Correct"))
        radio_layout.addWidget(QRadioButton("Incorrect"))
        radio_layout.addWidget(QRadioButton("No Answer"))
        cell_layout.addLayout(radio_layout)
        
        special_layout.addWidget(cell_frame)
        
        # Add other special components here
        
        # Add tab
        self.tab_widget.addTab(special_tab, "Special Components")
        
        # Add the tab widget to the main layout
        self.main_layout.addWidget(self.tab_widget)
        
    def _apply_selected_theme(self):
        """Apply the selected theme."""
        theme_name = self.theme_combo.currentText().lower()
        font_size = self.font_size_spin.value()
        
        # Apply the theme
        self.theme_manager.apply_theme(theme_name, font_size)

def main():
    """Run the theme test application."""
    app = QApplication(sys.argv)
    window = ThemeTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()