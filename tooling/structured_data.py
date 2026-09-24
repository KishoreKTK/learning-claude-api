# structured_data.py
# Getting structured JSON out of Claude by handing it a tool schema that
# describes the output shape, then forcing that tool with tool_choice.
from anthropic.types import ToolParam

from conversation import add_user_message, chat

article_schema = ToolParam(
    {
        "name": "article_output",
        "description": "Return a scholarly article broken into its individual parts. Use this tool whenever the user asks for an article, paper, or write-up so the title, author and body text come back as separate fields instead of one blob of prose.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the article.",
                },
                "author": {
                    "type": "string",
                    "description": "The full name of the article's author.",
                },
                "body": {
                    "type": "string",
                    "description": "The body of the article as a single paragraph of prose.",
                },
            },
            "required": ["title", "author", "body"],
        },
    }
)

schedule_plan_schema = ToolParam(
    {
        "name": "schedule_plan_output",
        "description": "Return a plan of reminders extracted from an employee's free-text description of their day. Use this tool to turn a loose request such as 'remind me before the 10am standup and an hour before the 4pm deadline' into a list of discrete reminders, each with the exact message text and the exact timestamp it should fire at. Resolve every relative time ('in two hours', 'tomorrow morning', '30 minutes before') into an absolute ISO 8601 timestamp using the reference datetime supplied in the conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reminders": {
                    "type": "array",
                    "description": "One entry per reminder that should be created.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The message text shown in the reminder notification, e.g. 'Join the sprint standup video call'.",
                            },
                            "timestamp": {
                                "type": "string",
                                "description": "The exact moment the reminder should fire, as an ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SS).",
                            },
                            "category": {
                                "type": "string",
                                "description": "The kind of commitment this reminder is for. Must be one of: 'meeting', 'deadline', 'personal', or 'other'.",
                            },
                        },
                        "required": ["content", "timestamp", "category"],
                    },
                }
            },
            "required": ["reminders"],
        },
    }
)


def structured_output(prompt, schema, system=None):
    """Ask Claude for a single forced tool call and return its input dict.

    tool_choice pins the response to `schema`, so the model cannot answer with
    plain prose - the tool_use block's `input` is already-validated JSON.
    """
    messages = []
    add_user_message(messages, prompt)

    response = chat(
        messages,
        system=system,
        tools=[schema],
        tool_choice={"type": "tool", "name": schema["name"]},
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == schema["name"]:
            return block.input

    raise ValueError(f"Model did not call {schema['name']}")


def write_article(topic):
    """The notebook's article example, but returned as fields instead of prose."""
    return structured_output(
        f"Write a one-paragraph scholarly article about {topic}. "
        "Include a title and author name.",
        article_schema,
    )


def plan_reminders(request, reference_datetime):
    """Turn a free-text scheduling request into a list of reminder dicts."""
    plan = structured_output(
        f"The current date and time is {reference_datetime}.\n\n"
        f"Here is my day:\n{request}\n\n"
        "Extract every reminder I need, resolving all relative times against "
        "the current date and time above.",
        schedule_plan_schema,
    )
    return plan["reminders"]
