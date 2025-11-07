"""Parser for Claude Code transcript JSONL files."""

import json
from pathlib import Path
from typing import Any


def is_warmup_conversation(messages: list[dict[str, Any]]) -> bool:
    """Detect if a conversation starts with warmup.

    Warmup is when the first user message is "Warmup" followed by assistant greeting.

    Args:
        messages: List of message dictionaries

    Returns:
        True if conversation starts with warmup, False otherwise
    """
    if len(messages) < 1:
        return False

    first_msg = messages[0]

    # Check if first message is from user
    role = first_msg.get("role") or first_msg.get("message", {}).get("role")
    if role != "user":
        return False

    # Get content (handle nested message.content format)
    content = first_msg.get("content") or first_msg.get("message", {}).get("content")

    # Check if content is "Warmup"
    if isinstance(content, str):
        return content.strip() == "Warmup"

    return False


def should_include_conversation(
    messages: list[dict[str, Any]], min_messages: int = 1, trim_warmup: bool = True
) -> bool:
    """Determine if a conversation should be included based on length.

    Args:
        messages: List of message dictionaries
        min_messages: Minimum number of messages to include conversation (default 1)
        trim_warmup: Whether to remove warmup messages before counting

    Returns:
        True if conversation should be included, False otherwise
    """
    if not messages:
        return False

    # Optionally trim warmup before counting
    if trim_warmup and is_warmup_conversation(messages):
        messages_to_count = messages[2:]  # Skip first 2 messages (user "Warmup" + assistant greeting)
    else:
        messages_to_count = messages

    # Count non-meta messages (handle both direct isMeta and nested message formats)
    actual_messages = [
        m for m in messages_to_count if not (m.get("isMeta", False) or m.get("message", {}).get("isMeta", False))
    ]

    return len(actual_messages) >= min_messages


class TranscriptParser:
    """Parse Claude Code transcript JSONL files."""

    def __init__(self, file_path: Path):
        """Initialize parser with a transcript file path."""
        self.file_path = file_path
        self.messages: list[dict[str, Any]] = []
        self._parse()

    def _parse(self):
        """Parse the JSONL file."""
        with open(self.file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        self.messages.append(data)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse line in {self.file_path}: {e}")

    def get_conversation_info(self) -> dict[str, Any]:
        """Get basic information about the conversation."""
        if not self.messages:
            return {}

        # Find first and last timestamps
        timestamps = []
        for msg in self.messages:
            if "timestamp" in msg:
                timestamps.append(msg["timestamp"])

        # Count actual messages (not meta messages)
        actual_messages = [m for m in self.messages if not m.get("isMeta", False)]

        info = {
            "file_name": self.file_path.name,
            "message_count": len(actual_messages),
            "total_entries": len(self.messages),
            "start_time": min(timestamps) if timestamps else None,
            "end_time": max(timestamps) if timestamps else None,
        }

        # Try to get conversation ID and session ID
        if self.file_path.stem:
            info["conversation_id"] = self.file_path.stem

        # Try to get session ID from first message
        if self.messages and "sessionId" in self.messages[0]:
            info["session_id"] = self.messages[0]["sessionId"]

        return info

    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages from the transcript."""
        return self.messages

    def get_messages_without_warmup(self) -> list[dict[str, Any]]:
        """Get messages with warmup trimmed.

        Returns:
            List of messages after warmup is removed (skips first 2 if warmup detected)
        """
        if is_warmup_conversation(self.messages):
            return self.messages[2:]  # Skip user "Warmup" + assistant greeting
        return self.messages

    def get_summary(self) -> str | None:
        """Try to extract a summary or title from the conversation."""
        # Look for system messages or first user message
        for msg in self.messages:
            if msg.get("type") == "conversation_title":
                return msg.get("content", "")
            elif msg.get("role") == "user" and msg.get("content"):
                # Return first line of first user message as summary
                content = msg["content"]
                if isinstance(content, str):
                    return content.split("\n")[0][:100] + ("..." if len(content) > 100 else "")
        return None
