# conversation.py
# Client, message helpers and the chat() wrapper shared by every module here.
from anthropic import Anthropic
from anthropic.types import Message
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

client = Anthropic()
model = "claude-haiku-4-5"


def add_user_message(messages, message):
    user_message = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)


def add_assistant_message(messages, message):
    assistant_message = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)


def chat(
    messages,
    system=None,
    stop_sequences=[],
    tools=None,
    tool_choice=None,
):
    # The notebooks pass temperature=1.0 here, but anthropic 1.x dropped the
    # sampling params (temperature/top_p/top_k) from messages.create(), so
    # passing one raises TypeError. 1.0 was the default anyway.
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "stop_sequences": stop_sequences,
    }

    if tools:
        params["tools"] = tools

    if tool_choice:
        params["tool_choice"] = tool_choice

    if system:
        params["system"] = system

    message = client.messages.create(**params)
    return message


def text_from_message(message):
    return "\n".join([block.text for block in message.content if block.type == "text"])
