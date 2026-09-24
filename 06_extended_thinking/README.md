# Module 06: Extended Thinking

> **What you learn:** let Claude **reason before answering**, control how much it thinks
> with `effort`, read or hide its reasoning, and pass thinking blocks back correctly in
> multi-turn conversations.
>
> **Prerequisites:** [02 SDK Basics](../02_sdk_basics/README.md), [04 Tool Use](../04_tool_use/README.md) · **Next:** [07 Text Editor Tool](../07_text_editor_tool/README.md)

## Files

| File | What's in it |
| --- | --- |
| [thinking_chat.py](thinking_chat.py) | `chat()` with thinking on, `thinking_params()` (per-model config), block-preserving `add_*_message()`, `thinking_from_message()`, `print_usage()` |
| [flow.py](flow.py) | Three demos: the two-turn flow, the same flow with thinking stripped, redacted thinking |
| [notebooks/thinking_complete.ipynb](notebooks/thinking_complete.ipynb) | Course notebook (written for older models, see section 8) |

```bash
python flow.py              # ask → think → answer → follow up (blocks preserved)
python flow.py stripped     # the same follow-up with thinking blocks dropped
python flow.py redacted     # trigger a redacted_thinking block
```

---

## 1. What is extended thinking?

Normally Claude starts writing the answer immediately. With thinking on, it first
produces **reasoning**: working through the problem, checking itself, considering
alternatives. Then it writes the final answer.

```text
Without thinking:  question ──────────────────────► answer
With thinking:     question ──► [ reasoning … ] ──► better answer
```

The reasoning comes back as `thinking` blocks **before** the `text` block:

```python
message.content == [ThinkingBlock(thinking="Let me consider each box...", signature="..."),
                    TextBlock(text="Draw from the box labelled MIXED...")]
```

---

## 2. How to turn it on (current models)

```python
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    thinking={"type": "adaptive", "display": "summarized"},  # Claude decides how much to think
    output_config={"effort": "medium"},                       # the depth dial
    messages=[{"role": "user", "content": PUZZLE}],
)

for block in response.content:
    if block.type == "thinking":
        print("THINKING:", block.thinking)
    elif block.type == "text":
        print("ANSWER:", block.text)
```

### The three settings

| Setting | Values | Meaning |
| --- | --- | --- |
| `thinking.type` | `"adaptive"` | Claude decides when and how much to think (current models) |
| | `"enabled"` + `budget_tokens` | Old fixed budget, **only** Haiku 4.5 / Sonnet 4.5 and older |
| `thinking.display` | `"omitted"` (default) | You get `thinking` blocks with **empty text**. Thinking still happens and is still billed |
| | `"summarized"` | A readable summary of the reasoning |
| `output_config.effort` | `low` · `medium` · `high` (default) · `xhigh` · `max` | How hard to think; more effort means better on hard problems, slower, more tokens |

> The raw chain of thought is **never** returned on any current model, only a summary
> (or nothing).

### Per-model rules ([thinking_chat.py](thinking_chat.py) `thinking_params()` handles this)

| Model | Config | Notes |
| --- | --- | --- |
| Opus 5, Sonnet 5, Opus 4.7/4.8 | `{"type": "adaptive"}` | `budget_tokens` → **400** |
| Opus 5 | thinking is **on by default** even if you omit `thinking` | |
| Fable 5 / 5.1 | always on; omit `thinking` or send adaptive | `disabled` → 400 |
| Haiku 4.5, Sonnet 4.5 | `{"type": "enabled", "budget_tokens": N}` (N ≥ 1024, < `max_tokens`) | `effort` → error |

```python
LEGACY_THINKING_MODELS = {"claude-haiku-4-5", "claude-sonnet-4-5"}

def thinking_params(model, budget_tokens=2048):
    if model in LEGACY_THINKING_MODELS:
        return {"type": "enabled", "budget_tokens": budget_tokens}
    return {"type": "adaptive", "display": "summarized"}
```

---

## 3. The most important rule: pass thinking blocks back unchanged

In a multi-turn conversation, the assistant turn must go back **exactly as received**,
thinking blocks included.

```python
first = chat(messages)                    # returns the whole Message
add_assistant_message(messages, first)    # appends first.content: ALL blocks, byte for byte
add_user_message(messages, FOLLOW_UP)
second = chat(messages)                   # continues from turn 1's reasoning
```

❌ **Wrong:**

```python
add_assistant_message(messages, text_from_message(first))   # thinking blocks lost
```

What happens if you drop them (`python flow.py stripped`):

- **Opus 5** accepts it, but turn 2 **re-derives everything** from the answer text alone.
  The reasoning is lost, and you pay for it again.
- **Fable 5.1** detects the edited history and returns a **400**.

Keeping the blocks is correct on every model, so the helper does it by default.

---

## 4. Redacted thinking

Sometimes reasoning comes back **encrypted** as a `redacted_thinking` block:

```text
block types: ['redacted_thinking', 'text']
--- thinking ---
[redacted: 588 chars of encrypted reasoning]
```

You can't read it (`block.data` is ciphertext), but you **must still pass it back
unchanged**. It's the same rule as section 3, and another reason never to rebuild an
assistant turn from its text.

```python
def thinking_from_message(message):
    parts = []
    for block in message.content:
        if block.type == "thinking":
            parts.append(block.thinking or "[thinking happened, not displayed]")
        elif block.type == "redacted_thinking":
            parts.append(f"[redacted: {len(block.data)} chars of encrypted reasoning]")
    return "\n".join(parts)
```

---

## 5. Choosing an effort level

| Effort | Use for | Example |
| --- | --- | --- |
| `low` | Simple, high-volume, latency-sensitive tasks | Classification, short rewrites, the fake-database sentence in [streamresponse.py](../02_sdk_basics/streamresponse.py) |
| `medium` | Everyday reasoning; good cost/quality balance | This module's default (`EFFORT = "medium"`) |
| `high` (default) | Intelligence-sensitive work | Code review, analysis, planning |
| `xhigh` | Coding and agentic tasks on the newest models | Multi-file refactors, long tool loops |
| `max` | Correctness matters more than cost | Hard math, tricky logic, high-stakes decisions |

**Measure, don't guess:** run your [Module 03 eval](../03_prompt_evaluation/README.md) at
two effort levels and keep the cheaper one if the score holds.

---

## 6. More examples

### A. Logic puzzle (this module's flow)

```python
PUZZLE = ("Three boxes are labelled APPLES, ORANGES and MIXED. Every label is wrong. "
          "You may draw one fruit from one box. Which box do you draw from, and how "
          "do you relabel all three?")
FOLLOW_UP = "Now change one thing: only the MIXED label is wrong. Does your method still work?"
```

### B. Streaming the thinking summary, then the answer

```python
with client.messages.stream(
    model="claude-opus-5", max_tokens=16000,
    thinking={"type": "adaptive", "display": "summarized"},
    messages=[{"role": "user", "content": "Plan a 3-city Europe trip in 7 days on €1500."}],
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(event.delta.thinking, end="", flush=True)
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
```

### C. Thinking + tools

`thinking_chat.chat()` accepts `tools=`. Claude reasons, calls a tool, reasons about the
result, and so on. Store every assistant `Message` whole (thinking + `tool_use`) as in
[Module 04](../04_tool_use/README.md).

```python
response = chat(messages, tools=ALL_SCHEMAS)   # from 04_tool_use/tools.py
```

### D. Cheaper thinking for a simple task

```python
chat(messages, effort="low")      # still thinks, briefly
```

### E. Inspect the cost of thinking

```python
print_usage("turn 1", first)   # [turn 1] in=85 out=1432 stop=end_turn
# thinking tokens are billed as output tokens, even when display is "omitted"
```

---

## 7. Where to use it (real-world scenarios)

| Scenario | Why thinking helps |
| --- | --- |
| Complex coding (debugging, refactoring, architecture) | Plans before writing; catches edge cases |
| Math, finance, pricing calculations | Step-by-step reduces arithmetic and logic errors |
| Legal/contract analysis | Weighs clauses against each other before concluding |
| Multi-step agents with tools | Plans which tool to call next and checks results |
| LLM-as-judge graders ([Module 03](../03_prompt_evaluation/README.md)) | More consistent, better-justified scores |
| Hard extraction from messy documents ([Module 05](../05_structured_data/README.md)) | Resolves ambiguity before filling the schema |
| Strategy and planning (roadmaps, trip plans, schedules) | Considers constraints together |

**When NOT to use high effort:** simple chat, translation, classification, and anything
latency-critical. Use `low` (or Haiku without thinking).

---

## 8. What changed since the course notebook

The notebook targets `claude-sonnet-4-5` on `anthropic` 0.x. This project uses `anthropic`
1.x and `claude-opus-5`:

| Notebook | Now | Why |
| --- | --- | --- |
| `{"type": "enabled", "budget_tokens": 1024}` | `{"type": "adaptive"}` + `output_config.effort` | `budget_tokens` → 400 on 4.7+ |
| Thinking text shown by default | `display` defaults to `"omitted"` → ask for `"summarized"` | Changed default on current models |
| `temperature=1.0` | Removed | Sampling params removed (TypeError in SDK 1.x / 400 on 4.6+) |
| `effort` n/a | Sent only for non-legacy models | Haiku 4.5 / Sonnet 4.5 error on `effort` |

---

## 9. Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| `budget_tokens` on Opus 5 / Sonnet 5 / 4.7+ | 400 | `{"type": "adaptive"}` |
| `effort` on Haiku 4.5 | Error | Only send `output_config` to 4.6+ models |
| Rebuilding the assistant turn from text | Lost reasoning (Opus 5) / 400 (Fable 5.1) | `add_assistant_message(messages, message)` |
| `response.content[0].text` | AttributeError: first block is `thinking` | Filter `type == "text"` |
| Expecting to see thinking without `display` | Empty strings | `"display": "summarized"` |
| `max_tokens` too small | Answer cut off after long thinking | Use ~16000 (non-streaming) or stream for bigger |
| Assistant prefill with thinking | 400 on new models | Structured outputs ([05](../05_structured_data/README.md)) |
| Printing summaries on the Windows console | `UnicodeEncodeError` (cp1252) | `sys.stdout.reconfigure(encoding="utf-8")` (done in `flow.py`) |

---

## 10. Level up: basic → better

| What we did (basic) | Better way | Where |
| --- | --- | --- |
| One global `EFFORT` | Tune effort **per task** with an eval | [03](../03_prompt_evaluation/README.md) + section 5 |
| Thinking in a plain chat | Thinking **between tool calls** in an agent | [04](../04_tool_use/README.md) + example C |
| Read the summary after the call | Stream the summary live so the user sees progress | example B |
| Long agent runs could stop anywhere | **Task budgets** (beta) so Claude paces itself | Future Module 14 |
| Growing history with thinking blocks | Context editing / compaction for very long sessions | Future modules |
| Thinking + file edits by hand | Thinking + the built-in text editor tool | [07](../07_text_editor_tool/README.md) |

---

## 11. Practice

1. Run `flow.py` and `flow.py stripped` back to back and compare turn-2 answers and `out=` tokens.
2. Change `EFFORT` to `low`, then `max`, on the puzzle. Compare answer quality and tokens.
3. Set `MODEL = "claude-haiku-4-5"` and confirm `thinking_params()` switches to `budget_tokens`.
4. Stream the thinking summary with example B.
5. Give the thinking chat the Module 04 tools and ask it to plan your reminders.

## Cheat sheet

```text
Turn on:  thinking={"type":"adaptive","display":"summarized"}, output_config={"effort": "..."}
Legacy:   Haiku 4.5 / Sonnet 4.5 → {"type":"enabled","budget_tokens":N}, no effort
Blocks:   thinking / redacted_thinking come BEFORE text; pass them back UNCHANGED
Effort:   low (simple) · medium · high (default) · xhigh (coding/agents) · max (hardest)
Billing:  thinking tokens = output tokens, even when omitted
```
