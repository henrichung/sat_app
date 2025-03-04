"""
Factory for business layer managers.
Provides centralized creation of manager instances.
"""
import logging
import os
from typing import Dict, Any, Optional

from ..dal.database_manager import DatabaseManager
from ..dal.repositories import QuestionRepository, ScoreRepository, WorksheetRepository
from ..utils.logger import get_logger
from .question_manager import QuestionManager
from .worksheet_generator import WorksheetGenerator
from .scorer import ScoringService
from .import_export_manager import ImportExportManager
from .settings_manager import SettingsManager
from ..config.config_manager import ConfigManager


class ManagerFactory:
    """
    Factory for creating and caching business layer manager instances.
    
    Ensures that managers are properly initialized with their dependencies
    and reused across the application.
    """
    
    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any] = None, config_manager: ConfigManager = None):
        """
        Initialize the ManagerFactory.
        
        Args:
            db_manager: Database manager instance
            config: Configuration dictionary (optional)
            config_manager: Configuration manager instance (optional)
        """
        self.logger = get_logger(__name__)
        self.db_manager = db_manager
        self.config = config or {}
        self.config_manager = config_manager
        self._repositories: Dict[str, Any] = {}
        self._managers: Dict[str, Any] = {}
    
    def get_question_repository(self) -> QuestionRepository:
        """
        Get the QuestionRepository instance.
        
        Returns:
            A QuestionRepository instance
        """
        if 'question_repository' not in self._repositories:
            self._repositories['question_repository'] = QuestionRepository(self.db_manager)
            self.logger.debug("Created QuestionRepository instance")
        
        return self._repositories['question_repository']
    
    def get_score_repository(self) -> ScoreRepository:
        """
        Get the ScoreRepository instance.
        
        Returns:
            A ScoreRepository instance
        """
        if 'score_repository' not in self._repositories:
            self._repositories['score_repository'] = ScoreRepository(self.db_manager)
            self.logger.debug("Created ScoreRepository instance")
        
        return self._repositories['score_repository']
    
    def get_question_manager(self) -> QuestionManager:
        """
        Get the QuestionManager instance.
        
        Returns:
            A QuestionManager instance
        """
        if 'question_manager' not in self._managers:
            # Get or create the repository
            question_repository = self.get_question_repository()
            
            # Create the manager with the repository
            self._managers['question_manager'] = QuestionManager(question_repository)
            self.logger.debug("Created QuestionManager instance")
        
        return self._managers['question_manager']
    
    def get_worksheet_repository(self) -> WorksheetRepository:
        """
        Get the WorksheetRepository instance.
        
        Returns:
            A WorksheetRepository instance
        """
        if 'worksheet_repository' not in self._repositories:
            self._repositories['worksheet_repository'] = WorksheetRepository(self.db_manager)
            self.logger.debug("Created WorksheetRepository instance")
        
        return self._repositories['worksheet_repository']

    def get_worksheet_generator(self) -> WorksheetGenerator:
        """
        Get the WorksheetGenerator instance.
        
        Returns:
            A WorksheetGenerator instance
        """
        if 'worksheet_generator' not in self._managers:
            # Get or create the repositories
            question_repository = self.get_question_repository()
            worksheet_repository = self.get_worksheet_repository()
            
            # Create the generator with the repositories
            self._managers['worksheet_generator'] = WorksheetGenerator(
                question_repository, 
                worksheet_repository
            )
            self.logger.debug("Created WorksheetGenerator instance")
        
        return self._managers['worksheet_generator']
    
    def get_scoring_service(self) -> ScoringService:
        """
        Get the ScoringService instance.
        
        Returns:
            A ScoringService instance
        """
        if 'scoring_service' not in self._managers:
            # Get or create the repositories
            score_repository = self.get_score_repository()
            question_repository = self.get_question_repository()
            
            # Get the worksheet repository if available
            worksheet_repository = None
            if 'worksheet_repository' in self._repositories:
                worksheet_repository = self._repositories['worksheet_repository']
            else:
                # Create worksheet repository if needed
                from ..dal.repositories import WorksheetRepository
                worksheet_repository = WorksheetRepository(self.db_manager)
                self._repositories['worksheet_repository'] = worksheet_repository
                self.logger.debug("Created WorksheetRepository instance for ScoringService")
            
            # Create the service with the repositories
            self._managers['scoring_service'] = ScoringService(
                score_repository, 
                question_repository,
                worksheet_repository
            )
            self.logger.debug("Created ScoringService instance")
        
        return self._managers['scoring_service']
        
    def get_import_export_manager(self) -> ImportExportManager:
        """
        Get the ImportExportManager instance.
        
        Returns:
            An ImportExportManager instance
        """
        if 'import_export_manager' not in self._managers:
            # Get or create the repository
            question_repository = self.get_question_repository()
            
            # Get the image base path from configuration
            # Default to data/images if not specified
            image_base_path = self.config.get('image_base_path', 'data/images')
            
            # Make sure the path is absolute
            if not os.path.isabs(image_base_path):
                # If it's a relative path, make it absolute based on the current working directory
                image_base_path = os.path.abspath(image_base_path)
            
            # Create the manager with the repository and image path
            self._managers['import_export_manager'] = ImportExportManager(
                question_repository,
                image_base_path
            )
            self.logger.debug(f"Created ImportExportManager instance with image path: {image_base_path}")
        
        return self._managers['import_export_manager']
        
    def get_settings_manager(self) -> SettingsManager:
        """
        Get the SettingsManager instance.
        
        Returns:
            A SettingsManager instance
        """
        if 'settings_manager' not in self._managers:
            # Check if we have a config manager
            if not self.config_manager:
                raise ValueError("ConfigManager is required to create SettingsManager")
            
            # Create the manager with the config manager
            self._managers['settings_manager'] = SettingsManager(self.config_manager)
            self.logger.debug("Created SettingsManager instance")
        
        return self._managers['settings_manager']