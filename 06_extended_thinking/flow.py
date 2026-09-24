# flow.py
# One simple flow, start to finish:
#
#   ask -> Claude thinks -> answer -> follow up on the same thread
#
# The point of the second turn is the whole lesson: the assistant's first turn
# goes back into `messages` intact, thinking blocks and all.
import sys

from thinking_chat import (
    MODEL,
    add_assistant_message,
    add_user_message,
    chat,
    print_usage,
    text_from_message,
    thinking_from_message,
)

# Model output is UTF-8; the default Windows console is cp1252 and raises
# UnicodeEncodeError on characters like -> the moment Claude writes one.
sys.stdout.reconfigure(encoding="utf-8")

MAGIC_STRING = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"

PUZZLE = (
    "Three boxes are labelled APPLES, ORANGES and MIXED. Every label is wrong. "
    "You may draw one fruit from one box. Which box do you draw from, and how "
    "do you relabel all three?"
)

FOLLOW_UP = "Now change one thing: only the MIXED label is wrong. Does your method still work?"


def banner(text):
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


def show(message):
    reasoning = thinking_from_message(message)
    if reasoning:
        print("--- thinking ---")
        print(reasoning)
    print("--- answer ---")
    print(text_from_message(message))


def demo_flow():
    """The flow: two turns, with the first turn's reasoning carried forward."""
    messages = []

    banner(f"Turn 1 ({MODEL})")
    add_user_message(messages, PUZZLE)
    first = chat(messages)
    show(first)
    print_usage("turn 1", first)

    # The Message goes back whole. This is the line the flow exists to show.
    add_assistant_message(messages, first)

    banner("Turn 2 - follow-up on the same thread")
    add_user_message(messages, FOLLOW_UP)
    second = chat(messages)
    show(second)
    print_usage("turn 2", second)

    add_assistant_message(messages, second)
    print(f"\nConversation is {len(messages)} messages; "
          f"first assistant turn carried {len(first.content)} blocks.")


def demo_stripped():
    """The same second turn, but with the thinking blocks dropped first.

    Run this next to demo_flow() and compare. claude-opus-5 accepts the edited
    history without complaint - turn 2 simply re-derives everything from the
    answer text instead of picking up where turn 1 left off. It is not always
    this forgiving: Claude Fable 5.1 checks for edited history and 400s.
    """
    messages = []
    add_user_message(messages, PUZZLE)
    first = chat(messages)

    text_only = [block for block in first.content if block.type == "text"]
    print(f"Dropping {len(first.content) - len(text_only)} of "
          f"{len(first.content)} blocks from the assistant turn.")
    add_assistant_message(messages, text_only)

    banner("Turn 2 - thinking blocks stripped")
    add_user_message(messages, FOLLOW_UP)
    second = chat(messages)
    show(second)
    print_usage("turn 2 (stripped)", second)


def demo_redacted():
    """The notebook's redacted-thinking trigger.

    The magic string asks the API for a redacted_thinking block: reasoning that
    comes back encrypted. You cannot read it, and you still have to pass it
    back unchanged - which is exactly why add_assistant_message() appends the
    Message rather than a rebuilt string.
    """
    messages = []
    add_user_message(messages, MAGIC_STRING)

    banner(f"Redacted thinking ({MODEL})")
    message = chat(messages)
    print("block types:", [block.type for block in message.content])
    show(message)
    print_usage("redacted", message)


DEMOS = {"flow": demo_flow, "stripped": demo_stripped, "redacted": demo_redacted}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "flow"
    if name not in DEMOS:
        sys.exit(f"unknown demo {name!r}; pick one of {', '.join(DEMOS)}")
    DEMOS[name]()
