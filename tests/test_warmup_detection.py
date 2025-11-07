"""Test warmup message detection and removal."""

from claude_notes.parser import is_warmup_conversation, should_include_conversation


def test_detect_real_warmup():
    """Test detecting warmup with real format."""
    messages = [
        {"role": "user", "content": "Warmup"},
        {"role": "assistant", "content": [{"type": "text", "text": "I'm ready to help..."}]},
        {"role": "user", "content": "Fix the bug"},
        {"role": "assistant", "content": [{"type": "text", "text": "Let me help..."}]},
    ]

    assert is_warmup_conversation(messages) is True


def test_no_warmup_in_conversation():
    """Test conversation with no warmup."""
    messages = [
        {"role": "user", "content": "Fix the bug"},
        {"role": "assistant", "content": [{"type": "text", "text": "Let me help..."}]},
    ]

    assert is_warmup_conversation(messages) is False


def test_empty_messages():
    """Test handling empty message list."""
    messages = []
    assert is_warmup_conversation(messages) is False


def test_filter_short_conversations_default():
    """Test filtering conversations shorter than default threshold."""
    # Short conversation (5 lines after warmup)
    short_messages = [
        {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello"}]},
    ]

    # Long conversation (15 lines)
    long_messages = [{"role": "user", "content": [{"type": "text", "text": "Line " + str(i)}]} for i in range(15)]

    # Default threshold is 10
    assert not should_include_conversation(short_messages, min_messages=10)
    assert should_include_conversation(long_messages, min_messages=10)


def test_filter_respects_custom_threshold():
    """Test custom minimum message threshold."""
    messages = [{"role": "user", "content": [{"type": "text", "text": f"Message {i}"}]} for i in range(5)]

    # Should be excluded with threshold 10
    assert not should_include_conversation(messages, min_messages=10)

    # Should be included with threshold 3
    assert should_include_conversation(messages, min_messages=3)


def test_filter_handles_empty():
    """Test filtering handles empty conversations."""
    assert not should_include_conversation([], min_messages=1)


def test_warmup_detection_with_real_data(tmp_path):
    """Test warmup detection with realistic sanitized conversation data."""
    import shutil
    from pathlib import Path

    # Copy fixture to tmp_path
    fixture_path = Path(__file__).parent / "fixtures" / "sample_conversation.jsonl"
    test_file = tmp_path / "conversation.jsonl"
    shutil.copy(fixture_path, test_file)

    # Parse the conversation
    from claude_notes.parser import TranscriptParser

    parser = TranscriptParser(test_file)

    # Get messages with and without warmup
    all_messages = parser.get_messages()
    trimmed_messages = parser.get_messages_without_warmup()

    # Warmup should be first 2 messages (user "Warmup" + assistant greeting)
    assert len(all_messages) >= 2
    assert len(trimmed_messages) == len(all_messages) - 2

    # Verify first message is "Warmup"
    first_msg = all_messages[0]
    content = first_msg.get("content") or first_msg.get("message", {}).get("content")
    assert content == "Warmup"

    # Verify first message after warmup is the real user request
    if len(trimmed_messages) > 0:
        first_real_msg = trimmed_messages[0]
        content_text = first_real_msg.get("message", {}).get("content", [{}])[0].get("text", "")
        assert len(content_text) > 0  # Should have real content
