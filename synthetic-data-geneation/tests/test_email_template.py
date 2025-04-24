import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock
from pydantic import BaseModel
import sys
import os.path

# Add the project root to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Adjust the import path based on your project structure
from src.templates.email_template import EmailTemplate
from src.templates.product_template import ProductTemplate
from src.utils.config_loader import load_config


config = load_config("config/system_config.yaml")
# Test the EmailTemplate class
email_template = EmailTemplate(config)
prompt ,output_model = email_template.build_prompt(1)
print(prompt)
print(output_model)

# Test the ProductTemplate class
product_template = ProductTemplate(config)
prompt ,output_model = product_template.build_prompt(1)
print(prompt)
print(output_model)