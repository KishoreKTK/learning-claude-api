# utils.py
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv(override=True)

client = Anthropic()
DEFAULT_MODEL = "claude-haiku-4-5"


def add_user_message(messages, text):
    """Add a user message to the conversation history."""
    user_message = {"role": "user", "content": text}
    messages.append(user_message)


def add_assistant_message(messages, text):
    """Add an assistant message to the conversation history."""
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)


def chat(messages, model=DEFAULT_MODEL, max_tokens=1000, system=None, temperature=1.0, stop_sequences=[]):
    """
    Send a chat request to Claude.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (default: claude-haiku-4-5)
        max_tokens: Maximum tokens in response
        system: Optional system prompt
        temperature: Temperature for generation (0.0-1.0)
        stop_sequences: List of stop sequences
        
    Returns:
        String response from the model
    """
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    
    if system:
        params["system"] = system
    
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    
    message = client.messages.create(**params)
    return message.content[0].text