# Bug Fix and Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix Rich markup escaping bug and add warmup detection, short chat filtering, date display, and time-based filtering features

**Architecture:** Four parallel tracks with clear separation of concerns:
1. Bug Fix (terminal formatter) - Fix Rich markup interpretation in file paths
2. Warmup & Filtering (parser layer) - Detect/trim warmup, filter short chats
3. Date Display (formatter layer) - Add start dates to output
4. Time Filtering (CLI layer) - Add time-based filtering flags

**Tech Stack:** Python 3.11+, Click (CLI), Rich (terminal formatting), uv (package management)

---

## Track 1: Bug Fix - Rich Markup Escaping

**Priority:** CRITICAL (blocks usage)

**Problem:** File paths containing brackets like `[/Users/...]` are interpreted as Rich markup tags, causing crashes.

**Solution:** Escape Rich markup characters in text content before printing.

### Task 1.1: Write failing test for markup escaping

**Files:**
- Create: `tests/test_markup_escaping.py`

**Step 1: Write the failing test**

```python
"""Test Rich markup escaping in terminal formatter."""

from claude_notes.formatters.terminal import TerminalFormatter
from rich.console import Console
from io import StringIO


def test_file_path_with_brackets_does_not_crash():
    """Test that file paths with brackets don't cause markup errors."""
    # Create a console that captures output
    output = StringIO()
    console = Console(file=output, force_terminal=True, width=80)
    formatter = TerminalFormatter(console)

    # Message with file path containing brackets
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I found the file at [/Users/quark/workspace/test.sh]"
                }
            ]
        }
    ]

    conversation_info = {
        "file_name": "test.jsonl",
        "message_count": 1
    }

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
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Check out [this link](https://example.com)"
                }
            ]
        }
    ]

    conversation_info = {
        "file_name": "test.jsonl",
        "message_count": 1
    }

    # Should work without exception
    formatter.display_conversation(messages, conversation_info)
    result = output.getvalue()
    assert "example.com" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_markup_escaping.py::test_file_path_with_brackets_does_not_crash -v`

Expected: FAIL with MarkupError (replicates the bug)

**Step 3: Commit the failing test**

```bash
jj commit -m "test(terminal): add failing test for Rich markup escaping

Test demonstrates bug where file paths with brackets cause MarkupError.
Ref: Track 1 - Bug Fix"
```

### Task 1.2: Implement Rich markup escaping

**Files:**
- Modify: `src/claude_notes/formatters/terminal.py:110-130`

**Step 1: Add escaping utility function**

Add after imports in `terminal.py`:

```python
def escape_rich_markup(text: str) -> str:
    """Escape Rich markup characters to prevent interpretation.

    Escapes square brackets that could be interpreted as Rich markup tags.
    Does not escape markdown-style links [text](url).
    """
    # Don't escape markdown links [text](url)
    # Use a regex to escape [ and ] that aren't part of markdown links
    import re

    # First, protect markdown links by replacing them temporarily
    markdown_link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = []

    def protect_link(match):
        links.append(match.group(0))
        return f"__MDLINK_{len(links) - 1}__"

    text = re.sub(markdown_link_pattern, protect_link, text)

    # Now escape remaining square brackets
    text = text.replace("[", r"\[").replace("]", r"\]")

    # Restore markdown links
    for i, link in enumerate(links):
        text = text.replace(f"__MDLINK_{i}__", link)

    return text
```

**Step 2: Apply escaping in _display_message_group**

Replace the problematic line (around line 118):

```python
# OLD:
self.console.print(f"{indent}{part}")

# NEW:
escaped_part = escape_rich_markup(part)
self.console.print(f"{indent}{escaped_part}")
```

**Step 3: Run tests to verify fix**

Run: `uv run pytest tests/test_markup_escaping.py -v`

Expected: Both tests PASS

**Step 4: Run full test suite**

Run: `make test`

Expected: All tests pass

**Step 5: Commit the fix**

```bash
jj commit -m "fix(terminal): escape Rich markup in file paths

Escape square brackets in text content to prevent Rich from interpreting
file paths and other content as markup tags. Preserves markdown links.

Fixes MarkupError when displaying file paths with brackets.
Ref: Track 1 - Bug Fix"
```

---

## Track 2: Warmup Detection & Filtering

**Goal:** Detect and remove Claude warmup messages, filter out short conversations

### Task 2.1: Write tests for warmup detection

**Files:**
- Create: `tests/test_warmup_detection.py`

**Step 1: Write warmup detection tests**

```python
"""Test warmup message detection and removal."""

from claude_notes.parser import TranscriptParser, detect_warmup_end


def test_detect_simple_warmup():
    """Test detecting warmup in simple case."""
    messages = [
        {"role": "assistant", "content": [{"type": "text", "text": "I'm Claude..."}]},
        {"role": "assistant", "content": [{"type": "text", "text": "How can I help?"}]},
        {"role": "user", "content": [{"type": "text", "text": "Fix the bug"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Let me help..."}]},
    ]

    warmup_end_idx = detect_warmup_end(messages)
    # First real user message is at index 2
    assert warmup_end_idx == 2


def test_no_warmup_in_conversation():
    """Test conversation with no warmup."""
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "Fix the bug"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Let me help..."}]},
    ]

    warmup_end_idx = detect_warmup_end(messages)
    assert warmup_end_idx == 0  # No warmup


def test_empty_messages():
    """Test handling empty message list."""
    messages = []
    warmup_end_idx = detect_warmup_end(messages)
    assert warmup_end_idx == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_warmup_detection.py -v`

Expected: FAIL with "detect_warmup_end not defined"

**Step 3: Commit failing tests**

```bash
jj commit -m "test(parser): add failing tests for warmup detection

Tests for detecting and removing Claude's initial warmup messages.
Ref: Track 2 - Warmup & Filtering"
```

### Task 2.2: Implement warmup detection

**Files:**
- Modify: `src/claude_notes/parser.py:1-10` (add function)

**Step 1: Add warmup detection function**

Add before the `TranscriptParser` class:

```python
def detect_warmup_end(messages: list[dict[str, Any]]) -> int:
    """Detect where warmup messages end and real conversation begins.

    Warmup is Claude's initial greeting before the user starts.
    Returns the index of the first real user message.

    Args:
        messages: List of message dictionaries

    Returns:
        Index where warmup ends (0 if no warmup detected)
    """
    if not messages:
        return 0

    # Find first user message that's not just a greeting/empty
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            # Check if it has actual content (not just warmup acknowledgment)
            content = msg.get("content", [])
            if content:
                # Get text from first content block
                text = ""
                if isinstance(content, list) and len(content) > 0:
                    first_block = content[0]
                    if isinstance(first_block, dict):
                        text = first_block.get("text", "")
                    elif isinstance(first_block, str):
                        text = first_block

                # Skip very short messages (likely just "ok", "sure", etc.)
                if len(text.strip()) > 10:
                    return i

    # No substantial user message found
    return 0
```

**Step 2: Add method to TranscriptParser to apply trimming**

Add method to `TranscriptParser` class:

```python
def get_messages_without_warmup(self) -> list[dict[str, Any]]:
    """Get messages with warmup trimmed.

    Returns:
        List of messages after warmup is removed
    """
    warmup_end = detect_warmup_end(self.messages)
    return self.messages[warmup_end:]
```

**Step 3: Run tests**

Run: `uv run pytest tests/test_warmup_detection.py -v`

Expected: All tests PASS

**Step 4: Commit implementation**

```bash
jj commit -m "feat(parser): add warmup detection and trimming

Detect Claude's initial warmup messages and provide method to exclude them.
Warmup ends at the first substantial user message (>10 chars).

Ref: Track 2 - Warmup & Filtering"
```

### Task 2.3: Write tests for short chat filtering

**Files:**
- Modify: `tests/test_warmup_detection.py` (add tests)

**Step 1: Add short chat filtering tests**

Append to existing test file:

```python
def test_filter_short_conversations_default():
    """Test filtering conversations shorter than default threshold."""
    from claude_notes.parser import should_include_conversation

    # Short conversation (5 lines after warmup)
    short_messages = [
        {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello"}]},
    ]

    # Long conversation (15 lines)
    long_messages = [
        {"role": "user", "content": [{"type": "text", "text": "Line " + str(i)}]}
        for i in range(15)
    ]

    # Default threshold is 10
    assert not should_include_conversation(short_messages, min_messages=10)
    assert should_include_conversation(long_messages, min_messages=10)


def test_filter_respects_custom_threshold():
    """Test custom minimum message threshold."""
    from claude_notes.parser import should_include_conversation

    messages = [
        {"role": "user", "content": [{"type": "text", "text": f"Message {i}"}]}
        for i in range(5)
    ]

    # Should be excluded with threshold 10
    assert not should_include_conversation(messages, min_messages=10)

    # Should be included with threshold 3
    assert should_include_conversation(messages, min_messages=3)


def test_filter_handles_empty():
    """Test filtering handles empty conversations."""
    from claude_notes.parser import should_include_conversation

    assert not should_include_conversation([], min_messages=1)
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_warmup_detection.py::test_filter_short_conversations_default -v`

Expected: FAIL with "should_include_conversation not defined"

**Step 3: Commit failing tests**

```bash
jj commit -m "test(parser): add failing tests for short chat filtering

Tests for filtering out conversations below message threshold.
Ref: Track 2 - Warmup & Filtering"
```

### Task 2.4: Implement short chat filtering

**Files:**
- Modify: `src/claude_notes/parser.py` (add function after detect_warmup_end)

**Step 1: Add filtering function**

```python
def should_include_conversation(
    messages: list[dict[str, Any]],
    min_messages: int = 10,
    trim_warmup: bool = True
) -> bool:
    """Determine if a conversation should be included based on length.

    Args:
        messages: List of message dictionaries
        min_messages: Minimum number of messages to include conversation
        trim_warmup: Whether to count messages after warmup only

    Returns:
        True if conversation should be included, False otherwise
    """
    if not messages:
        return False

    # Optionally trim warmup before counting
    if trim_warmup:
        warmup_end = detect_warmup_end(messages)
        messages_to_count = messages[warmup_end:]
    else:
        messages_to_count = messages

    # Count non-meta messages
    actual_messages = [m for m in messages_to_count if not m.get("isMeta", False)]

    return len(actual_messages) >= min_messages
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_warmup_detection.py -v`

Expected: All tests PASS

**Step 3: Run full test suite**

Run: `make test`

Expected: All tests pass

**Step 4: Commit implementation**

```bash
jj commit -m "feat(parser): add short conversation filtering

Filter out conversations below configurable message threshold.
Optionally counts messages after warmup removal.

Ref: Track 2 - Warmup & Filtering"
```

### Task 2.5: Integrate filtering into CLI

**Files:**
- Modify: `src/claude_notes/cli.py:210-243` (add CLI options)
- Modify: `src/claude_notes/cli.py:288-313` (apply filtering)

**Step 1: Add CLI options for filtering**

Add after line 241 (before the `emoji_fallbacks` option):

```python
@click.option(
    "--trim-warmup/--no-trim-warmup",
    default=True,
    help="Remove Claude's initial warmup messages from conversations",
)
@click.option(
    "--min-messages",
    type=int,
    default=0,
    help="Minimum number of messages to include a conversation (0 = include all)",
)
```

**Step 2: Add parameters to show function**

Update function signature (around line 243):

```python
def show(
    path: Path,
    raw: bool,
    no_pager: bool,
    format: str,
    output: str | None,
    session_order: str,
    message_order: str,
    style: str | None,
    typing_speed: float,
    pause_duration: float,
    cols: int,
    rows: int,
    max_duration: float | None,
    emoji_fallbacks: bool,
    trim_warmup: bool,
    min_messages: int,
):
```

**Step 3: Apply filtering in conversation loading**

Replace lines 288-313 with:

```python
    # Load all conversations
    from claude_notes.parser import should_include_conversation

    conversations = []
    for jsonl_file in jsonl_files:
        try:
            parser = TranscriptParser(jsonl_file)

            # Get messages (with or without warmup)
            if trim_warmup:
                messages = parser.get_messages_without_warmup()
            else:
                messages = parser.get_messages()

            # Apply minimum message filter
            if min_messages > 0 and not should_include_conversation(
                messages, min_messages=min_messages, trim_warmup=False
            ):
                continue  # Skip this conversation

            info = parser.get_conversation_info()

            # Get the start timestamp for sorting (convert to UTC)
            start_time = parse_start_time(info.get("start_time", ""))

            # Get file modification time as fallback (in UTC)
            file_mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime, tz=timezone.utc)

            conversations.append(
                {
                    "file": jsonl_file,
                    "info": info,
                    "messages": messages,
                    "start_time": start_time,
                    "file_mtime": file_mtime,
                }
            )
        except Exception as e:
            console.print(f"[red]Error parsing {jsonl_file.name}: {e}[/red]")
```

**Step 4: Test manually**

Run: `uv run claude-notes show . --min-messages 20 --trim-warmup`

Expected: Shows only conversations with 20+ messages after warmup

**Step 5: Commit CLI integration**

```bash
jj commit -m "feat(cli): integrate warmup trimming and message filtering

Add --trim-warmup/--no-trim-warmup and --min-messages options.
Apply filtering when loading conversations.

Ref: Track 2 - Warmup & Filtering"
```

---

## Track 3: Date Display

**Goal:** Show start date/time next to each conversation session

### Task 3.1: Write tests for date display

**Files:**
- Create: `tests/test_date_display.py`

**Step 1: Write date formatting tests**

```python
"""Test date display in conversation headers."""

from datetime import datetime, timezone
from claude_notes.formatters.terminal import TerminalFormatter
from rich.console import Console
from io import StringIO


def test_date_appears_in_conversation_output():
    """Test that conversation start date is visible in output."""
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=80)
    formatter = TerminalFormatter(console)

    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "Hello"}]
        }
    ]

    # Create conversation info with start time
    start_time = datetime(2025, 11, 6, 14, 30, 0, tzinfo=timezone.utc)
    conversation_info = {
        "file_name": "test.jsonl",
        "message_count": 1,
        "start_time": start_time.isoformat()
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
            "role": "user",
            "content": [{"type": "text", "text": "Hello"}]
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
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_date_display.py -v`

Expected: Tests run but may not find date in output (feature not implemented)

**Step 3: Commit failing tests**

```bash
jj commit -m "test(formatter): add tests for date display in conversations

Tests that conversation start dates appear in formatted output.
Ref: Track 3 - Date Display"
```

### Task 3.2: Implement date display in terminal formatter

**Files:**
- Modify: `src/claude_notes/formatters/terminal.py:46-49`

**Step 1: Update _display_header method**

Replace the empty header method (around line 46-49):

```python
def _display_header(self, info: dict[str, Any]) -> None:
    """Display conversation header with start date."""
    # Format start time if available
    start_time_str = info.get("start_time")
    if start_time_str:
        from datetime import datetime
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            # Format as readable date
            date_display = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.console.print(f"[dim]Session: {date_display}[/dim]")
            self.console.print()  # Blank line after header
        except (ValueError, AttributeError):
            # If parsing fails, show raw or skip
            pass
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_date_display.py -v`

Expected: Both tests PASS

**Step 3: Test manually with actual data**

Run: `uv run claude-notes show .`

Expected: Each conversation shows "Session: YYYY-MM-DD HH:MM:SS" at the top

**Step 4: Commit implementation**

```bash
jj commit -m "feat(formatter): display session start date in terminal output

Show formatted start date/time at the beginning of each conversation.
Falls back gracefully if date is missing or unparseable.

Ref: Track 3 - Date Display"
```

### Task 3.3: Add date display to HTML formatter

**Files:**
- Modify: `src/claude_notes/formatters/html.py` (around conversation header generation)

**Step 1: Find HTML header generation**

Run: `uv run grep -n "conversation-header\|Conversation.*started" src/claude_notes/formatters/html.py`

Expected: Shows lines where HTML headers are generated

**Step 2: Add date to HTML headers**

Add date display in the conversation header section. Look for where conversation ID is used and add date nearby:

```python
# Add this where conversation headers are generated
if conversation_info.get("start_time"):
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(conversation_info["start_time"].replace("Z", "+00:00"))
        date_str = dt.strftime("%B %d, %Y at %H:%M")
        html_parts.append(f'<div class="conversation-date">{date_str}</div>')
    except (ValueError, AttributeError):
        pass
```

**Step 3: Test HTML output**

Run: `uv run claude-notes show . --format html --output test-output.html`

Expected: HTML file contains date information for each conversation

**Step 4: Commit HTML formatter changes**

```bash
jj commit -m "feat(formatter): display session date in HTML output

Add formatted start date to HTML conversation headers.
Ref: Track 3 - Date Display"
```

---

## Track 4: Time-based Filtering

**Goal:** Add CLI flags to filter conversations by time range (--last-week, --last-month, --last-year)

### Task 4.1: Write tests for time filtering

**Files:**
- Create: `tests/test_time_filtering.py`

**Step 1: Write time filtering tests**

```python
"""Test time-based conversation filtering."""

from datetime import datetime, timedelta, timezone
from claude_notes.cli import filter_by_time_range


def test_filter_last_week():
    """Test filtering conversations from last week."""
    now = datetime.now(timezone.utc)

    # Conversations at different times
    week_ago = now - timedelta(days=5)
    month_ago = now - timedelta(days=20)
    year_ago = now - timedelta(days=400)

    conversations = [
        {"start_time": week_ago, "info": {"file_name": "recent.jsonl"}},
        {"start_time": month_ago, "info": {"file_name": "month.jsonl"}},
        {"start_time": year_ago, "info": {"file_name": "old.jsonl"}},
    ]

    filtered = filter_by_time_range(conversations, "week")
    assert len(filtered) == 1
    assert filtered[0]["info"]["file_name"] == "recent.jsonl"


def test_filter_last_month():
    """Test filtering conversations from last month."""
    now = datetime.now(timezone.utc)

    week_ago = now - timedelta(days=5)
    month_ago = now - timedelta(days=20)
    year_ago = now - timedelta(days=400)

    conversations = [
        {"start_time": week_ago, "info": {"file_name": "recent.jsonl"}},
        {"start_time": month_ago, "info": {"file_name": "month.jsonl"}},
        {"start_time": year_ago, "info": {"file_name": "old.jsonl"}},
    ]

    filtered = filter_by_time_range(conversations, "month")
    assert len(filtered) == 2  # Includes last week and last month


def test_filter_last_year():
    """Test filtering conversations from last year."""
    now = datetime.now(timezone.utc)

    week_ago = now - timedelta(days=5)
    month_ago = now - timedelta(days=20)
    year_ago = now - timedelta(days=400)

    conversations = [
        {"start_time": week_ago, "info": {"file_name": "recent.jsonl"}},
        {"start_time": month_ago, "info": {"file_name": "month.jsonl"}},
        {"start_time": year_ago, "info": {"file_name": "old.jsonl"}},
    ]

    filtered = filter_by_time_range(conversations, "year")
    assert len(filtered) == 2  # Includes recent conversations, excludes very old


def test_filter_none_returns_all():
    """Test that None time_range returns all conversations."""
    conversations = [
        {"start_time": datetime.now(timezone.utc), "info": {"file_name": "test.jsonl"}},
    ]

    filtered = filter_by_time_range(conversations, None)
    assert len(filtered) == len(conversations)


def test_filter_handles_missing_timestamps():
    """Test filtering handles conversations without timestamps."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=5)

    conversations = [
        {"start_time": week_ago, "info": {"file_name": "recent.jsonl"}},
        {"start_time": None, "info": {"file_name": "no-timestamp.jsonl"}},
    ]

    # Without timestamp, conversation is excluded from time filtering
    filtered = filter_by_time_range(conversations, "week")
    assert len(filtered) == 1
    assert filtered[0]["info"]["file_name"] == "recent.jsonl"
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_time_filtering.py -v`

Expected: FAIL with "filter_by_time_range not defined"

**Step 3: Commit failing tests**

```bash
jj commit -m "test(cli): add failing tests for time-based filtering

Tests for filtering conversations by last week/month/year.
Ref: Track 4 - Time Filtering"
```

### Task 4.2: Implement time filtering function

**Files:**
- Modify: `src/claude_notes/cli.py` (add function after parse_start_time)

**Step 1: Add time filtering function**

Add after the `parse_start_time` function (around line 200):

```python
def filter_by_time_range(
    conversations: list[dict],
    time_range: str | None
) -> list[dict]:
    """Filter conversations by time range.

    Args:
        conversations: List of conversation dictionaries with start_time
        time_range: One of 'week', 'month', 'year', or None

    Returns:
        Filtered list of conversations
    """
    if not time_range:
        return conversations

    now = datetime.now(timezone.utc)

    # Define cutoff based on time range
    if time_range == "week":
        cutoff = now - timedelta(days=7)
    elif time_range == "month":
        cutoff = now - timedelta(days=30)
    elif time_range == "year":
        cutoff = now - timedelta(days=365)
    else:
        return conversations  # Unknown range, return all

    # Filter conversations after cutoff
    filtered = []
    for conv in conversations:
        start_time = conv.get("start_time")
        if start_time and isinstance(start_time, datetime):
            # Ensure start_time is timezone-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            if start_time >= cutoff:
                filtered.append(conv)

    return filtered
```

**Step 2: Add missing import**

At top of file, ensure timedelta is imported:

```python
from datetime import datetime, timezone, timedelta
```

**Step 3: Run tests**

Run: `uv run pytest tests/test_time_filtering.py -v`

Expected: All tests PASS

**Step 4: Commit implementation**

```bash
jj commit -m "feat(cli): add time-based filtering function

Implement filter_by_time_range to filter conversations by week/month/year.
Ref: Track 4 - Time Filtering"
```

### Task 4.3: Add CLI options for time filtering

**Files:**
- Modify: `src/claude_notes/cli.py:210-243` (add CLI options)
- Modify: `src/claude_notes/cli.py:315-320` (apply filtering)

**Step 1: Add CLI option**

Add after the `--min-messages` option (before function definition):

```python
@click.option(
    "--time-range",
    type=click.Choice(["week", "month", "year"]),
    help="Show only conversations from the specified time range",
)
```

**Step 2: Add parameter to show function**

Update function signature to include `time_range: str | None`:

```python
def show(
    path: Path,
    raw: bool,
    no_pager: bool,
    format: str,
    output: str | None,
    session_order: str,
    message_order: str,
    style: str | None,
    typing_speed: float,
    pause_duration: float,
    cols: int,
    rows: int,
    max_duration: float | None,
    emoji_fallbacks: bool,
    trim_warmup: bool,
    min_messages: int,
    time_range: str | None,
):
```

**Step 3: Apply time filtering**

After sorting conversations (around line 315-320), add filtering:

```python
    # Sort conversations by start time, with file modification time as fallback
    # Use timezone-aware datetime.min to avoid comparison issues
    conversations.sort(
        key=lambda x: x["start_time"] or x["file_mtime"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=(session_order == "desc"),
    )

    # Apply time-based filtering
    if time_range:
        conversations = filter_by_time_range(conversations, time_range)
        if not conversations:
            console.print(f"[yellow]No conversations found in the last {time_range}[/yellow]")
            return
```

**Step 4: Test manually**

Run: `uv run claude-notes show . --time-range week`

Expected: Shows only conversations from the last 7 days

Run: `uv run claude-notes show . --time-range month`

Expected: Shows conversations from the last 30 days

**Step 5: Commit CLI integration**

```bash
jj commit -m "feat(cli): add --time-range flag for filtering by date

Add --time-range option with week/month/year choices.
Filter conversations after loading and sorting.

Ref: Track 4 - Time Filtering"
```

---

## Integration & Testing

### Task 5.1: Integration testing

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
"""Integration tests for combined features."""

from pathlib import Path
from claude_notes.cli import show
from click.testing import CliRunner


def test_all_features_together(tmp_path):
    """Test that all features work together without conflicts."""
    runner = CliRunner()

    # Assuming test data exists or create minimal test data
    # Test combining multiple flags
    result = runner.invoke(
        show,
        [
            str(tmp_path),
            "--trim-warmup",
            "--min-messages", "5",
            "--time-range", "month",
            "--no-pager",
        ],
    )

    # Should not crash (exit code 0 or 1 for no data is ok)
    assert result.exit_code in [0, 1]
```

**Step 2: Run integration tests**

Run: `uv run pytest tests/test_integration.py -v`

**Step 3: Run full test suite**

Run: `make test`

Expected: All tests pass

**Step 4: Commit integration tests**

```bash
jj commit -m "test(integration): add tests for combined features

Verify all features work together without conflicts.
Ref: Integration & Testing"
```

### Task 5.2: Update documentation

**Files:**
- Modify: `CLAUDE.md` (update CLI usage section)

**Step 1: Update CLI usage section**

Add new options to the CLI Usage section:

```markdown
### CLI Usage

```bash
# Show transcripts with warmup removed
uv run claude-notes show . --trim-warmup

# Show only conversations with 15+ messages
uv run claude-notes show . --min-messages 15

# Show conversations from last week
uv run claude-notes show . --time-range week

# Show recent long conversations without warmup
uv run claude-notes show . --trim-warmup --min-messages 20 --time-range month

# Keep warmup messages (default is to remove)
uv run claude-notes show . --no-trim-warmup
```
```

**Step 2: Test documentation examples**

Run each command from the documentation to verify they work.

**Step 3: Commit documentation**

```bash
jj commit -m "docs(cli): document new filtering and display options

Add examples for --trim-warmup, --min-messages, and --time-range.
Ref: Integration & Testing"
```

### Task 5.3: Final verification

**Step 1: Run full test suite**

Run: `make test`

Expected: All tests pass

**Step 2: Build package**

Run: `make build`

Expected: Build succeeds

**Step 3: Test with real data**

Run: `uv run claude-notes show /Users/quark/workspace/claude-notes`

Expected:
- No MarkupError crashes
- Dates displayed for each session
- Can filter by time range
- Can filter by message count
- Can toggle warmup trimming

**Step 4: Final commit**

```bash
jj commit -m "feat: complete bug fix and filtering features

Summary of changes:
- Fix Rich markup escaping bug for file paths with brackets
- Add warmup detection and trimming (--trim-warmup flag)
- Add short conversation filtering (--min-messages flag)
- Display session start dates in output
- Add time-based filtering (--time-range week/month/year)

All tracks integrated and tested.
Ref: Bug Fix and Features - Complete"
```

---

## Execution Guide

**Parallel Execution:** These tracks can be worked on simultaneously:
- Track 1 (Bug Fix) - **HIGHEST PRIORITY** - Blocks usage
- Track 2 (Warmup & Filtering) - Independent, parser layer
- Track 3 (Date Display) - Independent, formatter layer
- Track 4 (Time Filtering) - Independent, CLI layer

**Sequential Dependencies:**
- Track 2 tasks must be done in order (2.1 → 2.2 → 2.3 → 2.4 → 2.5)
- Track 3 tasks can be done in parallel (3.2 and 3.3 independent)
- Track 4 tasks must be done in order (4.1 → 4.2 → 4.3)
- Integration (Task 5) requires all tracks complete

**Suggested Order if Working Alone:**
1. Track 1 (Bug Fix) - Get this done first
2. Track 2 (Warmup & Filtering) - Core functionality
3. Track 3 (Date Display) - User-facing improvement
4. Track 4 (Time Filtering) - Additional feature
5. Integration & Testing - Verify everything works together
