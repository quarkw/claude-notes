"""Test Rich markup escaping in terminal formatter."""

from io import StringIO

from rich.console import Console

from claude_notes.formatters.terminal import TerminalFormatter


def test_file_path_with_brackets_does_not_crash():
    """Test that file paths with brackets don't cause markup errors."""
    # Create a console that captures output
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = TerminalFormatter(console)

    # Message with file path containing brackets (this structure matches actual JSONL format)
    messages = [
        {
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "I found the file at [/Users/quark/workspace/test.sh]"}],
            }
        }
    ]

    conversation_info = {"file_name": "test.jsonl", "message_count": 1}

    # This should not raise MarkupError
    try:
        formatter.display_conversation(messages, conversation_info)
        assert True  # Success if no exception
    except Exception as e:
        assert False, f"Expected no exception but got: {e}"


def test_markdown_links_still_work():
    """Test that markdown links still render correctly."""
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = TerminalFormatter(console)

    messages = [
        {
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Check out [this link](https://example.com)"}],
            }
        }
    ]

    conversation_info = {"file_name": "test.jsonl", "message_count": 1}

    # Should work without exception
    formatter.display_conversation(messages, conversation_info)
    result = output.getvalue()
    assert "example.com" in result
