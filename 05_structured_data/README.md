# Module 05: Structured Data (Reliable JSON from Claude)

> **What you learn:** get **machine-readable, schema-valid JSON** from Claude instead of
> prose you have to parse. You'll see three techniques, from oldest to most robust.
>
> **Prerequisites:** [04 Tool Use](../04_tool_use/README.md) · **Next:** [06 Extended Thinking](../06_extended_thinking/README.md)

## Files

| File | What's in it |
| --- | --- |
| [../04_tool_use/structured_data.py](../04_tool_use/structured_data.py) | `article_schema`, `schedule_plan_schema`, `structured_output()`, `write_article()`, `plan_reminders()` |
| [../04_tool_use/scheduling_agent.py](../04_tool_use/scheduling_agent.py) | `demo_structured` (extract a plan → run it as one batch) and `demo_article` |
| [notebooks/structured_data.ipynb](notebooks/structured_data.ipynb) | Course notebook (exercise) |
| [notebooks/structured_data_completed.ipynb](notebooks/structured_data_completed.ipynb) | Course notebook (solution) |

> The code lives in `04_tool_use/` because it shares `conversation.chat()` with the agent
> and the agent imports it back.

```bash
cd ../04_tool_use
python scheduling_agent.py article      # article → {title, author, body}
python scheduling_agent.py structured   # free-text day → validated reminder list → 1 batch
```

---

## 1. Why structured data?

Your code can't reliably use *"Sure! Here's the article titled 'Quantum Leaps' by Dr. Jane
Smith..."*. It needs this:

```json
{"title": "Quantum Leaps", "author": "Dr. Jane Smith", "body": "..."}
```

Every time Claude's output feeds a program (database insert, API call, UI component,
another tool), you need structure.

---

## 2. Three techniques compared

| # | Technique | How | Guaranteed valid? | Works on |
| --- | --- | --- | --- | --- |
| 1 | **Prefill + stop sequence** ([Module 03](../03_prompt_evaluation/README.md)) | Start the reply with `` ```json ``, stop at `` ``` `` | ❌ Usually valid, not guaranteed | Haiku 4.5 and older only (400 on Opus 5 / 4.6+) |
| 2 | **Forced tool call** *(this module's code)* | Define a tool whose input schema *is* your output shape, force it with `tool_choice` | ✅ Matches the schema (add `strict: true` for a hard guarantee) | Most models (**not** Fable 5.1 / Opus 5.5, see warning) |
| 3 | **`output_config.format`** / `messages.parse()` | Constrain the response itself to a JSON Schema or Pydantic model | ✅ Guaranteed | All current models: the modern default |

---

## 3. Technique 2: Tool schema + `tool_choice` (what we built)

### Step 1: Describe the output shape as a tool

```python
article_schema = {
    "name": "article_output",
    "description": "Return a scholarly article broken into its individual parts...",
    "input_schema": {
        "type": "object",
        "properties": {
            "title":  {"type": "string", "description": "The title of the article."},
            "author": {"type": "string", "description": "The full name of the article's author."},
            "body":   {"type": "string", "description": "The body as a single paragraph."},
        },
        "required": ["title", "author", "body"],
    },
}
```

### Step 2: Force Claude to call it

```python
def structured_output(prompt, schema, system=None):
    messages = []
    add_user_message(messages, prompt)
    response = chat(
        messages,
        system=system,
        tools=[schema],
        tool_choice={"type": "tool", "name": schema["name"]},   # ← must call THIS tool
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == schema["name"]:
            return block.input            # already a Python dict
    raise ValueError(f"Model did not call {schema['name']}")
```

### Step 3: Use the dict

```python
article = structured_output("Write a one-paragraph article about computer science. "
                            "Include a title and author name.", article_schema)
print(article["title"], "by", article["author"])
```

We never execute the tool. **The "tool call" is just a container for the JSON.**

### `tool_choice` options

| Value | Meaning |
| --- | --- |
| `{"type": "auto"}` (default) | Claude decides whether to use a tool |
| `{"type": "any"}` | Must use *some* tool |
| `{"type": "tool", "name": "x"}` | Must use tool `x` (structured output) |
| `{"type": "none"}` | Must not use tools |

> ⚠️ **Forced `tool_choice` (`any` / `tool`) returns a 400 on Claude Fable 5.1 and Claude
> Opus 5.5.** On those models use technique 3, or `auto` plus a prompt instruction plus
> `strict: true`.

---

## 4. The real-world version: schedule extraction

`schedule_plan_schema` turns a messy request into a clean list:

```text
"I have the sprint standup at 10:00 and I want a nudge 15 minutes before it.
 The Q3 budget deadline is at 17:00 - remind me two hours ahead..."
```

↓ `plan_reminders(request, "2026-09-24 08:00:00")`

```json
{"reminders": [
  {"content": "Sprint standup in 15 minutes",   "timestamp": "2026-09-24T09:45:00", "category": "meeting"},
  {"content": "Q3 budget deadline in 2 hours",  "timestamp": "2026-09-24T15:00:00", "category": "deadline"},
  {"content": "Leave now for dentist (18:30)",  "timestamp": "2026-09-24T18:00:00", "category": "personal"}
]}
```

Schema tricks used:

- **Arrays of objects** (`"type": "array", "items": {...}`) for a variable number of results.
- **Instructions inside descriptions**, e.g. "Resolve every relative time ... into an
  absolute ISO 8601 timestamp using the reference datetime".
- **A reference datetime in the prompt**, so "two hours ahead" can be resolved.
- **Categories listed** in the description. Better still: `"enum": ["meeting", "deadline", "personal", "other"]`.

**Extract, then act:** `demo_structured` first gets the validated plan, prints it (you
could show it to the user or save it), and **then** runs all reminders as one batch.
That's safer than letting an agent act immediately
([Module 04](../04_tool_use/README.md) `demo_agent`).

---

## 5. Technique 3: `output_config.format` (the modern way)

### With a raw JSON Schema

```python
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    messages=[{"role": "user", "content": "Extract: John Smith (john@example.com) wants the Enterprise plan."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name":  {"type": "string"},
                    "email": {"type": "string"},
                    "plan":  {"type": "string", "enum": ["Free", "Pro", "Enterprise"]},
                },
                "required": ["name", "email", "plan"],
                "additionalProperties": False,
            },
        }
    },
)
data = json.loads(next(b.text for b in response.content if b.type == "text"))
```

### With Pydantic (validated Python objects)

```python
from pydantic import BaseModel

class Contact(BaseModel):
    name: str
    email: str
    plan: str
    interests: list[str]
    demo_requested: bool

response = client.messages.parse(
    model="claude-opus-5",
    max_tokens=16000,
    messages=[{"role": "user", "content":
        "Extract: Jane Doe (jane@co.com) wants Enterprise, interested in API and SDKs, wants a demo."}],
    output_format=Contact,
)
contact = response.parsed_output          # a Contact instance
print(contact.name, contact.interests)
```

### Strict tool use (tools as actions, with guaranteed args)

```python
{"name": "book_flight", "strict": True,
 "input_schema": {"type": "object",
                  "properties": {"destination": {"type": "string"},
                                 "passengers": {"type": "integer", "enum": [1,2,3,4,5,6]}},
                  "required": ["destination", "passengers"],
                  "additionalProperties": False}}
```

---

## 6. More examples (schemas worth copying)

| Use case | Key fields |
| --- | --- |
| **Invoice extraction** | `vendor`, `invoice_number`, `date`, `line_items[] {description, qty, unit_price}`, `total` |
| **Support ticket triage** | `category` (enum), `priority` (enum low/med/high), `summary`, `needs_human` (bool) |
| **Sentiment analysis** | `sentiment` (enum), `confidence` (number 0–1), `aspects[] {topic, sentiment}` |
| **Resume parsing** | `name`, `email`, `skills[]`, `experience[] {company, role, start, end}` |
| **Meeting notes → actions** | `decisions[]`, `action_items[] {owner, task, due_date}` |
| **Product catalog enrichment** | `title`, `bullet_points[]`, `tags[]`, `category` (enum) |
| **Eval grader** ([Module 03](../03_prompt_evaluation/README.md)) | `strengths[]`, `weaknesses[]`, `reasoning`, `score` (integer 1–10) |

Example: the Module 03 grader as a forced tool, so it never fails to parse:

```python
grade_schema = {
    "name": "submit_grade",
    "description": "Submit the evaluation of the solution.",
    "input_schema": {"type": "object", "properties": {
        "strengths":  {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "reasoning":  {"type": "string"},
        "score":      {"type": "integer", "minimum": 1, "maximum": 10}},
        "required": ["strengths", "weaknesses", "reasoning", "score"]}}
grade = structured_output(eval_prompt, grade_schema)   # always a dict with an int score
```

---

## 7. Where to use it (real-world scenarios)

| Scenario | Why structure is needed |
| --- | --- |
| Document processing (invoices, receipts, contracts) | Fields go straight into a database or ERP |
| Form auto-fill from emails or chat | Each field maps to a form input |
| Classification pipelines (tickets, reviews, moderation) | Downstream routing needs an exact enum value |
| Turning natural language into API calls (this module's reminders) | Timestamps and params must be exact |
| Generating UI content (cards, product pages) | Front end renders known fields |
| LLM-as-judge / evals | Scores must be numbers you can average |
| Data enrichment at scale | Consistent columns for a spreadsheet or warehouse |

---

## 8. Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Parsing prose with regex | Breaks on small wording changes | Use a schema (technique 2 or 3) |
| Free-form strings where an enum fits | "Meeting", "meeting", "mtg" | `"enum": [...]` |
| No `required` list | Missing fields | List every field you need |
| Forced `tool_choice` on Fable 5.1 / Opus 5.5 | 400 error | `output_config.format`, or `auto` + `strict` |
| Relative info without context | Wrong dates | Put the reference date/time in the prompt |
| Trusting values blindly | Valid JSON but wrong numbers | Validate business rules (totals add up, dates in range) |
| Prefill on new models | 400 error | Technique 3 |

---

## 9. Level up: basic → better

| What we did (basic) | Better way | Where |
| --- | --- | --- |
| Prefill + stop sequence ([03](../03_prompt_evaluation/README.md)) | Forced tool (this module) | here |
| Forced tool without `strict` | `"strict": True` + `additionalProperties: false` | section 5 |
| Forced tool | `output_config.format` / `messages.parse(output_format=Model)` | section 5 |
| Dict from `block.input` | Pydantic model with types and validation | section 5 |
| Extraction answers instantly | Thinking first for hard extractions (messy docs, math) | [06 Extended Thinking](../06_extended_thinking/README.md) |
| Extract from text | Extract from images and PDFs (receipts, scans) | Future Module 09 |
| One document at a time | Message Batches API for thousands of documents | Future Module 10 |

---

## 10. Practice

1. Add `"enum"` to `category` in `schedule_plan_schema`.
2. Rewrite `grade_by_model()` in Module 03 to use `grade_schema` above, and remove the prefill.
3. Build an invoice extractor with `messages.parse()` and a Pydantic `Invoice` model.
4. Add a check that each reminder timestamp is in the future before running the batch.

## Cheat sheet

```text
Need JSON?  new models → output_config.format / messages.parse(output_format=PydanticModel)
            tool trick → tools=[schema], tool_choice={"type":"tool","name":...} → block.input
            tool args  → "strict": True + additionalProperties:false
Schema tips: required[] · enum · arrays of objects · instructions in descriptions
Avoid:      prefill on 4.6+/Opus 5 · forced tool_choice on Fable 5.1/Opus 5.5
```
