import re

def process_criteria(input_str: str) -> dict:
    """
    Process an input string by splitting it on semicolons, 'OR', and 'AND', 
    then further splitting each substring on colons, equal signs, less than symbols, 
    or greater than symbols. It also handles lists of values separated by commas.

    Parameters:
    input_str (str): The input string to process.

    Returns:
    dict: Dictionary representing the processed key-value pairs.
    """
    try:
        # Check if the input is a string
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string.")

        # Split the input string on semicolons, 'OR', and 'AND'
        criteria_segments = re.split(r'\s*;\s*|\s+OR\s+|\s+AND\s+', input_str)
        result_dict = {}

        # Define regular expressions to split substrings and list values
        outer_delimiters = r"[:=<>]"
        list_splitter = r"\s*,\s*"

        for segment in criteria_segments:
            # Strip leading and trailing whitespaces from each segment
            segment = segment.strip()
            if not segment:
                continue

            # Split on outer delimiters, expecting key-value pairs
            key_value = re.split(outer_delimiters, segment, 1)
            
            if len(key_value) < 2:
                continue
            
            key = key_value[0].strip()
            values = re.split(list_splitter, key_value[1].strip())

            # Filter empty string values
            values = [value.strip() for value in values if value.strip()]

            # Save to result dictionary
            result_dict[key] = values

        return result_dict

    except Exception as e:
        raise ValueError(f"An error occurred: {e}")
    

def reorder_criteria(criteria: str) -> str:
    """
    Reorder criteria based on predefined prefixes. Criteria with recognized prefixes
    will be ordered first according to the prefix order, followed by criteria with
    unrecognized prefixes.

    Parameters:
    criteria (str): A string of criteria separated by semicolons.

    Returns:
    str: A reordered string of criteria, separated by semicolons.

    Raises:
    ValueError: If the input is not a string or if processing fails.
    """
    # Define the order of prefixes to match
    order_of_prefixes = ['DDC_CD', 'DDC_DTL', 'DDC_EA1', 'DDC_EA2', 'DDC_EA3']
    
    # Validate input type
    if not isinstance(criteria, str):
        raise ValueError("Input must be a string.")

    try:
        # Split the criteria string into a list using the semicolon as the delimiter
        criteria_list = [crit.strip() for crit in criteria.split(';') if crit.strip()]

        # Define a helper function to determine the sort key based on prefix order
        def sort_key(crit):
            for index, prefix in enumerate(order_of_prefixes):
                if crit.startswith(prefix):
                    return index
            return len(order_of_prefixes)  # Ensures non-matches are sorted to the end

        # Sort the list of criteria based on the sort key
        sorted_criteria = sorted(criteria_list, key=sort_key)

        # Join the sorted criteria list into a final string
        return ';'.join(sorted_criteria)

    except Exception as e:
        raise ValueError(f"An error occurred while processing criteria: {e}")
