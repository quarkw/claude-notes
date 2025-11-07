"""Test date display in conversation headers."""

from datetime import datetime, timezone
from io import StringIO

from claude_notes.formatters.terminal import TerminalFormatter
from rich.console import Console


def test_date_appears_in_conversation_output():
    """Test that conversation start date is visible in output."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = TerminalFormatter(console)

    messages = [
        {
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}]
            }
        }
    ]

    # Create conversation info with start time
    start_time = datetime(2025, 11, 6, 14, 30, 0, tzinfo=timezone.utc)
    conversation_info = {
        "file_name": "test.jsonl",
        "message_count": 1,
        "start_time": start_time.isoformat(),
    }

    formatter.display_conversation(messages, conversation_info)
    result = output.getvalue()

    # Should contain date in some format (year at minimum)
    assert "2025" in result


def test_missing_date_handled_gracefully():
    """Test that missing start date doesn't crash."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = TerminalFormatter(console)

    messages = [
        {
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}]
            }
        }
    ]

    conversation_info = {
        "file_name": "test.jsonl",
        "message_count": 1,
        # No start_time
    }

    # Should not crash
    formatter.display_conversation(messages, conversation_info)
    result = output.getvalue()
    assert result  # Got some output
