#!/usr/bin/env python3
"""
Script to generate synthetic data using the Generator class.
"""

import os
import sys
import argparse
import traceback
from pathlib import Path

# Add the project root to the path if running this script directly
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.generator import generate_synthetic_data
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def main():
    """
    Main function to parse arguments and generate synthetic data.
    """
    logger.info("Starting synthetic data generation script")
    
    parser = argparse.ArgumentParser(description="Generate synthetic data using templates")
    
    parser.add_argument(
        "--config", 
        default="config/system_config.yaml", 
        help="Path to the configuration file"
    )
    
    parser.add_argument(
        "--template", 
        required=True, 
        choices=["emails", "products"], 
        help="Template to use for data generation"
    )
    
    parser.add_argument(
        "--count", 
        type=int, 
        default=10, 
        help="Number of items to generate"
    )
    
    parser.add_argument(
        "--format", 
        choices=["json", "csv"], 
        help="Output format (overrides config default)"
    )
    
    # Add debug flag for verbose logging
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    logger.info(f"Arguments parsed: template={args.template}, count={args.count}, format={args.format}, config={args.config}")
    
    try:
        # Ensure config directory exists
        config_dir = os.path.dirname(args.config)
        if config_dir and not os.path.exists(config_dir):
            logger.info(f"Creating config directory: {config_dir}")
            os.makedirs(config_dir)
            print(f"Created config directory: {config_dir}")
        
        # Ensure the output directory exists
        output_dir = "data/output"
        logger.debug(f"Ensuring output directory exists: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the data
        logger.info(f"Calling generate_synthetic_data with template={args.template}, count={args.count}")
        output_path = generate_synthetic_data(
            config_path=args.config,
            template_name=args.template,
            count=args.count,
            output_format=args.format
        )
        
        logger.info(f"Data generation successful, output saved to: {output_path}")
        print(f"✅ Successfully generated synthetic data")
        print(f"📁 Output saved to: {output_path}")
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        print(f"❌ Error generating synthetic data: {error_msg}")
        print(f"💡 Hint: Check if the file path is correct and the file exists.")
        sys.exit(1)
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Value error: {error_msg}")
        print(f"❌ Error generating synthetic data: {error_msg}")
        
        # Provide more helpful messages based on common errors
        if "string indices must be integers" in error_msg:
            logger.debug("Detected 'string indices' error, likely due to response parsing issues")
            print(f"💡 Hint: There might be an issue with parsing the LLM response. Check if the response format matches the expected structure.")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Unexpected error: {e}")
        print(f"❌ Error generating synthetic data: {error_msg}")
        
        # Get traceback for detailed debugging
        tb = traceback.format_exc()
        logger.debug(f"Traceback: {tb}")
        
        print(f"💡 For more details, check the logs.")
        sys.exit(1)


if __name__ == "__main__":
    main() 