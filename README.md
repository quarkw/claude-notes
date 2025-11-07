# Claude Notes

Transform Claude Code transcript JSONL files into readable terminal and HTML formats.

## Overview

Claude Notes is a command-line tool that converts Claude Code conversation transcripts (stored as JSONL files) into human-readable formats. It supports both terminal output with rich formatting and HTML export for web viewing.

```bash
uvx claude-notes show
```

https://github.com/user-attachments/assets/ca710fb3-558a-4ce5-9bf5-e42c80caf2bf

```bash
uvx claude-notes show --format html --output conversations.html
```

https://github.com/user-attachments/assets/e4cb9404-bdee-4a12-8e06-e1e2216b9165


## Features

- Terminal display with syntax highlighting and rich formatting
- HTML export with navigation, timestamps, and professional styling
- Interactive pager for browsing long conversations
- Project discovery - automatically finds Claude projects
- **Smart project matching** - works with paths containing underscores, spaces, non-ASCII characters, and special characters
- **Powerful filtering** - by message count, time period, with/without warmup messages
- **Short flags** - convenient aliases for commonly used options
- Humanized timestamps - shows "2 hours ago" instead of raw timestamps
- Tool result formatting - properly displays Bash, Read, Edit, MultiEdit, and Grep tool usage
- Navigation links - jump to specific messages in HTML output

## Acknowledge

This tool was heavily inspired by https://github.com/daaain/claude-code-log

## Usage

#### HTML Output

```bash
# Export to HTML file
uvx claude-notes show --format html --output conversations.html

# Print HTML to stdout
uvx claude-notes show --format html
```

#### Terminal Output

```bash
# View conversations for current directory
uvx claude-notes show

# View conversations for specific project path
uvx claude-notes show /path/to/project

# Disable pager (show all at once) - short flag available
uvx claude-notes show --no-pager
uvx claude-notes show -n

# Show raw JSON data - short flag available
uvx claude-notes show --raw
uvx claude-notes show -r
```

## Filtering Conversations

Claude Notes supports powerful filtering to help you find relevant conversations:

### By Conversation Length

Filter by minimum number of messages using `--min-messages` (or `-M`):

```bash
# Show only conversations with 15+ messages
uvx claude-notes show --min-messages 15
uvx claude-notes show -M 15

# Combine with other filters
uvx claude-notes show -M 20 -p week
```

**What counts as a "message"?**

A message is any non-meta communication between you and Claude. This includes:
- Your requests and questions (user messages)
- Claude's responses (assistant messages)

This does NOT include:
- Meta messages (internal system messages)
- Warmup messages (Claude's initial greeting - removed by default)

By default, warmup messages are excluded from the count. Use `--no-trim-warmup` to include them.

### By Time Period

Filter by recency using `--past` (or `-p`):

```bash
# Show conversations from the past hour
uvx claude-notes show --past hour
uvx claude-notes show -p hour

# Show conversations from the past day
uvx claude-notes show -p day

# Show conversations from the past week
uvx claude-notes show -p week

# Show conversations from the past month
uvx claude-notes show -p month

# Show conversations from the past year
uvx claude-notes show -p year
```

### Warmup Messages

By default, Claude Notes removes Claude's initial warmup messages (the greeting before you start working). To keep them:

```bash
# Keep warmup messages
uvx claude-notes show --no-trim-warmup
```

Note: There is no `--trim-warmup` flag because trimming is the default behavior.

### Combining Filters

All filters can be combined:

```bash
# Recent long conversations without warmup (default behavior)
uvx claude-notes show --min-messages 20 --past month
uvx claude-notes show -M 20 -p month

# Show everything from the past week including warmup
uvx claude-notes show --past week --no-trim-warmup
```

## Short Flags Reference

For faster typing, most flags have short alternatives:

| Long Flag | Short Flag | Description |
|-----------|------------|-------------|
| `--raw` | `-r` | Show raw JSON data |
| `--no-pager` | `-n` | Disable pager |
| `--format` | `-f` | Output format (terminal/html/animated) |
| `--output` | `-o` | Output file path |
| `--session-order` | `-s` | Session ordering (asc/desc) |
| `--message-order` | `-m` | Message ordering (asc/desc) |
| `--min-messages` | `-M` | Minimum message count filter |
| `--past` | `-p` | Time period filter |

Example using short flags:

```bash
uvx claude-notes show -f html -o output.html -M 15 -p week
```

## HTML Features

The HTML output includes:

- **Message Navigation**: Each message has a clickable heading with anchor links
- **Humanized Timestamps**: Shows when each message was created (e.g., "2 hours ago")
- **Tool Result Formatting**: 
  - Bash commands with syntax highlighting
  - File operations (Read, Edit, MultiEdit)
  - Search results (Grep)
- **Responsive Design**: Works well on desktop and mobile
- **Professional Styling**: Clean, readable typography

## How It Works

Claude Code stores conversation transcripts as JSONL files in `~/.claude/projects/`. Each line represents a message, tool use, or tool result. Claude Notes:

1. Discovers Claude projects by scanning the projects directory
2. Matches project paths (handles special characters automatically)
3. Parses JSONL transcript files
4. Groups related messages by role continuity
5. Formats tool usage and results appropriately
6. Outputs in your chosen format (terminal or HTML)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/claude-notes/issues)
- Feature requests: [GitHub Discussions](https://github.com/yourusername/claude-notes/discussions)
