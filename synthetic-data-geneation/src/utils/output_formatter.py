import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class OutputFormatter:
    """
    Handles formatting and saving of LLM response data based on configuration.
    
    This class provides functionality to format LLM-generated data into JSON or CSV
    format and save it to the specified output directory with appropriate organization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OutputFormatter with configuration.
        
        Args:
            config: Dictionary containing output configuration parameters
                   including output format, file path, etc.
        """
        logger.info("Initializing OutputFormatter")
        self.config = config
        
        # Extract output configuration
        self.default_format = config.get('output', {}).get('default_format', 'json')
        logger.debug(f"Default output format: {self.default_format}")
        
        self.base_output_path = config.get('output', {}).get('file_path', 'data/output/')
        logger.debug(f"Base output path: {self.base_output_path}")
        
        self.include_metadata = config.get('output', {}).get('include_metadata', True)
        logger.debug(f"Include metadata: {self.include_metadata}")
        
        # Ensure output directory exists
        try:
            os.makedirs(self.base_output_path, exist_ok=True)
            logger.debug(f"Created/ensured output directory: {self.base_output_path}")
        except Exception as e:
            logger.exception(f"Failed to create output directory: {e}")
            raise
    
    def format_and_save(self, 
                       response: Any, 
                       template_name: str) -> str:
        """
        Format and save the LLM response data based on the template name.
        
        Args:
            response: The response from LLM containing content and metadata
            template_name: The name of the template used for generation
            
        Returns:
            The path where the data was saved
        """
        logger.info(f"Formatting and saving response for template: {template_name}")
        
        try:
            # Log the response structure
            logger.debug(f"Response type: {type(response)}")
            if hasattr(response, 'content'):
                logger.debug(f"Response has 'content' attribute, type: {type(response.content)}")
                logger.debug(f"Response content length: {len(response.content) if isinstance(response.content, str) else 'not a string'}")
            else:
                logger.warning("Response object does not have 'content' attribute")
                
            # Extract the data from the response
            logger.debug("Extracting data from response")
            
            # Check if response is already parsed or needs parsing
            if isinstance(response, dict) and 'content' in response:
                logger.debug("Response is already a dictionary with 'content' key")
                content = response['content']
                model = response.get('model', 'unknown')
                usage = response.get('usage', {})
            elif hasattr(response, 'content'):
                logger.debug("Response is an object with 'content' attribute, trying to parse JSON")
                try:
                    # Try to parse content as JSON
                    content_str = response.content
                    import json
                    content = json.loads(content_str)
                    logger.debug(f"Successfully parsed content JSON, found keys: {list(content.keys()) if isinstance(content, dict) else 'not a dict'}")
                    model = getattr(response, 'model', 'unknown')
                    usage = getattr(response, 'usage', {})
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse response content as JSON: {content_str[:100]}...")
                    # Create a content structure with the template name as key and raw content
                    content = {template_name: response.content}
                    model = getattr(response, 'model', 'unknown')
                    usage = getattr(response, 'usage', {})
            else:
                logger.error(f"Unexpected response structure: {response}")
                raise ValueError(f"Unexpected response structure: {response}")
                
            # Ensure content is properly structured
            logger.debug("Checking template data in content")
            
            # Check if the content is directly the template data (not nested)
            if isinstance(content, list):
                logger.debug("Content is a direct list, wrapping with template name")
                content = {template_name: content}
            
            # Extract the template-specific data
            if template_name not in content:
                logger.error(f"Template data '{template_name}' not found in response content. Available keys: {list(content.keys()) if isinstance(content, dict) else 'content is not a dict'}")
                
                # Try to handle special case for email template
                if 'emails' in content:
                    logger.warning("Found 'emails' key instead of template name in content, adapting")
                    content = {template_name: content['emails']}
                elif 'products' in content:
                    logger.warning("Found 'products' key instead of template name in content, adapting")
                    content = {template_name: content['products']}
                else:
                    raise ValueError(f"Template data '{template_name}' not found in response content")
            
            logger.debug(f"Extracted template data for '{template_name}'")
            template_data = content[template_name]
            
            if not isinstance(template_data, list):
                logger.error(f"Expected list of dictionaries for template '{template_name}', got {type(template_data)}")
                # Try to convert to list if it's not already
                if isinstance(template_data, dict):
                    logger.warning("Template data is a dict, trying to convert to list")
                    template_data = [template_data]
                else:
                    raise ValueError(f"Expected list of dictionaries for template '{template_name}'")
            
            # Create template directory if it doesn't exist
            self.template_dir = os.path.join(self.base_output_path, template_name)
            logger.debug(f"Creating template directory: {self.template_dir}")
            os.makedirs(self.template_dir, exist_ok=True)
            
            # Determine the output format
            output_format = self.default_format.lower()
            logger.info(f"Using output format: {output_format}")
            
            # Save the data in the appropriate format
            if output_format == 'json':
                logger.debug("Saving as JSON format")
                return self._save_as_json(template_data, template_name)
            elif output_format == 'csv':
                logger.debug("Saving as CSV format")
                return self._save_as_csv(template_data, template_name)
            else:
                logger.error(f"Unsupported output format: {output_format}")
                raise ValueError(f"Unsupported output format: {output_format}")
                
        except Exception as e:
            logger.exception(f"Error in format_and_save: {e}")
            raise
    
    def _save_as_json(self, data: List[Dict[str, Any]], template_name: str) -> str:
        """
        Save data as JSON file.
        
        Args:
            data: List of dictionaries to save
            template_name: The name of the template
            
        Returns:
            The path where the JSON file was saved
        """
        logger.debug(f"Saving {len(data)} items as JSON for {template_name}")
        file_path = os.path.join(self.template_dir, f"{template_name}.json")
        logger.debug(f"JSON file path: {file_path}")
        
        # Read existing data if file exists
        existing_data = []
        if os.path.exists(file_path):
            try:
                logger.debug(f"Reading existing JSON data from {file_path}")
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    logger.warning(f"Existing JSON data is not a list, resetting to empty list")
                    existing_data = []
            except json.JSONDecodeError as e:
                # Handle empty or invalid JSON file
                logger.warning(f"Existing JSON file is invalid or empty: {e}")
                existing_data = []
            except Exception as e:
                logger.exception(f"Error reading existing JSON file: {e}")
                existing_data = []
        
        # Combine existing data with new data
        combined_data = existing_data + data
        logger.debug(f"Combined data has {len(combined_data)} items")
        
        # Write updated data to file
        try:
            logger.debug(f"Writing JSON data to {file_path}")
            with open(file_path, 'w') as f:
                json.dump(combined_data, f, indent=2)
            logger.info(f"Successfully saved JSON data to {file_path}")
        except Exception as e:
            logger.exception(f"Error writing JSON data: {e}")
            raise
        
        return file_path
    
    def _save_as_csv(self, data: List[Dict[str, Any]], template_name: str) -> str:
        """
        Save data as CSV file.
        
        Args:
            data: List of dictionaries to save
            template_name: The name of the template
            
        Returns:
            The path where the CSV file was saved
        """
        logger.debug(f"Saving {len(data)} items as CSV for {template_name}")
        file_path = os.path.join(self.template_dir, f"{template_name}.csv")
        logger.debug(f"CSV file path: {file_path}")
        
        try:
            # Convert to DataFrame
            logger.debug("Converting data to DataFrame")
            df_new = pd.json_normalize(data)
            
            # Append to existing CSV if it exists
            if os.path.exists(file_path):
                try:
                    logger.debug(f"Reading existing CSV data from {file_path}")
                    df_existing = pd.read_csv(file_path)
                    logger.debug(f"Concatenating DataFrames: existing={len(df_existing)}, new={len(df_new)}")
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    logger.debug(f"Combined DataFrame has {len(df_combined)} rows")
                    df_combined.to_csv(file_path, index=False)
                except Exception as e:
                    logger.exception(f"Error reading or appending to existing CSV: {e}")
                    logger.warning("Saving only new data due to error with existing CSV")
                    df_new.to_csv(file_path, index=False)
            else:
                logger.debug("No existing CSV, creating new file")
                df_new.to_csv(file_path, index=False)
                
            logger.info(f"Successfully saved CSV data to {file_path}")
            
        except Exception as e:
            logger.exception(f"Error in _save_as_csv: {e}")
            raise
        
        return file_path
