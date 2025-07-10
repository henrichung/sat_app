"""
Student response interface for the SAT Question Bank application.
Provides functionality for recording student responses to worksheets.
"""
import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QSplitter, QTabWidget, QGroupBox, QLineEdit, QRadioButton,
    QButtonGroup, QScrollArea, QFrame, QCheckBox, QHeaderView,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap

from sat_app.business.scorer import ScoringService
from sat_app.ui.components.response_grid import ResponseGrid


class StudentResponseView(QWidget):
    """
    Main view for recording student responses to worksheets.
    
    Provides a tabbed interface for selecting students and worksheets,
    and recording responses to questions.
    """
    
    # Signals
    responses_saved = pyqtSignal(str, int)  # student_id, worksheet_id
    
    def __init__(self, scoring_service: ScoringService, parent=None):
        """
        Initialize the StudentResponseView.
        
        Args:
            scoring_service: Service for recording and analyzing scores
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.scoring_service = scoring_service
        
        # Data storage
        self.current_student_id = ""
        self.current_worksheet_id = 0
        self.questions = []
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._load_worksheets()
        self._load_students()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Selection Tab
        selection_tab = QWidget()
        selection_layout = QVBoxLayout(selection_tab)
        
        # Student Selection
        student_group = QGroupBox("Student Selection")
        student_layout = QVBoxLayout(student_group)
        
        student_entry_layout = QHBoxLayout()
        student_entry_layout.addWidget(QLabel("Student ID:"))
        
        self.student_combo = QComboBox()
        self.student_combo.setEditable(True)
        self.student_combo.currentTextChanged.connect(self._student_selected)
        student_entry_layout.addWidget(self.student_combo)
        
        student_layout.addLayout(student_entry_layout)
        selection_layout.addWidget(student_group)
        
        # Worksheet Selection
        worksheet_group = QGroupBox("Worksheet Selection")
        worksheet_layout = QVBoxLayout(worksheet_group)
        
        worksheet_selection_layout = QHBoxLayout()
        worksheet_selection_layout.addWidget(QLabel("Worksheet:"))
        
        self.worksheet_combo = QComboBox()
        self.worksheet_combo.currentIndexChanged.connect(self._worksheet_selected)
        worksheet_selection_layout.addWidget(self.worksheet_combo)
        
        worksheet_layout.addLayout(worksheet_selection_layout)
        
        # Worksheet info
        self.worksheet_info_label = QLabel("No worksheet selected")
        worksheet_layout.addWidget(self.worksheet_info_label)
        
        selection_layout.addWidget(worksheet_group)
        
        # Load button
        self.load_btn = QPushButton("Load Questions")
        self.load_btn.clicked.connect(self._load_questions)
        self.load_btn.setEnabled(False)
        selection_layout.addWidget(self.load_btn)
        
        # Add stretch to push everything to the top
        selection_layout.addStretch()
        
        # Response Tab
        response_tab = QWidget()
        response_layout = QVBoxLayout(response_tab)
        
        # Response status
        self.response_status_label = QLabel("No worksheet loaded")
        response_layout.addWidget(self.response_status_label)
        
        # Response grid
        self.response_grid = ResponseGrid()
        response_layout.addWidget(self.response_grid)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Responses")
        self.save_btn.clicked.connect(self._save_responses)
        self.save_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("Clear All Responses")
        self.clear_btn.clicked.connect(self._clear_all_responses)
        self.clear_btn.setEnabled(False)
        
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.clear_btn)
        
        response_layout.addLayout(action_layout)
        
        # Add tabs
        self.tab_widget.addTab(selection_tab, "Selection")
        self.tab_widget.addTab(response_tab, "Responses")
        self.tab_widget.setTabEnabled(1, False)  # Disable Responses tab until questions are loaded
        
        main_layout.addWidget(self.tab_widget)
    
    def _load_students(self):
        """Load available students."""
        try:
            students = self.scoring_service.get_all_students()
            
            # Save current selection
            current_text = self.student_combo.currentText()
            
            # Update the combobox
            self.student_combo.clear()
            
            # Add all students
            for student_id in students:
                self.student_combo.addItem(student_id)
            
            # Restore selection if possible
            if current_text and self.student_combo.findText(current_text) >= 0:
                self.student_combo.setCurrentText(current_text)
            
        except Exception as e:
            self.logger.error(f"Error loading students: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading students: {str(e)}")
    
    def _load_worksheets(self):
        """Load available worksheets."""
        try:
            worksheets = self.scoring_service.get_available_worksheets()
            
            self.worksheet_combo.clear()
            self.worksheet_combo.addItem("-- Select Worksheet --", 0)
            
            for worksheet in worksheets:
                # Display title and question count
                self.worksheet_combo.addItem(
                    f"{worksheet['title']} ({worksheet['question_count']} questions)",
                    worksheet['id']
                )
            
        except Exception as e:
            self.logger.error(f"Error loading worksheets: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading worksheets: {str(e)}")
    
    def _student_selected(self, student_id: str):
        """
        Handle student selection.
        
        Args:
            student_id: ID of the selected student
        """
        self.current_student_id = student_id.strip()
        
        # Enable/disable the load button based on selections
        self.load_btn.setEnabled(
            bool(self.current_student_id) and self.current_worksheet_id > 0
        )
    
    def _worksheet_selected(self, index: int):
        """
        Handle worksheet selection.
        
        Args:
            index: Index of the selected worksheet
        """
        # Get the worksheet ID from the combo box
        self.current_worksheet_id = self.worksheet_combo.currentData()
        
        # Update the worksheet info
        if self.current_worksheet_id:
            # Find the worksheet in the available worksheets
            worksheets = self.scoring_service.get_available_worksheets()
            for worksheet in worksheets:
                if worksheet['id'] == self.current_worksheet_id:
                    self.worksheet_info_label.setText(
                        f"Title: {worksheet['title']}\n"
                        f"Description: {worksheet['description']}\n"
                        f"Questions: {worksheet['question_count']}"
                    )
                    break
        else:
            self.worksheet_info_label.setText("No worksheet selected")
        
        # Enable/disable the load button based on selections
        self.load_btn.setEnabled(
            bool(self.current_student_id) and self.current_worksheet_id > 0
        )
    
    def _load_questions(self):
        """Load questions for the selected worksheet."""
        if not self.current_worksheet_id or not self.current_student_id:
            QMessageBox.warning(self, "Warning", "Please select both a student and a worksheet")
            return
        
        try:
            # Get worksheet status to see if student has already provided responses
            status = self.scoring_service.get_student_worksheet_status(
                self.current_student_id, 
                self.current_worksheet_id
            )
            
            if not status.get('success', False):
                QMessageBox.critical(self, "Error", f"Error loading worksheet: {status.get('error', 'Unknown error')}")
                return
            
            # Load questions
            self.questions = self.scoring_service.get_questions_for_worksheet(self.current_worksheet_id)
            
            if not self.questions:
                QMessageBox.information(self, "Information", "No questions available for this worksheet")
                return
            
            # Update status label
            if status['answered_count'] > 0:
                self.response_status_label.setText(
                    f"Student: {self.current_student_id} | "
                    f"Worksheet: {status['worksheet_title']} | "
                    f"Responses: {status['answered_count']}/{status['total_questions']} | "
                    f"Correct: {status['correct_count']}/{status['answered_count']}"
                )
            else:
                self.response_status_label.setText(
                    f"Student: {self.current_student_id} | "
                    f"Worksheet: {status['worksheet_title']} | "
                    f"No responses recorded yet"
                )
            
            # Load questions into the response grid
            self.response_grid.set_questions(self.questions)
            
            # If there are existing responses, load them
            if status['answered_count'] > 0:
                # Convert the answered_questions list to the new response format for the grid
                existing_responses = {}
                for q in status['answered_questions']:
                    question_type = next((question.get('question_type', 'multiple_choice') 
                                        for question in self.questions if question['id'] == q['id']), 
                                       'multiple_choice')
                    
                    if question_type == 'free_response':
                        # For free response, we need to get the actual student answer
                        # For now, use empty string as placeholder - this will be enhanced
                        # when we add the StudentResponse repository
                        existing_responses[q['id']] = {
                            'student_answer': '',  # TODO: Load actual student answer
                            'is_correct': q['correct']
                        }
                    else:
                        # For multiple choice, just convert boolean to new format
                        existing_responses[q['id']] = {
                            'is_correct': q['correct']
                        }
                
                self.response_grid.set_responses(existing_responses)
            
            # Enable the responses tab and switch to it
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
            
            # Enable action buttons
            self.save_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Error loading questions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading questions: {str(e)}")
    
    def _save_responses(self):
        """Save the current responses."""
        if not self.current_student_id or not self.current_worksheet_id:
            QMessageBox.warning(self, "Warning", "Student ID and worksheet must be selected")
            return
        
        responses = self.response_grid.get_responses()
        
        if not responses:
            QMessageBox.warning(self, "Warning", "No responses to save")
            return
        
        try:
            # Convert new response format to old format for backward compatibility
            # TODO: Update ScoringService to handle StudentResponse model
            old_format_responses = {}
            for question_id, response_data in responses.items():
                # Extract the is_correct value for the old scoring system
                old_format_responses[question_id] = response_data.get('is_correct')
            
            # Save the responses (using old format for now)
            result = self.scoring_service.record_bulk_answers(
                self.current_student_id,
                self.current_worksheet_id,
                old_format_responses
            )
            
            # TODO: Also save student answers to StudentResponse table for free response questions
            # This would require adding a new method to save actual student responses
            
            if result.get('success', False):
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Saved {result['success_count']} responses successfully."
                )
                
                # Emit the responses_saved signal
                self.responses_saved.emit(self.current_student_id, self.current_worksheet_id)
                
                # Update the status
                self._load_questions()
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Error saving responses: {result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            self.logger.error(f"Error saving responses: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving responses: {str(e)}")
    
    def _clear_all_responses(self):
        """Clear all responses for the current student and worksheet."""
        if not self.current_student_id or not self.current_worksheet_id:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            f"Are you sure you want to clear all responses for student {self.current_student_id} on this worksheet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.scoring_service.clear_student_worksheet_responses(
                    self.current_student_id,
                    self.current_worksheet_id
                )
                
                if result.get('success', False):
                    QMessageBox.information(self, "Success", "All responses cleared successfully")
                    
                    # Clear the grid
                    self.response_grid.set_responses({})
                    
                    # Update the status
                    self._load_questions()
                else:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Error clearing responses: {result.get('error', 'Unknown error')}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error clearing responses: {str(e)}")
                QMessageBox.critical(self, "Error", f"Error clearing responses: {str(e)}")