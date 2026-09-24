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

# The conversation history - grows with every turn, so Claude sees the
# whole exchange on each request and answers in context.
messages = []

print("Chatbot ready. Type 'quit' or 'exit' to stop (or press Ctrl+C).\n")

while True:
    try:
        userInput = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        break

    if not userInput:
        continue

    if userInput.lower() in ("quit", "exit"):
        print("Goodbye!")
        break

    # 1. Add the user's message to the history
    addUserMessage(messages, userInput)

    # 2. Send the whole history to Claude
    answer = chat(messages)

    # 3. Add the response back to the history and print it
    addAssistantMessage(messages, answer)
    print(f"Claude: {answer}\n")
