"""
Reusable grid component for answer selection.
Provides a grid-based interface for recording student responses.
"""
import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QGridLayout, QSpacerItem, QSizePolicy, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ResponseGridCell(QFrame):
    """
    Individual cell for the response grid.
    
    Displays question information and provides appropriate input controls
    based on question type (radio buttons for MC, text input for free response).
    """
    
    response_changed = pyqtSignal(int, object)  # question_id, response_data
    
    def __init__(self, question: Dict[str, Any], parent=None):
        """
        Initialize the ResponseGridCell.
        
        Args:
            question: Question data dictionary containing question_type field
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.question = question
        self.question_id = question["id"]
        self.question_type = question.get("question_type", "multiple_choice")
        
        # UI components (will be created in _setup_ui)
        self.question_label = None
        self.btn_group = None
        self.correct_btn = None
        self.incorrect_btn = None
        self.no_answer_btn = None
        self.response_input = None  # For free response questions
        
        # Setup UI
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("class", "ResponseGridCell") # Used for theme-based styling
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components based on question type."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Question text
        question_text = self.question["text"]
        if len(question_text) > 100:
            question_text = question_text[:97] + "..."
        
        self.question_label = QLabel(question_text)
        self.question_label.setWordWrap(True)
        self.question_label.setProperty("class", "question-label")
        font = self.question_label.font()
        font.setBold(True)
        self.question_label.setFont(font)
        layout.addWidget(self.question_label)
        
        # Add question type indicator
        type_label = QLabel(f"({self.question_type.replace('_', ' ').title()})")
        type_label.setProperty("class", "question-type-label")
        font = type_label.font()
        font.setPointSize(font.pointSize() - 1)
        font.setItalic(True)
        type_label.setFont(font)
        layout.addWidget(type_label)
        
        # Create input controls based on question type
        if self.question_type == "free_response":
            self._setup_free_response_ui(layout)
        else:
            self._setup_multiple_choice_ui(layout)
    
    def _setup_multiple_choice_ui(self, layout):
        """Set up UI for multiple choice questions."""
        # Response buttons
        response_layout = QHBoxLayout()
        
        self.correct_btn = QRadioButton("Correct")
        self.incorrect_btn = QRadioButton("Incorrect")
        self.no_answer_btn = QRadioButton("No Answer")
        
        # Group the radio buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.correct_btn)
        self.btn_group.addButton(self.incorrect_btn)
        self.btn_group.addButton(self.no_answer_btn)
        
        # Default to no answer
        self.no_answer_btn.setChecked(True)
        
        # Connect signals
        self.correct_btn.toggled.connect(lambda checked: 
                                       self._handle_mc_response(True) if checked else None)
        self.incorrect_btn.toggled.connect(lambda checked: 
                                         self._handle_mc_response(False) if checked else None)
        self.no_answer_btn.toggled.connect(lambda checked: 
                                         self._handle_mc_clear() if checked else None)
        
        response_layout.addWidget(self.correct_btn)
        response_layout.addWidget(self.incorrect_btn)
        response_layout.addWidget(self.no_answer_btn)
        response_layout.addStretch()
        
        layout.addLayout(response_layout)
    
    def _setup_free_response_ui(self, layout):
        """Set up UI for free response questions."""
        # Student answer input
        layout.addWidget(QLabel("Student Answer:"))
        self.response_input = QTextEdit()
        self.response_input.setMaximumHeight(80)
        self.response_input.setPlaceholderText("Enter student's answer here...")
        self.response_input.textChanged.connect(self._handle_free_response_change)
        layout.addWidget(self.response_input)
        
        # Grading controls
        grading_layout = QHBoxLayout()
        
        self.correct_btn = QRadioButton("Correct")
        self.incorrect_btn = QRadioButton("Incorrect")
        self.ungraded_btn = QRadioButton("Ungraded")
        
        # Group the radio buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.correct_btn)
        self.btn_group.addButton(self.incorrect_btn)
        self.btn_group.addButton(self.ungraded_btn)
        
        # Default to ungraded
        self.ungraded_btn.setChecked(True)
        
        # Connect signals
        self.correct_btn.toggled.connect(lambda checked: 
                                       self._handle_fr_grading(True) if checked else None)
        self.incorrect_btn.toggled.connect(lambda checked: 
                                         self._handle_fr_grading(False) if checked else None)
        self.ungraded_btn.toggled.connect(lambda checked: 
                                        self._handle_fr_grading(None) if checked else None)
        
        grading_layout.addWidget(QLabel("Grade:"))
        grading_layout.addWidget(self.correct_btn)
        grading_layout.addWidget(self.incorrect_btn)
        grading_layout.addWidget(self.ungraded_btn)
        grading_layout.addStretch()
        
        layout.addLayout(grading_layout)
    
    def set_response(self, response_data: Dict[str, Any]):
        """
        Set the response for this question.
        
        Args:
            response_data: Dictionary containing response data:
                For MC: {'is_correct': True/False/None}
                For FR: {'student_answer': str, 'is_correct': True/False/None}
        """
        if not response_data:
            return
        
        # Block signals temporarily to avoid triggering events
        if self.btn_group:
            self.btn_group.blockSignals(True)
        
        if self.question_type == "free_response":
            # Set student answer
            student_answer = response_data.get('student_answer', '')
            if self.response_input:
                self.response_input.blockSignals(True)
                self.response_input.setPlainText(student_answer)
                self.response_input.blockSignals(False)
            
            # Set grading
            is_correct = response_data.get('is_correct')
            if is_correct is True and self.correct_btn:
                self.correct_btn.setChecked(True)
            elif is_correct is False and self.incorrect_btn:
                self.incorrect_btn.setChecked(True)
            elif self.ungraded_btn:
                self.ungraded_btn.setChecked(True)
        else:
            # Multiple choice response
            is_correct = response_data.get('is_correct')
            if is_correct is True and self.correct_btn:
                self.correct_btn.setChecked(True)
            elif is_correct is False and self.incorrect_btn:
                self.incorrect_btn.setChecked(True)
            elif self.no_answer_btn:
                self.no_answer_btn.setChecked(True)
        
        # Update styling
        self._update_styling(response_data.get('is_correct'))
        
        # Re-enable signals
        if self.btn_group:
            self.btn_group.blockSignals(False)
    
    def get_response(self) -> Dict[str, Any]:
        """
        Get the current response data.
        
        Returns:
            Dictionary containing response data based on question type
        """
        if self.question_type == "free_response":
            student_answer = self.response_input.toPlainText() if self.response_input else ""
            is_correct = None
            if self.correct_btn and self.correct_btn.isChecked():
                is_correct = True
            elif self.incorrect_btn and self.incorrect_btn.isChecked():
                is_correct = False
            
            return {
                'student_answer': student_answer,
                'is_correct': is_correct
            }
        else:
            is_correct = None
            if self.correct_btn and self.correct_btn.isChecked():
                is_correct = True
            elif self.incorrect_btn and self.incorrect_btn.isChecked():
                is_correct = False
            
            return {
                'is_correct': is_correct
            }
    
    def _update_styling(self, is_correct: Optional[bool]):
        """Update cell styling based on correctness."""
        # First remove any special styling classes
        self.setProperty("class", "ResponseGridCell")
        
        if is_correct is True:
            self.setProperty("class", "ResponseGridCell-correct")
        elif is_correct is False:
            self.setProperty("class", "ResponseGridCell-incorrect")
        
        # Force style recalculation
        self.style().unpolish(self)
        self.style().polish(self)
    
    def _handle_mc_response(self, is_correct: bool):
        """Handle multiple choice response selection."""
        self._update_styling(is_correct)
        response_data = self.get_response()
        self.response_changed.emit(self.question_id, response_data)
    
    def _handle_mc_clear(self):
        """Handle clearing multiple choice response."""
        self._update_styling(None)
        response_data = self.get_response()
        self.response_changed.emit(self.question_id, response_data)
    
    def _handle_free_response_change(self):
        """Handle free response text change."""
        response_data = self.get_response()
        self.response_changed.emit(self.question_id, response_data)
    
    def _handle_fr_grading(self, is_correct: Optional[bool]):
        """Handle free response grading change."""
        self._update_styling(is_correct)
        response_data = self.get_response()
        self.response_changed.emit(self.question_id, response_data)


class ResponseGrid(QWidget):
    """
    Grid component for displaying and selecting multiple answers.
    
    Provides a grid layout of ResponseGridCells for efficient answer selection.
    """
    
    responses_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """
        Initialize the ResponseGrid.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.questions = []
        self.responses = {}
        self.cells = {}
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        main_layout = QVBoxLayout(self)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        self.status_label = QLabel("No questions loaded")
        header_layout.addWidget(self.status_label)
        
        # Batch operations
        self.mark_all_correct_btn = QPushButton("Mark All Correct")
        self.mark_all_incorrect_btn = QPushButton("Mark All Incorrect")
        self.clear_all_btn = QPushButton("Clear All")
        
        self.mark_all_correct_btn.clicked.connect(lambda: self._mark_all(True))
        self.mark_all_incorrect_btn.clicked.connect(lambda: self._mark_all(False))
        self.clear_all_btn.clicked.connect(self._clear_all)
        
        header_layout.addWidget(self.mark_all_correct_btn)
        header_layout.addWidget(self.mark_all_incorrect_btn)
        header_layout.addWidget(self.clear_all_btn)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        
        scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(scroll_area)
    
    def set_questions(self, questions: List[Dict[str, Any]]):
        """
        Set the questions to display in the grid.
        
        Args:
            questions: List of question data dictionaries
        """
        self.questions = questions
        self.responses = {}
        self.cells = {}
        self._reload_grid()
    
    def get_responses(self) -> Dict[int, Dict[str, Any]]:
        """
        Get the current responses.
        
        Returns:
            Dictionary mapping question IDs to response data
        """
        return self.responses
    
    def set_responses(self, responses: Dict[int, Dict[str, Any]]):
        """
        Set responses for the loaded questions.
        
        Args:
            responses: Dictionary mapping question IDs to response data
        """
        self.responses = responses.copy()
        
        # Update cells with the responses
        for question_id, response_data in self.responses.items():
            if question_id in self.cells:
                self.cells[question_id].set_response(response_data)
        
        self._update_status()
    
    def _reload_grid(self):
        """Reload the grid display."""
        # Clear existing layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.questions:
            self.status_label.setText("No questions loaded")
            return
        
        # Determine grid dimensions - use 3 columns
        num_cols = 3
        num_rows = (len(self.questions) + num_cols - 1) // num_cols
        
        # Add cells to the grid
        for i, question in enumerate(self.questions):
            row = i // num_cols
            col = i % num_cols
            
            cell = ResponseGridCell(question)
            cell.response_changed.connect(self._handle_cell_response)
            
            question_id = question["id"]
            self.cells[question_id] = cell
            
            # Set initial response state if available
            if question_id in self.responses:
                cell.set_response(self.responses[question_id])
            
            self.grid_layout.addWidget(cell, row, col)
        
        # Add empty cells to fill the last row if needed
        remaining = num_cols - (len(self.questions) % num_cols)
        if remaining < num_cols:
            for i in range(remaining):
                spacer = QSpacerItem(
                    20, 20, 
                    QSizePolicy.Policy.Expanding, 
                    QSizePolicy.Policy.Minimum
                )
                self.grid_layout.addItem(spacer, num_rows - 1, num_cols - i - 1)
        
        self._update_status()
    
    def _handle_cell_response(self, question_id: int, response_data: Dict[str, Any]):
        """
        Handle response change from a cell.
        
        Args:
            question_id: ID of the question
            response_data: Response data dictionary
        """
        if not response_data or (response_data.get('is_correct') is None and 
                                not response_data.get('student_answer', '').strip()):
            # Remove empty responses
            if question_id in self.responses:
                del self.responses[question_id]
        else:
            self.responses[question_id] = response_data
        
        self._update_status()
        self.responses_changed.emit(self.responses)
    
    def _mark_all(self, is_correct: bool):
        """
        Mark all questions with the same response.
        
        Args:
            is_correct: Whether to mark all as correct (True) or incorrect (False)
        """
        for question in self.questions:
            question_id = question["id"]
            question_type = question.get("question_type", "multiple_choice")
            
            if question_type == "free_response":
                # For free response, only set grading, preserve existing student answer
                existing_response = self.responses.get(question_id, {})
                response_data = {
                    'student_answer': existing_response.get('student_answer', ''),
                    'is_correct': is_correct
                }
            else:
                # For multiple choice, just set correctness
                response_data = {'is_correct': is_correct}
            
            self.responses[question_id] = response_data
            if question_id in self.cells:
                self.cells[question_id].set_response(response_data)
        
        self._update_status()
        self.responses_changed.emit(self.responses)
    
    def _clear_all(self):
        """Clear all responses."""
        self.responses = {}
        for cell in self.cells.values():
            if cell.question_type == "free_response":
                # For free response, create empty response data
                empty_response = {'student_answer': '', 'is_correct': None}
                cell.set_response(empty_response)
            else:
                # For multiple choice, create empty response data
                empty_response = {'is_correct': None}
                cell.set_response(empty_response)
        
        self._update_status()
        self.responses_changed.emit(self.responses)
    
    def _update_status(self):
        """Update the status label."""
        answered = len(self.responses)
        total = len(self.questions)
        
        # Count correct responses
        correct = sum(1 for response in self.responses.values() 
                     if response.get('is_correct') is True)
        
        # Count questions with student answers (for free response)
        with_answers = sum(1 for response in self.responses.values() 
                          if response.get('student_answer', '').strip())
        
        if answered > 0:
            self.status_label.setText(
                f"{answered}/{total} questions responded | "
                f"{correct}/{answered} graded correct ({correct/answered*100:.1f}%) | "
                f"{with_answers} with student answers"
            )
        else:
            self.status_label.setText(f"0/{total} questions responded")