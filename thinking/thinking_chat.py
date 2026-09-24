# thinking_chat.py
# Helpers for the extended-thinking flow.
#
# The one thing that matters here: chat() returns the whole Message, not just
# its text. Thinking blocks have to go back to the API unchanged on the next
# turn, so nothing downstream is allowed to throw them away.
from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(override=True)

client = Anthropic()

MODEL = "claude-opus-5"
EFFORT = "medium"  # low | medium | high | xhigh | max - how deep the thinking goes

# Models still on the old fixed-budget thinking API. Everything from 4.6 on
# takes {"type": "adaptive"} instead and rejects budget_tokens with a 400.
LEGACY_THINKING_MODELS = {"claude-haiku-4-5", "claude-sonnet-4-5"}


def thinking_params(model, budget_tokens=2048):
    """The `thinking` value this model actually accepts."""
    if model in LEGACY_THINKING_MODELS:
        # The notebook's shape: a hard ceiling, must be < max_tokens, min 1024.
        return {"type": "enabled", "budget_tokens": budget_tokens}
    # Adaptive: Claude decides how much to think. `display` is opt-in - the
    # default is "omitted", which returns thinking blocks with empty text.
    return {"type": "adaptive", "display": "summarized"}


def add_user_message(messages, message):
    messages.append(
        {
            "role": "user",
            "content": message.content if isinstance(message, Message) else message,
        }
    )


def add_assistant_message(messages, message):
    """Append an assistant turn.

    Passing the Message itself puts the full block list back on the wire -
    thinking blocks included, byte for byte. Rebuilding the turn from
    text_from_message() would drop them and break the next request.
    """
    messages.append(
        {
            "role": "assistant",
            "content": message.content if isinstance(message, Message) else message,
        }
    )


def chat(
    messages,
    system=None,
    model=MODEL,
    max_tokens=16000,
    thinking=True,
    effort=EFFORT,
    tools=None,
):
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}

    if thinking:
        params["thinking"] = thinking_params(model)
        # effort is 4.6+ only; Haiku 4.5 and Sonnet 4.5 error on it.
        if model not in LEGACY_THINKING_MODELS:
            params["output_config"] = {"effort": effort}

    if system:
        params["system"] = system

    if tools:
        params["tools"] = tools

    # No temperature: sampling params were removed on 4.6+ models (400), and
    # on the older ones thinking already pins temperature to 1.
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(block.text for block in message.content if block.type == "text")


def thinking_from_message(message):
    """The reasoning Claude exposed, if any.

    Three cases worth telling apart: a summary, an empty string (thinking
    happened and was billed, but display was "omitted"), and a redacted block
    (encrypted, unreadable here, still has to be echoed back).
    """
    parts = []
    for block in message.content:
        if block.type == "thinking":
            parts.append(block.thinking or "[thinking happened, not displayed]")
        elif block.type == "redacted_thinking":
            parts.append(f"[redacted: {len(block.data)} chars of encrypted reasoning]")
    return "\n".join(parts)


def print_usage(label, message):
    u = message.usage
    print(f"[{label}] in={u.input_tokens} out={u.output_tokens} stop={message.stop_reason}")
