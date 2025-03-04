"""
Reusable grid component for answer selection.
Provides a grid-based interface for recording student responses.
"""
import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ResponseGridCell(QFrame):
    """
    Individual cell for the response grid.
    
    Displays question information and provides radio buttons for response selection.
    """
    
    response_changed = pyqtSignal(int, object)
    
    def __init__(self, question: Dict[str, Any], parent=None):
        """
        Initialize the ResponseGridCell.
        
        Args:
            question: Question data dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.question = question
        self.question_id = question["id"]
        
        # Setup UI
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #f8f8f8; border-radius: 5px; padding: 8px; }")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Question text
        question_text = self.question["text"]
        if len(question_text) > 100:
            question_text = question_text[:97] + "..."
        
        self.question_label = QLabel(question_text)
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.question_label)
        
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
                                       self._handle_response(True) if checked else None)
        self.incorrect_btn.toggled.connect(lambda checked: 
                                         self._handle_response(False) if checked else None)
        self.no_answer_btn.toggled.connect(lambda checked: 
                                         self._handle_clear() if checked else None)
        
        response_layout.addWidget(self.correct_btn)
        response_layout.addWidget(self.incorrect_btn)
        response_layout.addWidget(self.no_answer_btn)
        response_layout.addStretch()
        
        layout.addLayout(response_layout)
    
    def set_response(self, is_correct: Optional[bool]):
        """
        Set the response for this question.
        
        Args:
            is_correct: True for correct, False for incorrect, None for no answer
        """
        # Block signals temporarily to avoid triggering the toggled event
        self.btn_group.blockSignals(True)
        
        if is_correct is True:
            self.correct_btn.setChecked(True)
        elif is_correct is False:
            self.incorrect_btn.setChecked(True)
        else:
            self.no_answer_btn.setChecked(True)
        
        self.btn_group.blockSignals(False)
    
    def _handle_response(self, is_correct: bool):
        """
        Handle response selection.
        
        Args:
            is_correct: Whether the answer is correct
        """
        self.response_changed.emit(self.question_id, is_correct)
    
    def _handle_clear(self):
        """Handle clearing the response."""
        self.response_changed.emit(self.question_id, None)


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
    
    def get_responses(self) -> Dict[int, bool]:
        """
        Get the current responses.
        
        Returns:
            Dictionary mapping question IDs to correctness (True/False)
        """
        return self.responses
    
    def set_responses(self, responses: Dict[int, bool]):
        """
        Set responses for the loaded questions.
        
        Args:
            responses: Dictionary mapping question IDs to correctness
        """
        self.responses = responses.copy()
        
        # Update cells with the responses
        for question_id, is_correct in self.responses.items():
            if question_id in self.cells:
                self.cells[question_id].set_response(is_correct)
        
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
    
    def _handle_cell_response(self, question_id: int, is_correct: Optional[bool]):
        """
        Handle response change from a cell.
        
        Args:
            question_id: ID of the question
            is_correct: Whether the answer is correct, or None for no answer
        """
        if is_correct is None:
            if question_id in self.responses:
                del self.responses[question_id]
        else:
            self.responses[question_id] = is_correct
        
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
            self.responses[question_id] = is_correct
            if question_id in self.cells:
                self.cells[question_id].set_response(is_correct)
        
        self._update_status()
        self.responses_changed.emit(self.responses)
    
    def _clear_all(self):
        """Clear all responses."""
        self.responses = {}
        for cell in self.cells.values():
            cell.set_response(None)
        
        self._update_status()
        self.responses_changed.emit(self.responses)
    
    def _update_status(self):
        """Update the status label."""
        answered = len(self.responses)
        total = len(self.questions)
        correct = sum(1 for val in self.responses.values() if val)
        
        self.status_label.setText(
            f"{answered}/{total} questions answered | "
            f"{correct}/{answered} correct ({correct/answered*100:.1f}% correct)" if answered else
            f"0/{total} questions answered"
        )