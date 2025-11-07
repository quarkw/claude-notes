"""Test time-based conversation filtering."""
# ruff: noqa: UP017  # Use timezone.utc for Python <3.11 compatibility

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
