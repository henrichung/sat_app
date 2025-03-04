"""
Settings manager for the SAT Question Bank application.
Handles application settings management, validation, and persistence.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple

from sat_app.config.config_manager import ConfigManager


class SettingsManager:
    """
    Manages application settings.
    
    Provides an interface for accessing and updating application settings,
    with validation and persistence through the ConfigManager.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the SettingsManager.
        
        Args:
            config_manager: The application configuration manager
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all application settings organized by section.
        
        Returns:
            A dictionary containing all settings organized by section
        """
        return self.config_manager.config
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """
        Get all UI-specific settings.
        
        Returns:
            A dictionary containing UI settings
        """
        if 'ui' in self.config_manager.config:
            return self.config_manager.config['ui']
        return {}
    
    def get_database_settings(self) -> Dict[str, Any]:
        """
        Get all database-specific settings.
        
        Returns:
            A dictionary containing database settings
        """
        if 'database' in self.config_manager.config:
            return self.config_manager.config['database']
        return {}
    
    def get_image_settings(self) -> Dict[str, Any]:
        """
        Get all image-specific settings.
        
        Returns:
            A dictionary containing image settings
        """
        if 'images' in self.config_manager.config:
            return self.config_manager.config['images']
        return {}
    
    def get_output_settings(self) -> Dict[str, Any]:
        """
        Get all output-specific settings.
        
        Returns:
            A dictionary containing output settings
        """
        if 'output' in self.config_manager.config:
            return self.config_manager.config['output']
        return {}
    
    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Update a specific setting value.
        
        Args:
            section: The configuration section
            key: The configuration key
            value: The new value
            
        Returns:
            True if the update was successful, False otherwise
        """
        # Validate the setting before updating
        if not self._validate_setting(section, key, value):
            self.logger.error(f"Invalid setting value for {section}.{key}: {value}")
            return False
            
        # Update the setting
        result = self.config_manager.update_setting(section, key, value)
        
        # Handle special cases, like directory creation after path changes
        if result and self._is_path_setting(section, key):
            self._handle_path_update(section, key, value)
            
        return result
    
    def get_available_themes(self) -> List[str]:
        """
        Get a list of available UI themes.
        
        Returns:
            A list of available theme names
        """
        # Currently supported themes
        return ["light", "dark", "system"]
    
    def get_available_font_sizes(self) -> List[int]:
        """
        Get a list of available font sizes.
        
        Returns:
            A list of available font sizes
        """
        # Common font size options
        return [8, 9, 10, 11, 12, 14, 16, 18, 20]
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to their default values.
        
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            # Replace the current config with the default config
            self.config_manager.config = self.config_manager.DEFAULT_CONFIG.copy()
            
            # Save the configuration
            result = self.config_manager._save_config()
            
            # Create required directories
            self.config_manager._create_required_directories()
            
            return result
        except Exception as e:
            self.logger.error(f"Error resetting to default settings: {str(e)}")
            return False
    
    def _validate_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Validate a setting value.
        
        Args:
            section: The configuration section
            key: The configuration key
            value: The value to validate
            
        Returns:
            True if the value is valid, False otherwise
        """
        # Validate UI settings
        if section == "ui":
            if key == "theme" and value not in self.get_available_themes():
                return False
            if key == "font_size" and not isinstance(value, int):
                return False
            if key == "font_size" and value not in self.get_available_font_sizes():
                return False
                
        # Validate path settings
        if self._is_path_setting(section, key):
            # Path cannot be empty
            if not value:
                return False
        
        return True
    
    def _is_path_setting(self, section: str, key: str) -> bool:
        """
        Check if a setting is a file path setting.
        
        Args:
            section: The configuration section
            key: The configuration key
            
        Returns:
            True if the setting is a path setting, False otherwise
        """
        path_settings = {
            "database": ["path"],
            "images": ["question_images_dir", "answer_images_dir"],
            "output": ["worksheets_dir"]
        }
        
        return section in path_settings and key in path_settings[section]
    
    def _handle_path_update(self, section: str, key: str, value: Any) -> None:
        """
        Handle updates to path settings.
        
        This may involve creating new directories or migrating data.
        
        Args:
            section: The configuration section
            key: The configuration key
            value: The new path value
        """
        # Create the directory if it doesn't exist
        try:
            import os
            os.makedirs(value, exist_ok=True)
            self.logger.info(f"Created directory for updated path setting: {value}")
        except Exception as e:
            self.logger.error(f"Error creating directory for path setting: {str(e)}")