"""
Question browser module for the SAT Question Bank application.
Provides functionality to browse, search, and filter questions.
"""
import os
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QMessageBox, QMenu, QAbstractItemView,
    QDialog, QDialogButtonBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QModelIndex
from PyQt6.QtGui import QAction, QIcon

from ..business.question_manager import QuestionManager
from ..dal.models import Question
from ..utils.logger import get_logger
from .models.question_table_model import QuestionTableModel
from .delegates.question_delegates import (
    ActionButtonDelegate, StudentHistoryDelegate, 
    WorksheetSelectionDelegate, DifficultyDelegate
)


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
        
        # Create model and view for questions
        self.student_mode_active = False
        
        # Initialize model
        self.model = QuestionTableModel(self)
        self.model.setWorksheetSelectionEnabled(self.enable_worksheet_selection)
        
        # Create table view
        self.question_table = QTableView()
        self.question_table.setModel(self.model)
        self.question_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.question_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Configure edit triggers - allow editing for our delegate columns only
        # NoEditTriggers for standard columns, but we'll open persistent editors for delegate columns
        self.question_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Configure column appearance
        self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.ID_COLUMN, QHeaderView.ResizeMode.ResizeToContents)  # ID
        self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.TEXT_COLUMN, QHeaderView.ResizeMode.Stretch)  # Question
        self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.TAGS_COLUMN, QHeaderView.ResizeMode.ResizeToContents)  # Tags
        self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.DIFFICULTY_COLUMN, QHeaderView.ResizeMode.ResizeToContents)  # Difficulty
        self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.STUDENT_HISTORY_COLUMN, QHeaderView.ResizeMode.ResizeToContents)  # Student history
        
        # Set up context menu for right-click actions
        self.question_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.question_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Difficulty delegate for color-coded difficulty display
        self.difficulty_delegate = DifficultyDelegate(self)
        self.question_table.setItemDelegateForColumn(QuestionTableModel.DIFFICULTY_COLUMN, self.difficulty_delegate)
        
        # Student history delegate
        self.student_history_delegate = StudentHistoryDelegate(self)
        self.student_history_delegate.worksheetClicked.connect(self._show_worksheet_details)
        self.question_table.setItemDelegateForColumn(QuestionTableModel.STUDENT_HISTORY_COLUMN, self.student_history_delegate)
        
        # Worksheet selection delegate if enabled
        if self.enable_worksheet_selection:
            self.worksheet_delegate = WorksheetSelectionDelegate(self)
            self.worksheet_delegate.addToWorksheet.connect(self._add_to_worksheet)
            self.worksheet_delegate.removeFromWorksheet.connect(self._remove_from_worksheet)
            self.question_table.setItemDelegateForColumn(QuestionTableModel.WORKSHEET_COLUMN, self.worksheet_delegate)
        
        # Set column widths for worksheet column if enabled
        if self.enable_worksheet_selection:
            self.question_table.horizontalHeader().setSectionResizeMode(QuestionTableModel.WORKSHEET_COLUMN, QHeaderView.ResizeMode.ResizeToContents)
            self.worksheet_column = QuestionTableModel.WORKSHEET_COLUMN
        
        # For compatibility with older code
        self.student_history_column = QuestionTableModel.STUDENT_HISTORY_COLUMN
        
        # Connect double-click to view question
        self.question_table.doubleClicked.connect(self._handle_double_click)
        
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
            # Calculate pagination parameters
            limit = self.questions_per_page
            offset = (self.current_page - 1) * self.questions_per_page

            # Get total questions count for pagination (without fetching all questions)
            if self.filters:
                self.total_questions = self.question_manager.count_filtered_questions(self.filters)
            else:
                self.total_questions = self.question_manager.count_all_questions()
                
            # Apply student filtering if needed
            student_filter_applied = False
            if self.current_student_id and self.show_answered_questions:
                # Get answered question IDs for filtering
                answered_question_ids = set(self.student_answered_questions.keys())
                
                # Add to filters to exclude these questions at the database level
                if answered_question_ids:
                    if 'exclude_ids' not in self.filters:
                        self.filters['exclude_ids'] = []
                    self.filters['exclude_ids'].extend(list(answered_question_ids))
                    
                # Recalculate total count with exclusions
                if self.filters:
                    self.total_questions = self.question_manager.count_filtered_questions(self.filters)
                
                student_filter_applied = True
            
            # Fetch only the questions for the current page using LIMIT/OFFSET
            if self.filters:
                self.current_questions = self.question_manager.filter_questions(
                    self.filters, limit=limit, offset=offset
                )
            else:
                self.current_questions = self.question_manager.get_all_questions(
                    limit=limit, offset=offset
                )
            
            # Update results label with appropriate text based on filters
            label_text = ""
            if self.filters:
                # Create readable filter text (exclude internal exclude_ids filter)
                filter_text = ", ".join([f"{k}={v}" for k, v in self.filters.items() 
                                       if v and k != 'exclude_ids'])
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
            if self.current_page > total_pages and total_pages > 0:
                self.current_page = total_pages
                # Re-fetch with adjusted page if needed
                return self.refresh_questions()
            
            # Update page label
            self.page_label.setText(f"Page {self.current_page} of {total_pages}")
            
            # Enable/disable pagination buttons
            self.prev_page_button.setEnabled(self.current_page > 1)
            self.next_page_button.setEnabled(self.current_page < total_pages)
            
            # Populate table
            self._populate_table()
            
        except Exception as e:
            self.logger.error(f"Error refreshing questions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading questions: {str(e)}")
    
    def _populate_table(self):
        """Update the model with current questions data."""
        # Close any existing editors before updating data
        for row in range(self.model.rowCount()):
            self.question_table.closePersistentEditor(self.model.index(row, QuestionTableModel.STUDENT_HISTORY_COLUMN))
            if self.enable_worksheet_selection:
                self.question_table.closePersistentEditor(self.model.index(row, QuestionTableModel.WORKSHEET_COLUMN))
                
        # Update student data in delegates
        if hasattr(self, 'student_history_delegate'):
            self.student_history_delegate.setStudentAnsweredQuestions(self.student_answered_questions)
        
        # Update worksheet selection if enabled
        if self.enable_worksheet_selection and hasattr(self, 'worksheet_delegate'):
            # Convert list to dictionary for delegate
            selected_dict = {q.question_id: True for q in self.selected_for_worksheet}
            self.worksheet_delegate.setSelectedQuestions(selected_dict)
            self.worksheet_delegate.setStudentAnsweredQuestions(self.student_answered_questions)
            # Force update the delegate's data
            self.model.setSelectedForWorksheet(self.selected_for_worksheet)
            
        # Update model with current questions
        self.model.setQuestions(self.current_questions)
        self.model.setStudentAnsweredQuestions(self.student_answered_questions)
        self.model.setSelectedForWorksheet(self.selected_for_worksheet)
        
        # Open persistent editors for custom delegate columns after model update is complete
        for row in range(self.model.rowCount()):
            self.question_table.openPersistentEditor(self.model.index(row, QuestionTableModel.STUDENT_HISTORY_COLUMN))
            if self.enable_worksheet_selection:
                self.question_table.openPersistentEditor(self.model.index(row, QuestionTableModel.WORKSHEET_COLUMN))
        
        self.logger.debug(f"Updated model with {len(self.current_questions)} questions")
    
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
        self.show_answered_questions = (state == Qt.CheckState.Checked.value)
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
    
    def _handle_double_click(self, index):
        """Handle double-click on a question row."""
        if not index.isValid():
            return
            
        # Get question ID from the model - make sure we're handling clicks on any column
        row = index.row()
        
        # Avoid handling clicks on special columns with editors
        column = index.column()
        if column in [QuestionTableModel.STUDENT_HISTORY_COLUMN, 
                     QuestionTableModel.WORKSHEET_COLUMN]:
            return
            
        # Get question ID from the ID column
        model_index = self.model.index(row, QuestionTableModel.ID_COLUMN)
        question_id = int(self.model.data(model_index, Qt.ItemDataRole.DisplayRole))
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
        
        # Update model configuration
        self.model.setWorksheetSelectionEnabled(enabled)
        
        # Set up or remove worksheet delegate
        if enabled:
            # Create and configure worksheet delegate if it doesn't exist
            if not hasattr(self, 'worksheet_delegate'):
                self.worksheet_delegate = WorksheetSelectionDelegate(self)
                self.worksheet_delegate.addToWorksheet.connect(self._add_to_worksheet)
                self.worksheet_delegate.removeFromWorksheet.connect(self._remove_from_worksheet)
            
            # Set the delegate for the worksheet column
            self.question_table.setItemDelegateForColumn(QuestionTableModel.WORKSHEET_COLUMN, self.worksheet_delegate)
            
            # Set column resize mode
            self.question_table.horizontalHeader().setSectionResizeMode(
                QuestionTableModel.WORKSHEET_COLUMN, 
                QHeaderView.ResizeMode.ResizeToContents
            )
            
            # Update for compatibility with older code
            self.worksheet_column = QuestionTableModel.WORKSHEET_COLUMN
            
            # Make worksheet selection controls visible if they exist
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setParent(self)
                self.clear_worksheet_button.setParent(self)
                self.create_worksheet_button.setParent(self)
        else:
            # Remove worksheet delegate
            if hasattr(self, 'worksheet_delegate'):
                self.question_table.setItemDelegateForColumn(QuestionTableModel.WORKSHEET_COLUMN, None)
            
            # Update for compatibility with older code
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
    
    def _show_context_menu(self, position):
        """Show context menu with actions for the selected question."""
        # Get the row at the position clicked
        index = self.question_table.indexAt(position)
        if not index.isValid():
            return
        
        # Get question ID from the row
        row = index.row()
        id_index = self.model.index(row, QuestionTableModel.ID_COLUMN)
        question_id = int(self.model.data(id_index, Qt.ItemDataRole.DisplayRole))
        
        # Create menu and actions
        menu = QMenu(self)
        
        view_action = QAction("View Question", self)
        view_action.triggered.connect(lambda: self.view_question.emit(question_id))
        
        edit_action = QAction("Edit Question", self)
        edit_action.triggered.connect(lambda: self.edit_question.emit(question_id))
        
        delete_action = QAction("Delete Question", self)
        delete_action.triggered.connect(lambda: self._delete_question(question_id))
        
        # Add actions to menu
        menu.addAction(view_action)
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        # If worksheet selection is enabled, add those options too
        if self.enable_worksheet_selection:
            menu.addSeparator()
            
            # Get the full question object
            question = self.model.getQuestion(row)
            
            # Check if already in worksheet selection
            if any(q.question_id == question_id for q in self.selected_for_worksheet):
                worksheet_action = QAction("Remove from Worksheet", self)
                worksheet_action.triggered.connect(lambda: self._remove_from_worksheet(question))
            else:
                # Check if already answered by student
                already_answered = question_id in self.student_answered_questions
                if already_answered:
                    worksheet_action = QAction("Already Answered by Student", self)
                    worksheet_action.setEnabled(False)
                else:
                    worksheet_action = QAction("Add to Worksheet", self)
                    worksheet_action.triggered.connect(lambda: self._add_to_worksheet(question))
            
            menu.addAction(worksheet_action)
        
        # Show menu at cursor position
        menu.exec(self.question_table.viewport().mapToGlobal(position))
    
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
        
        # Difficulty with color coding
        difficulty_label = QLabel(question.difficulty_label)
        
        # Set style based on difficulty level
        if question.difficulty_label == "Easy":
            difficulty_label.setProperty("class", "difficulty-easy")
        elif question.difficulty_label == "Medium":
            difficulty_label.setProperty("class", "difficulty-medium")
        elif question.difficulty_label == "Hard":
            difficulty_label.setProperty("class", "difficulty-hard")
        elif question.difficulty_label == "Very Hard":
            difficulty_label.setProperty("class", "difficulty-very-hard")
            
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