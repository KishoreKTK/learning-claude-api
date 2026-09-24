import json
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils import add_user_message, add_assistant_message, chat


def grade_by_model(test_case, output):
    """
    Use Claude to evaluate the AI-generated solution.
    
    Args:
        test_case: Dictionary containing the original task and format
        output: String with the model's response to evaluate
        
    Returns:
        Dictionary with evaluation results (strengths, weaknesses, reasoning, score)
    """
    eval_prompt = f"""
You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

Original Task:
<task>
{test_case['task']}
</task>

Solution to Evaluate:
<solution>
{output}
</solution>

Output Format
Provide your evaluation as a structured JSON object with the following fields, in this specific order:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your overall assessment
- "score": A number between 1-10

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "reasoning": "explanation",
    "score": 8
}}
"""

    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    eval_text = chat(messages, stop_sequences=["```"])
    
    try:
        evaluation = json.loads(eval_text)
        return evaluation
    except json.JSONDecodeError as e:
        print(f"Error parsing evaluation JSON: {e}")
        return {
            "strengths": ["Could not parse evaluation"],
            "weaknesses": [],
            "reasoning": f"JSON parsing error: {str(e)}",
            "score": 0
        }


if __name__ == "__main__":
    # Test with a sample task and output
    sample_task = {
        "task": "Write a Python function to reverse a string",
        "format": "python"
    }
    
    sample_output = """
def reverse_string(s):
    return s[::-1]

# Test
print(reverse_string("hello"))  # Output: olleh
"""
    
    print("Running model-based evaluation...\n")
    evaluation = grade_by_model(sample_task, sample_output)
    
    print("Evaluation Results:")
    print(json.dumps(evaluation, indent=2))
