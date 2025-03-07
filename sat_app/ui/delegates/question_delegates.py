"""
Delegates for question table views.
Provides custom rendering and interaction for question table cells.
"""
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QStyledItemDelegate, QWidget, QHBoxLayout,
    QPushButton, QApplication, QStyleOptionViewItem, QLabel
)
from PyQt6.QtCore import Qt, QModelIndex, QRect, QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QPainter

from ..models.question_table_model import QuestionTableModel
from ...dal.models import Question


class ActionButtonDelegate(QStyledItemDelegate):
    """
    Delegate for rendering action buttons in a cell.
    
    Creates view, edit, and delete buttons for question actions.
    """
    
    # Signals
    viewQuestion = pyqtSignal(int)
    editQuestion = pyqtSignal(int)
    deleteQuestion = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the delegate.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the cell.
        
        Args:
            painter: Painter to use
            option: Style options
            index: Model index
        """
        # Clear the background
        painter.fillRect(option.rect, option.palette.base())
        
        # We don't actually paint anything here, as we'll use the editor for display
        # This allows us to have interactive buttons that respond to mouse clicks
        
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """
        Create an editor widget for this cell.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Widget containing action buttons
        """
        # Get question ID from the model
        question_id = index.model().data(
            index.siblingAtColumn(QuestionTableModel.ID_COLUMN), 
            Qt.ItemDataRole.DisplayRole
        )
        
        # Create widget with buttons
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # View button
        view_button = QPushButton("View")
        view_button.setProperty("question_id", question_id)
        view_button.clicked.connect(lambda: self.viewQuestion.emit(int(question_id)))
        layout.addWidget(view_button)
        
        # Edit button
        edit_button = QPushButton("Edit")
        edit_button.setProperty("question_id", question_id)
        edit_button.clicked.connect(lambda: self.editQuestion.emit(int(question_id)))
        layout.addWidget(edit_button)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setProperty("question_id", question_id)
        delete_button.clicked.connect(lambda: self.deleteQuestion.emit(int(question_id)))
        layout.addWidget(delete_button)
        
        return widget
    
    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Update the editor's geometry.
        
        Args:
            editor: Editor widget
            option: Style options
            index: Model index
        """
        editor.setGeometry(option.rect)


class StudentHistoryDelegate(QStyledItemDelegate):
    """
    Delegate for rendering student history information.
    
    Shows if a question has been answered by a student and in which worksheet.
    """
    
    # Signal for when a worksheet is clicked
    worksheetClicked = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the delegate.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self.student_answered_questions: Dict[int, Any] = {}
        
    def setStudentAnsweredQuestions(self, answered_questions: Dict[int, Any]) -> None:
        """
        Set the questions answered by a student.
        
        Args:
            answered_questions: Dictionary mapping question IDs to worksheet info
        """
        self.student_answered_questions = answered_questions
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the cell.
        
        Args:
            painter: Painter to use
            option: Style options
            index: Model index
        """
        # Clear the background
        painter.fillRect(option.rect, option.palette.base())
        
        # We don't actually paint anything here, as we'll use the editor for display
        
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """
        Create an editor widget for this cell.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Widget containing student history information
        """
        # Get question ID from the model
        question_id = int(index.model().data(
            index.siblingAtColumn(QuestionTableModel.ID_COLUMN), 
            Qt.ItemDataRole.DisplayRole
        ))
        
        # Create widget to display history
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        if question_id in self.student_answered_questions:
            # Question has been answered by this student
            worksheet_info = self.student_answered_questions[question_id]
            if isinstance(worksheet_info, list) and len(worksheet_info) == 2:
                worksheet_id, worksheet_title = worksheet_info
                
                # Display button showing which worksheet this was in
                history_button = QPushButton(f"In WS #{worksheet_id}")
                history_button.setToolTip(f"This question appeared in worksheet: {worksheet_title}")
                history_button.setStyleSheet("background-color: #FFD580;")  # Light orange color
                history_button.setProperty("worksheet_id", worksheet_id)
                history_button.clicked.connect(lambda: self.worksheetClicked.emit(worksheet_id))
                
                layout.addWidget(history_button)
            else:
                history_label = QLabel("✓ Answered")
                history_label.setStyleSheet("color: green; font-weight: bold;")
                layout.addWidget(history_label)
        else:
            # Question has not been answered by this student
            history_label = QLabel("Not seen")
            layout.addWidget(history_label)
        
        return widget
    
    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Update the editor's geometry.
        
        Args:
            editor: Editor widget
            option: Style options
            index: Model index
        """
        editor.setGeometry(option.rect)


class WorksheetSelectionDelegate(QStyledItemDelegate):
    """
    Delegate for rendering worksheet selection buttons.
    
    Allows adding or removing questions from the worksheet.
    """
    
    # Signals
    addToWorksheet = pyqtSignal(Question)
    removeFromWorksheet = pyqtSignal(Question)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the delegate.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self.selected_for_worksheet: Dict[int, bool] = {}
        self.student_answered_questions: Dict[int, Any] = {}
        
    def setSelectedQuestions(self, selected: Dict[int, bool]) -> None:
        """
        Set the selected questions.
        
        Args:
            selected: Dictionary mapping question IDs to selection state
        """
        self.selected_for_worksheet = selected
    
    def setStudentAnsweredQuestions(self, answered_questions: Dict[int, Any]) -> None:
        """
        Set the questions answered by a student.
        
        Args:
            answered_questions: Dictionary mapping question IDs to worksheet info
        """
        self.student_answered_questions = answered_questions
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Paint the cell.
        
        Args:
            painter: Painter to use
            option: Style options
            index: Model index
        """
        # Clear the background
        painter.fillRect(option.rect, option.palette.base())
        
        # We don't actually paint anything here, as we'll use the editor for display
        
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """
        Create an editor widget for this cell.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Widget containing worksheet selection button
        """
        # Get question from the model
        question = index.model().data(index, QuestionTableModel.QuestionRole)
        question_id = question.question_id
        
        # Create widget with button
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Check if this question has been answered by the current student
        # Here we just check if the question is in the answered questions dict
        already_answered = question_id in self.student_answered_questions
        
        # Check if question is already selected for worksheet
        is_selected = question_id in self.selected_for_worksheet
        
        # If already answered by this student, disable adding to worksheet
        if already_answered:
            add_button = QPushButton("Add")
            add_button.setEnabled(False)
            add_button.setToolTip("This question has already been answered by this student")
            layout.addWidget(add_button)
        elif is_selected:
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self.removeFromWorksheet.emit(question))
            layout.addWidget(remove_button)
        else:
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda: self.addToWorksheet.emit(question))
            layout.addWidget(add_button)
        
        return widget
    
    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        Update the editor's geometry.
        
        Args:
            editor: Editor widget
            option: Style options
            index: Model index
        """
        editor.setGeometry(option.rect)