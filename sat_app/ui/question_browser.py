"""
Question browser module for the SAT Question Bank application.
Provides functionality to browse, search, and filter questions.
"""
import os
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QMessageBox, QMenu, QAbstractItemView,
    QDialog, QDialogButtonBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

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
    
    # Signal emitted when questions are selected for a worksheet
    questions_selected_for_worksheet = pyqtSignal(list)
    
    # Signal emitted when worksheet selection changes
    worksheet_selection_changed = pyqtSignal()
    
    def __init__(self, question_manager: QuestionManager, parent=None, enable_worksheet_selection: bool = False):
        """
        Initialize the question browser.
        
        Args:
            question_manager: The manager for question operations
            parent: The parent widget
            enable_worksheet_selection: Whether to enable worksheet selection functionality
        """
        super().__init__(parent)
        
        self.logger = get_logger(__name__)
        self.question_manager = question_manager
        self.current_page = 1
        self.questions_per_page = 20
        self.total_questions = 0
        self.filters: Dict[str, Any] = {}
        self.current_questions: List[Question] = []
        self.enable_worksheet_selection = enable_worksheet_selection
        self.selected_for_worksheet: List[Question] = []
        self.worksheet_column = None  # Initialize attribute to fix error
        
        # For tracking student answered questions
        self.current_student_id = None
        self.student_answered_questions = {}  # {question_id: [worksheet_id, worksheet_title]}
        self.show_answered_questions = False
        
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
        
        # Student filter row
        student_filter_layout = QHBoxLayout()
        
        self.student_filter = QComboBox()
        self.student_filter.setMinimumWidth(150)
        self.student_filter.addItem("All Students", None)
        student_filter_layout.addWidget(self.student_filter, 1)
        
        # Connect student selection change
        self.student_filter.currentIndexChanged.connect(self._on_student_changed)
        
        # Checkbox for answered questions
        self.show_answered_checkbox = QCheckBox("Hide Already Answered")
        self.show_answered_checkbox.setChecked(False)
        self.show_answered_checkbox.setEnabled(False)  # Initially disabled until student is selected
        self.show_answered_checkbox.stateChanged.connect(self._on_answered_filter_changed)
        student_filter_layout.addWidget(self.show_answered_checkbox)
        
        # Refresh student list button
        self.refresh_students_button = QPushButton("↻")
        self.refresh_students_button.setToolTip("Refresh student list")
        self.refresh_students_button.setMaximumWidth(30)
        self.refresh_students_button.clicked.connect(self._load_student_list)
        student_filter_layout.addWidget(self.refresh_students_button)
        
        filter_layout.addRow("Student:", student_filter_layout)
        
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
        
        # Create question table with appropriate columns (Add worksheet column if enabled)
        # Add extra column for answered status when in student filtering mode
        self.student_mode_active = False
        base_columns = 5  # ID, Question, Tags, Difficulty, Actions
        selection_columns = 1 if self.enable_worksheet_selection else 0  # Worksheet selection
        student_columns = 1  # Student answered column
        
        column_count = base_columns + selection_columns + student_columns
        
        self.question_table = QTableWidget(0, column_count)
        self.question_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.question_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.question_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Dynamically set columns based on active modes
        headers = ["ID", "Question", "Tags", "Difficulty", "Actions"]
        
        # Add student history column
        headers.append("Student History")
        self.student_history_column = 5
        
        # Add worksheet selection column if enabled
        if self.enable_worksheet_selection:
            headers.append("Worksheet")
            self.worksheet_column = 6
            
        self.question_table.setHorizontalHeaderLabels(headers)
        
        # Set column widths
        self.question_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.question_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Question
        self.question_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        self.question_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Difficulty
        self.question_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        self.question_table.horizontalHeader().setSectionResizeMode(self.student_history_column, QHeaderView.ResizeMode.ResizeToContents)
        
        # Set worksheet column width if enabled
        if self.enable_worksheet_selection:
            self.question_table.horizontalHeader().setSectionResizeMode(self.worksheet_column, QHeaderView.ResizeMode.ResizeToContents)
        
        # Connect double-click to view question
        self.question_table.itemDoubleClicked.connect(self._handle_double_click)
        
        main_layout.addWidget(self.question_table, 1)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        self.prev_page_button = QPushButton("Previous")
        self.prev_page_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_page_button)
        
        self.page_label = QLabel("Page 1")
        pagination_layout.addWidget(self.page_label, 1, Qt.AlignCenter)
        
        self.next_page_button = QPushButton("Next")
        self.next_page_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_page_button)
        
        main_layout.addLayout(pagination_layout)
        
        # Add worksheet selection controls if enabled
        if self.enable_worksheet_selection:
            worksheet_controls = QHBoxLayout()
            
            self.selected_count_label = QLabel("0 questions selected for worksheet")
            worksheet_controls.addWidget(self.selected_count_label, 1)
            
            self.clear_worksheet_button = QPushButton("Clear Selection")
            self.clear_worksheet_button.clicked.connect(self.clear_worksheet_selection)
            self.clear_worksheet_button.setEnabled(False)
            worksheet_controls.addWidget(self.clear_worksheet_button)
            
            self.create_worksheet_button = QPushButton("Create Worksheet")
            self.create_worksheet_button.clicked.connect(self._create_worksheet)
            self.create_worksheet_button.setEnabled(False)
            worksheet_controls.addWidget(self.create_worksheet_button)
            
            main_layout.addLayout(worksheet_controls)
        
        # Add button
        self.add_button = QPushButton("Add New Question")
        self.add_button.clicked.connect(self._add_new_question)
        main_layout.addWidget(self.add_button)
        
        # Load initial data
        self.refresh_questions()
        
        # Load student data
        self._load_student_list()
        
        self.logger.info("Question browser initialized")
    
    def refresh_questions(self):
        """Refresh the question list with current filters and pagination."""
        try:
            # Get filtered questions
            if self.filters:
                questions = self.question_manager.filter_questions(self.filters)
            else:
                questions = self.question_manager.get_all_questions()
            
            # Filter out questions that have been answered by the selected student if checkbox is selected
            student_filter_applied = False
            if self.current_student_id and self.show_answered_questions:
                # Get question IDs that have been answered by this student
                answered_question_ids = set(self.student_answered_questions.keys())
                
                # Remove answered questions from the display list
                filtered_questions = [q for q in questions if q.question_id not in answered_question_ids]
                
                # Update the results count
                filtered_out_count = len(questions) - len(filtered_questions)
                questions = filtered_questions
                student_filter_applied = True
                
            self.total_questions = len(questions)
            
            # Update results label with appropriate text based on filters
            label_text = ""
            if self.filters:
                filter_text = ", ".join([f"{k}={v}" for k, v in self.filters.items() if v])
                label_text = f"Showing {self.total_questions} questions ({filter_text})"
            else:
                label_text = f"Showing all {self.total_questions} questions"
            
            # Add student filter info if applicable
            if student_filter_applied:
                label_text += f" - Hiding questions already answered by {self.current_student_id}"
            elif self.current_student_id:
                label_text += f" - Showing question history for {self.current_student_id}"
                
            self.results_label.setText(label_text)
            
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
            
            # Student history column (column 5)
            if self.current_student_id:
                # Create a widget to show student's history with this question
                history_widget = QWidget()
                history_layout = QHBoxLayout(history_widget)
                history_layout.setContentsMargins(2, 2, 2, 2)
                
                question_id = question.question_id
                
                if question_id in self.student_answered_questions:
                    # Question has been answered by this student
                    worksheet_info = self.student_answered_questions[question_id]
                    if isinstance(worksheet_info, list) and len(worksheet_info) == 2:
                        worksheet_id, worksheet_title = worksheet_info
                        
                        # Display button showing which worksheet this was in
                        history_label = QPushButton(f"In WS #{worksheet_id}")
                        history_label.setToolTip(f"This question appeared in worksheet: {worksheet_title}")
                        history_label.setStyleSheet("background-color: #FFD580;")  # Light orange color
                        history_label.setProperty("worksheet_id", worksheet_id)
                        history_label.clicked.connect(lambda checked, ws_id=worksheet_id: self._show_worksheet_details(ws_id))
                        
                        history_layout.addWidget(history_label)
                    else:
                        history_label = QLabel("✓ Answered")
                        history_label.setStyleSheet("color: green; font-weight: bold;")
                        history_layout.addWidget(history_label)
                else:
                    # Question has not been answered by this student
                    history_label = QLabel("Not seen")
                    history_layout.addWidget(history_label)
                
                self.question_table.setCellWidget(row, self.student_history_column, history_widget)
            else:
                # No student selected, just show empty cell
                self.question_table.setItem(row, self.student_history_column, QTableWidgetItem(""))
            
            # Add worksheet selection button if enabled
            if self.enable_worksheet_selection and self.worksheet_column is not None:
                worksheet_col = self.worksheet_column
                worksheet_widget = QWidget()
                worksheet_layout = QHBoxLayout(worksheet_widget)
                worksheet_layout.setContentsMargins(2, 2, 2, 2)
                
                # Check if question is already selected for worksheet
                is_selected = any(q.question_id == question.question_id for q in self.selected_for_worksheet)
                
                # Check if this question has been answered by the current student
                already_answered = (self.current_student_id and 
                                   question.question_id in self.student_answered_questions and 
                                   self.show_answered_questions)
                
                # If already answered by this student, disable adding to worksheet
                if already_answered:
                    add_button = QPushButton("Add")
                    add_button.setEnabled(False)
                    add_button.setToolTip("This question has already been answered by this student")
                    worksheet_layout.addWidget(add_button)
                elif is_selected:
                    remove_button = QPushButton("Remove")
                    remove_button.setProperty("question_id", question.question_id)
                    remove_button.clicked.connect(lambda checked, q=question: self._remove_from_worksheet(q))
                    worksheet_layout.addWidget(remove_button)
                else:
                    add_button = QPushButton("Add")
                    add_button.setProperty("question_id", question.question_id)
                    add_button.clicked.connect(lambda checked, q=question: self._add_to_worksheet(q))
                    worksheet_layout.addWidget(add_button)
                
                self.question_table.setCellWidget(row, worksheet_col, worksheet_widget)
        
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
            
        # Student filter and answered questions
        if self.current_student_id and self.show_answered_questions:
            # Special handling for filtered questions - will be managed in refresh_questions
            # Just set a flag here
            self.student_filter_active = True
        else:
            self.student_filter_active = False
        
        # Update filters and refresh
        self.filters = filters
        self.current_page = 1  # Reset to first page
        self.refresh_questions()
        
        self.logger.debug(f"Applied filters: {filters}")
    
    def _load_student_list(self):
        """Load the list of students for filtering."""
        try:
            # Get student list using the question manager's method
            student_ids = []
            if hasattr(self.question_manager, 'get_student_list'):
                student_ids = self.question_manager.get_student_list()
            
            # If we couldn't get any student IDs, just keep the "All Students" option
            if not student_ids:
                self.logger.warning("No students found or unable to get student list")
                return
            
            # Save current selection
            current_index = self.student_filter.currentIndex()
            current_data = self.student_filter.currentData()
            
            # Clear the combobox except for the first item ("All Students")
            while self.student_filter.count() > 1:
                self.student_filter.removeItem(1)
            
            # Add student IDs
            for student_id in student_ids:
                self.student_filter.addItem(f"Student: {student_id}", student_id)
            
            # Try to restore previous selection, otherwise select "All Students"
            if current_data:
                index = self.student_filter.findData(current_data)
                if index >= 0:
                    self.student_filter.setCurrentIndex(index)
                else:
                    self.student_filter.setCurrentIndex(0)  # All Students
                
        except Exception as e:
            self.logger.error(f"Error loading student list: {str(e)}")
    
    def _on_student_changed(self, index):
        """Handle student selection change."""
        student_id = self.student_filter.currentData()
        
        # Enable or disable the answered checkbox based on student selection
        self.show_answered_checkbox.setEnabled(student_id is not None)
        
        if student_id != self.current_student_id:
            self.current_student_id = student_id
            
            # If a specific student is selected, load their answered questions
            if student_id:
                self._load_student_answered_questions(student_id)
            else:
                # Clear student data if "All Students" selected
                self.student_answered_questions = {}
                self.show_answered_checkbox.setChecked(False)
                self.show_answered_questions = False
            
            # Refresh the table to show student history
            self.refresh_questions()
    
    def _on_answered_filter_changed(self, state):
        """Handle change in the 'Hide Already Answered' checkbox."""
        self.show_answered_questions = (state == Qt.CheckState.Checked)
        self.refresh_questions()
    
    def _load_student_answered_questions(self, student_id):
        """Load the list of questions that have been answered by the student."""
        try:
            # Use the question manager method if available
            if hasattr(self.question_manager, 'get_student_answered_questions'):
                self.student_answered_questions = self.question_manager.get_student_answered_questions(student_id)
                self.logger.debug(f"Loaded {len(self.student_answered_questions)} answered questions for student {student_id}")
                return
                
            # Fallback to direct database query if method not available
            self.logger.warning("Question manager method not available, using fallback approach")
            
            # Get access to score repository - multiple approaches for flexibility
            score_repo = None
            
            # Try to get the score repository from question_manager
            if hasattr(self.question_manager, 'score_repository'):
                score_repo = self.question_manager.score_repository
            elif hasattr(self.question_manager, 'db_manager'):
                # Create a temporary score repository
                from ..dal.repositories import ScoreRepository
                score_repo = ScoreRepository(self.question_manager.db_manager)
            
            if not score_repo:
                self.logger.error("Could not access score repository")
                return
            
            # Query the database for all questions this student has answered
            query = """
            SELECT s.question_id, s.worksheet_id, w.title 
            FROM scores s 
            LEFT JOIN worksheets w ON s.worksheet_id = w.worksheet_id
            WHERE s.student_id = ? 
            GROUP BY s.question_id
            """
            
            result = score_repo.db_manager.execute_query(query, (student_id,))
            
            # Reset the answered questions dictionary
            self.student_answered_questions = {}
            
            if result:
                for row in result:
                    question_id = row['question_id']
                    worksheet_id = row['worksheet_id']
                    worksheet_title = row.get('title', f"Worksheet #{worksheet_id}")
                    
                    # Store the worksheet information with the question
                    self.student_answered_questions[question_id] = [worksheet_id, worksheet_title]
            
            self.logger.debug(f"Loaded {len(self.student_answered_questions)} answered questions for student {student_id}")
            
        except Exception as e:
            self.logger.error(f"Error loading student answered questions: {str(e)}")
    
    def _show_worksheet_details(self, worksheet_id):
        """Show details for a worksheet."""
        try:
            # Get worksheet repository
            worksheet_repo = None
            if hasattr(self.question_manager, 'worksheet_repository'):
                worksheet_repo = self.question_manager.worksheet_repository
            elif hasattr(self.question_manager, 'db_manager'):
                # Create a temporary worksheet repository
                from ..dal.repositories import WorksheetRepository
                worksheet_repo = WorksheetRepository(self.question_manager.db_manager)
            
            if not worksheet_repo:
                QMessageBox.warning(self, "Error", f"Could not access worksheet repository.")
                return
            
            # Get the worksheet
            worksheet = worksheet_repo.get_worksheet(worksheet_id)
            if not worksheet:
                QMessageBox.warning(self, "Error", f"Worksheet #{worksheet_id} not found.")
                return
            
            # Show worksheet details in a dialog
            message = f"<b>Worksheet #{worksheet_id}: {worksheet.title}</b><br>"
            message += f"<p>{worksheet.description}</p>"
            message += f"<p>Contains {len(worksheet.question_ids)} questions</p>"
            message += f"<p>Created: {worksheet.created_at.strftime('%Y-%m-%d')}</p>"
            
            # If there's a PDF path, show it
            if worksheet.pdf_path:
                message += f"<p>PDF: {worksheet.pdf_path}</p>"
            
            QMessageBox.information(self, f"Worksheet #{worksheet_id} Details", message)
            
        except Exception as e:
            self.logger.error(f"Error showing worksheet details: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error showing worksheet details: {str(e)}")
        
    
    def clear_filters(self):
        """Clear all filters and refresh the question list."""
        self.search_input.clear()
        self.tag_filter.clear()
        self.difficulty_filter.setCurrentIndex(0)  # "All"
        self.student_filter.setCurrentIndex(0)  # "All Students"
        self.show_answered_checkbox.setChecked(False)
        
        # Reset student-related variables
        self.current_student_id = None
        self.student_answered_questions = {}
        self.show_answered_questions = False
        
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
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                success = self.question_manager.delete_question(question_id)
                if success:
                    QMessageBox.information(self, "Success", "Question deleted successfully")
                    self.question_deleted.emit(question_id)
                    
                    # If question was in worksheet selection, remove it
                    if self.enable_worksheet_selection:
                        self.selected_for_worksheet = [q for q in self.selected_for_worksheet 
                                                      if q.question_id != question_id]
                    
                    self.refresh_questions()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete question")
        
        except KeyError:
            self.logger.error(f"Question not found: {question_id}")
            QMessageBox.warning(self, "Error", f"Question with ID {question_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting question: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error deleting question: {str(e)}")
            
    def _add_to_worksheet(self, question: Question):
        """
        Add a question to the worksheet selection.
        
        Args:
            question: The question to add
        """
        # Check if question is already in the selection
        if not any(q.question_id == question.question_id for q in self.selected_for_worksheet):
            self.selected_for_worksheet.append(question)
            self.logger.debug(f"Added question {question.question_id} to worksheet selection")
            
            # Update UI elements if they exist
            if hasattr(self, 'selected_count_label'):
                count = len(self.selected_for_worksheet)
                self.selected_count_label.setText(f"{count} questions selected for worksheet")
                self.clear_worksheet_button.setEnabled(count > 0)
                self.create_worksheet_button.setEnabled(count > 0)
            
            # Emit signals with the updated list
            self.questions_selected_for_worksheet.emit(self.selected_for_worksheet)
            self.worksheet_selection_changed.emit()
            
            # Refresh the table to update the button
            self.refresh_questions()
    
    def _remove_from_worksheet(self, question: Question):
        """
        Remove a question from the worksheet selection.
        
        Args:
            question: The question to remove
        """
        # Remove the question from the selection
        self.selected_for_worksheet = [q for q in self.selected_for_worksheet 
                                      if q.question_id != question.question_id]
        self.logger.debug(f"Removed question {question.question_id} from worksheet selection")
        
        # Update UI elements if they exist
        if hasattr(self, 'selected_count_label'):
            count = len(self.selected_for_worksheet)
            self.selected_count_label.setText(f"{count} questions selected for worksheet")
            self.clear_worksheet_button.setEnabled(count > 0)
            self.create_worksheet_button.setEnabled(count > 0)
        
        # Emit signals with the updated list
        self.questions_selected_for_worksheet.emit(self.selected_for_worksheet)
        self.worksheet_selection_changed.emit()
        
        # Refresh the table to update the button
        self.refresh_questions()
    
    def get_selected_for_worksheet(self) -> List[Question]:
        """
        Get the list of questions selected for the worksheet.
        
        Returns:
            List of Question objects selected for the worksheet
        """
        return self.selected_for_worksheet
    
    def set_worksheet_selection_mode(self, enabled: bool):
        """
        Set whether worksheet selection mode is enabled.
        
        Args:
            enabled: Whether to enable worksheet selection mode
        """
        if self.enable_worksheet_selection == enabled:
            return
            
        self.enable_worksheet_selection = enabled
        
        # Update the column count and headers
        if enabled:
            # Ensure we have both student history and worksheet columns
            if self.question_table.columnCount() < 7:
                # We need 7 columns: ID, Question, Tags, Difficulty, Actions, Student History, Worksheet
                self.question_table.setColumnCount(7)
                headers = ["ID", "Question", "Tags", "Difficulty", "Actions", "Student History", "Worksheet"]
                self.question_table.setHorizontalHeaderLabels(headers)
                
                # Set column indices
                self.student_history_column = 5
                self.worksheet_column = 6
                
                # Set column resize modes
                self.question_table.horizontalHeader().setSectionResizeMode(self.student_history_column, 
                                                                          QHeaderView.ResizeMode.ResizeToContents)
                self.question_table.horizontalHeader().setSectionResizeMode(self.worksheet_column, 
                                                                          QHeaderView.ResizeMode.ResizeToContents)
                
            # Make worksheet selection controls visible if they exist
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setParent(self)
                self.clear_worksheet_button.setParent(self)
                self.create_worksheet_button.setParent(self)
        else:
            # We'd keep 6 columns but hide the worksheet column
            if self.question_table.columnCount() > 6:
                # Remove worksheet column but keep student history
                self.question_table.setColumnCount(6)
                headers = ["ID", "Question", "Tags", "Difficulty", "Actions", "Student History"]
                self.question_table.setHorizontalHeaderLabels(headers)
                
                # We still have student history
                self.student_history_column = 5
                # But no worksheet column
                self.worksheet_column = None
                
            # Hide worksheet selection controls if they exist
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setParent(None)
                self.clear_worksheet_button.setParent(None)
                self.create_worksheet_button.setParent(None)
        
        # Refresh the table to update the display
        self.refresh_questions()
        
    def add_to_worksheet(self, question_id: int):
        """
        Add a question to the worksheet by ID.
        
        Args:
            question_id: ID of the question to add
        """
        # Check if already in the selection
        if any(q.question_id == question_id for q in self.selected_for_worksheet):
            return
            
        # Get the question from the manager
        try:
            question = self.question_manager.get_question(question_id)
            if question:
                self._add_to_worksheet(question)
        except Exception as e:
            self.logger.error(f"Error adding question to worksheet: {str(e)}")
    
    def load_questions_to_worksheet(self, questions: List[Question]):
        """
        Load a list of questions into the worksheet selection.
        
        Args:
            questions: List of questions to add to the worksheet
        """
        self.selected_for_worksheet = questions.copy()
        
        # Update UI elements if available
        if hasattr(self, 'selected_count_label'):
            count = len(self.selected_for_worksheet)
            self.selected_count_label.setText(f"{count} questions selected for worksheet")
            self.clear_worksheet_button.setEnabled(count > 0)
            self.create_worksheet_button.setEnabled(count > 0)
        
        # Emit signals
        self.questions_selected_for_worksheet.emit(self.selected_for_worksheet)
        self.worksheet_selection_changed.emit()
        
        # Refresh display
        self.refresh_questions()
    
    def clear_worksheet_selections(self):
        """Clear all questions from the worksheet selection."""
        if not self.selected_for_worksheet:
            return
            
        self.selected_for_worksheet.clear()
        
        # Update UI elements if available
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.setText("0 questions selected for worksheet")
            self.clear_worksheet_button.setEnabled(False)
            self.create_worksheet_button.setEnabled(False)
        
        # Emit signals
        self.questions_selected_for_worksheet.emit(self.selected_for_worksheet)
        self.worksheet_selection_changed.emit()
        
        # Refresh display
        self.refresh_questions()
    
    # Maintain backward compatibility
    get_selected_worksheet_questions = get_selected_for_worksheet
    clear_worksheet_selection = clear_worksheet_selections
    
    def _create_worksheet(self):
        """Create a worksheet with the selected questions."""
        if not self.selected_for_worksheet:
            QMessageBox.warning(self, "Warning", "No questions selected for worksheet")
            return
            
        # Emit the signal with the selected questions
        self.questions_selected_for_worksheet.emit(self.selected_for_worksheet)
        
        # Show confirmation message
        count = len(self.selected_for_worksheet)
        QMessageBox.information(
            self, 
            "Worksheet Created", 
            f"Created worksheet with {count} questions. Go to the Worksheet tab to configure and generate the PDF."
        )


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