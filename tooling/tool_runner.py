# tool_runner.py
# Tool dispatch, including the batch_tool that fans out to several tools at once.
import json

from tools import TOOL_FUNCTIONS


def run_batch(invocations=[]):
    """Run every invocation in one batch_tool call and collect the outputs.

    Each invocation is {"name": <tool name>, "arguments": <JSON string>}, so the
    arguments have to be decoded before they can be splatted into the function.
    """
    batch_output = []

    for invocation in invocations:
        name = invocation["name"]
        args = json.loads(invocation["arguments"])

        tool_output = run_tool(name, args)

        batch_output.append({"tool_name": name, "output": tool_output})

    return batch_output


def run_tool(tool_name, tool_input):
    if tool_name == "batch_tool":
        return run_batch(**tool_input)

    if tool_name in TOOL_FUNCTIONS:
        return TOOL_FUNCTIONS[tool_name](**tool_input)

    raise ValueError(f"Unknown tool: {tool_name}")


def run_tools(message):
    tool_requests = [block for block in message.content if block.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks
