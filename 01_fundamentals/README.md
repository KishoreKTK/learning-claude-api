# Module 01: Claude Fundamentals

> **What you learn:** what happens when you "ask Claude something": the request lifecycle,
> tokens, the message format, what comes back, and how to pick a model.
>
> **Prerequisites:** none · **Next:** [02 SDK Basics](../02_sdk_basics/README.md)

Files here:

- [claude_intro_notes.txt](claude_intro_notes.txt): my original notes
- [claude_models.png](claude_models.png): the model family chart from the course

---

## 1. What is Claude and how do you reach it?

Claude is a large language model (LLM). You never run it yourself. You send an HTTPS
request to the **Anthropic API** and get the generated text back. There is one main
endpoint:

```text
POST https://api.anthropic.com/v1/messages
```

Everything in this project (chat, streaming, tools, structured output, thinking) is a
different way of calling that same endpoint.

---

## 2. The five-phase request flow

```text
 ┌────────┐ 1  ┌────────────┐ 2  ┌───────────────┐ 3  ┌──────────┐
 │ Client │──► │ Your server│──► │ Anthropic API │──► │  Model   │
 │ (UI)   │ ◄──│ (Python)   │ ◄──│               │ ◄──│processing│
 └────────┘ 5  └────────────┘ 4  └───────────────┘    └──────────┘
```

| Phase | What happens | Detail |
| --- | --- | --- |
| **1. Request to server** | The user types something in your app | Your front end sends it to **your** backend, never straight to Anthropic, because the API key must stay secret on the server |
| **2. Request to Anthropic API** | Your backend calls the API via the SDK or plain HTTP | Required: **API key**, **model**, **messages**, **max_tokens** |
| **3. Model processing** | Tokenize → embed → contextualize → generate | See section 3 |
| **4. Response to server** | The API returns a `Message` object | Contains `content`, `usage`, `stop_reason` |
| **5. Response to client** | Your backend sends the text (or a stream) to the UI | *(This phase was missing from my notes.)* Your server can post-process first: log usage, filter, format |

**Why a server in the middle?** If the key is in browser or mobile code, anyone can
extract it and spend your money. The server also stores conversation history, enforces
rate limits, and logs cost.

---

## 3. What the model does (phase 3)

| Step | What it means | Analogy |
| --- | --- | --- |
| **Tokenization** | Text is split into tokens: word pieces of about 3–4 characters in English | Cutting a sentence into puzzle pieces |
| **Embedding** | Each token becomes a long list of numbers that encodes its meaning | Giving each piece coordinates on a "meaning map" |
| **Contextualization** | Each embedding is adjusted by the tokens around it ("bank" near "river" vs. near "money") | Pieces changing shape based on their neighbours |
| **Generation** | The model predicts the most likely next token, appends it, and repeats until it stops | Autocomplete, one token at a time |

Consequences worth remembering:

- **You pay per token**, for both input and output.
- **Output is generated one token at a time**, which is why streaming (Module 02) exists.
- **The model has no memory between requests.** You resend the whole conversation every
  time (Module 02).

---

## 4. Anatomy of a request

```python
client.messages.create(
    model="claude-haiku-4-5",          # which model
    max_tokens=1000,                   # hard cap on OUTPUT tokens
    system="You are a concise tutor.", # optional: role and rules
    messages=[                         # the conversation so far
        {"role": "user", "content": "What is a token?"},
    ],
)
```

| Field | Required | Notes |
| --- | --- | --- |
| `model` | ✅ | Exact ID string, e.g. `claude-haiku-4-5`, `claude-opus-5` |
| `max_tokens` | ✅ | If the model hits it, the answer is cut off (`stop_reason = "max_tokens"`) |
| `messages` | ✅ | Alternating `user` / `assistant` turns; the first must be `user` |
| `system` | optional | Instructions that apply to the whole conversation |
| `stop_sequences` | optional | Strings that end generation early (Module 03) |
| `tools`, `tool_choice` | optional | Let Claude call functions (Module 04 / 05) |
| `thinking`, `output_config` | optional | Reasoning and effort (Module 06) |

The API key is not a field. The SDK sends it as a header, read from `ANTHROPIC_API_KEY`.

---

## 5. Anatomy of a response

```json
{
  "id": "msg_01AbC...",
  "type": "message",
  "role": "assistant",
  "model": "claude-haiku-4-5",
  "content": [
    { "type": "text", "text": "A token is a chunk of text..." }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 18, "output_tokens": 42 }
}
```

- **`content` is a list of blocks**, not a string. Block types you will meet: `text`,
  `tool_use` (Module 04), `thinking` / `redacted_thinking` (Module 06).
- **`usage`** is what you're billed for.
- **`stop_reason`** tells you why it stopped:

| `stop_reason` | Meaning | What to do |
| --- | --- | --- |
| `end_turn` | Finished naturally | Use the answer |
| `max_tokens` | Hit your `max_tokens` cap | Raise the cap, or ask it to continue |
| `stop_sequence` | Hit one of your `stop_sequences` | Expected if you set one (Module 03) |
| `tool_use` | Wants you to run a tool | Run it and send back a `tool_result` (Module 04) |
| `pause_turn` | Paused a long server-side turn | Send the response back to let it continue |
| `refusal` | Declined for safety reasons | Check `stop_details`; don't read `content` as an answer |

---

## 6. Choosing a model

The course chart ([claude_models.png](claude_models.png)) shows the three tiers. The idea
still holds: **smarter costs more and is slower.** The chart is older than the current
lineup, though. For example, it says Haiku has no reasoning, but Haiku 4.5 supports
extended thinking.

Current lineup (API prices per 1M tokens, input / output):

| Model | ID | Context | Price | Use it for |
| --- | --- | --- | --- | --- |
| Claude Fable 5.1 | `claude-fable-5-1` | 1M | $10 / $50 | The hardest reasoning, long autonomous agent work |
| Claude Opus 5 | `claude-opus-5` | 1M | $5 / $25 | Default "smart" model: complex coding, planning, analysis |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | $2 / $10 | High-volume production work that still needs quality |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | $1 / $5 | Fast, cheap: classification, extraction, simple chat |

**Rule of thumb:** prototype with a capable model, get it working, then measure with an
eval (Module 03) whether a cheaper model holds the same quality.

### Cost example

A support bot handles 10,000 chats/day, each about 1,500 input and 300 output tokens:

```text
Haiku 4.5 : (10,000×1,500×$1  + 10,000×300×$5 ) / 1M = $15 + $15  = $30/day
Opus 5    : (10,000×1,500×$5  + 10,000×300×$25) / 1M = $75 + $75  = $150/day
```

That's 5× the price, which is why picking the model per task matters.

---

## 7. Where this knowledge is used (real-world)

| Situation | Fundamental that matters |
| --- | --- |
| Answers are cut off mid-sentence | `max_tokens` too low → check `stop_reason == "max_tokens"` |
| Bot "forgets" what the user said | API is stateless → resend history (Module 02) |
| Monthly bill is higher than expected | Tokens × price → log `usage`, choose a cheaper model, cache (future Module 08) |
| Mobile app with Claude inside | Never ship the key → route through your server (phase 1→2) |
| Picking a model for a new feature | Balance cost, speed and intelligence (section 6) |
| Long documents fail | Context window limit (200K for Haiku, 1M for the others) |

---

## 8. Common misconceptions

- ❌ "Claude remembers my previous request." → ✅ Every request is independent.
- ❌ "`max_tokens` limits the input." → ✅ It only limits the **output**.
- ❌ "`response.content` is the answer string." → ✅ It's a list of blocks.
- ❌ "1 token = 1 word." → ✅ Roughly ¾ of a word in English; code and other languages
  often use more.

---

## 9. Level up → where this goes next

| Basic idea here | Next step | Module |
| --- | --- | --- |
| A request has `messages` | Build and grow the list for multi-turn chat | 02 |
| Output is generated token by token | Stream it to the user live | 02 |
| `content` is a list of blocks | Handle `tool_use` blocks | 04 |
| `stop_reason` | `tool_use` drives the agentic loop | 04 |
| Model choice by tier | Measure quality per model with evals | 03 |
| Thinking-capable models | Turn reasoning on and tune `effort` | 06 |

---

## 10. Practice

1. Call the API, print `response.usage`, and work out the cost with the table above.
2. Set `max_tokens=10` and confirm `stop_reason` is `"max_tokens"`.
3. Ask the same question to Haiku and Opus and compare answer quality, latency and cost.

## Cheat sheet

```text
Required: model · max_tokens · messages (+ API key via env)
Response: content[] (blocks) · usage (tokens → $) · stop_reason
Stateless: resend the whole conversation each call
Pick model: Haiku (cheap/fast) → Sonnet (balanced) → Opus (smart) → Fable (smartest)
```
