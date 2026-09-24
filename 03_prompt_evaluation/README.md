# Module 03: Prompt Engineering and Prompt Evaluation

> **What you learn:** how to write better prompts, and how to prove a prompt is better
> by building a test dataset, running the prompt on every case, and grading the outputs
> with code and with Claude.
>
> **Prerequisites:** [02 SDK Basics](../02_sdk_basics/README.md) · **Next:** [04 Tool Use](../04_tool_use/README.md)

## Files

```text
03_prompt_evaluation/
├── 01_basic_pipeline/            ← version 1: hand-built, step by step
│   ├── generating_sample.py      ← Claude writes the test cases → dataset.json
│   ├── grade_by_model.py         ← Claude grades an output (strengths, weaknesses, score)
│   ├── validate_syntax.py        ← code grader: is it valid Python / JSON / regex?
│   ├── run_evaluation.py         ← runs everything, averages the scores
│   ├── dataset.json              ← 3 AWS tasks (regex, json, python)
│   └── evaluation_results.json   ← last run: scores 8.0 / 7.5 / 7.5
├── 02_prompt_evaluator/
│   └── prompt_evaluator.py       ← version 2: reusable PromptEvaluator class + HTML report
└── notebooks/
    ├── prompt_evals_fns.ipynb    ← course notebook for version 1
    └── prompting_completed.ipynb ← course notebook for version 2
```

Run:

```bash
cd 01_basic_pipeline
python generating_sample.py      # writes dataset.json
python run_evaluation.py         # writes evaluation_results.json, prints average
python validate_syntax.py        # offline self-test of the code grader

cd ../02_prompt_evaluator
python prompt_evaluator.py       # writes dataset.json, output.json, output.html
```

---

## Part A: Prompt engineering

### 1. Why engineer prompts?

The same model gives very different quality depending on how you ask. Prompt engineering
means making the request **clear, specific and structured** so the output is correct and
consistent.

### 2. Techniques (from weakest prompt to strongest)

**❌ Vague:**

```text
Make a meal plan for an athlete.
```

**✅ 1. Be clear and direct.** Say exactly what you want in the first line.

```text
Generate a one-day meal plan for an athlete that meets their dietary restrictions.
```

**✅ 2. Be specific.** Add guidelines and output requirements.

```text
Guidelines:
1. Include accurate daily calorie amount
2. Show protein, fat, and carb amounts
3. Specify when to eat each meal
4. Use only foods that fit restrictions
5. List all portion sizes in grams
```

**✅ 3. Structure with XML tags.** Separate your data from your instructions so Claude
doesn't confuse them.

```text
<athlete_information>
- Height: 180 cm
- Weight: 75 kg
- Goal: build muscle
- Dietary restrictions: vegetarian
</athlete_information>
```

**✅ 4. Give examples (few-shot).** Show one or two ideal input → output pairs.

```text
<example>
Input: "The service was slow but the food was amazing"
Output: {"sentiment": "mixed", "aspects": {"service": "negative", "food": "positive"}}
</example>
```

**✅ 5. Use a system prompt for the role.**

```python
system = "You are a sports nutritionist who writes compact, precise plans."
```

**✅ 6. Prefill + stop sequences** *(older technique; model-dependent, see the warning below)*.
Start Claude's reply for it, and stop at a marker:

```python
add_user_message(messages, prompt)
add_assistant_message(messages, "```json")      # Claude continues *after* this
text = chat(messages, stop_sequences=["```"])   # stops before the closing fence
data = json.loads(text)                         # pure JSON, no prose around it
```

> ⚠️ **Prefill only works on older models.** It works on `claude-haiku-4-5`, which this
> module uses. On **Opus 5, Sonnet 5, Fable, and the 4.6+ family**, an assistant prefill
> returns a **400 error**. The modern replacement is structured outputs
> → [Module 05](../05_structured_data/README.md).

### 3. Prompt templates

Reusable prompts contain `{placeholders}` that get filled in per test case.
`PromptEvaluator.render()` does this, and uses `{{ }}` for literal braces:

```python
evaluator.render("Plan for a {goal} athlete, {weight} kg", {"goal": "marathon", "weight": 60})
# → "Plan for a marathon athlete, 60 kg"
```

---

## Part B: Prompt evaluation

### 4. What is an eval?

An **eval** is an automated test suite for a prompt. Instead of reading one output and
thinking "looks fine", you run the prompt on many inputs and get a **number** you can
compare between prompt versions.

```text
   ┌──────────────┐    ┌────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ 1. Draft     │──► │ 2. Dataset │──► │ 3. Run   │──► │ 4. Grade │──► │ 5. Score │
   │    prompt    │    │ (test cases)│   │ prompt on│    │ each     │    │ average, │
   └──────────────┘    └────────────┘    │ each case│    │ output   │    │ compare  │
          ▲                              └──────────┘    └──────────┘    └────┬─────┘
          └──────────────────── 6. Change prompt, re-run ◄────────────────────┘
```

### 5. Step 2: Build a dataset

Write the cases by hand, or have **Claude generate them** ([generating_sample.py](01_basic_pipeline/generating_sample.py)):

```json
[
  {"task": "Parse an AWS S3 bucket name from an S3 URI (e.g., s3://my-bucket/path/to/file.txt)", "format": "regex"},
  {"task": "Create a JSON configuration object for an AWS Lambda function that runs every 5 minutes...", "format": "json"},
  {"task": "Write a Python function that extracts the region code from an AWS ARN string...", "format": "python"}
]
```

Version 2 generates in two stages, which gives more varied cases:

1. `generate_unique_ideas()`: N distinct scenario ideas ("vegan marathon runner",
   "powerlifter with nut allergy", ...).
2. `generate_test_case()`: turns each idea into `prompt_inputs` plus `solution_criteria`.
   Cases are generated **in parallel** with `ThreadPoolExecutor`.

### 6. Step 3: Run the prompt

```python
def run_prompt(test_case):
    prompt = f"""
Please solve the following task:

{test_case['task']}

* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
"""
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    return chat(messages, stop_sequences=["```"])
```

### 7. Step 4: Grade, three kinds of grader

| Grader | How | Good for | Weakness |
| --- | --- | --- | --- |
| **Code** | Python checks: `json.loads`, `ast.parse`, `re.compile`, length, keywords | Objective facts: valid syntax, required fields, word limits | Can't judge quality |
| **Model** | Another Claude call scores against criteria | Subjective quality: helpfulness, correctness, tone | Costs tokens; can be biased or inconsistent |
| **Human** | A person reviews | Ground truth, spot checks | Slow, expensive |

**Code grader** ([validate_syntax.py](01_basic_pipeline/validate_syntax.py)):

```python
def validate_python(text):
    try:
        ast.parse(text.strip()); return 10
    except SyntaxError:
        return 0
```

**Model grader** ([grade_by_model.py](01_basic_pipeline/grade_by_model.py)) asks for
strengths, weaknesses, reasoning **then** score, in that order. Writing the reasoning
before the number gives better-calibrated scores.

**Stricter model grader** (version 2, `grade_output()`) adds:

- per-case `solution_criteria`
- `extra_criteria` as **mandatory** requirements: any violation means a score ≤ 3
- a scoring rubric: 1–3 fails mandatory · 4–6 weak secondary · 7–8 minor issues · 9–10 meets everything

### 8. Step 5: Score

Version 1 combines both graders:

```text
final score = (model_score + syntax_score) / 2      e.g. (6 + 10) / 2 = 8.0
```

Last run ([evaluation_results.json](01_basic_pipeline/evaluation_results.json)):

| Case | Model | Syntax | Final |
| --- | --- | --- | --- |
| regex: S3 bucket | 6 | 10 | 8.0 |
| json: Lambda config | 5 | 10 | 7.5 |
| python: ARN region | 5 | 10 | 7.5 |
| **Average** | | | **7.67** |

Version 2 reports the average, a **pass rate** (score ≥ 7), and an **HTML report** with
every case.

### 9. Using the reusable evaluator (version 2)

```python
evaluator = PromptEvaluator(max_concurrent_tasks=3)   # more = faster, but watch rate limits

evaluator.generate_dataset(
    task_description="Write a compact, concise 1 day meal plan for a single athlete",
    prompt_inputs_spec={
        "height": "Athlete's height in cm",
        "weight": "Athlete's weight in kg",
        "goal": "Goal of the athlete",
        "restrictions": "Dietary restrictions of the athlete",
    },
    num_cases=5,
    output_file="dataset.json",
)

def run_prompt(inputs):             # ← the prompt you are testing
    ...
    return chat(messages)

evaluator.run_evaluation(
    run_prompt_function=run_prompt,
    dataset_file="dataset.json",
    extra_criteria="Must include daily caloric total and macronutrient breakdown",
)
```

To compare prompts, keep the **same dataset**, change only `run_prompt`, re-run, and
compare the averages.

---

## 10. More examples of what to eval

| Prompt under test | Code grader | Model-grader criteria |
| --- | --- | --- |
| Support reply writer | Length < 150 words; no "I'm just an AI" | Polite, solves the issue, follows policy |
| SQL generator | Parses with `sqlglot`; runs on a test DB | Query answers the question |
| Product description writer | Contains product name; no prices invented | Persuasive, accurate to specs |
| Ticket classifier | Output ∈ {billing, bug, feature, other} | n/a (compare to labeled answers) |
| Summarizer | ≤ N bullets | Faithful, nothing important missing |
| Meal plan (course) | Has calories, macros, grams | Fits restrictions, realistic |

---

## 11. Where to use it (real-world scenarios)

| Scenario | Why evals matter |
| --- | --- |
| Before shipping any prompt to production | Catch failures on edge cases you didn't think of |
| Switching models (e.g. Opus → Haiku to save cost) | Prove quality holds on the cheaper model |
| Editing a prompt that "already works" | Make sure the fix doesn't break other cases (regression testing) |
| Comparing two prompt ideas | Pick the winner with numbers, not gut feel |
| CI pipeline | Run evals on every prompt change, like unit tests |
| Compliance and safety | Mandatory-criteria graders ("never gives medical diagnosis") |

---

## 12. Common mistakes and known issues

| Issue | Where | Effect | Fix |
| --- | --- | --- | --- |
| Assistant prefill | all graders/generators | 400 on Opus 5 / Sonnet 5 / 4.6+ models | Structured outputs ([05](../05_structured_data/README.md)) |
| `json.loads` on free text | `grade_by_model.py` | Parse failure → fallback score **0** skews the average | Schema-constrained grader output ([05](../05_structured_data/README.md)) |
| Self-test missing `format` | `validate_syntax.py` `__main__` | Prints `Python task: 0`, `Regex task: 0` though comments say 10 | Add `"format": "python"` / `"regex"` to those test dicts |
| Only 3 test cases | `dataset.json` | Average is noisy | 20–100+ varied cases, including edge cases |
| Same model generates, answers and grades | whole pipeline | Grader may be lenient towards its own style | Use a stronger/different grader model; spot-check by hand |
| High `max_concurrent_tasks` | version 2 | 429 rate-limit errors | Keep it low, or use the Batches API |
| Syntax score is all-or-nothing (0/10) | version 1 | Dominates the average | Weight it, or use it as a pass/fail gate |

---

## 13. Level up: basic → better

| What we did (basic) | Better way | Where |
| --- | --- | --- |
| Prefill `` ```json `` + stop sequence to get JSON | Forced tool / `output_config.format`, guaranteed valid JSON | [05 Structured Data](../05_structured_data/README.md) |
| Grader writes JSON we hope parses | Grader returns through a schema (`score` is always a number) | [05](../05_structured_data/README.md) |
| Grader answers immediately | Grader **thinks first** for more consistent scores | [06 Extended Thinking](../06_extended_thinking/README.md) |
| Grading text outputs only | Evaluate **agents**: did it call the right tools with the right args? | [04 Tool Use](../04_tool_use/README.md) |
| Sequential loop (version 1) | Thread pool (version 2) → Message Batches API (50% cheaper, async) | Future Module 10 |
| One model | Run the same eval on Haiku / Sonnet / Opus and pick the cheapest that passes | [01 model table](../01_fundamentals/README.md#6-choosing-a-model) |
| Print the average | Track scores per prompt version over time (CSV/JSON history) | Exercise below |

---

## 14. Practice

1. Fix the `validate_syntax.py` self-test so all three lines print 10.
2. Grow the dataset to 10 cases and re-run. Does the average move?
3. Write a second `run_prompt` with XML tags and an example. Beat 7.67 on the same dataset.
4. Add a code grader that fails Python outputs containing `print(` (the task said "function only").
5. Save each run's average with a timestamp into `history.json`.

## Cheat sheet

```text
Prompt: clear first line · specific guidelines · XML-tag the data · examples · system role
Eval:   dataset → run prompt → grade (code + model) → average → change prompt → repeat
Grader: reasoning BEFORE score · mandatory criteria · rubric 1–10
Warn:   prefill = Haiku 4.5 / older only; use structured outputs on new models
```
