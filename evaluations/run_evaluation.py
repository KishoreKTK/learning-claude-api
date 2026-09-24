import json
from statistics import mean
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import add_user_message, add_assistant_message, chat
from grade_by_model import grade_by_model
from validate_syntax import grade_syntax


def load_dataset(filename="dataset.json"):
    """Load the dataset from a JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run generating_sample.py first.")
        return []


def run_prompt(test_case):
    """
    Pass a test case to Claude and get a solution.
    
    Args:
        test_case: Dictionary containing the task
        
    Returns:
        String with the model's response (code, JSON, or regex)
    """
    prompt = f"""
Please solve the following task:

{test_case['task']}

* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
"""

    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    output = chat(messages, stop_sequences=["```"])
    return output


def run_test_case(test_case):
    """
    Run one test case: generate output, then grade it using both model and syntax validators.
    
    Args:
        test_case: Dictionary containing the task
        
    Returns:
        Dictionary with output, test_case, scores, and reasoning
    """
    # Generate solution
    output = run_prompt(test_case)
    
    # Get model-based evaluation
    model_grade = grade_by_model(test_case, output)
    model_score = model_grade.get("score", 0)
    reasoning = model_grade.get("reasoning", "")
    
    # Get syntax validation score
    syntax_score = grade_syntax(output, test_case)
    
    # Combine both scores
    combined_score = (model_score + syntax_score) / 2
    
    return {
        "output": output,
        "test_case": test_case,
        "model_score": model_score,
        "syntax_score": syntax_score,
        "score": combined_score,
        "reasoning": reasoning,
        "evaluation": model_grade,
    }


def run_eval(dataset):
    """
    Run all test cases in a dataset and collect evaluation results.
    
    Args:
        dataset: List of test case dictionaries
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    for i, test_case in enumerate(dataset, 1):
        print(f"Running test case {i}/{len(dataset)}...")
        result = run_test_case(test_case)
        results.append(result)
    
    # Calculate and print average score
    if results:
        average_score = mean([result["score"] for result in results])
        print(f"\nAverage score: {average_score:.2f}")
    
    return results


def save_results(results, filename="evaluation_results.json"):
    """Save evaluation results to a JSON file."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    # Load the dataset
    dataset = load_dataset()
    
    if not dataset:
        print("No dataset available. Exiting.")
        exit(1)
    
    print(f"Loaded {len(dataset)} test cases from dataset.json\n")
    
    # Run evaluation on all test cases
    results = run_eval(dataset)
    
    # Save results to file
    save_results(results)
    
    # Print summary
    print(f"\nEvaluation complete! {len(results)} test cases processed.")

