"""
Table model for question data.
Provides a model for displaying questions in a table view.
"""
from typing import List, Any, Optional, Dict
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QObject

from ...dal.models import Question


class QuestionTableModel(QAbstractTableModel):
    """
    Table model for question data.
    
    Provides a model for use with QTableView to display questions with
    sorting, filtering, and custom data roles for specialized display.
    """
    
    # Custom roles
    QuestionRole = Qt.ItemDataRole.UserRole + 1
    QuestionIdRole = Qt.ItemDataRole.UserRole + 2
    
    # Column indices
    ID_COLUMN = 0
    TEXT_COLUMN = 1
    TAGS_COLUMN = 2
    DIFFICULTY_COLUMN = 3
    STUDENT_HISTORY_COLUMN = 4
    WORKSHEET_COLUMN = 5
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the model.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self.questions: List[Question] = []
        
        # For tracking student answered questions
        self.student_answered_questions: Dict[int, Any] = {}
        
        # For tracking worksheet selection
        self.worksheet_selection_enabled = False
        self.selected_for_worksheet: List[Question] = []
        
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of rows.
        
        Args:
            parent: Parent index
            
        Returns:
            Number of rows
        """
        return len(self.questions)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of columns.
        
        Args:
            parent: Parent index
            
        Returns:
            Number of columns
        """
        base_columns = 4  # ID, Question, Tags, Difficulty
        student_column = 1  # Student history
        worksheet_column = 1 if self.worksheet_selection_enabled else 0  # Worksheet
        
        return base_columns + student_column + worksheet_column
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get data for the specified index and role.
        
        Args:
            index: The model index
            role: The data role
            
        Returns:
            The data for the role
        """
        if not index.isValid() or index.row() >= len(self.questions):
            return None
        
        row = index.row()
        col = index.column()
        question = self.questions[row]
        
        # Basic display roles
        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.ID_COLUMN:
                return str(question.question_id)
            elif col == self.TEXT_COLUMN:
                # Truncate long text
                text = question.question_text
                if len(text) > 100:
                    return text[:97] + "..."
                return text
            elif col == self.TAGS_COLUMN:
                return ", ".join(question.subject_tags) if question.subject_tags else ""
            elif col == self.DIFFICULTY_COLUMN:
                return question.difficulty_label
        
        # Custom roles
        elif role == self.QuestionRole:
            return question
        elif role == self.QuestionIdRole:
            return question.question_id
            
        # Make sure we return the Question object for all columns to support delegates
        elif col in [self.STUDENT_HISTORY_COLUMN, self.WORKSHEET_COLUMN]:
            if role == Qt.ItemDataRole.UserRole:
                return question
        
        # Special handling for text alignment
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == self.ID_COLUMN:
                return Qt.AlignmentFlag.AlignCenter
            else:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Get header data.
        
        Args:
            section: Section index
            orientation: Orientation
            role: Data role
            
        Returns:
            Header data
        """
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            headers = ["ID", "Question", "Tags", "Difficulty", "Student History"]
            
            # Add worksheet column if enabled
            if self.worksheet_selection_enabled:
                headers.append("Worksheet")
            
            if 0 <= section < len(headers):
                return headers[section]
        
        return None
    
    def setQuestions(self, questions: List[Question]) -> None:
        """
        Set the questions data.
        
        Args:
            questions: List of Question objects
        """
        self.beginResetModel()
        self.questions = questions
        self.endResetModel()
    
    def setStudentAnsweredQuestions(self, answered_questions: Dict[int, Any]) -> None:
        """
        Set the questions answered by a student.
        
        Args:
            answered_questions: Dictionary mapping question IDs to worksheet info
        """
        self.beginResetModel()
        self.student_answered_questions = answered_questions
        self.endResetModel()
    
    def setWorksheetSelectionEnabled(self, enabled: bool) -> None:
        """
        Set whether worksheet selection is enabled.
        
        Args:
            enabled: Whether to enable worksheet selection
        """
        if self.worksheet_selection_enabled == enabled:
            return
            
        self.beginResetModel()
        self.worksheet_selection_enabled = enabled
        self.endResetModel()
    
    def setSelectedForWorksheet(self, selected: List[Question]) -> None:
        """
        Set the questions selected for a worksheet.
        
        Args:
            selected: List of questions selected for worksheet
        """
        self.beginResetModel()
        self.selected_for_worksheet = selected
        self.endResetModel()
    
    def isSelectedForWorksheet(self, question_id: int) -> bool:
        """
        Check if a question is selected for the worksheet.
        
        Args:
            question_id: ID of the question
            
        Returns:
            True if selected, False otherwise
        """
        return any(q.question_id == question_id for q in self.selected_for_worksheet)
        
    def getSelectedForWorksheetDict(self) -> Dict[int, bool]:
        """
        Get a dictionary of selected question IDs.
        
        Returns:
            Dictionary mapping question IDs to True if selected
        """
        return {q.question_id: True for q in self.selected_for_worksheet}
    
    def getQuestion(self, row: int) -> Optional[Question]:
        """
        Get the question at the specified row.
        
        Args:
            row: Row index
            
        Returns:
            Question at the row, or None if out of bounds
        """
        if 0 <= row < len(self.questions):
            return self.questions[row]
        return None