#!/usr/bin/env python3
"""
Test script to demonstrate the usage of the OutputFormatter class.
"""

import os
import sys
import os.path

# Add the project root to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.output_formatter import OutputFormatter

def main():
    """
    Demonstrate how to use the OutputFormatter class.
    """
    # Sample configuration
    config = {
        'output': {
            'default_format': 'json',
            'file_path': 'data/output/',
            'include_metadata': True
        },
        'templates': {
            'include': [
                'email_template.yaml',
                'product_template.yaml'
            ]
        }
    }
    
    # Create formatter instance
    formatter = OutputFormatter(config)
    
    # Sample response from LLM
    sample_response = {
        'content': {
            'email': [
                {
                    'id': 1,
                    'subject': 'Welcome to our platform',
                    'body': 'Thank you for signing up!',
                    'recipient': 'user@example.com'
                },
                {
                    'id': 2,
                    'subject': 'Your monthly newsletter',
                    'body': 'Here are this month\'s updates...',
                    'recipient': 'subscriber@example.com'
                }
            ],
            'product': [
                {
                    'id': 101,
                    'name': 'Smartphone',
                    'price': 599.99,
                    'category': 'Electronics'
                },
                {
                    'id': 102,
                    'name': 'Laptop',
                    'price': 999.99,
                    'category': 'Electronics'
                }
            ]
        },
        'model': 'gpt-4',
        'usage': {
            'prompt_tokens': 245,
            'completion_tokens': 520,
            'total_tokens': 765
        }
    }
    
    # Format and save email data
    email_path = formatter.format_and_save(sample_response, 'email')
    print(f"Email data saved to: {email_path}")
    
    # Change output format to CSV and save product data
    config['output']['default_format'] = 'csv'
    formatter = OutputFormatter(config)
    product_path = formatter.format_and_save(sample_response, 'product')
    print(f"Product data saved to: {product_path}")
    
    # Append more data to demonstrate updating existing files
    more_data = {
        'content': {
            'email': [
                {
                    'id': 3,
                    'subject': 'Important announcement',
                    'body': 'We have exciting news to share!',
                    'recipient': 'all@example.com'
                }
            ],
            'product': [
                {
                    'id': 103,
                    'name': 'Headphones',
                    'price': 149.99,
                    'category': 'Electronics'
                }
            ]
        },
        'model': 'gpt-4',
        'usage': {
            'prompt_tokens': 150,
            'completion_tokens': 300,
            'total_tokens': 450
        }
    }
    
    # Test appending to existing files
    config['output']['default_format'] = 'json'
    formatter = OutputFormatter(config)
    email_path = formatter.format_and_save(more_data, 'email')
    print(f"Updated email data saved to: {email_path}")
    
    config['output']['default_format'] = 'csv'
    formatter = OutputFormatter(config)
    product_path = formatter.format_and_save(more_data, 'product')
    print(f"Updated product data saved to: {product_path}")


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs('data/output/', exist_ok=True)
    main() 