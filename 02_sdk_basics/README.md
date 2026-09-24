# Module 02: SDK Basics (Calls, Conversations, Streaming)

> **What you learn:** set up the Python SDK, make your first call, hold a multi-turn
> conversation, stream responses live, and use system prompts.
>
> **Prerequisites:** [01 Fundamentals](../01_fundamentals/README.md) · **Next:** [03 Prompt Evaluation](../03_prompt_evaluation/README.md)

## Files

| File | What it shows | Run |
| --- | --- | --- |
| [hello.py](hello.py) | One question, then a follow-up that relies on history | `python hello.py` |
| [chatbot.py](chatbot.py) | Interactive terminal chatbot with memory | `python chatbot.py` (type `quit` to exit) |
| [streamresponse.py](streamresponse.py) | Printing text as it's generated, then the final message | `python streamresponse.py` |
| [../utils.py](../utils.py) | Shared `chat()` / `add_*_message()` helpers used by Module 03 | imported |

---

## 1. Setup

```bash
pip install anthropic python-dotenv
```

```python
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)   # reads .env; override=True beats a stale shell variable
client = Anthropic()         # picks up ANTHROPIC_API_KEY automatically
model = "claude-haiku-4-5"
```

> **Never hardcode the key** in code you commit. `.env` is in `.gitignore`.

---

## 2. Single call

```python
response = client.messages.create(
    model=model,
    max_tokens=1000,
    messages=[{"role": "user", "content": "Define quantum computing in one sentence."}],
)
print(response.content[0].text)
```

**How it works:** you send one `user` message and get one `Message` back. Its `content`
is a list of blocks, and `[0].text` takes the text of the first one.

---

## 3. Multi-turn conversation (memory)

The API is **stateless**. To make Claude "remember", you keep a list and resend all of it
every time.

```python
messages = []

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})

def chat(messages):
    response = client.messages.create(model=model, max_tokens=1000, messages=messages)
    return response.content[0].text

add_user_message(messages, "Define quantum computing in one sentence.")
answer = chat(messages)
add_assistant_message(messages, answer)          # ← store Claude's reply

add_user_message(messages, "Write another sentence.")   # "another" only makes sense with history
print(chat(messages))
```

What goes over the wire on the second call:

```json
[
  {"role": "user",      "content": "Define quantum computing in one sentence."},
  {"role": "assistant", "content": "Quantum computing uses qubits..."},
  {"role": "user",      "content": "Write another sentence."}
]
```

**Rules:** the first message must be `user`. Roles normally alternate (consecutive
same-role messages are merged into one turn).

### The chatbot loop ([chatbot.py](chatbot.py))

```text
while True:
    read input  →  add_user_message  →  chat(messages)  →  add_assistant_message  →  print
```

---

## 4. System prompts

A `system` prompt sets the role, tone and rules for the whole conversation. It isn't part
of `messages`.

```python
response = client.messages.create(
    model=model,
    max_tokens=500,
    system="You are a patient Python tutor. Answer in at most 3 sentences and include one code example.",
    messages=[{"role": "user", "content": "What is a list comprehension?"}],
)
```

Good system prompts cover:

- **Role:** "You are a customer support agent for Acme Bank."
- **Rules:** "Never give investment advice. If unsure, say so."
- **Format:** "Reply in bullet points." / "Reply in JSON."
- **Audience:** "The user is a beginner."

---

## 5. Streaming

Without streaming, the user stares at a blank screen until the whole answer is ready.
With streaming, text appears as it's generated.

```python
with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1000,
    output_config={"effort": "low"},     # simple task → think less, answer faster
    messages=[{"role": "user", "content": "Write a one sentence description of a fake database."}],
) as stream:
    for text in stream.text_stream:       # text chunks as they arrive
        print(text, end="", flush=True)
    final = stream.get_final_message()    # the full Message (usage, stop_reason); read it inside the `with`

print("\nTokens:", final.usage.output_tokens)
```

**When to stream:** chat UIs, long outputs, and any large `max_tokens`. The SDK expects
streaming for very long generations, to avoid HTTP timeouts.

### Streaming inside the chatbot

```python
def chat_stream(messages):
    with client.messages.stream(model=model, max_tokens=1000, messages=messages) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print()
        return stream.get_final_message().content[0].text
```

---

## 6. More examples

### A. Translator (system prompt + single call)

```python
def translate(text, target="Tamil"):
    r = client.messages.create(
        model=model, max_tokens=500,
        system=f"Translate the user's text to {target}. Output only the translation.",
        messages=[{"role": "user", "content": text}],
    )
    return r.content[0].text
```

### B. Summarizer with a length rule

```python
def summarize(article, bullets=3):
    r = client.messages.create(
        model=model, max_tokens=400,
        messages=[{"role": "user", "content":
            f"Summarize in exactly {bullets} bullet points:\n\n<article>\n{article}\n</article>"}],
    )
    return r.content[0].text
```

### C. Track cost per conversation

```python
PRICE_IN, PRICE_OUT = 1 / 1_000_000, 5 / 1_000_000   # Haiku 4.5, $ per token
total = 0.0

def chat_and_bill(messages):
    global total
    r = client.messages.create(model=model, max_tokens=1000, messages=messages)
    total += r.usage.input_tokens * PRICE_IN + r.usage.output_tokens * PRICE_OUT
    return r.content[0].text
```

### D. Handle errors properly

```python
import anthropic

try:
    r = client.messages.create(model=model, max_tokens=500, messages=messages)
except anthropic.AuthenticationError:
    print("Bad API key: check .env")
except anthropic.RateLimitError:
    print("Rate limited: slow down (the SDK already retried twice)")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
except anthropic.APIConnectionError:
    print("Network problem")
```

### E. Detect a truncated answer

```python
r = client.messages.create(model=model, max_tokens=50, messages=messages)
if r.stop_reason == "max_tokens":
    print("⚠️ Answer was cut off: raise max_tokens")
```

---

## 7. Where to use it (real-world scenarios)

| Scenario | Pattern from this module |
| --- | --- |
| Customer support chat widget | Multi-turn history + system prompt (role, policy) + streaming |
| "Summarize this email" button | Single call + system prompt |
| Internal Q&A bot in Slack/Teams | Multi-turn, one `messages` list per thread |
| Writing assistant (drafts, rewrites) | Streaming so text appears as it's typed |
| Language translation service | Single call, strict "output only the translation" system prompt |
| Coding tutor | System prompt sets level and format; multi-turn for follow-ups |
| CLI helper tool | [chatbot.py](chatbot.py)-style loop |

---

## 8. Common mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Not appending the assistant reply | Bot forgets its own answers | `add_assistant_message` after every call |
| `response.content[0].text` everywhere | Crash when the first block is `thinking` or `tool_use` | Filter blocks by `type == "text"` (see Level up) |
| Passing `temperature=...` | `TypeError` on `anthropic` 1.x / 400 on new models | Remove it: sampling params are gone |
| History grows forever | Slower and more expensive each turn | Trim old turns, summarize, or use caching/compaction (future modules) |
| Reading `get_final_message()` after the `with` block | Stream already closed | Call it inside the `with` |
| Key in code | Leaked on GitHub | `.env` + `load_dotenv()` |

**Known issues in this project's code:**

- [utils.py](../utils.py): `chat()` accepts `temperature=1.0` but never sends it (good, it
  would break). The parameter is misleading and can be deleted.
- `stop_sequences=[]` as a default argument is a mutable default. It's harmless here
  because it's never modified, but `None` is the idiomatic choice.

---

## 9. Level up: basic → better

| What we did (basic) | Better way | Where it's covered |
| --- | --- | --- |
| `return response.content[0].text` | `"\n".join(b.text for b in r.content if b.type == "text")` | [04 conversation.py](../04_tool_use/conversation.py) `text_from_message` |
| Store assistant turn as a **string** | Store `response.content` (all blocks) so tool/thinking blocks survive | [04](../04_tool_use/README.md), [06](../06_extended_thinking/README.md) |
| Ask for a format in plain words | Guaranteed JSON with schemas | [05 Structured Data](../05_structured_data/README.md) |
| "Looks good to me" testing | Measure prompt quality with datasets and graders | [03 Prompt Evaluation](../03_prompt_evaluation/README.md) |
| Chatbot can only talk | Chatbot that can **act** (call functions) | [04 Tool Use](../04_tool_use/README.md) |
| `effort: "low"` in streaming | Full control of reasoning depth | [06 Extended Thinking](../06_extended_thinking/README.md) |
| Resend the same long system prompt every call | Prompt caching (up to ~90% cheaper) | Future Module 08 |

---

## 10. Practice

1. Add a `system` prompt to [chatbot.py](chatbot.py) that makes it a pirate. Check it stays in character.
2. Switch the chatbot to streaming with `chat_stream()` above.
3. Print a running token and cost total after each turn.
4. Add a `/reset` command that clears `messages`.
5. Keep only the last 10 messages and notice what the bot forgets.

## Cheat sheet

```python
client.messages.create(model=..., max_tokens=..., messages=[...], system="...")
client.messages.stream(...)  →  stream.text_stream  /  stream.get_final_message()
History = list of {"role": "user"|"assistant", "content": ...}; resend it every time
```
