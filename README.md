# learning-claude-api

Everything I've built while learning Anthropic's Claude API, from a first chatbot to tool-using agents, model-graded evals and extended thinking.

## Project Structure

```
learning-claude-api/
├── README.md                          # This file
├── .env                               # API configuration (git ignored)
├── utils.py                           # Shared utilities (chat client, helpers)
│
├── evaluations/                       # Evaluation pipeline
│   ├── generating_sample.py           # Generate test dataset
│   ├── grade_by_model.py             # Model-based evaluation
│   ├── validate_syntax.py            # Syntax validation
│   ├── run_evaluation.py             # Main evaluation runner
│   ├── dataset.json                  # Generated test cases
│   └── evaluation_results.json       # Evaluation results
│
├── thinking/                          # Extended thinking flow
│   ├── thinking_chat.py              # chat() with thinking, block-preserving helpers
│   ├── flow.py                       # Two-turn flow + stripped/redacted contrasts
│   └── README.md                     # What changed since the notebook
│
├── notes/                             # Learning materials & documentation
│   ├── Claude INtro.txt              # Claude introduction notes
│   ├── Claude Models.png             # Model reference image
│   └── _76f0142b9b42419d9bc8835c3dbeeb38_001_prompt_evals_fns.ipynb  # Notebook with complete examples
│
└── Learning Examples/
    ├── chatbot.py                    # Multi-turn conversation example
    ├── hello.py                      # Basic chat example
    └── streamresponse.py             # Streaming response example
```

## Quick Start

### 1. Install Dependencies
```bash
pip install anthropic python-dotenv
```

### 2. Set up Environment
Create a `.env` file in the root directory:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Run the Evaluation Pipeline

From the project root:

```bash
# Step 1: Generate dataset
cd evaluations
python generating_sample.py

# Step 2: Run evaluation (generates both model grades and syntax validation)
python run_evaluation.py

# Step 3: Check results
cat evaluation_results.json
```

## File Descriptions

### Core Files

**utils.py**
- Centralized Anthropic client configuration
- Helper functions: `add_user_message()`, `add_assistant_message()`, `chat()`
- Loads API key from `.env`

### Evaluation Pipeline

**generating_sample.py**
- Generates AWS-related tasks (Python, JSON, Regex)
- Creates `dataset.json` with 3 test cases

**run_prompt() in grade_by_model.py**
- Takes a task and generates a solution using Claude

**grade_by_model.py**
- Uses Claude to evaluate solutions
- Returns: strengths, weaknesses, reasoning, score (1-10)

**validate_syntax.py**
- Validates Python syntax using `ast.parse()`
- Validates JSON using `json.loads()`
- Validates regex using `re.compile()`

**run_evaluation.py**
- Orchestrates the full pipeline
- Combines model grades + syntax validation scores
- Calculates average score
- Saves results to `evaluation_results.json`

### Learning Examples

- **hello.py**: Simple one-shot chat
- **chatbot.py**: Multi-turn conversation with history
- **streamresponse.py**: Streaming text responses

## Evaluation Scoring

Each test case gets scored by:

1. **Model Score (1-10)**: Expert evaluation by Claude
2. **Syntax Score (0 or 10)**: Valid or invalid based on format

**Final Score = (Model Score + Syntax Score) / 2**

Average of all test cases is printed and saved to results.

## Notes

- The notebook in `notes/` contains the original Jupyter implementation
- Refer to it for more detailed explanations and examples
- All evaluation scripts are self-contained and can be run independently
