"""
Question browser module for the SAT Question Bank application.
Provides functionality to browse, search, and filter questions.
"""
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QMessageBox, QMenu, QAbstractItemView,
    QDialog, QDialogButtonBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon

from ..business.question_manager import QuestionManager
from ..dal.models import Question
from ..utils.logger import get_logger


class QuestionBrowser(QWidget):
    """
    Question browser widget.
    
    Allows users to view, search, filter, and select questions from the database.
    Provides pagination for efficient exploration of large datasets.
    """
    
    # Signal emitted when a question is selected for editing
    edit_question = pyqtSignal(int)
    
    # Signal emitted when a question is selected for viewing details
    view_question = pyqtSignal(int)
    
    # Signal emitted when a question is deleted
    question_deleted = pyqtSignal(int)
    
    def __init__(self, question_manager: QuestionManager, parent=None):
        """
        Initialize the question browser.
        
        Args:
            question_manager: The manager for question operations
            parent: The parent widget
        """
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.question_manager = question_manager
        self.current_page = 1
        self.questions_per_page = 20
        self.total_questions = 0
        self.filters: Dict[str, Any] = {}
        self.current_questions: List[Question] = []
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create filter section
        filter_group = QGroupBox("Search and Filter")
        filter_layout = QFormLayout()
        
        # Text search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search question text...")
        self.search_input.returnPressed.connect(self.apply_filters)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.apply_filters)
        search_layout.addWidget(self.search_button)
        
        filter_layout.addRow("Search:", search_layout)
        
        # Tag filter
        self.tag_filter = QLineEdit()
        self.tag_filter.setPlaceholderText("Enter tag (e.g., Algebra)")
        filter_layout.addRow("Tag:", self.tag_filter)
        
        # Difficulty filter
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItems(["All", "Easy", "Medium", "Hard", "Very Hard"])
        filter_layout.addRow("Difficulty:", self.difficulty_filter)
        
        # Filter actions
        filter_buttons = QHBoxLayout()
        
        self.apply_filter_button = QPushButton("Apply Filters")
        self.apply_filter_button.clicked.connect(self.apply_filters)
        filter_buttons.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton("Clear Filters")
        self.clear_filter_button.clicked.connect(self.clear_filters)
        filter_buttons.addWidget(self.clear_filter_button)
        
        filter_layout.addRow("", filter_buttons)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Results count
        self.results_label = QLabel("Showing 0 questions")
        main_layout.addWidget(self.results_label)
        
        # Create question table
        self.question_table = QTableWidget(0, 5)  # Rows will be added dynamically, 5 columns
        self.question_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.question_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.question_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.question_table.setHorizontalHeaderLabels(["ID", "Question", "Tags", "Difficulty", "Actions"])
        
        # Set column widths
        self.question_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.question_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Question
        self.question_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        self.question_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Difficulty
        self.question_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        # Connect double-click to view question
        self.question_table.itemDoubleClicked.connect(self._handle_double_click)
        
        main_layout.addWidget(self.question_table, 1)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        self.prev_page_button = QPushButton("Previous")
        self.prev_page_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_page_button)
        
        self.page_label = QLabel("Page 1")
        pagination_layout.addWidget(self.page_label, 1, Qt.AlignmentFlag.AlignCenter)
        
        self.next_page_button = QPushButton("Next")
        self.next_page_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_page_button)
        
        main_layout.addLayout(pagination_layout)
        
        # Add button
        self.add_button = QPushButton("Add New Question")
        self.add_button.clicked.connect(self._add_new_question)
        main_layout.addWidget(self.add_button)
        
        # Load initial data
        self.refresh_questions()
        
        self.logger.info("Question browser initialized")
    
    def refresh_questions(self):
        """Refresh the question list with current filters and pagination."""
        try:
            # Get filtered questions
            if self.filters:
                questions = self.question_manager.filter_questions(self.filters)
            else:
                questions = self.question_manager.get_all_questions()
            
            self.total_questions = len(questions)
            
            # Update results label
            if self.filters:
                filter_text = ", ".join([f"{k}={v}" for k, v in self.filters.items() if v])
                self.results_label.setText(f"Showing {self.total_questions} questions ({filter_text})")
            else:
                self.results_label.setText(f"Showing all {self.total_questions} questions")
            
            # Calculate pagination
            total_pages = max(1, (self.total_questions + self.questions_per_page - 1) // self.questions_per_page)
            if self.current_page > total_pages:
                self.current_page = total_pages
            
            # Update page label
            self.page_label.setText(f"Page {self.current_page} of {total_pages}")
            
            # Enable/disable pagination buttons
            self.prev_page_button.setEnabled(self.current_page > 1)
            self.next_page_button.setEnabled(self.current_page < total_pages)
            
            # Get current page questions
            start_idx = (self.current_page - 1) * self.questions_per_page
            end_idx = min(start_idx + self.questions_per_page, self.total_questions)
            self.current_questions = questions[start_idx:end_idx]
            
            # Populate table
            self._populate_table()
            
        except Exception as e:
            self.logger.error(f"Error refreshing questions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading questions: {str(e)}")
    
    def _populate_table(self):
        """Populate the question table with current page data."""
        # Clear existing rows
        self.question_table.setRowCount(0)
        
        # Add questions for current page
        for row, question in enumerate(self.current_questions):
            self.question_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(question.question_id))
            self.question_table.setItem(row, 0, id_item)
            
            # Question text (truncated if needed)
            question_text = question.question_text
            if len(question_text) > 100:
                question_text = question_text[:97] + "..."
            text_item = QTableWidgetItem(question_text)
            self.question_table.setItem(row, 1, text_item)
            
            # Tags
            tags_str = ", ".join(question.subject_tags) if question.subject_tags else ""
            tags_item = QTableWidgetItem(tags_str)
            self.question_table.setItem(row, 2, tags_item)
            
            # Difficulty
            difficulty_item = QTableWidgetItem(question.difficulty_label)
            self.question_table.setItem(row, 3, difficulty_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            view_button = QPushButton("View")
            view_button.setProperty("question_id", question.question_id)
            view_button.clicked.connect(lambda checked, qid=question.question_id: self.view_question.emit(qid))
            actions_layout.addWidget(view_button)
            
            edit_button = QPushButton("Edit")
            edit_button.setProperty("question_id", question.question_id)
            edit_button.clicked.connect(lambda checked, qid=question.question_id: self.edit_question.emit(qid))
            actions_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.setProperty("question_id", question.question_id)
            delete_button.clicked.connect(lambda checked, qid=question.question_id: self._delete_question(qid))
            actions_layout.addWidget(delete_button)
            
            self.question_table.setCellWidget(row, 4, actions_widget)
        
        self.logger.debug(f"Populated table with {len(self.current_questions)} questions")
    
    def apply_filters(self):
        """Apply current filters and refresh the question list."""
        # Collect filter values
        filters = {}
        
        # Text search
        search_text = self.search_input.text().strip()
        if search_text:
            filters['text_search'] = search_text
        
        # Tag filter
        tag_filter = self.tag_filter.text().strip()
        if tag_filter:
            filters['subject_tags'] = tag_filter
        
        # Difficulty filter
        difficulty = self.difficulty_filter.currentText()
        if difficulty != "All":
            filters['difficulty'] = difficulty
        
        # Update filters and refresh
        self.filters = filters
        self.current_page = 1  # Reset to first page
        self.refresh_questions()
        
        self.logger.debug(f"Applied filters: {filters}")
    
    def clear_filters(self):
        """Clear all filters and refresh the question list."""
        self.search_input.clear()
        self.tag_filter.clear()
        self.difficulty_filter.setCurrentIndex(0)  # "All"
        
        self.filters = {}
        self.current_page = 1  # Reset to first page
        self.refresh_questions()
        
        self.logger.debug("Cleared all filters")
    
    def next_page(self):
        """Move to the next page of questions."""
        total_pages = max(1, (self.total_questions + self.questions_per_page - 1) // self.questions_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.refresh_questions()
    
    def prev_page(self):
        """Move to the previous page of questions."""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_questions()
    
    def _handle_double_click(self, item):
        """Handle double-click on a question row."""
        row = item.row()
        question_id = int(self.question_table.item(row, 0).text())
        self.view_question.emit(question_id)
    
    def _add_new_question(self):
        """Signal to add a new question."""
        self.edit_question.emit(-1)  # Use -1 to indicate new question
    
    def _delete_question(self, question_id: int):
        """
        Delete a question after confirmation.
        
        Args:
            question_id: ID of the question to delete
        """
        try:
            # Confirm deletion
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete question {question_id}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                success = self.question_manager.delete_question(question_id)
                if success:
                    QMessageBox.information(self, "Success", "Question deleted successfully")
                    self.question_deleted.emit(question_id)
                    self.refresh_questions()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete question")
        
        except KeyError:
            self.logger.error(f"Question not found: {question_id}")
            QMessageBox.warning(self, "Error", f"Question with ID {question_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting question: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error deleting question: {str(e)}")


class QuestionDetailDialog(QDialog):
    """
    Dialog for displaying question details.
    
    Shows all information about a question, including text, images,
    answer options, and explanation.
    """
    
    def __init__(self, question: Question, parent=None):
        """
        Initialize the question detail dialog.
        
        Args:
            question: The question to display
            parent: The parent widget
        """
        super().__init__(parent)
        
        self.question = question
        self.setWindowTitle(f"Question {question.question_id}")
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Question text
        question_group = QGroupBox("Question")
        question_layout = QVBoxLayout()
        
        question_text = QLabel(question.question_text)
        question_text.setWordWrap(True)
        question_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        question_layout.addWidget(question_text)
        
        # Question image if available
        if question.question_image_path and os.path.exists(question.question_image_path):
            image_label = QLabel()
            pixmap = QPixmap(question.question_image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio)
                image_label.setPixmap(pixmap)
                question_layout.addWidget(image_label)
        
        question_group.setLayout(question_layout)
        scroll_layout.addWidget(question_group)
        
        # Answer options
        answers_group = QGroupBox("Answer Options")
        answers_layout = QVBoxLayout()
        
        # Helper function to create answer option display
        def add_answer_option(option, text, image_path, is_correct):
            option_layout = QVBoxLayout()
            
            # Option header with correct indicator
            header_text = f"Option {option}: {' (CORRECT)' if is_correct else ''}"
            header = QLabel(header_text)
            if is_correct:
                header.setStyleSheet("font-weight: bold; color: green;")
            option_layout.addWidget(header)
            
            # Answer text
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            option_layout.addWidget(text_label)
            
            # Answer image if available
            if image_path and os.path.exists(image_path):
                image_label = QLabel()
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio)
                    image_label.setPixmap(pixmap)
                    option_layout.addWidget(image_label)
            
            option_widget = QWidget()
            option_widget.setLayout(option_layout)
            answers_layout.addWidget(option_widget)
        
        # Add each answer option
        add_answer_option('A', question.answer_a, question.answer_image_a, question.correct_answer == 'A')
        add_answer_option('B', question.answer_b, question.answer_image_b, question.correct_answer == 'B')
        add_answer_option('C', question.answer_c, question.answer_image_c, question.correct_answer == 'C')
        add_answer_option('D', question.answer_d, question.answer_image_d, question.correct_answer == 'D')
        
        answers_group.setLayout(answers_layout)
        scroll_layout.addWidget(answers_group)
        
        # Explanation
        if question.answer_explanation:
            explanation_group = QGroupBox("Explanation")
            explanation_layout = QVBoxLayout()
            
            explanation_text = QLabel(question.answer_explanation)
            explanation_text.setWordWrap(True)
            explanation_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            explanation_layout.addWidget(explanation_text)
            
            explanation_group.setLayout(explanation_layout)
            scroll_layout.addWidget(explanation_group)
        
        # Metadata
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QFormLayout()
        
        # Tags
        tags_label = QLabel(", ".join(question.subject_tags))
        metadata_layout.addRow("Tags:", tags_label)
        
        # Difficulty
        difficulty_label = QLabel(question.difficulty_label)
        metadata_layout.addRow("Difficulty:", difficulty_label)
        
        metadata_group.setLayout(metadata_layout)
        scroll_layout.addWidget(metadata_group)
        
        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)