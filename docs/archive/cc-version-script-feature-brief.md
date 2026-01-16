# Feature Brief: CC Version Script

**Date**: 2026-01-16
**Prepared by**: User Agent (Workscope-20260116-095953)
**For**: Feature-Writer Agent

---

## Executive Summary

A Python CLI tool (`src/cc_version.py`) that manages Claude Code version installation and auto-update settings, streamlining the process of switching between Claude Code versions for phantom reads investigation trials.

---

## Problem Statement

The Experiment-Methodology-01.md document describes manual steps for setting up the right Claude Code version for testing phantom reads. This involves:

1. Editing `~/.claude/settings.json` to disable auto-updates
2. Running multiple npm commands to uninstall, clean cache, and reinstall specific versions

These manual steps are tedious and error-prone. A convenience script would reduce friction when running multiple trials across different Claude Code versions.

---

## Solution Overview

Create `src/cc_version.py` - an executable Python script that wraps npm and Claude Code commands to provide a simplified CLI for:

- Toggling Claude Code's auto-update behavior via `~/.claude/settings.json`
- Listing available Claude Code versions
- Checking current installation status
- Installing specific versions with automatic uninstall/cache-clean/reinstall flow
- Resetting to default Anthropic-intended state

The script follows a conservative error-handling philosophy: any edge case or unexpected condition results in an error message and exit, never attempting recovery or workarounds. It's a convenience wrapper, not a robust installer.

---

## Relationship to Existing Systems

### Related Scripts

- **`scripts/install_cc.sh`**: Simple bash script that installs a specific version. The new Python script will provide a superset of this functionality with better error handling and additional features (auto-update management, status display, version listing).

- **`scripts/archive_claude_sessions.py`**: Demonstrates Python patterns for accessing `~/.claude/` directory. The new script can follow similar patterns (Path.home(), argparse, type hints).

### Related Documentation

- **`docs/core/Experiment-Methodology-01.md`**: Documents the manual process this script automates. Will need minor updates to reference the new script as the preferred method.

---

## Deliverables

### 1. New File: `src/cc_version.py`

Primary deliverable - executable Python script with shebang. Key characteristics:

- Uses `argparse` for CLI with mutually exclusive command flags
- Manages `~/.claude/settings.json` for auto-update toggle
- Wraps npm commands for version management
- Conservative error handling (exit on any unexpected condition)
- Clear, helpful error messages to stderr
- Exit code 0 for success, 1 for any error

### 2. Updates: Documentation

**Files to update** (1):
- `docs/core/Experiment-Methodology-01.md` - Add note referencing the script as an alternative to manual steps

---

## Design Constraints

### CLI Commands (Finalized)

| Command                 | Description                                                                                         |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| `--disable-auto-update` | Set `env.DISABLE_AUTOUPDATER` to "1" in `~/.claude/settings.json`                                   |
| `--enable-auto-update`  | Remove `env.DISABLE_AUTOUPDATER` from `~/.claude/settings.json`                                     |
| `--list`                | List available Claude Code versions (pass-through of `npm view @anthropic-ai/claude-code versions`) |
| `--status`              | Show auto-updater state, currently installed version, and latest available version                  |
| `--install <version>`   | Install specific Claude Code version (validates against available versions first)                   |
| `--reset`               | Restore defaults: enable auto-update + install latest version                                       |
| `--help`                | Show usage information                                                                              |

### Settings File Details

- **Path**: `~/.claude/settings.json`
- **Setting name**: `env.DISABLE_AUTOUPDATER` (note: includes the "R" at the end)
- **Value when disabled**: `"1"` (string)
- **Enabling auto-update**: Remove the key entirely (Claude Code default is auto-update enabled)

### Backup Strategy

- Backup naming: `settings.json.TIMESTAMP.cc_version_backup` (e.g., `settings.json.20260116_103045.cc_version_backup`)
- Timestamp format: `YYYYMMDD_HHMMSS`
- Backups accumulate with unique timestamps
- Easy batch deletion: `rm ~/.claude/*.cc_version_backup`
- No `--restore-backup` command; backups are emergency-only for manual recovery
- Backup created BEFORE any modification to settings.json

### Prerequisites (Checked on Every Run)

1. `npm` must be installed and accessible (`npm --version`)
2. `claude` must be installed and accessible (`claude --version`)

If either check fails, script exits with helpful error message indicating the user needs to install the missing tool first.

### Error Handling Philosophy

**Conservative approach**: Exit with error on ANY unexpected condition:

- `~/.claude/settings.json` does not exist: Error and exit
- `~/.claude/settings.json` is empty: Error and exit
- `~/.claude/settings.json` contains invalid JSON: Error and exit
- `env` key exists but isn't a dict: Error and exit
- Permission denied: Error and exit
- npm command fails: Error and exit
- Requested version not in available versions list: Error and exit
- Multiple commands specified: Error and exit

The script does not attempt recovery, rollback, or workarounds. Users can investigate issues and use standard tools (npm, manual editing) if the script fails.

### Mutual Exclusivity

Only one command per invocation. If user provides multiple commands (e.g., `--disable-auto-update --install 2.0.58`), exit with error and helpful message.

### Output Conventions

- Normal output to stdout
- Errors to stderr
- Exit code 0 for success, 1 for error
- No colored output (avoid NO_COLOR complexity)
- Clear, helpful messages

### Platform Support

- Unix-like systems only: macOS, Linux, Windows (using WSL)
- Uses `~/.claude/` path (does not support Windows native `%USERPROFILE%\.claude\`)
- sudo/permission issues bubble up naturally through subprocess; script does not handle them specially

---

## Out of Scope

- **Installing Claude Code from scratch**: If Claude Code isn't already installed, user must install it first
- **Installing npm/Node.js**: If npm isn't available, user must install it first
- **Windows native support**: Only `~/.claude/` path is supported
- **Restore from backup command**: Backups are for emergency manual recovery only
- **Dry-run mode**: Script is simple enough that `--status` provides sufficient preview
- **Colored output**: Keep it simple
- **Rollback on failure**: If install fails, user must recover manually
- **Network error handling**: npm errors bubble up as-is

---

## Success Criteria

1. Running `./src/cc_version.py --status` shows current auto-update state, installed version, and latest available version
2. Running `./src/cc_version.py --disable-auto-update` creates backup and sets the setting
3. Running `./src/cc_version.py --install 2.0.58` successfully installs that version after validation
4. Running `./src/cc_version.py --reset` returns system to Anthropic defaults
5. All error conditions produce helpful stderr messages and exit code 1
6. Script has executable shebang and runs directly without `python` prefix

---

## Implementation Notes

### File Count Summary

- 1 new Python script: `src/cc_version.py`
- 1 documentation update: `docs/core/Experiment-Methodology-01.md`

### npm Commands Used

```bash
# Check npm availability
npm --version

# List available versions (for --list and validation)
npm view @anthropic-ai/claude-code versions
npm view @anthropic-ai/claude-code versions --json  # for parsing

# Uninstall current
npm uninstall -g @anthropic-ai/claude-code

# Clean cache
npm cache clean --force

# Install specific version
npm install -g @anthropic-ai/claude-code@<version>
```

### Claude Commands Used

```bash
# Check availability and get current version
claude --version
# Output format: "2.1.3 (Claude Code)"
```

### Exemplar Script for Patterns

`scripts/archive_claude_sessions.py` demonstrates:
- `Path.home() / ".claude"` for Claude directory
- `argparse` for CLI argument parsing
- Google-style docstrings
- Type hints throughout
- Modular function structure

---

## Questions for Feature-Writer

None - this brief captures all design decisions from the conversation with the User.
