import json
import re

def normalize_json_string(json_str):
    try:
        json_str = re.sub(r'<br\s*/?>', ' ', json_str)  # Replace <br/> with space
        json_str = json_str.replace('\n', ' ')  # Remove all newlines

        parsed_json = json.loads(json_str)
        return parsed_json  # Return as a Python dictionary

    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        return None  # Return None if parsing fails