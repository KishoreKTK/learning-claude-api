import json
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils import add_user_message, add_assistant_message, chat


def generate_dataset():
    """
    Generate an evaluation dataset for prompt evaluation.
    Creates tasks that require Python, JSON, or Regex solutions for AWS-related tasks.
    """
    prompt = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects,
each representing a task that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
    {
        "task": "Description of task",
        "format": "json" or "python" or "regex"
    },
    ...additional
]
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
* Focus on tasks that do not require writing much code

Please generate 3 objects.
"""

    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    text = chat(messages, stop_sequences=["```"])
    return json.loads(text)


def save_dataset(dataset, filename="dataset.json"):
    """Save dataset to a JSON file."""
    with open(filename, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"Dataset saved to {filename}")


if __name__ == "__main__":
    print("Generating dataset...")
    dataset = generate_dataset()
    print(f"Generated {len(dataset)} test cases")
    save_dataset(dataset)
    print("Done!")
