# Claude API Practice Project

My hands-on notes and code for building with the Claude API, organized as a course.
Each numbered folder is one module: code you can run, the original course notebook,
and a `README.md` with the concepts, examples, where to use them, real-world scenarios,
and what to learn next.

---

## Learning roadmap

```text
 01 Fundamentals ──► 02 SDK Basics ──► 03 Prompt Evaluation
  (how Claude works)   (first calls,       (write prompts, measure them)
                        chat, streaming)            │
                                                    ▼
 07 Text Editor Tool ◄── 06 Extended Thinking ◄── 05 Structured Data ◄── 04 Tool Use
  (built-in tools)        (reasoning before        (reliable JSON out)    (Claude calls
                           answering)                                      your functions)
```

Each module builds on the one before it. Where a module does something the basic way,
its README has a **"Level up"** section that shows the better way and names the module
that teaches it.

| # | Module | You learn | Status |
| --- | --- | --- | --- |
| 01 | [Fundamentals](01_fundamentals/README.md) | Request lifecycle, tokens, models, response anatomy, stop reasons | ✅ Notes |
| 02 | [SDK Basics](02_sdk_basics/README.md) | Client setup, single call, multi-turn chat, streaming, system prompts | ✅ Code + notes |
| 03 | [Prompt Evaluation](03_prompt_evaluation/README.md) | Prompt-engineering techniques, test datasets, code + model graders, scoring | ✅ Code + notes |
| 04 | [Tool Use](04_tool_use/README.md) | Tool schemas, `tool_use` / `tool_result`, the agentic loop, batch tool | ✅ Code + notes |
| 05 | [Structured Data](05_structured_data/README.md) | Forcing JSON with `tool_choice`, `output_config.format`, strict tools | ✅ Code (in 04) + notes |
| 06 | [Extended Thinking](06_extended_thinking/README.md) | Adaptive thinking, effort, thinking blocks, redacted thinking | ✅ Code + notes |
| 07 | [Text Editor Tool](07_text_editor_tool/README.md) | Anthropic-defined tools, file view/create/edit, path safety | 📓 Notebook + notes (script TODO) |

---

## Folder structure

```text
Claude Practice Project/
├── README.md                     ← you are here (roadmap + index)
├── utils.py                      ← shared chat helpers (used by 03/01_basic_pipeline)
├── .env                          ← ANTHROPIC_API_KEY (git-ignored)
│
├── 01_fundamentals/
│   ├── README.md
│   ├── claude_intro_notes.txt    ← my original notes
│   └── claude_models.png         ← model family chart
│
├── 02_sdk_basics/
│   ├── README.md
│   ├── hello.py                  ← one question + one follow-up
│   ├── chatbot.py                ← interactive multi-turn chatbot
│   └── streamresponse.py         ← streaming output
│
├── 03_prompt_evaluation/
│   ├── README.md
│   ├── 01_basic_pipeline/        ← hand-built eval: dataset → run → grade → score
│   ├── 02_prompt_evaluator/      ← reusable PromptEvaluator class + HTML report
│   └── notebooks/
│
├── 04_tool_use/
│   ├── README.md
│   ├── tools.py                  ← tool functions + JSON schemas
│   ├── tool_runner.py            ← dispatch + batch_tool fan-out
│   ├── conversation.py           ← client + helpers (returns full Message)
│   ├── structured_data.py        ← used by Module 05
│   ├── scheduling_agent.py       ← agentic loop + demos
│   └── notebooks/
│
├── 05_structured_data/
│   ├── README.md                 ← code lives in ../04_tool_use/structured_data.py
│   └── notebooks/
│
├── 06_extended_thinking/
│   ├── README.md
│   ├── thinking_chat.py          ← chat() with thinking, block-preserving helpers
│   ├── flow.py                   ← two-turn flow + stripped/redacted demos
│   └── notebooks/
│
└── 07_text_editor_tool/
    ├── README.md
    └── notebooks/
```

> **Why is `structured_data.py` in `04_tool_use/`?** It imports `conversation.chat`, and
> `scheduling_agent.py` imports it back, so the two modules share one folder. Module 05's
> README explains it and links to the file.

---

## Setup (once)

```bash
pip install anthropic python-dotenv pydantic
```

Create `.env` in the project root:

```text
ANTHROPIC_API_KEY=sk-ant-...
```

Every script calls `load_dotenv()`, which searches parent folders for `.env`, so you can
run any script from inside its own module folder:

```bash
cd 02_sdk_basics && python hello.py
cd 04_tool_use   && python scheduling_agent.py agent
cd 06_extended_thinking && python flow.py
```

---

## Quick lookup: "I want to…" → where it is

| I want to… | Module | File |
| --- | --- | --- |
| Send one message and print the answer | 02 | [hello.py](02_sdk_basics/hello.py) |
| Keep a conversation going (memory) | 02 | [chatbot.py](02_sdk_basics/chatbot.py) |
| Show text as it's generated | 02 | [streamresponse.py](02_sdk_basics/streamresponse.py) |
| Test whether my prompt is actually good | 03 | [run_evaluation.py](03_prompt_evaluation/01_basic_pipeline/run_evaluation.py) |
| Generate test cases automatically | 03 | [prompt_evaluator.py](03_prompt_evaluation/02_prompt_evaluator/prompt_evaluator.py) |
| Check generated code/JSON/regex is valid | 03 | [validate_syntax.py](03_prompt_evaluation/01_basic_pipeline/validate_syntax.py) |
| Let Claude call my Python functions | 04 | [tools.py](04_tool_use/tools.py), [tool_runner.py](04_tool_use/tool_runner.py) |
| Run a loop until Claude is done using tools | 04 | [scheduling_agent.py](04_tool_use/scheduling_agent.py) |
| Get guaranteed JSON back | 05 | [structured_data.py](04_tool_use/structured_data.py) |
| Make Claude reason before answering | 06 | [thinking_chat.py](06_extended_thinking/thinking_chat.py) |
| Let Claude read and edit files | 07 | [text_editor_tool.ipynb](07_text_editor_tool/notebooks/text_editor_tool.ipynb) |

---

## The improvement map (basic → better)

What each module did the simple way, and where the better way lives:

| Basic approach (where) | Problem | Better approach (where) |
| --- | --- | --- |
| `response.content[0].text` (02) | Breaks when the first block is `thinking` or `tool_use` | Loop over blocks, filter `type == "text"` (04, 06) |
| Store the assistant turn as a string (02) | Loses thinking/tool blocks | Store `message.content`, the full block list (04, 06) |
| Prefill `` ```json `` + stop sequence for JSON (03) | 400 error on Opus 5 / 4.6+ models; can still produce invalid JSON | Forced tool (05) or `output_config.format` (05) |
| Model grader parses free-text JSON (03) | `json.loads` can fail, and the fallback gives a score of 0 | Grader returns via schema (05) |
| One tool call per round trip (04) | Slow for N similar actions | Parallel tool calls / `batch_tool` (04) |
| `while True` agent loop (04) | Can loop forever | Add a `max_turns` guard, or use the SDK Tool Runner (04 → Level up) |
| Fixed `budget_tokens` thinking (06 notebook) | 400 error on 4.7+ models | `{"type": "adaptive"}` + `effort` (06) |
| Hand-written file tool schema (custom) | Claude isn't trained on it | Anthropic-defined `text_editor_20250728` (07) |

---

## Topics not yet covered (suggested next modules)

| Next topic | Why it matters | Builds on |
| --- | --- | --- |
| 08 Prompt caching | Up to ~90% cheaper on repeated long context (system prompts, documents) | 02 |
| 09 Vision & PDFs | Send images and documents as content blocks | 02 |
| 10 Message Batches API | 50% cheaper for bulk/offline jobs such as big eval runs | 03 |
| 11 Server tools (web search, code execution) | Tools Anthropic runs for you, with no loop code | 04, 07 |
| 12 RAG (retrieval) | Answer questions over your own documents | 02, 05 |
| 13 MCP (Model Context Protocol) | Plug standard tool servers into Claude | 04 |
| 14 Agents (Tool Runner, Agent SDK, Managed Agents) | Production-grade agent loops | 04, 06, 07 |

---

## Conventions used in the code

- **SDK:** `anthropic` 1.x. `temperature` / `top_p` / `top_k` were removed from
  `messages.create()`; passing them raises an error. None of the code passes them.
- **Models:** `claude-haiku-4-5` for cheap course exercises (Modules 02–05) and
  `claude-opus-5` for thinking and streaming (Modules 02, 06).
- **Windows console:** scripts that print model output call
  `sys.stdout.reconfigure(encoding="utf-8")`. Without it, cp1252 crashes on characters like `→`.
