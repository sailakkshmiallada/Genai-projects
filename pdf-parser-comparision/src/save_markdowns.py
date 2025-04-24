"""
Markdown File Saving Module

This module provides functionality for saving markdown content to files in a 
designated results directory. It handles file path creation, directory existence 
checks, and proper file encoding.
"""

import os
from pathlib import Path
from .logger import setup_logger

# Initialize module logger
logger = setup_logger(__name__)

def save_markdown(content: str, filename: str) -> None:
    """
    Save markdown content to a file in the results/ folder.
    
    Args:
        content (str): Markdown content to save
        filename (str): Name of the file (with or without .md extension)
            
    Raises:
        ValueError: If content or filename is invalid
        OSError: If file creation or writing fails
    """
    try:
        # Input validation
        if not content:
            logger.warning("Empty content provided for saving")
        
        if not filename:
            logger.error("No filename provided")
            raise ValueError("Filename must not be empty")

        # Ensure .md extension
        if not filename.endswith(".md"):
            filename += ".md"
            logger.debug(f"Added .md extension to filename: {filename}")

        # Set up paths
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        results_folder = current_dir.parent / "results"
        
        # Create results directory if it doesn't exist
        try:
            results_folder.mkdir(exist_ok=True)
            logger.debug(f"Ensured results directory exists: {results_folder}")
        except Exception as e:
            logger.error(f"Failed to create results directory: {str(e)}")
            raise OSError(f"Failed to create results directory: {str(e)}")

        file_path = results_folder / filename
        
        # Save the content
        logger.debug(f"Writing markdown content to: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Successfully saved markdown file: {file_path}")

    except Exception as e:
        logger.error(f"Error saving markdown file {filename}: {str(e)}", exc_info=True)
        raise Exception(f"Failed to save markdown: {str(e)}")
