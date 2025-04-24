# src/utils/config_loader.py
import yaml
import os
from pathlib import Path

def load_config(config_path):
    """Load configuration from YAML file with support for includes"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Process includes if present
    if 'templates' in config and 'include' in config['templates']:
        base_dir = os.path.dirname(config_path)
        for include_path in config['templates']['include']:
            # Convert relative path to absolute if needed
            abs_include_path = include_path
            if not os.path.isabs(include_path):
                abs_include_path = os.path.join(base_dir, include_path)
            
            # Load and merge included config
            included_config = load_included_config(abs_include_path)
            merge_configs(config, included_config)
    
    return config

def load_included_config(include_path):
    """Load an included configuration file"""
    with open(include_path, 'r') as f:
        return yaml.safe_load(f)

def merge_configs(base_config, included_config):
    """Merge included config into base config"""
    for key, value in included_config.items():
        if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
            # If both are dictionaries, merge recursively
            merge_configs(base_config[key], value)
        else:
            # Otherwise overwrite or add the key-value pair
            base_config[key] = value