# Module 07: Text Editor Tool (Anthropic-Defined Tools)

> **What you learn:** use a tool that **Anthropic defines and Claude is trained on**. You
> don't write its schema, only the code that carries out its commands. With it, Claude can
> view, create and edit files, which is the core of AI coding assistants.
>
> **Prerequisites:** [04 Tool Use](../04_tool_use/README.md) · **Next:** future modules (server tools, MCP, agents)

## Files

| File | What's in it |
| --- | --- |
| [notebooks/text_editor_tool.ipynb](notebooks/text_editor_tool.ipynb) | Course notebook: `TextEditorTool` class, `run_tool` dispatcher, agentic loop |

**Status:** notebook only. Turning it into scripts (`text_editor.py`, `editor_agent.py`)
like Modules 04 and 06 is the next exercise. Fix the notebook bugs in section 7 when you
do.

---

## 1. What is an Anthropic-defined tool?

In [Module 04](../04_tool_use/README.md) you wrote every tool: the name, description and
JSON schema. An **Anthropic-defined** tool is different:

| | Custom tool (Module 04) | Anthropic-defined tool (this module) |
| --- | --- | --- |
| Schema | You write `input_schema` | **Built into the model**; you declare only `type` + `name` |
| Model skill | Learns from your description | **Trained** on this exact tool, so it's very reliable |
| Execution | Your code | **Still your code** (client-side): you do the file operations |

```python
tools = [{"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}]
#         ↑ version-dated type             ↑ fixed name. No input_schema!
```

Other Anthropic-defined **client-side** tools: `{"type": "bash_20250124", "name": "bash"}`.
There are also **server-side** tools (web search, code execution) that Anthropic runs for
you (future Module 11).

---

## 2. The commands

Claude sends a `tool_use` whose `input.command` is one of:

| `command` | Inputs | What your code must do |
| --- | --- | --- |
| `view` | `path`, optional `view_range: [start, end]` | Return file contents with line numbers, or list a directory |
| `create` | `path`, `file_text` | Write a new file |
| `str_replace` | `path`, `old_str`, `new_str` | Replace **exactly one** occurrence; error if 0 or more than 1 match |
| `insert` | `path`, `insert_line`, `insert_text` | Insert text after line N (0 = top of file) |

> `undo_edit` existed in older versions of the tool. It is **not** part of
> `text_editor_20250728`. You can keep backups yourself, but Claude won't send `undo_edit`.

Example `tool_use` from Claude:

```json
{"type": "tool_use", "id": "toolu_01...", "name": "str_replace_based_edit_tool",
 "input": {"command": "str_replace", "path": "app/main.py",
           "old_str": "def add(a, b):\n    return a - b",
           "new_str": "def add(a, b):\n    return a + b"}}
```

---

## 3. How it works: the loop

It's the same agentic loop as Module 04, with a different dispatcher:

```python
editor = TextEditorTool(base_dir="./workspace")

def run_tool(name, tool_input):
    if name != "str_replace_based_edit_tool":
        raise ValueError(f"Unknown tool: {name}")
    cmd = tool_input["command"]
    if cmd == "view":
        return editor.view(tool_input["path"], tool_input.get("view_range"))
    if cmd == "create":
        return editor.create(tool_input["path"], tool_input["file_text"])
    if cmd == "str_replace":
        return editor.str_replace(tool_input["path"], tool_input["old_str"], tool_input["new_str"])
    if cmd == "insert":
        return editor.insert(tool_input["path"], tool_input["insert_line"], tool_input["insert_text"])
    raise ValueError(f"Unknown command: {cmd}")

def run_conversation(messages, max_turns=20):
    for _ in range(max_turns):
        response = chat(messages, tools=[{"type": "text_editor_20250728",
                                          "name": "str_replace_based_edit_tool"}])
        add_assistant_message(messages, response)
        if response.stop_reason != "tool_use":
            return response
        add_user_message(messages, run_tools(response))   # same run_tools as Module 04
```

A typical run for *"Fix the bug in calculator.py"*:

```text
Claude: view calculator.py            → you return the numbered lines
Claude: str_replace "a - b" → "a + b" → you edit, return "Successfully replaced..."
Claude: view calculator.py            → confirms the change
Claude: "Fixed: add() was subtracting." (end_turn)
```

---

## 4. Why `str_replace` needs exactly one match

If `old_str` appears twice, which one should change? Guessing could corrupt the file, so
the tool **refuses** and returns an error (`is_error: True`). Claude then retries with more
surrounding context to make the match unique. This makes edits precise and safe, and it's
how Claude Code edits files too.

---

## 5. Security: the path is untrusted input

Claude chooses the `path`. Your code must **confine every operation to one root folder**.

The notebook's check has a hole:

```python
abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
if not abs_path.startswith(self.base_dir):   # ❌ "/proj-evil/x" starts with "/proj"
    raise ValueError("Access denied")
```

Safer:

```python
from pathlib import Path

def _validate_path(self, file_path):
    root = Path(self.base_dir).resolve()
    target = (root / file_path).resolve()        # resolves "..", symlinks
    if not target.is_relative_to(root):
        raise ValueError(f"Access denied: {file_path} is outside {root}")
    return target
```

Also consider:

- a **dedicated workspace folder**, never your whole disk
- **backups** before every write (the notebook's `_backup_file` is a good idea)
- **git**, so every change can be reviewed and reverted
- **human approval** before writes in sensitive projects
- refusing to touch `.env`, keys, and `.git/`

---

## 6. Where to use it (real-world scenarios)

| Scenario | How the tool is used |
| --- | --- |
| AI coding assistant (like Claude Code) | view → str_replace to fix bugs, add features |
| Automated refactoring | Rename functions or update imports across files |
| Config file management | Update YAML/JSON/INI values precisely |
| Documentation upkeep | Update READMEs and docstrings when code changes |
| Test generation | view source → create `test_*.py` |
| Code review bot that proposes fixes | str_replace in a branch → open a PR |
| Content editing (Markdown sites, blogs) | Precise edits without rewriting whole files |
| Migration scripts | Apply the same change pattern across many files |

---

## 7. Known bugs in the course notebook (fix these when you script it)

| # | Bug | Effect | Fix |
| --- | --- | --- | --- |
| 1 | `run_tool` checks `tool_name == "str_replace_editor"`, but the declared name is `"str_replace_based_edit_tool"` | **Every call fails** with "Unknown tool name" | Compare against `"str_replace_based_edit_tool"` |
| 2 | `insert` reads `tool_input["new_str"]` | `KeyError`: the 20250728 tool sends `insert_text` | Use `tool_input["insert_text"]` |
| 3 | Handles `undo_edit` | Dead code: not sent by this tool version | Remove, or keep as a manual helper |
| 4 | `startswith` path check | Sibling-folder escape (section 5) | `Path.resolve().is_relative_to(root)` |
| 5 | `chat()` passes `temperature=1.0` | `TypeError` on `anthropic` 1.x | Remove it (as in the Module 04 `conversation.py`) |
| 6 | `create` raises if the file exists | Claude can't overwrite a file | Allowed by spec: back up, then overwrite |
| 7 | `while True` loop | Can run forever | `max_turns` guard |

---

## 8. More examples (prompts to try)

```text
1. "Create hello.py that prints the current date, then view it to confirm."
2. "There's a bug in calculator.py: add() returns the wrong result. Find and fix it."
3. "Add type hints to every function in utils.py."
4. "Insert a module docstring at the top of tools.py describing what it contains."
5. "In config.json, change log_level from DEBUG to INFO."
6. "Read README.md and add a 'Troubleshooting' section at the end."
```

---

## 9. Level up: basic → better

| What we did (basic) | Better way | Where |
| --- | --- | --- |
| Notebook only | Scripts: `text_editor.py` (class) + `editor_agent.py` (loop), like Module 04 | Exercise below |
| Edit files blindly | Add **thinking** so Claude plans multi-file changes | [06](../06_extended_thinking/README.md) |
| Edit only | Edit **and run**: add the `bash` tool to run tests after editing | Anthropic-defined `bash_20250124` |
| You host the file system | **Code execution** server tool: Anthropic's sandbox | Future Module 11 |
| Hand-built agent | **Claude Agent SDK**: Claude Code's full harness (Read/Edit/Bash/Grep) as a library | Future Module 14 |
| Trust the edits | Eval the agent: did the tests pass after its edits? | [03](../03_prompt_evaluation/README.md) |

---

## 10. Practice

1. Create `07_text_editor_tool/text_editor.py` from the notebook, with bugs 1–5 fixed.
2. Create `editor_agent.py` with the loop from section 3 and a `workspace/` folder.
3. Put a buggy `calculator.py` in `workspace/` and ask Claude to fix it.
4. Try to escape: ask it to view `../.env`. Your path check must refuse.
5. Add a `bash` tool (restricted to `pytest workspace/`) so Claude can run tests after editing.

## Cheat sheet

```text
Declare: {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}  (no schema)
Commands: view(path, view_range?) · create(path, file_text) · str_replace(path, old_str, new_str)
          insert(path, insert_line, insert_text)
You execute everything locally → return tool_result (is_error on failure)
Safety: resolve path → is_relative_to(root) · backups · git · approval for writes
```
