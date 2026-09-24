import json
import ast
import re
import sys
from pathlib import Path

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def validate_json(text):
    """Validate if text is valid JSON. Returns 10 if valid, 0 if invalid."""
    try:
        json.loads(text.strip())
        return 10
    except (json.JSONDecodeError, TypeError):
        return 0


def validate_python(text):
    """Validate if text is valid Python code. Returns 10 if valid, 0 if invalid."""
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0


def validate_regex(text):
    """Validate if text is a valid regular expression. Returns 10 if valid, 0 if invalid."""
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0


def grade_syntax(response, test_case):
    """
    Grade the syntax validity of the output based on the test case format type.
    
    Args:
        response: The model's output to validate
        test_case: Dictionary containing task info, including "format" field
        
    Returns:
        Integer score: 10 for valid syntax, 0 for invalid
    """
    format_type = test_case.get("format", "").lower()
    
    if format_type == "json":
        return validate_json(response)
    elif format_type == "python":
        return validate_python(response)
    elif format_type == "regex":
        return validate_regex(response)
    else:
        return 0


if __name__ == "__main__":
    # Test cases
    print("Testing JSON validation:")
    valid_json = '{"name": "John", "age": 30}'
    invalid_json = '{name: John}'
    print(f"Valid JSON: {validate_json(valid_json)}")  # Should be 10
    print(f"Invalid JSON: {validate_json(invalid_json)}")  # Should be 0
    
    print("\nTesting Python validation:")
    valid_python = "def hello():\n    return 'world'"
    invalid_python = "def hello(\n    return 'world'"
    print(f"Valid Python: {validate_python(valid_python)}")  # Should be 10
    print(f"Invalid Python: {validate_python(invalid_python)}")  # Should be 0
    
    print("\nTesting RegEx validation:")
    valid_regex = r"^[a-zA-Z0-9_]+@[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$"
    invalid_regex = r"[a-z"
    print(f"Valid RegEx: {validate_regex(valid_regex)}")  # Should be 10
    print(f"Invalid RegEx: {validate_regex(invalid_regex)}")  # Should be 0
    
    print("\nTesting grade_syntax with format inference:")
    test_json = {"task": "Create a JSON configuration", "format": "JSON"}
    test_python = {"task": "Write a Python function"}
    test_regex = {"task": "Create a regex pattern"}
    
    print(f"JSON task: {grade_syntax(valid_json, test_json)}")  # Should be 10
    print(f"Python task: {grade_syntax(valid_python, test_python)}")  # Should be 10
    print(f"Regex task: {grade_syntax(valid_regex, test_regex)}")  # Should be 10
