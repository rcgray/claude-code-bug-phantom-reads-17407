# Phantom Reads Workaround: MCP Filesystem Server

This document provides a workaround for the Claude Code "Phantom Reads" bug (Issue [#17407](https://github.com/anthropics/claude-code/issues/17407)) using the official Anthropic Filesystem MCP server.

## Overview

The Phantom Reads bug causes Claude Code to believe it has successfully read file contents when it has not. This workaround bypasses the native `Read` tool entirely by:

1. **Installing the Filesystem MCP server** - An official Anthropic MCP server that reads files reliably
2. **Disabling the native Read tool** - Forcing Claude to use the MCP alternative
3. **Configuring Claude Code** - Teaching agents to use the replacement tools

This approach is architecturally clean: rather than detecting and recovering from phantom reads, we prevent them entirely by using a different code path for file operations.

## Prerequisites

- **Claude Code** version 2.0.10 or later (for MCP support)
- **Node.js** 18+ (for running the MCP server via npx)
- Basic familiarity with JSON configuration files

## How It Works

### The Problem

Claude Code's native `Read` tool can return `<persisted-output>` markers instead of actual file content when reading large files or during high-context situations. The agent then proceeds as if it read the file, operating on incomplete or non-existent information.

### The Solution

The Filesystem MCP server reads files through standard Node.js file system operations, completely bypassing Claude Code's context management system. Since the MCP server performs a direct file read and returns the content immediately, it cannot produce phantom read markers.

By disabling the native `Read` tool and providing the MCP alternative, we force all file reads through the reliable path.

## Installation

### Step 1: Create MCP Server Configuration

Create a file named `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/ABSOLUTE/PATH/TO/YOUR/PROJECT"
      ]
    }
  }
}
```

**Important:** Replace `/ABSOLUTE/PATH/TO/YOUR/PROJECT` with the actual absolute path to your project directory. The MCP server requires absolute paths for security reasons.

**Example paths:**
- macOS/Linux: `/Users/username/Projects/my-project`
- Windows: `C:\\Users\\username\\Projects\\my-project`

### Step 2: Disable Native Read Tool

Create or update `.claude/settings.json` in your project:

```json
{
  "permissions": {
    "deny": [
      "Read"
    ]
  }
}
```

This prevents Claude from using the native `Read` tool, forcing it to use the MCP filesystem tools instead.

### Step 3: Add Agent Instructions to CLAUDE.md

Add the following section to your project's `CLAUDE.md` file:

```markdown
## File Reading Instructions

This project uses the Filesystem MCP server for reliable file reading. The native `Read` tool is disabled.

**To read files, use these MCP tools instead:**
- `mcp__filesystem__read_text_file` - Read a single file
- `mcp__filesystem__read_multiple_files` - Read multiple files at once
- `mcp__filesystem__list_directory` - List directory contents
- `mcp__filesystem__search_files` - Search for files by pattern

**Example usage:**
Instead of: `Read` tool with `file_path` parameter
Use: `mcp__filesystem__read_text_file` with `path` parameter

This workaround prevents the Phantom Reads bug (Issue #17407).
```

### Step 4: Restart Claude Code

After making these configuration changes:

1. Fully quit Claude Code (not just close the window)
2. Relaunch Claude Code
3. Navigate to your project directory

### Step 5: Verify Configuration

Inside Claude Code, run the `/mcp` command to verify the filesystem server is connected:

```
/mcp
```

You should see `filesystem` listed with status `connected`.

To verify the Read tool is denied, you can ask Claude to read a file using the native tool - it should refuse and explain it's not allowed.

## Tool Reference

The Filesystem MCP server provides these tools:

### Read Operations

| Tool | Purpose |
|------|---------|
| `read_text_file` | Read a single file's contents |
| `read_multiple_files` | Read multiple files in one operation |
| `read_media_file` | Read binary files (images, etc.) as base64 |
| `list_directory` | List files and subdirectories |
| `directory_tree` | Get recursive directory structure |
| `get_file_info` | Get file metadata (size, timestamps) |
| `search_files` | Search for files by pattern |

### Write Operations

| Tool | Purpose |
|------|---------|
| `write_file` | Create or overwrite a file |
| `edit_file` | Edit file with pattern matching |
| `create_directory` | Create a new directory |
| `move_file` | Move or rename files |

## Configuration Options

### Project-Level vs User-Level

**Project-level configuration** (recommended for sharing):
- `.mcp.json` at project root
- `.claude/settings.json` for permissions
- Can be checked into version control
- Anyone cloning the repo gets the workaround

**User-level configuration** (for personal use):
- `~/.claude.json` for MCP servers
- `~/.claude/settings.json` for permissions
- Applies to all your projects

### Multiple Allowed Directories

You can allow access to multiple directories:

```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/project",
        "/path/to/other/directory"
      ]
    }
  }
}
```

### Denying Additional Tools

If you want to force MCP tools for other operations, you can deny more native tools:

```json
{
  "permissions": {
    "deny": [
      "Read",
      "Write",
      "Edit",
      "Glob",
      "LS"
    ]
  }
}
```

Note: This is more aggressive and may affect Claude's normal operation. Start with just `Read` and expand if needed.

## Troubleshooting

### MCP Server Not Appearing

1. **Check JSON syntax**: Validate your `.mcp.json` file
2. **Verify paths are absolute**: Relative paths will fail silently
3. **Restart Claude Code completely**: Close all instances, then relaunch
4. **Check logs**: Look in `~/.claude/logs/` for MCP-related errors

### Server Shows "Failed" Status

1. **Verify Node.js is installed**: Run `node --version` in terminal
2. **Test manually**: Run `npx -y @modelcontextprotocol/server-filesystem /your/path` to see errors
3. **Check permissions**: Ensure you have read access to the configured directories

### Claude Still Uses Native Read

1. **Verify settings.json location**: Must be in `.claude/settings.json` (project) or `~/.claude/settings.json` (user)
2. **Check JSON syntax**: Invalid JSON is silently ignored
3. **Restart Claude Code**: Settings are loaded at startup

### MCP Tools Not Found

If Claude says it can't find `mcp__filesystem__read_text_file`:

1. Run `/mcp` to verify connection
2. The server may still be starting - wait a moment and try again
3. Check that the server name in `.mcp.json` matches (should be `filesystem`)

## Limitations

### Known Limitations

1. **Absolute paths required**: The MCP server configuration requires absolute paths, which aren't portable across machines. Each user may need to adjust the path.

2. **Additional tool in context**: The MCP tools add to Claude's available tool list, slightly increasing context usage.

3. **Different tool names**: Agents need to learn the MCP tool names (`read_text_file` vs `Read`). Existing prompts and commands may need updates.

4. **Node.js dependency**: Requires Node.js to be installed for the MCP server.

### What This Doesn't Fix

- Phantom reads from other tools (Grep, Glob, etc.) if they exist
- Issues unrelated to the Read tool
- Context window limitations (files are still large)

## Verification

To verify the workaround is functioning:

1. **Check MCP status**: `/mcp` should show `filesystem: connected`

2. **Test denied tool**: Ask Claude to "use the Read tool to read a file" - it should refuse

3. **Test MCP tool**: Ask Claude to read a file - it should use `mcp__filesystem__read_text_file`

4. **Examine response**: The file content should be returned directly, not a `<persisted-output>` marker

## References

- [Claude Code Issue #17407](https://github.com/anthropics/claude-code/issues/17407) - Phantom Reads bug report
- [Claude Code Issue #1380](https://github.com/anthropics/claude-code/issues/1380) - Disabling native tools
- [Filesystem MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - Official repository
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp) - Official MCP docs
- [MCP Protocol](https://modelcontextprotocol.io/) - Model Context Protocol specification

## Contributing

If you discover issues with this workaround or have improvements to suggest, please:

1. Test thoroughly in your environment
2. Document the specific Claude Code version and configuration
3. Open an issue or pull request with detailed reproduction steps

---

*This workaround was developed as part of the Phantom Reads Investigation project. It is provided as-is until an official fix is available from Anthropic.*
