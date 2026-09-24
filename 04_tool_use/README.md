# Module 04: Tool Use (Function Calling and the Agentic Loop)

> **What you learn:** give Claude tools (your Python functions), let it decide when to
> call them, run them, feed the results back, and loop until the task is done. This is
> the basis of every AI agent.
>
> **Prerequisites:** [02 SDK Basics](../02_sdk_basics/README.md) · **Next:** [05 Structured Data](../05_structured_data/README.md)

## Files

| File | What's in it |
| --- | --- |
| [tools.py](tools.py) | The tool **functions** (`get_current_datetime`, `add_duration_to_datetime`, `set_reminder`), their **schemas**, and `batch_tool_schema` |
| [tool_runner.py](tool_runner.py) | `run_tool` (dispatch by name), `run_tools` (build `tool_result` blocks), `run_batch` (fan out one `batch_tool` call) |
| [conversation.py](conversation.py) | Client, `chat()` that returns the **whole `Message`**, block-preserving `add_*_message()`, `text_from_message()` |
| [scheduling_agent.py](scheduling_agent.py) | The agentic loop `run_conversation()` and three demos |
| [structured_data.py](structured_data.py) | Used by [Module 05](../05_structured_data/README.md) |
| [notebooks/tools.ipynb](notebooks/tools.ipynb) | Course notebook: tools basics |
| [notebooks/tools_batch.ipynb](notebooks/tools_batch.ipynb) | Course notebook: batch tool |

```bash
python scheduling_agent.py              # structured + agent demos
python scheduling_agent.py agent        # Claude chooses batch_tool itself
python scheduling_agent.py structured   # extract a plan, then run it in one batch
python scheduling_agent.py article      # Module 05's example
```

**Scenario:** a corporate scheduling assistant. The employee describes their day and the
assistant sets every reminder.

---

## 1. What is tool use?

Claude can only produce text. It can't check the time, query your database, or send an
email. **Tool use** lets it *ask you* to do those things:

1. You describe the tools (name, what it does, what inputs it takes).
2. Claude replies with a `tool_use` block: "call `get_current_datetime` with these args".
3. **Your code** runs the function.
4. You send the output back as a `tool_result`.
5. Claude uses the result to continue, then answers or asks for another tool.

> Claude never runs your code itself. It only asks. You stay in control of what executes.

---

## 2. The flow

```text
 You                                   Claude
  │  user msg + tools=[schemas]          │
  │ ────────────────────────────────────►│
  │                                      │ decides it needs data
  │   assistant: tool_use(id, name, input)│
  │ ◄────────────────────────────────────│   stop_reason = "tool_use"
  │ run function locally                 │
  │  user: tool_result(id, output)       │
  │ ────────────────────────────────────►│
  │                                      │ may call more tools... (loop)
  │   assistant: final text              │
  │ ◄────────────────────────────────────│   stop_reason = "end_turn"
```

---

## 3. Step 1: Write the function

```python
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)
```

Tips: validate inputs and raise clear errors. The error text goes back to Claude so it
can fix its call.

## 4. Step 2: Write the schema

```python
get_current_datetime_schema = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time formatted according to the specified "
                   "format string. Use this tool when you need to know the current date and time...",
    "input_schema": {                      # JSON Schema
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "Python strftime format, e.g. '%Y-%m-%d'. Default '%Y-%m-%d %H:%M:%S'.",
            }
        },
        "required": [],
    },
}
```

**The description is the most important part.** Claude decides *whether* and *how* to
call a tool only from its name and description. Say what it does, when to use it, what it
returns, and give examples of valid inputs. The schemas in [tools.py](tools.py) are long
for this reason.

## 5. Step 3: Send tools with the request

```python
response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=1000,
    messages=messages,
    tools=[get_current_datetime_schema, add_duration_to_datetime_schema, set_reminder_schema],
)
```

The response contains a block like this:

```json
{"type": "tool_use", "id": "toolu_01A...", "name": "get_current_datetime", "input": {"date_format": "%H:%M"}}
```

## 6. Step 4: Run the tool and return the result

```python
def run_tools(message):
    results = []
    for block in message.content:
        if block.type != "tool_use":
            continue
        try:
            output = run_tool(block.name, block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": json.dumps(output), "is_error": False})
        except Exception as e:
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": f"Error: {e}", "is_error": True})
    return results
```

- **`tool_use_id` must match** the `id` of the request it answers.
- **All results go in ONE user message**, even when Claude asked for several tools at once.
- **Errors go back with `is_error: True`**, not dropped. Claude will usually retry
  correctly.

## 7. Step 5: The agentic loop

```python
def run_conversation(messages):
    while True:
        response = chat(messages, tools=ALL_SCHEMAS)
        add_assistant_message(messages, response)     # store ALL blocks, incl. tool_use
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break                                     # Claude is done

        add_user_message(messages, run_tools(response))  # send tool_results back
    return messages
```

This is why `conversation.py`'s `chat()` returns the whole `Message` and
`add_assistant_message()` stores `message.content`. The `tool_use` block must be in the
history, or the matching `tool_result` is rejected.

---

## 8. Batch tool: many actions in one round trip

Request: *"Remind me 15 min before the 10:00 standup, 2 h before the 17:00 budget deadline,
and 30 min before my 18:30 dentist appointment."*

Without batching, that can be **3 round trips**, one `set_reminder` each. The
`batch_tool` schema lets Claude pack all of them into **one** call:

```json
{
  "name": "batch_tool",
  "input": {
    "invocations": [
      {"name": "set_reminder", "arguments": "{\"content\": \"Standup in 15 min\", \"timestamp\": \"2026-09-24T09:45:00\"}"},
      {"name": "set_reminder", "arguments": "{\"content\": \"Q3 budget due in 2h\", \"timestamp\": \"2026-09-24T15:00:00\"}"},
      {"name": "set_reminder", "arguments": "{\"content\": \"Leave for dentist\", \"timestamp\": \"2026-09-24T18:00:00\"}"}
    ]
  }
}
```

```python
def run_batch(invocations=[]):
    out = []
    for inv in invocations:
        args = json.loads(inv["arguments"])          # arguments arrive as a JSON *string*
        out.append({"tool_name": inv["name"], "output": run_tool(inv["name"], args)})
    return out
```

> **Note:** current Claude models also make **parallel tool calls** natively: several
> `tool_use` blocks in one response. `batch_tool` is a pattern that nudges the model
> towards grouping. Either way, return every result in one user message.

---

## 9. More examples

### A. Weather + unit conversion (two tools that chain)

```python
tools = [
  {"name": "get_weather", "description": "Current weather for a city. Returns temp in Celsius.",
   "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
  {"name": "c_to_f", "description": "Convert Celsius to Fahrenheit.",
   "input_schema": {"type": "object", "properties": {"c": {"type": "number"}}, "required": ["c"]}},
]
# "What's the weather in Chennai in °F?" → get_weather("Chennai") → c_to_f(31) → answer
```

### B. Database lookup for support

```python
{"name": "get_order_status",
 "description": "Look up an order by its ID (format ORD-12345). Returns status, carrier, ETA.",
 "input_schema": {"type": "object",
                  "properties": {"order_id": {"type": "string", "pattern": "^ORD-\\d{5}$"}},
                  "required": ["order_id"]}}
```

### C. Calculator (LLMs are bad at exact arithmetic)

```python
{"name": "calculate", "description": "Evaluate an arithmetic expression exactly, e.g. '1234*5678'.",
 "input_schema": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}
# implement it with a safe parser, never eval()
```

### D. Action tool that needs confirmation

```python
def run_tool(name, args):
    if name == "send_email":
        if input(f"Send email to {args['to']}? [y/N] ") != "y":
            raise PermissionError("User declined to send the email")
    ...
```

### E. Loop with a safety limit

```python
def run_conversation(messages, max_turns=10):
    for _ in range(max_turns):
        response = chat(messages, tools=ALL_SCHEMAS)
        add_assistant_message(messages, response)
        if response.stop_reason != "tool_use":
            return response
        add_user_message(messages, run_tools(response))
    raise RuntimeError("Agent did not finish within max_turns")
```

---

## 10. Where to use it (real-world scenarios)

| Scenario | Tools you would give Claude |
| --- | --- |
| Scheduling assistant (this module) | `get_current_datetime`, `add_duration_to_datetime`, `set_reminder` |
| Customer support agent | `get_order_status`, `create_refund`, `escalate_to_human` |
| Internal data assistant | `run_sql(query)` (read-only), `plot_chart` |
| DevOps helper | `get_logs(service)`, `get_metrics`, `restart_service` (with confirmation) |
| Travel booking | `search_flights`, `search_hotels`, `book` |
| E-commerce shopping assistant | `search_products`, `add_to_cart`, `check_stock` |
| CRM assistant | `find_contact`, `log_call`, `create_task` |
| Personal finance bot | `get_transactions`, `categorize`, `calculate` |

---

## 11. Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Storing the assistant turn as text only | 400: `tool_result` without matching `tool_use` | `add_assistant_message(messages, response)` (whole content) |
| Tool results in separate user messages | Claude stops making parallel calls | Put all `tool_result` blocks in one message |
| Dropping failed tool calls | 400 / Claude confused | Return `is_error: True` with the error text |
| Vague descriptions | Wrong tool chosen, bad args | Detailed description + examples in each property |
| `while True` with no limit | Infinite loop, runaway cost | `max_turns` guard |
| Trusting inputs blindly | SQL injection, deleting data | Validate args; read-only tools; human confirmation for actions |
| Relative times without a reference | Wrong reminder times | Give the current datetime (or a tool for it) |

**Known issues in this project's code:**

- `run_conversation()` uses `while True` with no turn limit. Add example E's guard.
- `run_batch(invocations=[])`: mutable default argument. Use `None`.

---

## 12. Level up: basic → better

| What we did (basic) | Better way | Where |
| --- | --- | --- |
| Hand-written `while` loop | SDK **Tool Runner**: `@beta_tool` functions + `client.beta.messages.tool_runner(...)` runs the loop for you | Anthropic docs (future Module 14) |
| Hope tool args match the schema | `"strict": True` on the tool (with `additionalProperties: false`) guarantees valid args | [05 Structured Data](../05_structured_data/README.md) |
| Tools as **actions** | Tools as an **output format**: force a tool to get structured JSON | [05 Structured Data](../05_structured_data/README.md) |
| Claude calls tools without planning | Thinking + tools: reason between tool calls | [06 Extended Thinking](../06_extended_thinking/README.md) |
| Write every tool yourself | **Anthropic-defined tools** (text editor, bash) the model is trained on | [07 Text Editor Tool](../07_text_editor_tool/README.md) |
| You host every tool | **Server tools** (web search, code execution) run by Anthropic | Future Module 11 |
| Tools defined in code | **MCP**: plug in ready-made tool servers | Future Module 13 |
| Evaluate text answers | Evaluate agents: right tool, right args, right order | [03](../03_prompt_evaluation/README.md) + this module |

---

## 13. Practice

1. Add the `max_turns` guard to `run_conversation()`.
2. Add a `list_reminders` tool that returns the reminders set so far (store them in a list).
3. Add a `calculate` tool and ask "What is 2^31 − 1 divided by 7?"
4. Make `set_reminder` fail for past timestamps and watch Claude fix its call via `is_error`.
5. Remove `batch_tool` from `ALL_SCHEMAS` and count round trips for the same request.

## Cheat sheet

```text
Tool = function + schema {name, description, input_schema}
Loop:  chat(tools) → stop_reason=="tool_use"? → run → tool_result(tool_use_id) → repeat
Must:  store full assistant content · all results in one user message · is_error on failure
Batch: one tool_use carrying N invocations → one round trip
```
