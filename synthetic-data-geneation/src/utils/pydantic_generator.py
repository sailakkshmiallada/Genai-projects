import types
from pydantic import BaseModel, create_model
from typing import Type, Any, Dict, Optional, Tuple, Union, get_origin, get_args, List
from src.utils.logger import get_logger # Assuming you have this logger setup

# Configure logging
logger = get_logger(__name__)


# --- Type Mapping ---
TYPE_MAP: Dict[str, Type[Any]] = {
    'str': str,
    'string': str,
    'int': int,
    'integer': int,
    'float': float,
    'bool': bool,
    'boolean': bool,
    'list[str]': List[str],
    'list': List[Any],
    'dict': Dict[str, Any],
    'object': Dict[str, Any],
    'any': Any
}

def _get_type_from_string(type_str: str) -> Optional[Type[Any]]:
    """Converts a type string into a Python type object, handling Optional."""
    type_str = str(type_str).strip()
    logger.debug(f"Processing type string: {type_str}")
    # Handle Optional[<type>] - common pattern
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        inner_type_str = type_str[len("Optional["):-1].strip()
        inner_type = TYPE_MAP.get(inner_type_str.lower()) # Check lowercase
        if inner_type:
            return Optional[inner_type]
        else:
            logger.warning(f"Warning: Unknown inner type '{inner_type_str}' inside Optional. Default to Optional[str].")
            return Optional[str]
    # Handle basic types (case-insensitive check)
    elif type_str.lower() in TYPE_MAP:
        return TYPE_MAP[type_str.lower()]
    else:
        logger.warning(f"Warning: Unknown type  '{type_str}'. Defaulting to str.")
        return str


# --- Dynamic Model Creation ---

def create_pydantic_models(
    class_name: str,
    config_dict: Dict[str, str],
    list_field_name: str,
    base_class: Type[BaseModel] = BaseModel,
    docstring: Optional[str] = None
) -> Tuple[Type[BaseModel], Type[BaseModel]]: 
    """
    Dynamically creates two Pydantic BaseModel classes:
    1. An item model based on the configuration dictionary.
    2. A list model containing a list of items from the first model.

    Args:
        class_name: The base name for the generated item class (e.g., "EmailOutput").
        config_dict: The dictionary defining fields and their type strings for the item model.
        list_field_name: Name of the field containing the list in the list model.
        base_class: The Pydantic base class to inherit from for both models (default: BaseModel).
        docstring: An optional base docstring for the generated item class.
                    The list model docstring will be derived.               

    Returns:
        A tuple containing two dynamically created Pydantic BaseModel classes:
        (ItemModel, ListModel)

    Raises:
        ValueError: If the config_dict is empty, invalid, or results in no
                    valid fields for the item model.
    """
    # --- Input Validation (Copied from previous function) ---
    if not isinstance(config_dict, dict):
        logger.error(f"config must be a dictionary. Got {type(config_dict)}")
        raise ValueError("config must be a dictionary.")
    if not config_dict:
        logger.error("config_dict cannot be empty.")
        raise ValueError("config_dict cannot be empty.")

    # --- Generate Field Definitions for Item Model ---
    field_definitions: Dict[str, Tuple[Type[Any], Any]] = {}
    for name, type_str in config_dict.items():
        if not isinstance(name, str) or not isinstance(type_str, str):
            logger.warning(f"Warning: Invalid entry in config_dict: ({name}: {type_str}). Both key/value must be strings. Skipping.")
            continue

        field_type = _get_type_from_string(type_str)
        field_name = name.strip()

        if field_name and field_type:
            origin = get_origin(field_type)
            args = get_args(field_type)
            is_optional = (origin is Union or origin is getattr(types, 'UnionType', None)) \
                          and type(None) in args

            if is_optional:
                field_definitions[field_name] = (field_type, None)
            else:
                field_definitions[field_name] = (field_type, ...)
        else:
             logger.warning(f"Warning: Could not determine type for field '{field_name}' with type string '{type_str}'. Skipping field.")

    if not field_definitions:
         logger.error("No valid field definitions could be generated for the item model.")
         raise ValueError("No valid field definitions could be generated for the item model.")

    # --- Create Item Model ---
    item_model_doc = docstring or f"Dynamically generated model for {class_name}"
    item_model_kwargs = {'__doc__': item_model_doc, **field_definitions}

    ItemModel: Type[BaseModel] = create_model(
        class_name,
        __base__=base_class,
        **item_model_kwargs
    )
    logger.info(f"Successfully created item model: {class_name}")

    # --- Create List Model ---
    list_model_name = f"{class_name}List"
    list_model_doc = f"Pydantic model for a list of {class_name} instances"


    list_field_name_actual = list_field_name


    # Define the single field for the list model
    list_field_definitions = {
        list_field_name_actual: (List[ItemModel], ...) 
    }

     # Create the List Model
    ListModel: Type[BaseModel] = create_model(
        list_model_name,
        __base__=base_class,
        __doc__=list_model_doc,
        **list_field_definitions
    )
    logger.info(f"Successfully created list model: {list_model_name}")

    # Return both models as a tuple
    return ItemModel, ListModel