# tools.py
# Tool functions and their schemas.
from datetime import datetime, timedelta

from anthropic.types import ToolParam


def add_duration_to_datetime(
    datetime_str, duration=0, unit="days", input_format="%Y-%m-%d"
):
    date = datetime.strptime(datetime_str, input_format)

    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [
                31,
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


def set_reminder(content, timestamp):
    print(f"----\nSetting the following reminder for {timestamp}:\n{content}\n----")
    return f"Reminder set for {timestamp}: {content}"


add_duration_to_datetime_schema = ToolParam(
    {
        "name": "add_duration_to_datetime",
        "description": "Adds a specified duration to a datetime string and returns the resulting datetime in a detailed format. This tool converts an input datetime string to a Python datetime object, adds the specified duration in the requested unit, and returns a formatted string of the resulting datetime. It handles various time units including seconds, minutes, hours, days, weeks, months, and years, with special handling for month and year calculations to account for varying month lengths and leap years. The output is always returned in a detailed format that includes the day of the week, month name, day, year, and time with AM/PM indicator (e.g., 'Thursday, April 03, 2025 10:30:00 AM').",
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {
                    "type": "string",
                    "description": "The input datetime string to which the duration will be added. This should be formatted according to the input_format parameter.",
                },
                "duration": {
                    "type": "number",
                    "description": "The amount of time to add to the datetime. Can be positive (for future dates) or negative (for past dates). Defaults to 0.",
                },
                "unit": {
                    "type": "string",
                    "description": "The unit of time for the duration. Must be one of: 'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', or 'years'. Defaults to 'days'.",
                },
                "input_format": {
                    "type": "string",
                    "description": "The format string for parsing the input datetime_str, using Python's strptime format codes. For example, '%Y-%m-%d' for ISO format dates like '2025-04-03'. Defaults to '%Y-%m-%d'.",
                },
            },
            "required": ["datetime_str"],
        },
    }
)

get_current_datetime_schema = ToolParam(
    {
        "name": "get_current_datetime",
        "description": "Returns the current date and time formatted according to the specified format string. This tool provides the current system time formatted as a string. Use this tool when you need to know the current date and time, such as for timestamping records, calculating time differences, or displaying the current time to users. The default format returns the date and time in ISO-like format (YYYY-MM-DD HH:MM:SS).",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_format": {
                    "type": "string",
                    "description": "A string specifying the format of the returned datetime. Uses Python's strftime format codes. For example, '%Y-%m-%d' returns just the date in YYYY-MM-DD format, '%H:%M:%S' returns just the time in HH:MM:SS format, '%B %d, %Y' returns a date like 'May 07, 2025'. The default is '%Y-%m-%d %H:%M:%S' which returns a complete timestamp like '2025-05-07 14:32:15'.",
                    "default": "%Y-%m-%d %H:%M:%S",
                }
            },
            "required": [],
        },
    }
)

set_reminder_schema = ToolParam(
    {
        "name": "set_reminder",
        "description": "Creates a timed reminder that will notify the user at the specified time with the provided content. This tool schedules a notification to be delivered to the user at the exact timestamp provided. It should be used when a user wants to be reminded about something specific at a future point in time. The reminder system will store the content and timestamp, then trigger a notification through the user's preferred notification channels (mobile alerts, email, etc.) when the specified time arrives. Reminders are persisted even if the application is closed or the device is restarted. Users can rely on this function for important time-sensitive notifications such as meetings, tasks, medication schedules, or any other time-bound activities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The message text that will be displayed in the reminder notification. This should contain the specific information the user wants to be reminded about, such as 'Take medication', 'Join video call with team', or 'Pay utility bills'.",
                },
                "timestamp": {
                    "type": "string",
                    "description": "The exact date and time when the reminder should be triggered, formatted as an ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SS) or a Unix timestamp. The system handles all timezone processing internally, ensuring reminders are triggered at the correct time regardless of where the user is located. Users can simply specify the desired time without worrying about timezone configurations.",
                },
            },
            "required": ["content", "timestamp"],
        },
    }
)

batch_tool_schema = ToolParam(
    {
        "name": "batch_tool",
        "description": "Invoke multiple other tool calls simultaneously",
        "input_schema": {
            "type": "object",
            "properties": {
                "invocations": {
                    "type": "array",
                    "description": "The tool calls to invoke",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the tool to invoke",
                            },
                            "arguments": {
                                "type": "string",
                                "description": "The arguments to the tool, encoded as a JSON string",
                            },
                        },
                        "required": ["name", "arguments"],
                    },
                }
            },
            "required": ["invocations"],
        },
    }
)

# Every non-batch tool, keyed by the name Claude sees in the schema.
TOOL_FUNCTIONS = {
    "add_duration_to_datetime": add_duration_to_datetime,
    "get_current_datetime": get_current_datetime,
    "set_reminder": set_reminder,
}

ALL_SCHEMAS = [
    add_duration_to_datetime_schema,
    get_current_datetime_schema,
    set_reminder_schema,
    batch_tool_schema,
]
