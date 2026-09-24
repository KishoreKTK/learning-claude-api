# scheduling_agent.py
# The corporate scheduling assistant: one round trip sets every reminder.
#
#   python scheduling_agent.py            # both demos
#   python scheduling_agent.py agent      # model-driven batch_tool call
#   python scheduling_agent.py structured # structured extraction, then one batch
import json
import sys

from conversation import (
    add_assistant_message,
    add_user_message,
    chat,
    text_from_message,
)
from structured_data import plan_reminders, write_article
from tool_runner import run_tool, run_tools
from tools import ALL_SCHEMAS, get_current_datetime

# Claude's replies contain arrows and dashes the default Windows console
# codepage (cp1252) cannot encode, which crashes print() rather than the API call.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EMPLOYEE_REQUEST = """
Set up my reminders for today. I have the sprint standup at 10:00 and I want a
nudge 15 minutes before it. The Q3 budget deadline is at 17:00 - remind me two
hours ahead so I still have time to fix things. My dentist appointment is at
18:30 and I need to leave 30 minutes early to get there.
"""


def run_conversation(messages):
    """Standard agentic loop: keep answering tool calls until Claude stops asking."""
    while True:
        response = chat(messages, tools=ALL_SCHEMAS)

        add_assistant_message(messages, response)
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages


def batch_invocations(reminders):
    """Pack N reminders into the single batch_tool input the schema expects."""
    return {
        "invocations": [
            {
                "name": "set_reminder",
                "arguments": json.dumps(
                    {
                        "content": reminder["content"],
                        "timestamp": reminder["timestamp"],
                    }
                ),
            }
            for reminder in reminders
        ]
    }


def demo_agent():
    """Let Claude decide: it should reach for batch_tool rather than N calls."""
    print("=== Model-driven batch ===")
    messages = []
    add_user_message(
        messages,
        f"The current date and time is {get_current_datetime()}.\n"
        f"{EMPLOYEE_REQUEST}\n"
        "Use the batch_tool to set all of the reminders in a single call.",
    )
    run_conversation(messages)


def demo_structured():
    """Extract a validated plan first, then execute it in one batch call."""
    print("=== Structured extraction, then one batch ===")
    reminders = plan_reminders(EMPLOYEE_REQUEST, get_current_datetime())

    for reminder in reminders:
        print(f"[{reminder['category']}] {reminder['timestamp']} - {reminder['content']}")

    results = run_tool("batch_tool", batch_invocations(reminders))
    print(f"\n{len(results)} reminders set in 1 batch call.")


def demo_article():
    """The structured-data lesson's own example, kept runnable."""
    print("=== Structured article ===")
    article = write_article("computer science")
    print(f"{article['title']}\nby {article['author']}\n\n{article['body']}")


DEMOS = {
    "agent": demo_agent,
    "structured": demo_structured,
    "article": demo_article,
}

if __name__ == "__main__":
    requested = sys.argv[1:] or ["structured", "agent"]

    for name in requested:
        if name not in DEMOS:
            print(f"Unknown demo: {name}. Choose from {', '.join(DEMOS)}.")
            continue
        DEMOS[name]()
        print()
