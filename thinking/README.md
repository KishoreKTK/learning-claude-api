# thinking

Extended thinking, built from the course notebook:

- `ipynb files/_45af887a875a4d3c9b5cec1ea1178a13_001_thinking_complete.ipynb`

The notebook is three cells: a client, a `chat()` that takes `thinking=True`,
and one call that triggers a redacted thinking block. This folder turns that
into a flow you can run - a two-turn conversation where the first turn's
reasoning is carried into the second.

## Files

| File | What's in it |
| --- | --- |
| `thinking_chat.py` | `chat()` with thinking enabled, `add_*_message()` helpers that preserve blocks, and `thinking_params()` - the per-model config shape |
| `flow.py` | The flow itself, plus two contrast demos |

## Running

```bash
cd thinking
python flow.py              # the flow: ask -> think -> answer -> follow up
python flow.py stripped     # the same follow-up with thinking blocks dropped
python flow.py redacted     # the notebook's magic-string trigger
```

`ANTHROPIC_API_KEY` is read from the project's `.env`.

## The one thing the flow is about

`chat()` returns the whole `Message`, and `add_assistant_message()` appends
`message.content` - the entire block list - rather than a rebuilt string:

```python
first = chat(messages)
add_assistant_message(messages, first)   # thinking blocks go back unchanged
```

Thinking blocks must return to the API exactly as they came. The moment you
rebuild the assistant turn from `text_from_message()`, they are gone. Run
`flow.py` and `flow.py stripped` back to back to see the difference: with the
blocks intact, turn 2 continues the reasoning; with them dropped, turn 2
re-derives everything from the answer text alone.

Whether dropping them is *allowed* is model-dependent. `claude-opus-5` accepts
the edited history without an error - it just loses the reasoning. Claude Fable
5.1 checks for edited history and returns a 400. Keeping the blocks is correct
everywhere, which is why the helper does it by default.

## What changed since the notebook

The notebook targets `claude-sonnet-4-5` on `anthropic` 0.x. This project has
`anthropic` 1.0.0 and the flow defaults to `claude-opus-5`, which moves three
things:

- **`budget_tokens` is gone.** The notebook's
  `{"type": "enabled", "budget_tokens": 1024}` returns a 400 on 4.7+ models.
  The replacement is `{"type": "adaptive"}` - Claude decides how much to think
  - with `output_config={"effort": ...}` (`low` through `max`) as the dial.
  `thinking_params()` in `thinking_chat.py` emits whichever shape the model
  takes, so switching `MODEL` to `claude-haiku-4-5` still runs.
- **Thinking is hidden by default.** On the current models `display` defaults
  to `"omitted"`: you get `thinking` blocks whose text is an empty string, and
  the thinking still happens and is still billed. `thinking_params()` asks for
  `"summarized"` so there is something to print. The raw chain of thought is
  never returned on any current model.
- **`temperature` is gone from `messages.create()`.** Sampling params were
  removed on 4.6+ (400). The notebook passes `temperature=1.0`; `chat()` here
  omits it. On the older models it would have been pinned to 1 by thinking
  anyway.

`effort` is 4.6+ only - Haiku 4.5 and Sonnet 4.5 error on it - so `chat()`
sends `output_config` only when the model is not in `LEGACY_THINKING_MODELS`.

## Redacted thinking still happens

The notebook's magic string is not a historical artifact. On `claude-opus-5`:

```
block types: ['redacted_thinking', 'text']
--- thinking ---
[redacted: 588 chars of encrypted reasoning]
```

A `redacted_thinking` block carries encrypted reasoning in `.data`. You cannot
read it, and you still have to pass it back unchanged on the next turn - the
same rule as an ordinary thinking block, and the reason
`add_assistant_message()` never tries to reconstruct a turn from its text.

## Note on printing

`flow.py` reconfigures stdout to UTF-8. The default Windows console is cp1252
and raises `UnicodeEncodeError` the first time Claude writes a character like
`→` - which, with thinking summaries printed, is quickly.
