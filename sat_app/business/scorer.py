"""
Scoring and analytics module for the SAT Question Bank application.
Provides functionality for recording student responses and computing analytics.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter

from sat_app.dal.repositories import ScoreRepository, QuestionRepository, WorksheetRepository
from sat_app.dal.models import Score, Question, Worksheet


class ScoringService:
    """
    Service for recording and analyzing student scores.
    
    Provides methods for recording student responses, calculating performance metrics,
    and generating analytics reports.
    """
    
    def __init__(self, score_repository: ScoreRepository, question_repository: QuestionRepository,
                 worksheet_repository: Optional[WorksheetRepository] = None):
        """
        Initialize the ScoringService.
        
        Args:
            score_repository: Repository for accessing score data
            question_repository: Repository for accessing question data
            worksheet_repository: Repository for accessing worksheet data (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.score_repository = score_repository
        self.question_repository = question_repository
        self.worksheet_repository = worksheet_repository
    
    def record_answer(self, student_id: str, worksheet_id: int, question_id: int, correct: bool) -> bool:
        """
        Record a student's answer for a question.
        
        Args:
            student_id: ID of the student
            worksheet_id: ID of the worksheet
            question_id: ID of the question
            correct: Whether the answer was correct
        
        Returns:
            True if the score was recorded successfully, False otherwise
        """
        try:
            score = Score(
                student_id=student_id,
                worksheet_id=worksheet_id,
                question_id=question_id,
                correct=correct
            )
            
            score_id = self.score_repository.add_score(score)
            return score_id is not None
            
        except Exception as e:
            self.logger.error(f"Error recording answer: {str(e)}")
            return False
    
    def get_student_scores(self, student_id: str) -> List[Score]:
        """
        Get all scores for a student.
        
        Args:
            student_id: ID of the student
        
        Returns:
            List of Score objects for the student
        """
        return self.score_repository.get_scores_by_student(student_id)
    
    def calculate_student_performance(self, student_id: str) -> Dict[str, Any]:
        """
        Calculate performance metrics for a student.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Dictionary of performance metrics
        """
        scores = self.score_repository.get_scores_by_student(student_id)
        
        # If no scores, return empty metrics
        if not scores:
            return {
                "student_id": student_id,
                "total_questions": 0,
                "total_correct": 0,
                "percentage_correct": 0,
                "worksheets_completed": 0,
                "subject_performance": {},
                "difficulty_performance": {},
                "recent_performance": []
            }
        
        # Get all question IDs from scores
        question_ids = [score.question_id for score in scores]
        
        # Get question details for analysis
        questions = []
        for question_id in question_ids:
            question = self.question_repository.get_question(question_id)
            if question:
                questions.append(question)
        
        # Calculate basic metrics
        total_questions = len(scores)
        total_correct = sum(1 for score in scores if score.correct)
        percentage_correct = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate unique worksheets completed
        worksheets_completed = len(set(score.worksheet_id for score in scores))
        
        # Calculate performance by subject
        subject_performance = self._calculate_subject_performance(scores, questions)
        
        # Calculate performance by difficulty
        difficulty_performance = self._calculate_difficulty_performance(scores, questions)
        
        # Calculate recent performance trend
        recent_performance = self._calculate_recent_performance(scores)
        
        return {
            "student_id": student_id,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "percentage_correct": percentage_correct,
            "worksheets_completed": worksheets_completed,
            "subject_performance": subject_performance,
            "difficulty_performance": difficulty_performance,
            "recent_performance": recent_performance
        }
    
    def calculate_question_performance(self, question_id: int) -> Dict[str, Any]:
        """
        Calculate performance metrics for a specific question.
        
        Args:
            question_id: ID of the question
        
        Returns:
            Dictionary of performance metrics for the question
        """
        # Get all scores for this question
        scores = self._get_all_scores_for_question(question_id)
        
        # If no scores, return empty metrics
        if not scores:
            return {
                "question_id": question_id,
                "total_attempts": 0,
                "correct_attempts": 0,
                "success_rate": 0,
                "student_count": 0
            }
        
        # Calculate metrics
        total_attempts = len(scores)
        correct_attempts = sum(1 for score in scores if score.correct)
        success_rate = (correct_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        student_count = len(set(score.student_id for score in scores))
        
        return {
            "question_id": question_id,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "success_rate": success_rate,
            "student_count": student_count
        }
    
    def calculate_worksheet_performance(self, worksheet_id: int) -> Dict[str, Any]:
        """
        Calculate performance metrics for a specific worksheet.
        
        Args:
            worksheet_id: ID of the worksheet
        
        Returns:
            Dictionary of performance metrics for the worksheet
        """
        # Get all scores for this worksheet
        scores = self.score_repository.get_scores_by_worksheet(worksheet_id)
        
        # If no scores, return empty metrics
        if not scores:
            return {
                "worksheet_id": worksheet_id,
                "total_attempts": 0,
                "average_score": 0,
                "student_count": 0,
                "student_performances": []
            }
        
        # Get unique students who attempted this worksheet
        student_ids = set(score.student_id for score in scores)
        student_count = len(student_ids)
        
        # Calculate performance for each student
        student_performances = []
        for student_id in student_ids:
            student_scores = [score for score in scores if score.student_id == student_id]
            total_questions = len(student_scores)
            correct_answers = sum(1 for score in student_scores if score.correct)
            percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            student_performances.append({
                "student_id": student_id,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "percentage": percentage
            })
        
        # Calculate average score across all students
        average_score = statistics.mean([perf["percentage"] for perf in student_performances]) if student_performances else 0
        
        return {
            "worksheet_id": worksheet_id,
            "total_attempts": len(student_performances),
            "average_score": average_score,
            "student_count": student_count,
            "student_performances": student_performances
        }
    
    def get_comparative_analytics(self) -> Dict[str, Any]:
        """
        Get comparative analytics across all students.
        
        Returns:
            Dictionary of comparative analytics
        """
        # Get all scores
        all_scores = self._get_all_scores()
        
        # If no scores, return empty metrics
        if not all_scores:
            return {
                "total_students": 0,
                "total_questions_answered": 0,
                "average_score": 0,
                "difficult_questions": [],
                "easy_questions": []
            }
        
        # Get unique students
        student_ids = set(score.student_id for score in all_scores)
        total_students = len(student_ids)
        
        # Calculate total questions answered
        total_questions_answered = len(all_scores)
        
        # Calculate average score across all students
        correct_answers = sum(1 for score in all_scores if score.correct)
        average_score = (correct_answers / total_questions_answered) * 100 if total_questions_answered > 0 else 0
        
        # Identify difficult and easy questions
        question_performance = self._calculate_question_success_rates(all_scores)
        
        # Sort by success rate
        sorted_questions = sorted(question_performance.items(), key=lambda x: x[1])
        
        # Get 5 most difficult questions (lowest success rate)
        difficult_questions = [{"question_id": q_id, "success_rate": rate} for q_id, rate in sorted_questions[:5]]
        
        # Get 5 easiest questions (highest success rate)
        easy_questions = [{"question_id": q_id, "success_rate": rate} for q_id, rate in sorted_questions[-5:]]
        
        return {
            "total_students": total_students,
            "total_questions_answered": total_questions_answered,
            "average_score": average_score,
            "difficult_questions": difficult_questions,
            "easy_questions": easy_questions
        }
    
    def get_mastery_levels(self, student_id: str) -> Dict[str, Any]:
        """
        Calculate mastery levels for a student by subject.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Dictionary of mastery levels by subject
        """
        scores = self.score_repository.get_scores_by_student(student_id)
        
        # If no scores, return empty result
        if not scores:
            return {
                "student_id": student_id,
                "mastery_levels": {}
            }
        
        # Get all question IDs from scores
        question_ids = [score.question_id for score in scores]
        
        # Get question details for analysis
        questions = []
        for question_id in question_ids:
            question = self.question_repository.get_question(question_id)
            if question:
                questions.append(question)
        
        # Map each score to its question
        # Use a list of tuples instead of a dict with Score objects as keys
        score_question_pairs = []
        for score in scores:
            for question in questions:
                if score.question_id == question.question_id:
                    score_question_pairs.append((score, question))
                    break
        
        # Group by subject
        subject_scores = defaultdict(list)
        for score, question in score_question_pairs:
            for tag in question.subject_tags:
                subject_scores[tag].append(score.correct)
        
        # Calculate mastery level for each subject
        mastery_levels = {}
        for subject, results in subject_scores.items():
            if not results:
                continue
            
            correct_count = sum(1 for result in results if result)
            total_count = len(results)
            
            percentage = (correct_count / total_count) * 100 if total_count > 0 else 0
            
            # Define mastery levels
            if percentage >= 90:
                level = "Expert"
            elif percentage >= 75:
                level = "Proficient"
            elif percentage >= 60:
                level = "Competent"
            elif percentage >= 40:
                level = "Developing"
            else:
                level = "Needs Improvement"
            
            mastery_levels[subject] = {
                "percentage": percentage,
                "level": level,
                "questions_attempted": total_count,
                "questions_correct": correct_count
            }
        
        return {
            "student_id": student_id,
            "mastery_levels": mastery_levels
        }
    
    def _calculate_subject_performance(self, scores: List[Score], questions: List[Question]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance by subject.
        
        Args:
            scores: List of Score objects
            questions: List of Question objects
        
        Returns:
            Dictionary of performance metrics by subject
        """
        # Map question ID to question
        question_map = {q.question_id: q for q in questions}
        
        # Group scores by subject
        subject_scores = defaultdict(list)
        for score in scores:
            if score.question_id in question_map:
                question = question_map[score.question_id]
                for tag in question.subject_tags:
                    subject_scores[tag].append(score.correct)
        
        # Calculate performance for each subject
        subject_performance = {}
        for subject, results in subject_scores.items():
            correct = sum(1 for result in results if result)
            total = len(results)
            percentage = (correct / total) * 100 if total > 0 else 0
            
            subject_performance[subject] = {
                "correct": correct,
                "total": total,
                "percentage": percentage
            }
        
        return subject_performance
    
    def _calculate_difficulty_performance(self, scores: List[Score], questions: List[Question]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance by difficulty level.
        
        Args:
            scores: List of Score objects
            questions: List of Question objects
        
        Returns:
            Dictionary of performance metrics by difficulty level
        """
        # Map question ID to question
        question_map = {q.question_id: q for q in questions}
        
        # Group scores by difficulty
        difficulty_scores = defaultdict(list)
        for score in scores:
            if score.question_id in question_map:
                question = question_map[score.question_id]
                difficulty = question.difficulty_label or "Unspecified"
                difficulty_scores[difficulty].append(score.correct)
        
        # Calculate performance for each difficulty level
        difficulty_performance = {}
        for difficulty, results in difficulty_scores.items():
            correct = sum(1 for result in results if result)
            total = len(results)
            percentage = (correct / total) * 100 if total > 0 else 0
            
            difficulty_performance[difficulty] = {
                "correct": correct,
                "total": total,
                "percentage": percentage
            }
        
        return difficulty_performance
    
    def _calculate_recent_performance(self, scores: List[Score]) -> List[Dict[str, Any]]:
        """
        Calculate recent performance trend.
        
        Args:
            scores: List of Score objects
        
        Returns:
            List of performance metrics over time
        """
        # Sort scores by timestamp in ascending order
        sorted_scores = sorted(scores, key=lambda s: s.timestamp)
        
        # Group scores by day
        daily_scores = defaultdict(list)
        for score in sorted_scores:
            day = score.timestamp.date()
            daily_scores[day].append(score.correct)
        
        # Calculate daily performance
        daily_performance = []
        for day, results in sorted(daily_scores.items()):
            correct = sum(1 for result in results if result)
            total = len(results)
            percentage = (correct / total) * 100 if total > 0 else 0
            
            daily_performance.append({
                "date": day.isoformat(),
                "correct": correct,
                "total": total,
                "percentage": percentage
            })
        
        # Return the last 30 days of data (or less if not available)
        return daily_performance[-30:]
    
    def _get_all_scores(self) -> List[Score]:
        """
        Get all scores from the database.
        
        Returns:
            List of all Score objects
        """
        try:
            # This is a custom query that needs to be implemented in the repository
            # For now, we'll use a workaround to get all scores
            query = "SELECT * FROM scores"
            result = self.score_repository.db_manager.execute_query(query)
            
            if not result:
                return []
            
            return [Score.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting all scores: {str(e)}")
            return []
    
    def _get_all_scores_for_question(self, question_id: int) -> List[Score]:
        """
        Get all scores for a specific question.
        
        Args:
            question_id: ID of the question
        
        Returns:
            List of Score objects for the question
        """
        try:
            query = "SELECT * FROM scores WHERE question_id = ?"
            result = self.score_repository.db_manager.execute_query(query, (question_id,))
            
            if not result:
                return []
            
            return [Score.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting scores for question: {str(e)}")
            return []
    
    def _calculate_question_success_rates(self, scores: List[Score]) -> Dict[int, float]:
        """
        Calculate success rates for each question.
        
        Args:
            scores: List of Score objects
        
        Returns:
            Dictionary of question IDs mapped to success rates
        """
        # Group scores by question ID
        question_scores = defaultdict(list)
        for score in scores:
            question_scores[score.question_id].append(score.correct)
        
        # Calculate success rate for each question
        question_success_rates = {}
        for question_id, results in question_scores.items():
            correct = sum(1 for result in results if result)
            total = len(results)
            success_rate = (correct / total) * 100 if total > 0 else 0
            question_success_rates[question_id] = success_rate
        
        return question_success_rates
        
    def record_bulk_answers(self, student_id: str, worksheet_id: int, 
                           responses: Dict[int, bool]) -> Dict[str, Any]:
        """
        Record multiple student responses for a worksheet.
        
        Args:
            student_id: ID of the student
            worksheet_id: ID of the worksheet
            responses: Dictionary mapping question IDs to correctness (True/False)
        
        Returns:
            Dictionary with results of the operation
        """
        try:
            success_count = 0
            error_count = 0
            
            for question_id, correct in responses.items():
                try:
                    result = self.record_answer(student_id, worksheet_id, question_id, correct)
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    self.logger.error(f"Error recording response for question {question_id}: {str(e)}")
                    error_count += 1
            
            return {
                "success": True,
                "success_count": success_count,
                "error_count": error_count,
                "total_responses": len(responses)
            }
        except Exception as e:
            self.logger.error(f"Error in bulk recording: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_student_worksheet_status(self, student_id: str, worksheet_id: int) -> Dict[str, Any]:
        """
        Get the status of a student's responses for a worksheet.
        
        Args:
            student_id: ID of the student
            worksheet_id: ID of the worksheet
        
        Returns:
            Dictionary with worksheet response status
        """
        try:
            # Get the worksheet to retrieve all question IDs
            worksheet = None
            if self.worksheet_repository:
                worksheet = self.worksheet_repository.get_worksheet(worksheet_id)
            
            if not worksheet:
                return {
                    "success": False,
                    "error": f"Worksheet {worksheet_id} not found"
                }
            
            # Get all student scores for this worksheet
            student_scores = self.score_repository.get_student_worksheet_scores(student_id, worksheet_id)
            
            # Create a map of question ID to score
            scored_questions = {score.question_id: score.correct for score in student_scores}
            
            # Determine which questions have been answered and which are still pending
            answered_questions = []
            unanswered_questions = []
            
            for q_id in worksheet.question_ids:
                question = self.question_repository.get_question(q_id)
                if not question:
                    continue
                
                question_data = {
                    "id": q_id,
                    "text": question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text
                }
                
                if q_id in scored_questions:
                    question_data["answered"] = True
                    question_data["correct"] = scored_questions[q_id]
                    answered_questions.append(question_data)
                else:
                    question_data["answered"] = False
                    unanswered_questions.append(question_data)
            
            # Calculate statistics
            total_questions = len(worksheet.question_ids)
            answered_count = len(answered_questions)
            correct_count = sum(1 for q in answered_questions if q.get("correct", False))
            
            return {
                "success": True,
                "student_id": student_id,
                "worksheet_id": worksheet_id,
                "worksheet_title": worksheet.title,
                "total_questions": total_questions,
                "answered_count": answered_count,
                "unanswered_count": total_questions - answered_count,
                "correct_count": correct_count,
                "percentage_correct": (correct_count / answered_count * 100) if answered_count > 0 else 0,
                "completion_percentage": (answered_count / total_questions * 100) if total_questions > 0 else 0,
                "answered_questions": answered_questions,
                "unanswered_questions": unanswered_questions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting student worksheet status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_worksheets(self) -> List[Dict[str, Any]]:
        """
        Get a list of available worksheets for student responses.
        
        Returns:
            List of worksheets with basic information
        """
        try:
            if not self.worksheet_repository:
                self.logger.error("Worksheet repository not available")
                return []
            
            worksheets = self.worksheet_repository.get_all_worksheets()
            
            return [
                {
                    "id": worksheet.worksheet_id,
                    "title": worksheet.title,
                    "description": worksheet.description,
                    "question_count": len(worksheet.question_ids)
                }
                for worksheet in worksheets
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting available worksheets: {str(e)}")
            return []
    
    def get_questions_for_worksheet(self, worksheet_id: int) -> List[Dict[str, Any]]:
        """
        Get all questions for a worksheet with answer choices.
        
        Args:
            worksheet_id: ID of the worksheet
        
        Returns:
            List of questions with their answer choices
        """
        try:
            # Get the worksheet
            if not self.worksheet_repository:
                self.logger.error("Worksheet repository not available")
                return []
                
            worksheet = self.worksheet_repository.get_worksheet(worksheet_id)
            
            if not worksheet:
                self.logger.error(f"Worksheet {worksheet_id} not found")
                return []
            
            # Get all questions
            questions = []
            for q_id in worksheet.question_ids:
                question = self.question_repository.get_question(q_id)
                
                if question:
                    questions.append({
                        "id": question.question_id,
                        "text": question.question_text,
                        "image": question.question_image_path,
                        "answers": {
                            "A": question.answer_a,
                            "B": question.answer_b,
                            "C": question.answer_c,
                            "D": question.answer_d
                        },
                        "answer_images": {
                            "A": question.answer_image_a,
                            "B": question.answer_image_b,
                            "C": question.answer_image_c,
                            "D": question.answer_image_d
                        },
                        "correct_answer": question.correct_answer
                    })
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error getting questions for worksheet: {str(e)}")
            return []
    
    def clear_student_worksheet_responses(self, student_id: str, worksheet_id: int) -> Dict[str, Any]:
        """
        Clear all responses for a student's worksheet.
        
        Args:
            student_id: ID of the student
            worksheet_id: ID of the worksheet
        
        Returns:
            Dictionary with results of the operation
        """
        try:
            # Execute a custom query to delete all scores for this student and worksheet
            query = "DELETE FROM scores WHERE student_id = ? AND worksheet_id = ?"
            result = self.score_repository.db_manager.execute_query(query, (student_id, worksheet_id))
            
            if result is not None:
                return {
                    "success": True,
                    "message": f"Cleared all responses for student {student_id} on worksheet {worksheet_id}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to clear responses"
                }
                
        except Exception as e:
            self.logger.error(f"Error clearing student worksheet responses: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_students(self) -> List[str]:
        """
        Get a list of all student IDs who have recorded responses.
        
        Returns:
            List of unique student IDs
        """
        try:
            query = "SELECT DISTINCT student_id FROM scores ORDER BY student_id"
            result = self.score_repository.db_manager.execute_query(query)
            
            if not result:
                return []
            
            return [row['student_id'] for row in result]
            
        except Exception as e:
            self.logger.error(f"Error getting all students: {str(e)}")
            return []