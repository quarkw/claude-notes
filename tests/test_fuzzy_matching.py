"""Tests for fuzzy project matching logic."""

import pytest

from claude_notes.cli import fuzzy_match_encoded_names, is_safe_char


class TestIsSafeChar:
    """Test the is_safe_char function."""

    def test_safe_characters(self):
        """Test that alphanumeric characters and dash are safe."""
        assert is_safe_char("a")
        assert is_safe_char("Z")
        assert is_safe_char("0")
        assert is_safe_char("9")
        assert is_safe_char("-")

    def test_unsafe_characters(self):
        """Test that all other characters (space, special, non-ASCII) are unsafe."""
        assert not is_safe_char("_")
        assert not is_safe_char(" ")
        assert not is_safe_char("!")
        assert not is_safe_char(".")
        assert not is_safe_char("é")
        assert not is_safe_char("🎉")


class TestFuzzyMatchEncodedNames:
    """Test the fuzzy_match_encoded_names function."""

    def test_exact_match(self):
        """Test exact match with safe characters only."""
        matches, unknown_count = fuzzy_match_encoded_names(
            "-Users-quark-workspace-claude-notes", "-Users-quark-workspace-claude-notes"
        )
        assert matches
        assert unknown_count == 0

    def test_comprehensive_fuzzy_matching(self):
        """Test comprehensive real-world fuzzy matching with all character types.

        Programmatically generates a test string that alternates alphanumeric (safe)
        characters with unsafe characters. Since there are more unsafe chars than
        alphanum chars (62), the alphanum set loops to ensure complete coverage of:
        - All digits (0-9)
        - Lowercase letters (a-z)
        - Uppercase letters (A-Z)
        - Space, dot, underscore, common special chars
        - Extended unicode (accented chars like é, ñ, ü)
        - Multi-byte unicode (CJK characters, emoji)
        """
        # Define character sets
        # alphanum: 62 chars (10 digits + 26 lowercase + 26 uppercase)
        alphanum = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        # unsafe_chars: 100+ chars to force alphanum looping multiple times
        unsafe_chars = (
            " ._"  # Basic unsafe: space, dot, underscore
            "!@#$%^&*()+=[]{}|;:',<>?/\\`~\""  # Special chars
            "éñüöäåøæçßàèìòùâêîôûëïÿ"  # Accented/extended Latin
            "αβγδεζηθικλμνξοπρστυφχψω"  # Greek
            "日本語中国한국"  # CJK characters
            "🎉🚀🔥💯✨🌟⭐💫🎨🎭🎪🎬🎮🎯🎲🎰🎳"  # Emoji
            "™©®€£¥§¶†‡•"  # Other unicode symbols
        )

        # Generate alternating pattern: alphanum[i % len(alphanum)], unsafe[i], ...
        our_encoding = "-tmp-"
        claude_encoding = "-tmp-"

        for i, unsafe_char in enumerate(unsafe_chars):
            # Add alphanumeric (loop if needed)
            safe_char = alphanum[i % len(alphanum)]
            our_encoding += safe_char + unsafe_char
            claude_encoding += safe_char + "-"  # Unsafe chars become dashes in Claude's encoding

        # Test the match
        matches, unknown_count = fuzzy_match_encoded_names(our_encoding, claude_encoding)
        assert matches
        assert unknown_count == len(unsafe_chars)  # Each unsafe char counts as one unknown

    def test_different_lengths_no_match(self):
        """Test that different length encodings don't match."""
        matches, _unknown = fuzzy_match_encoded_names(
            "-tmp-test-project", "-tmp-test-project-extra"
        )
        assert not matches

    def test_different_safe_chars_no_match(self):
        """Test that different safe characters don't match."""
        matches, _unknown = fuzzy_match_encoded_names(
            "-tmp-test-project", "-tmp-test-different"
        )
        assert not matches
