# tooling

Batch tool use + structured data, built from the two course notebooks:

- `ipynb files/_400ec29330044fdfb29e816a63fc9c79_001_tools_008.ipynb`
- `ipynb files/_9a3ce1e725ad450e84368fe839fabd4b_002_structured_data.ipynb`

The scenario is the corporate scheduling assistant: an employee describes a day
with several meetings, deadlines and personal appointments, and the assistant
sets every reminder in **one** round trip instead of one call per reminder.

## Files

| File | What's in it |
| --- | --- |
| `tools.py` | The tool functions (`add_duration_to_datetime`, `get_current_datetime`, `set_reminder`) and their schemas, plus `batch_tool_schema` |
| `tool_runner.py` | `run_tool` / `run_tools` dispatch, and `run_batch` - the part that actually fans a `batch_tool` call out to the individual tools |
| `structured_data.py` | Tool schemas used as *output* formats: `article_schema` and `schedule_plan_schema`, forced with `tool_choice` |
| `scheduling_agent.py` | The agentic loop (`run_conversation`) and three runnable demos |

## Running

```bash
cd tooling
python scheduling_agent.py              # structured + agent demos
python scheduling_agent.py agent        # Claude picks batch_tool itself
python scheduling_agent.py structured   # extract a validated plan, then batch it
python scheduling_agent.py article       # the notebook's structured-output example
```

`ANTHROPIC_API_KEY` is read from the project's `.env`.

## Why the batch tool matters here

Without it, "remind me before the standup, before the budget deadline, and
before the dentist" is three `set_reminder` calls, and each one costs a full
request/response round trip through the agentic loop. With `batch_tool`, Claude
sends a single `tool_use` block:

```json
{
  "name": "batch_tool",
  "input": {
    "invocations": [
      {"name": "set_reminder", "arguments": "{\"content\": \"...\", \"timestamp\": \"...\"}"},
      {"name": "set_reminder", "arguments": "{\"content\": \"...\", \"timestamp\": \"...\"}"},
      {"name": "set_reminder", "arguments": "{\"content\": \"...\", \"timestamp\": \"...\"}"}
    ]
  }
}
```

`run_batch` decodes each `arguments` JSON string, calls the named tool, and
returns all outputs in one `tool_result`. Verified against the API: three
reminders arrive as 1 `tool_use` block holding 3 invocations.

## Two ways to get there

`demo_agent` lets the model decide - it reads the free-text request and emits
the batch call. `demo_structured` splits the job in two: first force
`schedule_plan_output` with `tool_choice` so the reminders come back as
validated JSON (relative times like "15 minutes before" already resolved to ISO
timestamps), then execute that list locally as one batch. The second form is
the one to reach for when you want to inspect or persist the plan before acting
on it.

## Notes on the SDK version

These notebooks were written for `anthropic` 0.x; this project has 1.0.0, which
changes two things:

- **`temperature` is gone from `messages.create()`.** The notebooks' `chat()`
  passes `temperature=1.0` and raises `TypeError` on 1.x. Sampling params were
  removed - 1.0 was the default, so `chat()` here just omits it.
- Printing model output on the default Windows console (cp1252) raises
  `UnicodeEncodeError` on characters like `→`, so `scheduling_agent.py`
  reconfigures stdout to UTF-8.

The structured-output pattern used here (a tool schema + `tool_choice`) is the
notebook's approach and works on every model. Current models also support
`output_config={"format": ...}`, which constrains the response directly instead
of routing it through a tool call - worth knowing about, but `tool_choice` is
what the lesson teaches.

`model` is set to `claude-haiku-4-5` in `conversation.py`, matching the
notebooks.
