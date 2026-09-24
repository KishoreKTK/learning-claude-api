from anthropic import Anthropic
from dotenv import load_dotenv

# override=True so the key in .env wins over any stale ANTHROPIC_API_KEY
# already set in the OS/shell environment.
load_dotenv(override=True)

client = Anthropic()  # Reads ANTHROPIC_API_KEY from the environment
model = "claude-haiku-4-5"

# Helper functions to maintain conversation history
def addUserMessage(messages, text):
    userMessage = {"role": "user", "content": text}
    messages.append(userMessage)

def addAssistantMessage(messages, text):
    assistantMessage = {"role": "assistant", "content": text}
    messages.append(assistantMessage)

def chat(messages):
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=messages
    )
    return response.content[0].text

# Example usage
messages = []

# Add initial user message
addUserMessage(messages, "Define quantum computing in one sentence.")
print(messages)

# Send to Claude and get response
answer = chat(messages)
print(answer)

# Add assistant response to history
addAssistantMessage(messages, answer)
print(messages)

# Add follow-up user message
addUserMessage(messages, "Write another sentence.")

# Send updated conversation history to Claude
answer = chat(messages)
print(answer)