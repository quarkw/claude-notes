"""Test CLI filtering integration."""

import json

from claude_notes.parser import TranscriptParser, should_include_conversation


def test_filtering_logic_integration(tmp_path):
    """Test that filtering logic works with real parser."""
    # Create a test JSONL file with warmup and short conversation
    test_file = tmp_path / "test_conversation.jsonl"

    # Create messages with warmup (user "Warmup" + assistant greeting)
    messages = [
        {
            "message": {"role": "user", "content": "Warmup"},
            "timestamp": "2025-11-06T09:59:50Z",
        },
        {
            "message": {"role": "assistant", "content": [{"type": "text", "text": "I'm Claude, ready to help!"}]},
            "timestamp": "2025-11-06T10:00:00Z",
        },
        {
            "message": {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
            "timestamp": "2025-11-06T10:00:10Z",
        },
        {
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Can you help me with a quick question?"}],
            },
            "timestamp": "2025-11-06T10:00:20Z",
        },
        {
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Of course!"}]},
            "timestamp": "2025-11-06T10:00:30Z",
        },
    ]

    # Write messages to JSONL file
    with open(test_file, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    # Parse the file
    parser = TranscriptParser(test_file)

    # Test warmup trimming
    all_messages = parser.get_messages()
    trimmed_messages = parser.get_messages_without_warmup()

    # Should have 5 messages total (2 warmup + 3 real), 3 after warmup trimming
    assert len(all_messages) == 5
    assert len(trimmed_messages) == 3

    # Test filtering with different thresholds
    # With all messages, should pass threshold of 3
    assert should_include_conversation(all_messages, min_messages=3, trim_warmup=False)

    # With warmup trimmed, should pass threshold of 3
    assert should_include_conversation(all_messages, min_messages=3, trim_warmup=True)

    # With warmup trimmed, should fail threshold of 4
    assert not should_include_conversation(all_messages, min_messages=4, trim_warmup=True)


def test_cli_respects_trim_warmup_flag(tmp_path):
    """Test that CLI properly passes trim_warmup flag to filtering logic."""
    import shutil
    from pathlib import Path

    # Copy fixture to tmp_path
    fixture_path = Path(__file__).parent / "fixtures" / "sample_conversation.jsonl"
    test_file = tmp_path / "conversation.jsonl"
    shutil.copy(fixture_path, test_file)

    from claude_notes.parser import TranscriptParser, should_include_conversation

    parser = TranscriptParser(test_file)
    all_messages = parser.get_messages()

    # With trim_warmup=True and min_messages=8, should exclude (only 6 after warmup)
    assert not should_include_conversation(all_messages, min_messages=8, trim_warmup=True)

    # With trim_warmup=False and min_messages=8, should include (9 total)
    assert should_include_conversation(all_messages, min_messages=8, trim_warmup=False)

    # With trim_warmup=True and min_messages=5, should include (6 after warmup)
    assert should_include_conversation(all_messages, min_messages=5, trim_warmup=True)
