from anthropic import Anthropic
from dotenv import load_dotenv

# override=True so the key in .env wins over any stale ANTHROPIC_API_KEY
# already set in the OS/shell environment.
load_dotenv(override=True)

client = Anthropic()  # Reads ANTHROPIC_API_KEY from the environment
model = "claude-opus-5"

# Prepare the list of messages with a user message
messages = [
    {"role": "user", "content": "Write a one sentence description of a fake database."}
]

# Use the streaming method to get chunks of text as they are generated
with client.messages.stream(
    model=model,
    max_tokens=100,
    output_config={"effort": "low"},  # shallow thinking - the task is trivial
    messages=messages
) as stream:
    # Iterate over the text chunks in the stream
    for text in stream.text_stream:
        # Print each chunk without a newline to simulate streaming output
        print(text, end="", flush=True)

    # The full assembled message - must be read inside the `with` block,
    # after the stream has been consumed.
    final_message = stream.get_final_message()

print("\n\nFinal assembled message:")
print(final_message)
