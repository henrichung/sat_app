"""
Configuration manager for the SAT Question Bank application.
Loads, validates, and provides access to application settings.
"""
import os
import json
import logging
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages configuration settings for the application.
    
    Handles loading configuration from JSON, validating settings,
    and providing access to configuration values.
    """
    
    DEFAULT_CONFIG = {
        "database": {
            "path": "data/sat_app.db"
        },
        "images": {
            "question_images_dir": "data/images/questions",
            "answer_images_dir": "data/images/answers"
        },
        "output": {
            "worksheets_dir": "data/worksheets"
        },
        "ui": {
            "theme": "light",
            "font_size": 12
        }
    }
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
    
    def load_config(self) -> bool:
        """
        Load configuration from the config file.
        
        If the config file doesn't exist, create it with default values.
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Check if config file exists
            if not os.path.exists(self.config_path):
                self.logger.info(f"Config file not found at {self.config_path}. Creating default configuration.")
                self.config = self.DEFAULT_CONFIG
                self._save_config()
            else:
                # Load config from file
                with open(self.config_path, 'r') as config_file:
                    self.config = json.load(config_file)
                self.logger.info("Configuration loaded successfully")
            
            # Validate config
            if not self._validate_config():
                self.logger.error("Configuration validation failed")
                return False
            
            # Create required directories
            self._create_required_directories()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return False
    
    def _save_config(self) -> bool:
        """
        Save the current configuration to the config file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.config_path, 'w') as config_file:
                json.dump(self.config, config_file, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def _validate_config(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required sections
        required_sections = ["database", "images", "output"]
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate database configuration
        if "path" not in self.config["database"]:
            self.logger.error("Missing database path in configuration")
            return False
        
        # Validate image directories
        for img_dir in ["question_images_dir", "answer_images_dir"]:
            if img_dir not in self.config["images"]:
                self.logger.error(f"Missing {img_dir} in configuration")
                return False
        
        # Validate output directories
        if "worksheets_dir" not in self.config["output"]:
            self.logger.error("Missing worksheets_dir in configuration")
            return False
        
        return True
    
    def _create_required_directories(self) -> None:
        """Create all required directories specified in the configuration."""
        try:
            # Create data directory
            os.makedirs(os.path.dirname(self.config["database"]["path"]), exist_ok=True)
            
            # Create image directories
            os.makedirs(self.config["images"]["question_images_dir"], exist_ok=True)
            os.makedirs(self.config["images"]["answer_images_dir"], exist_ok=True)
            
            # Create output directories
            os.makedirs(self.config["output"]["worksheets_dir"], exist_ok=True)
            
            self.logger.info("Created required directories")
        except Exception as e:
            self.logger.error(f"Error creating directories: {str(e)}")
    
    def get_db_path(self) -> str:
        """
        Get the database file path.
        
        Returns:
            The path to the database file
        """
        return self.config["database"]["path"]
    
    def get_question_images_dir(self) -> str:
        """
        Get the directory for question images.
        
        Returns:
            The path to the question images directory
        """
        return self.config["images"]["question_images_dir"]
    
    def get_answer_images_dir(self) -> str:
        """
        Get the directory for answer images.
        
        Returns:
            The path to the answer images directory
        """
        return self.config["images"]["answer_images_dir"]
    
    def get_worksheets_dir(self) -> str:
        """
        Get the directory for generated worksheets.
        
        Returns:
            The path to the worksheets directory
        """
        return self.config["output"]["worksheets_dir"]
    
    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration setting.
        
        Args:
            section: The configuration section
            key: The configuration key
            default: Default value if the setting doesn't exist
        
        Returns:
            The configuration value, or the default if not found
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Update a configuration setting.
        
        Args:
            section: The configuration section
            key: The configuration key
            value: The new value
        
        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # Create section if it doesn't exist
            if section not in self.config:
                self.config[section] = {}
            
            # Update the setting
            self.config[section][key] = value
            
            # Save the updated configuration
            return self._save_config()
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.
        
        Returns:
            A copy of the configuration dictionary
        """
        # Create a flattened dictionary with key paths
        flat_config = {}
        
        # Add database path
        flat_config['db_path'] = self.get_db_path()
        
        # Add image paths
        flat_config['question_images_dir'] = self.get_question_images_dir()
        flat_config['answer_images_dir'] = self.get_answer_images_dir()
        
        # Add a combined images base path for the import/export manager
        images_base = os.path.dirname(self.get_question_images_dir())
        flat_config['image_base_path'] = images_base
        
        # Add worksheets directory
        flat_config['worksheets_dir'] = self.get_worksheets_dir()
        
        # Add UI settings if they exist
        if 'ui' in self.config:
            for key, value in self.config['ui'].items():
                flat_config[f'ui_{key}'] = value
        
        return flat_config