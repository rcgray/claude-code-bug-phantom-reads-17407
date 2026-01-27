# CC Version Script Specification

**Version:** 1.0.0
**Date:** 2026-01-16
**Status:** Draft

## Overview

The CC Version Script is a Python CLI tool (`src/cc_version.py`) that manages Claude Code version installation and auto-update settings. It provides a unified interface for switching between Claude Code versions during phantom reads investigation trials, replacing the manual steps documented in the experiment methodology with a single streamlined command interface.

This specification defines the complete behavior of the version management script, including CLI command structure, settings file manipulation, npm command orchestration, and the conservative error-handling philosophy that governs all operations. The script operates as a convenience wrapper around existing npm and Claude Code commands, prioritizing clarity and safety over robustness.

For the broader investigation context this tool supports, see `docs/core/PRD.md`. For the experimental methodology that benefits from this script, see `docs/experiments/methodologies/Experiment-Methodology-01.md`.

## Purpose

The CC Version Script serves four critical functions:

1. **Auto-Update Management**: Provides simple commands to toggle Claude Code's auto-update behavior via `~/.claude/settings.json`, eliminating the need for manual JSON editing when switching between update-disabled trial mode and normal operation.

2. **Version Installation Orchestration**: Wraps the multi-step npm process (uninstall, cache clean, install) into a single validated command, reducing the risk of forgotten steps or typos during version switches.

3. **Installation Status Reporting**: Displays current auto-update state, installed version, and latest available version in a single view, enabling investigators to quickly verify their environment before running trials.

4. **Environment Reset**: Provides a single command to restore the system to Anthropic-intended defaults (auto-update enabled, latest version installed), simplifying cleanup after investigation sessions.

This specification establishes the authoritative definition of the CC Version Script's CLI interface, settings file manipulation behavior, error handling philosophy, and integration with npm commands.

## CLI Interface

The script provides a command-line interface with mutually exclusive operation flags. Only one operation may be specified per invocation.

### Command Reference

| Command                 | Description                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------- |
| `--disable-auto-update` | Set `env.DISABLE_AUTOUPDATER` to `"1"` in `~/.claude/settings.json`                |
| `--enable-auto-update`  | Remove `env.DISABLE_AUTOUPDATER` from `~/.claude/settings.json`                    |
| `--list`                | List available Claude Code versions from npm registry (human-readable output)      |
| `--status`              | Show auto-updater state, currently installed version, and latest available version |
| `--install <version>`   | Install specific Claude Code version (validates against available versions first)  |
| `--reset`               | Restore defaults: enable auto-update and install latest version                    |
| `--help`                | Show usage information                                                             |

### Mutual Exclusivity

The script enforces mutual exclusivity among operation flags. If a user provides multiple commands (e.g., `--disable-auto-update --install 2.0.58`), the script MUST exit with an error and display a helpful message indicating that only one operation can be performed per invocation.

### Exit Codes

| Code | Meaning             |
| ---- | ------------------- |
| `0`  | Success             |
| `1`  | Any error condition |

### Output Conventions

- Normal output directed to stdout
- Error messages directed to stderr
- No colored output (avoids `NO_COLOR` environment variable complexity)
- Messages MUST be clear and actionable

## Settings File Management

The script manipulates Claude Code's settings file to control auto-update behavior.

### Settings File Location

**Path:** `~/.claude/settings.json`

The script uses `Path.home() / ".claude" / "settings.json"` to locate the settings file, following the pattern established by other scripts in this project.

### Auto-Update Setting

| Setting             | JSON Path                 | Type   | Effect                                                    |
| ------------------- | ------------------------- | ------ | --------------------------------------------------------- |
| Disable auto-update | `env.DISABLE_AUTOUPDATER` | String | Value `"1"` disables auto-updates                         |
| Enable auto-update  | (key removed)             | N/A    | Absence of key enables auto-updates (Claude Code default) |

**Important:** The setting name includes the "R" at the end: `DISABLE_AUTOUPDATER`, not `DISABLE_AUTOUPDATE`.

### Settings Modification Algorithm

When modifying `settings.json`:

```
1. Read existing file content
2. Parse JSON
3. Create backup of original content
4. Modify the appropriate key(s)
5. Write updated JSON with consistent formatting
```

**Idempotent Behavior:** Both enable and disable operations are intentionally idempotent. Running `--disable-auto-update` when already disabled, or `--enable-auto-update` when already enabled, exits successfully with a message indicating the current state. This allows users to run these commands in scripts without checking state first.

**Disable Auto-Update Operation:**
```python
# Check if already disabled - exit early with success if so
if settings.get('env', {}).get('DISABLE_AUTOUPDATER') == "1":
    print("Auto-update is already disabled.")
    sys.exit(0)

# Ensure 'env' key exists as a dict
if 'env' not in settings:
    settings['env'] = {}
settings['env']['DISABLE_AUTOUPDATER'] = "1"
```

**Enable Auto-Update Operation:**
```python
# Check if already enabled (key missing or not "1") - exit early with success if so
if 'env' not in settings or 'DISABLE_AUTOUPDATER' not in settings['env']:
    print("Auto-update is already enabled.")
    sys.exit(0)

# Remove the key
del settings['env']['DISABLE_AUTOUPDATER']
# Clean up empty 'env' dict if no other keys remain
if not settings['env']:
    del settings['env']
```

### Backup Strategy

Before any modification to `settings.json`, the script MUST create a backup:

| Aspect           | Specification                                                                                                                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backup filename  | `settings.json.TIMESTAMP.cc_version_backup`                                                                                                                                                         |
| Backup location  | Same directory as `settings.json` (`~/.claude/`)                                                                                                                                                    |
| Timestamp format | `YYYYMMDD_HHMMSS` (e.g., `settings.json.20260116_103045.cc_version_backup`). Note: Uses underscore intentionally for filesystem compatibility, distinct from Workscope ID format which uses hyphen. |
| Accumulation     | Backups accumulate with unique timestamps                                                                                                                                                           |
| Batch deletion   | Users can delete all backups via `rm ~/.claude/*.cc_version_backup`                                                                                                                                 |
| Restoration      | Manual only; no `--restore-backup` command provided                                                                                                                                                 |

The backup exists for emergency manual recovery. If users need to restore from backup, they copy the most recent backup file manually.

## Version Management

The script orchestrates npm commands to manage Claude Code installations.

### npm Commands Used

**Version Listing (for `--list` command):**
```bash
npm view @anthropic-ai/claude-code versions
```
Passes through npm's default human-readable output directly to stdout.

**Version Listing (for internal validation):**
```bash
npm view @anthropic-ai/claude-code versions --json
```
Returns a JSON array of all available versions for programmatic parsing (used by `--install` validation and `--status` latest version lookup).

**Version Installation Sequence:**
```bash
npm uninstall -g @anthropic-ai/claude-code
npm cache clean --force
npm install -g @anthropic-ai/claude-code@<version>
```

This sequence MUST be executed in order. The script does not attempt to optimize by skipping steps.

**Current Version Query:**
```bash
claude --version
```
Returns output in format: `2.1.3 (Claude Code)`

The script parses this output to extract the version number.

### Version Validation

Before installing a requested version, the script MUST validate that the version exists in the npm registry:

1. Fetch available versions via `npm view ... versions --json`
2. Parse the JSON array
3. Check if requested version exists in the array
4. If not found, exit with error listing the requested version and suggesting `--list`

### Status Display

The `--status` command displays three pieces of information:

1. **Auto-updater state**: Enabled or Disabled (based on presence of `env.DISABLE_AUTOUPDATER`)
2. **Installed version**: Output of `claude --version`, parsed
3. **Latest available version**: Last element of versions array from npm

Example output format:
```
Auto-update: Disabled
Installed version: 2.0.58
Latest version: 2.1.6
```

### Reset Operation

The `--reset` command performs two operations in sequence:

1. Enable auto-update (remove `env.DISABLE_AUTOUPDATER` from settings)
2. Install latest version (equivalent to `--install` with the latest version)

This restores the system to Anthropic-intended defaults.

## Prerequisites

The script validates prerequisites before executing any operation.

### Required Tools

| Tool   | Validation Command | Purpose                             |
| ------ | ------------------ | ----------------------------------- |
| npm    | `npm --version`    | Package management for installation |
| claude | `claude --version` | Confirms Claude Code is installed   |

### Prerequisite Check Behavior

On every script invocation (regardless of the operation requested, including `--reset`, `--status`, `--list`, and all other commands), the script MUST:

1. Check that `npm --version` succeeds
2. Check that `claude --version` succeeds
3. If either check fails, exit with a helpful error message indicating which tool is missing and that the user must install it first

**Important:** This check runs BEFORE any operation logic. Even commands that might seem like they could work without Claude Code installed (like `--list`) require the prerequisite check to pass. This ensures consistent behavior and clear error messages across all commands.

**Example error message:**
```
Error: npm is not installed or not in PATH.
Please install Node.js and npm before using this script.
```

## Error Handling

The script follows a conservative error-handling philosophy: any unexpected condition results in an error message and exit, never attempting recovery or workarounds.

### Error Categories

#### 1. Prerequisite Errors

**Error:** Required tool (`npm` or `claude`) not available

**Example Message:**
```
Error: Claude Code is not installed.
Run: npm install -g @anthropic-ai/claude-code
```

**Recovery:** User must install the missing tool before using this script.

#### 2. Settings File Errors

**Error:** `~/.claude/settings.json` does not exist

**Example Message:**
```
Error: Settings file not found: ~/.claude/settings.json
Claude Code must be installed and have run at least once to create this file.
```

**Recovery:** User must ensure Claude Code is properly installed and has been run at least once.

**Error:** Settings file is empty

**Example Message:**
```
Error: Settings file is empty: ~/.claude/settings.json
```

**Recovery:** User must investigate and repair the settings file manually.

**Error:** Settings file contains invalid JSON

**Example Message:**
```
Error: Settings file contains invalid JSON: ~/.claude/settings.json
JSON error: Expecting property name enclosed in double quotes at line 3
```

**Recovery:** User must repair the JSON syntax manually.

**Error:** `env` key exists but is not a dictionary

**Example Message:**
```
Error: Unexpected settings structure: 'env' is not a dictionary.
```

**Recovery:** User must investigate the settings file structure.

#### 3. Permission Errors

**Error:** Cannot read or write settings file due to permissions

**Example Message:**
```
Error: Permission denied: ~/.claude/settings.json
```

**Recovery:** User must fix file permissions.

#### 4. npm Errors

**Error:** npm command fails (network error, package not found, etc.)

**Example Message:**
```
Error: npm command failed with exit code 1.
npm output: npm ERR! code E404
```

**Recovery:** User must investigate npm issues directly. Network errors and npm registry issues are passed through without interpretation.

#### 5. Version Errors

**Error:** Requested version not found in available versions

**Example Message:**
```
Error: Version '2.0.99' not found.
Use --list to see available versions.
```

**Recovery:** User should run `--list` and select a valid version.

#### 6. Argument Errors

**Error:** Multiple commands specified

**Example Message:**
```
Error: Only one command can be specified per invocation.
You provided: --disable-auto-update, --install
```

**Recovery:** User should run the script twice with one command each.

### Design Philosophy

The script does NOT attempt:

- **Recovery**: If something fails, the script exits
- **Rollback**: If install fails partway, the system is left in whatever state npm left it
- **Workarounds**: Edge cases exit with errors rather than attempting clever solutions
- **Network error interpretation**: npm errors bubble up as-is

This conservative approach is intentional. The script is a convenience wrapper for experienced users who can diagnose and fix issues using standard tools (npm, text editors) when the script fails.

## Platform Support

| Platform         | Supported | Notes                                     |
| ---------------- | --------- | ----------------------------------------- |
| macOS            | Yes       | Primary development platform              |
| Linux            | Yes       | Standard Unix paths                       |
| Windows (WSL)    | Yes       | Uses Unix paths via WSL                   |
| Windows (native) | No        | Does not support `%USERPROFILE%\.claude\` |

The script uses `~/.claude/` exclusively and does not detect or adapt to Windows native paths. Users on Windows MUST use WSL.

## Testing Scenarios

### Basic Functionality Tests

1. **Status display**: Run `--status` and verify it shows auto-update state, installed version, and latest version
2. **Disable auto-update**: Run `--disable-auto-update`, verify settings file contains `env.DISABLE_AUTOUPDATER: "1"`
3. **Enable auto-update**: Run `--enable-auto-update`, verify settings file no longer contains the key
4. **Version listing**: Run `--list` and verify it outputs available versions
5. **Version installation**: Run `--install <version>` with a valid older version, verify `claude --version` shows the new version
6. **Reset operation**: Run `--reset`, verify auto-update is enabled and latest version is installed

### Edge Case Tests

1. **Multiple commands**: Run with `--disable-auto-update --install 2.0.58`, verify error message about mutual exclusivity
2. **Invalid version**: Run `--install 99.99.99`, verify error message suggesting `--list`
3. **Missing settings file**: Temporarily rename settings file, run any command, verify appropriate error
4. **Malformed settings JSON**: Corrupt settings file, run any command, verify JSON error message
5. **Empty settings file**: Empty the settings file, run any command, verify appropriate error

### Prerequisite Tests

1. **Missing npm**: Temporarily remove npm from PATH, verify helpful error message
2. **Missing claude**: Temporarily remove claude from PATH, verify helpful error message

### Integration Tests

1. **Full workflow**: Disable auto-update, install specific version, verify version, reset, verify default state restored
2. **Backup creation**: Modify settings, verify timestamped backup file exists (e.g., `settings.json.YYYYMMDD_HHMMSS.cc_version_backup`) with correct content
3. **Idempotent enable**: Run `--enable-auto-update` twice, verify no error on second run
4. **Idempotent disable**: Run `--disable-auto-update` twice, verify no error on second run

## Best Practices

### For Users

1. **Check status first**: Before running trials, use `--status` to verify your environment is configured correctly

2. **Use reset after investigations**: After completing an investigation session, run `--reset` to restore normal Claude Code behavior

3. **Keep backups**: The script creates backups before modifications, but consider additional manual backups of `~/.claude/settings.json` if you have custom settings

**Recommended Trial Workflow:**
```bash
# 1. Disable auto-updates to prevent mid-trial version changes
./src/cc_version.py --disable-auto-update

# 2. Install target version
./src/cc_version.py --install 2.0.58

# 3. Verify configuration
./src/cc_version.py --status

# 4. Run trials...

# 5. Restore defaults when done
./src/cc_version.py --reset
```

### For Implementers

1. **Follow archive_claude_sessions.py patterns**: Use `Path.home() / ".claude"` for directory access, `argparse` for CLI, type hints throughout, and Google-style docstrings

2. **Preserve JSON formatting**: When writing settings.json, use `json.dump()` with `indent=2` to maintain human-readable formatting

3. **Capture subprocess output**: Use `subprocess.run()` with `capture_output=True` to collect both stdout and stderr for error messages

4. **Exit immediately on errors**: Do not attempt to continue after any error; call `sys.exit(1)` with a message to stderr

## Related Specifications

- **Experiment-Methodology-01.md**: Documents the manual process this script automates; references the script as the preferred alternative
- **Collect-Trials-Script-Overview.md**: Sister script for collecting trial artifacts; similar Python patterns and project integration
- **PRD.md**: Broader investigation context explaining why version management matters for phantom reads testing

---

*This specification defines the authoritative rules for the CC Version Script including CLI interface, settings management, npm orchestration, and error handling. All implementations must conform to these specifications.*

## Testing Support

This section describes the testability architecture that enables comprehensive automated unit testing of the CC Version Script. The implementation uses dependency injection patterns to isolate functions from external dependencies (filesystem, subprocess calls, system time), enabling thorough testing without requiring actual npm/claude installations or modifying real settings files.

### Dependency Injection Strategy

The script's functions interact with three categories of external dependencies that must be injectable for testing:

| Dependency Type          | Affected Operations                       | Injection Mechanism                                |
| ------------------------ | ----------------------------------------- | -------------------------------------------------- |
| **Filesystem paths**     | Settings file read/write, backup creation | Optional `settings_path: Path \| None` parameter   |
| **Subprocess execution** | npm commands, claude version check        | Optional `run_command: Callable \| None` parameter |
| **System time**          | Backup timestamp generation               | Optional `timestamp: str \| None` parameter        |

All injectable parameters default to `None`, preserving original behavior when called without arguments. When tests provide mock values, functions use those instead of real system resources.

### Path Injection

Functions that interact with the settings file accept an optional `settings_path` parameter:

```python
def read_settings(settings_path: Path | None = None) -> dict[str, Any]:
    """Read Claude Code settings from JSON file.

    Args:
        settings_path: Optional path override for testing. If None, uses
            ~/.claude/settings.json.
    """
    path = settings_path if settings_path is not None else get_settings_path()
    ...
```

This pattern applies to: `read_settings()`, `write_settings()`, `disable_auto_update()`, `enable_auto_update()`, `get_auto_update_status()`, `reset_to_defaults()`, and `show_status()`.

### Command Injection

Functions that execute subprocess commands accept an optional `run_command` callable:

```python
def check_npm_available(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None
) -> bool:
    """Check if npm is available on the system.

    Args:
        run_command: Optional command runner for testing. If None, uses
            subprocess.run. Must accept same signature as subprocess.run.
    """
    runner = run_command if run_command is not None else subprocess.run
    ...
```

This pattern applies to: `check_npm_available()`, `check_claude_available()`, `validate_prerequisites()`, `list_versions()`, `get_installed_version()`, `get_available_versions()`, `get_latest_version()`, `validate_version()`, `install_version()`, `reset_to_defaults()`, and `show_status()`.

### Timestamp Injection

The `create_backup()` function accepts an optional timestamp for deterministic backup naming in tests:

```python
def create_backup(settings_path: Path, timestamp: str | None = None) -> Path:
    """Create a timestamped backup of the settings file.

    Args:
        settings_path: Path to the settings file to backup.
        timestamp: Optional timestamp override for testing. If None, uses
            current time in YYYYMMDD_HHMMSS format.
    """
    ts = timestamp if timestamp is not None else datetime.now().strftime("%Y%m%d_%H%M%S")
    ...
```

### Test Architecture

Tests are organized into categories matching the function groupings:

1. **Settings File Utilities** - Tests for `read_settings()`, `write_settings()`, `create_backup()` using temporary directories
2. **Auto-Update Functions** - Tests for `disable_auto_update()`, `enable_auto_update()` with various initial states
3. **Version Query Functions** - Tests for `get_auto_update_status()`, `get_installed_version()`, `get_available_versions()`, `get_latest_version()`, `validate_version()` with mocked subprocess
4. **Command Functions** - Tests for `list_versions()`, `install_version()`, `reset_to_defaults()`, `show_status()` with full mocking
5. **Prerequisite Checking** - Tests for `check_npm_available()`, `check_claude_available()`, `validate_prerequisites()` with command injection
6. **CLI** - Tests for `create_parser()` mutual exclusivity and `main()` dispatch logic
7. **Integration** - End-to-end workflow tests with all dependencies mocked

### Test Fixtures

Tests use pytest fixtures for common test infrastructure:

- `tmp_settings_dir` - Temporary directory with settings.json for filesystem tests
- `mock_subprocess_run` - Configurable mock for subprocess.run returning specified outputs
- `sample_settings` - Dictionary factory for common settings configurations
- `mock_npm_versions` - Standard list of version strings for version-related tests

### Idempotent Operation Testing

Functions that call `sys.exit(0)` for idempotent early returns (e.g., "Auto-update is already disabled") are tested using pytest's `SystemExit` catching:

```python
def test_disable_auto_update_idempotent(tmp_settings_dir):
    # Setup: settings already have DISABLE_AUTOUPDATER = "1"
    with pytest.raises(SystemExit) as exc_info:
        disable_auto_update(settings_path=tmp_settings_dir / "settings.json")
    assert exc_info.value.code == 0
```

## Feature Implementation Plan (FIP)

### Phase 1: Core Infrastructure

- [x] **1.1** - Create `src/cc_version.py` with executable shebang and module docstring
  - [x] **1.1.1** - Add shebang line (`#!/usr/bin/env python`)
  - [x] **1.1.2** - Add module docstring describing script purpose
  - [x] **1.1.3** - Add required imports (`argparse`, `json`, `subprocess`, `sys`, `pathlib`)
- [x] **1.2** - Implement prerequisite checking functions
  - [x] **1.2.1** - Implement `check_npm_available()` function
  - [x] **1.2.2** - Implement `check_claude_available()` function
  - [x] **1.2.3** - Implement `validate_prerequisites()` that calls both checks
- [x] **1.3** - Implement settings file utilities
  - [x] **1.3.1** - Implement `get_settings_path()` returning `Path.home() / ".claude" / "settings.json"`
  - [x] **1.3.2** - Implement `read_settings()` with JSON parsing and error handling
  - [x] **1.3.3** - Implement `write_settings()` with backup creation and JSON formatting
  - [x] **1.3.4** - Implement `create_backup()` for settings file

### Phase 2: Auto-Update Management

- [x] **2.1** - Implement `--disable-auto-update` command
  - [x] **2.1.1** - Implement `disable_auto_update()` function
  - [x] **2.1.2** - Ensure `env` dict creation if missing
  - [x] **2.1.3** - Set `env.DISABLE_AUTOUPDATER` to `"1"`
- [x] **2.2** - Implement `--enable-auto-update` command
  - [x] **2.2.1** - Implement `enable_auto_update()` function
  - [x] **2.2.2** - Remove `env.DISABLE_AUTOUPDATER` key if present
  - [x] **2.2.3** - Clean up empty `env` dict if no other keys remain

### Phase 3: Version Query Operations

- [x] **3.1** - Implement `--list` command
  - [x] **3.1.1** - Implement `list_versions()` function
  - [x] **3.1.2** - Execute `npm view @anthropic-ai/claude-code versions` (no `--json` flag)
  - [x] **3.1.3** - Pass through npm's human-readable output directly to stdout
- [x] **3.2** - Implement `--status` command
  - [x] **3.2.1** - Implement `get_auto_update_status()` to check settings
  - [x] **3.2.2** - Implement `get_installed_version()` parsing `claude --version` output
  - [x] **3.2.3** - Implement `get_latest_version()` from npm versions list
  - [x] **3.2.4** - Implement `show_status()` combining all three values

### Phase 4: Version Installation

- [x] **4.1** - Implement version validation
  - [x] **4.1.1** - Implement `get_available_versions()` returning list from npm
  - [x] **4.1.2** - Implement `validate_version(version)` checking against available versions
- [x] **4.2** - Implement `--install` command
  - [x] **4.2.1** - Implement `install_version(version)` function
  - [x] **4.2.2** - Execute npm uninstall command
  - [x] **4.2.3** - Execute npm cache clean command
  - [x] **4.2.4** - Execute npm install command with version
  - [x] **4.2.5** - Verify installation with `claude --version`
- [x] **4.3** - Implement `--reset` command
  - [x] **4.3.1** - Implement `reset_to_defaults()` function
  - [x] **4.3.2** - Call enable_auto_update()
  - [x] **4.3.3** - Install latest version

### Phase 5: CLI Integration

- [x] **5.1** - Implement argument parsing
  - [x] **5.1.1** - Create `argparse.ArgumentParser` with description
  - [x] **5.1.2** - Add mutually exclusive group for commands
  - [x] **5.1.3** - Add all command flags with help text
- [x] **5.2** - Implement main entry point
  - [x] **5.2.1** - Implement `main()` function with prerequisite validation
  - [x] **5.2.2** - Dispatch to appropriate handler based on arguments
  - [x] **5.2.3** - Add `if __name__ == "__main__"` block
- [x] **5.3** - Verify script is executable
  - [x] **5.3.1** - Ensure file has executable permissions (`chmod +x`)

### Phase 6: Testing Support Infrastructure

- [x] **6.1** - Add path injection to settings file functions
  - [x] **6.1.1** - Update `read_settings()` signature to accept optional `settings_path: Path | None = None`
  - [x] **6.1.2** - Update `write_settings()` signature to accept optional `settings_path: Path | None = None`
  - [x] **6.1.3** - Update function bodies to use injected path when provided
- [x] **6.2** - Add timestamp injection to backup function
  - [x] **6.2.1** - Update `create_backup()` signature to accept optional `timestamp: str | None = None`
  - [x] **6.2.2** - Update function body to use injected timestamp when provided
- [x] **6.3** - Add command injection to prerequisite functions
  - [x] **6.3.1** - Update `check_npm_available()` to accept optional `run_command: Callable | None = None`
  - [x] **6.3.2** - Update `check_claude_available()` to accept optional `run_command: Callable | None = None`
  - [x] **6.3.3** - Update `validate_prerequisites()` to accept and pass through `run_command`
- [x] **6.4** - Add command injection to version query functions
  - [x] **6.4.1** - Update `list_versions()` to accept optional `run_command`
  - [x] **6.4.2** - Update `get_installed_version()` to accept optional `run_command`
  - [x] **6.4.3** - Update `get_available_versions()` to accept optional `run_command`
  - [x] **6.4.4** - Update `get_latest_version()` to pass through `run_command`
  - [x] **6.4.5** - Update `validate_version()` to pass through `run_command`
- [x] **6.5** - Add dependency injection to auto-update functions
  - [x] **6.5.1** - Update `disable_auto_update()` to accept optional `settings_path`
  - [x] **6.5.2** - Update `enable_auto_update()` to accept optional `settings_path`
  - [x] **6.5.3** - Update `get_auto_update_status()` to accept optional `settings_path`
- [x] **6.6** - Add dependency injection to command functions
  - [x] **6.6.1** - Update `install_version()` to accept optional `run_command` and `settings_path`
  - [x] **6.6.2** - Update `reset_to_defaults()` to accept optional `run_command` and `settings_path`
  - [x] **6.6.3** - Update `show_status()` to accept optional `run_command` and `settings_path`
- [x] **6.7** - Update all affected docstrings
  - [x] **6.7.1** - Add Args documentation for new optional parameters
  - [x] **6.7.2** - Ensure Google-style docstring format is maintained
- [x] **6.8** - Add Callable import
  - [x] **6.8.1** - Add `from collections.abc import Callable` to imports

### Phase 7: Test Implementation

- [x] **7.1** - Create test file and fixtures
  - [x] **7.1.1** - Create `tests/test_cc_version.py`
  - [x] **7.1.2** - Implement `tmp_settings_dir` fixture using pytest's `tmp_path`
  - [x] **7.1.3** - Implement `mock_subprocess_run` fixture factory
  - [x] **7.1.4** - Implement `sample_settings` fixture factory
  - [x] **7.1.5** - Implement `mock_npm_versions` fixture with standard version list
- [x] **7.2** - Implement settings file utility tests
  - [x] **7.2.1** - Test `get_settings_path()` returns correct path
  - [x] **7.2.2** - Test `read_settings()` success case
  - [x] **7.2.3** - Test `read_settings()` file not found error
  - [x] **7.2.4** - Test `read_settings()` empty file error
  - [x] **7.2.5** - Test `read_settings()` invalid JSON error
  - [x] **7.2.6** - Test `read_settings()` non-dict root error
  - [x] **7.2.7** - Test `write_settings()` creates backup
  - [x] **7.2.8** - Test `write_settings()` formats JSON correctly
  - [x] **7.2.9** - Test `write_settings()` invalid env type error
  - [x] **7.2.10** - Test `create_backup()` timestamp format
  - [x] **7.2.11** - Test `create_backup()` naming pattern
- [x] **7.3** - Implement auto-update function tests
  - [x] **7.3.1** - Test `disable_auto_update()` creates env key
  - [x] **7.3.2** - Test `disable_auto_update()` sets correct value
  - [x] **7.3.3** - Test `disable_auto_update()` idempotent behavior
  - [x] **7.3.4** - Test `enable_auto_update()` removes key
  - [x] **7.3.5** - Test `enable_auto_update()` cleans empty env dict
  - [x] **7.3.6** - Test `enable_auto_update()` idempotent behavior
  - [x] **7.3.7** - Test `enable_auto_update()` preserves other env keys
- [x] **7.4** - Implement version query function tests
  - [x] **7.4.1** - Test `get_auto_update_status()` returns "Disabled" when set
  - [x] **7.4.2** - Test `get_auto_update_status()` returns "Enabled" when unset
  - [x] **7.4.3** - Test `get_installed_version()` parses output correctly
  - [x] **7.4.4** - Test `get_installed_version()` command failure error
  - [x] **7.4.5** - Test `get_installed_version()` empty output error
  - [x] **7.4.6** - Test `get_available_versions()` parses JSON array
  - [x] **7.4.7** - Test `get_available_versions()` npm failure error
  - [x] **7.4.8** - Test `get_available_versions()` invalid JSON error
  - [x] **7.4.9** - Test `get_latest_version()` returns last element
  - [x] **7.4.10** - Test `validate_version()` returns True for valid
  - [x] **7.4.11** - Test `validate_version()` returns False for invalid
- [x] **7.5** - Implement command function tests
  - [x] **7.5.1** - Test `list_versions()` passes through npm output
  - [x] **7.5.2** - Test `list_versions()` npm error handling
  - [x] **7.5.3** - Test `install_version()` validates version first
  - [x] **7.5.4** - Test `install_version()` invalid version exits
  - [x] **7.5.5** - Test `install_version()` executes npm sequence
  - [x] **7.5.6** - Test `install_version()` verifies installation
  - [x] **7.5.7** - Test `reset_to_defaults()` enables auto-update
  - [x] **7.5.8** - Test `reset_to_defaults()` installs latest
  - [x] **7.5.9** - Test `show_status()` displays all info
- [x] **7.6** - Implement prerequisite checking tests
  - [x] **7.6.1** - Test `check_npm_available()` success
  - [x] **7.6.2** - Test `check_npm_available()` not found
  - [x] **7.6.3** - Test `check_claude_available()` success
  - [x] **7.6.4** - Test `check_claude_available()` not found
  - [x] **7.6.5** - Test `validate_prerequisites()` all pass
  - [x] **7.6.6** - Test `validate_prerequisites()` npm missing
  - [x] **7.6.7** - Test `validate_prerequisites()` claude missing
- [x] **7.7** - Implement CLI tests
  - [x] **7.7.1** - Test `create_parser()` mutual exclusivity
  - [x] **7.7.2** - Test `create_parser()` requires command
  - [x] **7.7.3** - Test `create_parser()` install accepts version
  - [x] **7.7.4** - Test `main()` validates prerequisites first
  - [x] **7.7.5** - Test `main()` dispatches to correct handlers
- [x] **7.8** - Implement integration tests
  - [x] **7.8.1** - Test full workflow: disable → install → status → reset
  - [x] **7.8.2** - Test backup accumulation across operations
  - [x] **7.8.3** - Test error propagation from settings
  - [x] **7.8.4** - Test error propagation from npm

### Phase 8: Testing Support Infrastructure

- [x] **8.1** - Add notes to `docs/experiments/methodologies/Experiment-Methodology-02.md` on using this script to disable CC auto-updater and set to the desired CC version.
- [x] **8.2** - Add mention of this script to `README.md` on using this script to setup on CC for an experiment.
