# Claude Code Changelog: Versions 2.1.6 to 2.1.22

**Created:** 2026-01-28
**Purpose:** Comprehensive record of Claude Code changes for Phantom Reads investigation context
**Sources:** [GitHub Releases](https://github.com/anthropics/claude-code/releases), [CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

---

## Overview

This document catalogs all changes to Claude Code between versions 2.1.6 and 2.1.22 (current as of 2026-01-28). This is relevant to our Phantom Reads investigation as it may reveal changes to file reading behavior, context management, or tool execution that could affect the bug's manifestation.

**Note on Version 2.1.20:** The original request mentioned 2.1.20 as "current" but version 2.1.22 is actually the latest release as of this writing.

---

## Version Summary Table

| Version | Release Date | Notable Changes |
|---------|--------------|-----------------|
| 2.1.22 | 2026-01-28 | Structured outputs fix for non-interactive mode |
| 2.1.21 | 2026-01-28 | File reading improvements, tool preference changes |
| 2.1.20 | 2026-01-27 | Session compaction fixes, wide character rendering |
| 2.1.19 | 2026-01-23 | Task system env var, crash fixes |
| 2.1.17 | 2026-01-22 | AVX instruction crash fix |
| 2.1.16 | 2026-01-22 | New task management system, OOM crash fixes |
| 2.1.15 | 2026-01-21 | npm deprecation notice, UI performance |
| 2.1.14 | 2026-01-20 | Context window blocking limit fix, memory leak fix |
| 2.1.12 | 2026-01-17 | Message rendering bug fix |
| 2.1.11 | 2026-01-17 | MCP connection request fix |
| 2.1.10 | Not specified | Session compaction, task management |
| 2.1.9 | Not specified | Performance issues reported, MCP improvements |
| 2.1.8 | Not specified | Customizable keyboard shortcuts |
| 2.1.7 | Not specified | Security fixes, context window calculation |
| 2.1.6 | Not specified | Search in /config, skill discovery |

---

## Detailed Changelog

### Version 2.1.22
**Release Date:** 2026-01-28 06:59

#### Fixes
- Fixed structured outputs for non-interactive (`-p`) mode

---

### Version 2.1.21
**Release Date:** 2026-01-28 02:25

#### Features
- Added support for full-width (zenkaku) number input from Japanese IME in option selection prompts
- **[VSCode]** Added automatic Python virtual environment activation, ensuring `python` and `pip` commands use the correct interpreter (configurable via `claudeCode.usePythonEnvironment` setting)

#### Fixes
- Fixed shell completion cache files being truncated on exit
- Fixed API errors when resuming sessions that were interrupted during tool execution
- Fixed auto-compact triggering too early on models with large output token limits
- Fixed task IDs potentially being reused after deletion
- Fixed file search not working in VS Code extension on Windows
- **[VSCode]** Fixed message action buttons having incorrect background colors

#### Improvements
- **Improved read/search progress indicators to show "Reading…" while in progress and "Read" when complete** *(potentially relevant to Phantom Reads)*
- **Improved Claude to prefer file operation tools (Read, Edit, Write) over bash equivalents (cat, sed, awk)** *(potentially relevant to Phantom Reads)*

---

### Version 2.1.20
**Release Date:** 2026-01-27 01:35

#### Features
- Added arrow key history navigation in vim normal mode when cursor cannot move further
- Added external editor shortcut (Ctrl+G) to the help menu for better discoverability
- Added PR review status indicator to the prompt footer, showing the current branch's PR state (approved, changes requested, pending, or draft) as a colored dot with a clickable link
- Added support for loading `CLAUDE.md` files from additional directories specified via `--add-dir` flag (requires setting `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`)
- Added ability to delete tasks via the `TaskUpdate` tool

#### Fixes
- **Fixed session compaction issues that could cause resume to load full history instead of the compact summary** *(potentially relevant to Phantom Reads - context management)*
- Fixed agents sometimes ignoring user messages sent while actively working on a task
- Fixed wide character (emoji, CJK) rendering artifacts where trailing columns were not cleared when replaced by narrower characters
- Fixed JSON parsing errors when MCP tool responses contain special Unicode characters
- Fixed up/down arrow keys in multi-line and wrapped text input to prioritize cursor movement over history navigation
- Fixed draft prompt being lost when pressing UP arrow to navigate command history
- Fixed ghost text flickering when typing slash commands mid-input
- Fixed marketplace source removal not properly deleting settings
- Fixed duplicate output in some commands like `/context`
- Fixed task list sometimes showing outside the main conversation view
- Fixed syntax highlighting for diffs occurring within multiline constructs like Python docstrings
- Fixed crashes when cancelling tool use

#### Improvements
- Improved `/sandbox` command UI to show dependency status with installation instructions when dependencies are missing
- Improved thinking status text with a subtle shimmer animation
- Improved task list to dynamically adjust visible items based on terminal height
- Improved fork conversation hint to show how to resume the original session

#### Changes
- Changed collapsed read/search groups to show present tense ("Reading", "Searching for") while in progress, and past tense ("Read", "Searched for") when complete
- Changed teammate messages to render with rich Markdown formatting (bold, code blocks, lists, etc.) instead of plain text
- Changed `ToolSearch` results to appear as a brief notification instead of inline in the conversation
- Changed the `/commit-push-pr` skill to automatically post PR URLs to Slack channels when configured via MCP tools
- Changed the `/copy` command to be available to all users
- Changed background agents to prompt for tool permissions before launching
- Changed permission rules like `Bash(*)` to be accepted and treated as equivalent to `Bash`
- Changed config backups to be timestamped and rotated (keeping 5 most recent) to prevent data loss

---

### Version 2.1.19
**Release Date:** 2026-01-23 21:56

#### Features
- Added env var `CLAUDE_CODE_ENABLE_TASKS`, set to `false` to keep the old system temporarily
- Added shorthand `$0`, `$1`, etc. for accessing individual arguments in custom commands

#### Fixes
- Fixed crashes on processors without AVX instruction support
- Fixed dangling Claude Code processes when terminal is closed by catching EIO errors from `process.exit()` and using SIGKILL as fallback
- Fixed `/rename` and `/tag` not updating the correct session when resuming from a different directory (e.g., git worktrees)
- Fixed resuming sessions by custom title not working when run from a different directory
- Fixed pasted text content being lost when using prompt stash (Ctrl+S) and restore
- Fixed agent list displaying "Sonnet (default)" instead of "Inherit (default)" for agents without an explicit model setting
- Fixed backgrounded hook commands not returning early, potentially causing the session to wait on a process that was intentionally backgrounded
- Fixed file write preview omitting empty lines

#### Changes
- Changed skills without additional permissions or hooks to be allowed without requiring approval
- Changed indexed argument syntax from `$ARGUMENTS.0` to `$ARGUMENTS[0]` (bracket syntax)

#### SDK
- Added replay of `queued_command` attachment messages as `SDKUserMessageReplay` events when `replayUserMessages` is enabled

#### VSCode
- Enabled session forking and rewind functionality for all users

---

### Version 2.1.17
**Release Date:** 2026-01-22 21:46

#### Fixes
- Fixed crashes on processors without AVX instruction support

---

### Version 2.1.16
**Release Date:** 2026-01-22 20:09

#### Features
- Added new task management system, including new capabilities like dependency tracking
- **[VSCode]** Added native plugin management support
- **[VSCode]** Added ability for OAuth users to browse and resume remote Claude sessions from the Sessions dialog

#### Fixes
- **Fixed out-of-memory crashes when resuming sessions with heavy subagent usage** *(potentially relevant to Phantom Reads - memory management)*
- Fixed an issue where the "context remaining" warning was not hidden after running `/compact`
- **[IDE]** Fixed a race condition on Windows where the Claude Code sidebar view container would not appear on start

---

### Version 2.1.15
**Release Date:** 2026-01-21 22:01

#### Features
- Added deprecation notification for npm installations - run `claude install` or see https://docs.anthropic.com/en/docs/claude-code/getting-started for more options

#### Improvements
- Improved UI rendering performance with React Compiler

#### Fixes
- Fixed the "Context left until auto-compact" warning not disappearing after running `/compact`
- Fixed MCP stdio server timeout not killing child process, which could cause UI freezes

---

### Version 2.1.14
**Release Date:** 2026-01-20 23:09

#### Features
- Added history-based autocomplete in bash mode (`!`) - type a partial command and press Tab to complete from your bash command history
- Added search to installed plugins list - type to filter by name or description
- Added support for pinning plugins to specific git commit SHAs, allowing marketplace entries to install exact versions

#### Fixes
- **Fixed a regression where the context window blocking limit was calculated too aggressively, blocking users at ~65% context usage instead of the intended ~98%** *(highly relevant to Phantom Reads - context management)*
- Fixed memory issues that could cause crashes when running parallel subagents
- **Fixed memory leak in long-running sessions where stream resources were not cleaned up after shell commands completed** *(potentially relevant to Phantom Reads)*
- Fixed `@` symbol incorrectly triggering file autocomplete suggestions in bash mode
- Fixed `@`-mention menu folder click behavior to navigate into directories instead of selecting them
- Fixed `/feedback` command generating invalid GitHub issue URLs when description is very long
- Fixed `/context` command to show the same token count and percentage as the status line in verbose mode
- Fixed an issue where `/config`, `/context`, `/model`, and `/todos` command overlays could close unexpectedly
- Fixed slash command autocomplete selecting wrong command when typing similar commands (e.g., `/context` vs `/compact`)
- Fixed inconsistent back navigation in plugin marketplace when only one marketplace is configured
- Fixed iTerm2 progress bar not clearing properly on exit, preventing lingering indicators and bell sounds

#### Improvements
- Improved backspace to delete pasted text as a single token instead of one character at a time

#### VSCode
- Added `/usage` command to display current plan usage

---

### Version 2.1.12
**Release Date:** 2026-01-17 16:18

#### Fixes
- Fixed message rendering bug

---

### Version 2.1.11
**Release Date:** 2026-01-17 01:39

#### Fixes
- Fixed excessive MCP connection requests for HTTP/SSE transports

---

### Version 2.1.10
**Release Date:** Not specified in official sources

#### Features
- Arrow key history navigation in vim normal mode when cursor cannot move further
- External editor shortcut (Ctrl+G) added to help menu for improved visibility
- PR review status indicator displaying current branch's PR state with colored dot and clickable link
- Support for loading `CLAUDE.md` files from directories via `--add-dir` flag (requires `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`)
- Task deletion capability via the `TaskUpdate` tool

#### Fixes
- **Fixed session compaction issues that could cause resume to load full history instead of compact summary** *(potentially relevant to Phantom Reads - context management)*
- Agents now respect user messages sent during active task work
- Wide character rendering artifacts corrected
- JSON parsing improved for MCP tool responses with special Unicode
- Multi-line text input arrow key behavior prioritizes cursor movement over history
- Draft prompt preservation when pressing UP for command history
- Ghost text flickering eliminated when typing slash commands
- Marketplace source removal now properly deletes settings
- Duplicate output in commands like `/context` eliminated
- Task list display confined to main conversation view
- Syntax highlighting for diffs in multiline constructs fixed
- Tool cancellation crashes resolved

#### Improvements
- `/sandbox` command UI enhanced with dependency status and installation instructions
- Thinking status text includes subtle shimmer animation
- Task list dynamically adjusts visible items based on terminal height
- Fork conversation hint displays session resumption guidance

#### Changes
- Read/search group display changed: present tense during progress, past tense when complete
- `ToolSearch` results displayed as brief notification instead of inline
- `/commit-push-pr` skill automatically posts PR URLs to Slack when configured
- `/copy` command available to all users
- Background agents prompt for tool permissions before launching
- Permission rules like `Bash(*)` now accepted as equivalent to `Bash`
- Config backups timestamped and rotated, maintaining 5 most recent versions

---

### Version 2.1.9
**Release Date:** Not specified in official sources

**⚠️ Known Issues:** This version had significant performance problems reported by users, including:
- Sessions becoming completely unresponsive with 100% CPU and ~7GB RAM usage
- Main thread stuck in infinite loops
- ~30GB RAM usage in some cases
- Startup time regression (~5 minutes vs normal in 2.1.7)

#### Features
- `auto:N` syntax for configuring MCP tool search auto-enable threshold (N = context window percentage 0-100)
- `plansDirectory` setting for customizing plan file storage locations
- External editor support (Ctrl+G) in AskUserQuestion "Other" input field
- Session URL attribution added to commits and PRs from web sessions
- `PreToolUse` hooks can return `additionalContext` to the model

#### Fixes
- Long sessions with parallel tool calls now function properly
- MCP server reconnection no longer hangs with unresolved cached promises
- Ctrl+Z suspend now works in Kitty keyboard protocol terminals
- "Cooked for 1m 6s" style turn duration messages toggleable via `showTurnDuration` setting
- Permission prompt feedback capability added
- Agent's final response displays inline in task notifications
- **Security vulnerability fixed: wildcard permission rules could match unintended compound commands**
- Windows false "file modified" errors eliminated
- Orphaned tool_result errors resolved with sibling tool failures
- **Context window blocking limit calculation corrected** *(relevant to Phantom Reads - context management)*
- Spinner flashing removed for local slash commands
- Terminal title animation jitter eliminated
- Plugins with git submodules initialize fully
- Bash escape sequence misinterpretation on Windows resolved
- Memory allocation overhead reduced for typing responsiveness

#### Changes
- MCP tool search auto mode enabled by default; context usage reduced significantly
- OAuth and API Console URLs migrated from console.anthropic.com to platform.claude.com
- VSCode `claudeProcessWrapper` setting now passes correct Claude binary path

---

### Version 2.1.8
**Release Date:** Not specified in official sources

#### Features
- **Customizable keyboard shortcuts with context-specific configuration**
- Chord sequence creation capability
- `/keybindings` command launches configuration interface
- Documentation available at https://code.claude.com/docs/en/keybindings

---

### Version 2.1.7
**Release Date:** Not specified in official sources

#### Features
- `showTurnDuration` setting hides turn duration messages
- Feedback capability when accepting permission prompts
- Agent's final response displays inline in task notifications

#### Fixes
- **Security vulnerability: wildcard permission rules could match compound shell operators—fixed**
- Windows cloud sync/antivirus false "file modified" errors corrected
- Orphaned tool_result errors eliminated
- **Context window blocking limit calculation uses effective context window** *(relevant to Phantom Reads - context management)*
- Spinner flashing removed for local slash commands
- Terminal title animation jitter reduced
- Plugins with git submodules now fully initialize
- Bash commands failing on Windows with temp directory escape sequences—resolved

#### Improvements
- Typing responsiveness improved through memory allocation optimization

#### Changes
- MCP tool search auto mode enabled by default
- OAuth/API Console URLs migrated to platform.claude.com
- VSCode `claudeProcessWrapper` setting corrected

---

### Version 2.1.6
**Release Date:** Not specified in official sources

#### Features
- Search functionality added to `/config` command for filtering settings
- Updates section in `/doctor` showing auto-update channel and npm versions
- Date range filtering for `/stats` command with `r` key cycling options
- **Automatic skill discovery from nested `.claude/skills` directories**
- `context_window.used_percentage` and `context_window.remaining_percentage` fields for status line
- Error display when editor fails during Ctrl+G

#### Fixes
- **Permission bypass via shell line continuation—security fix applied**
- False "File unexpectedly modified" errors eliminated
- Text styling misalignment in multi-line responses corrected
- Feedback panel closing unexpectedly when typing 'n'—fixed
- Rate limit warning appearing at low usage after weekly reset—corrected
- Rate limit options menu auto-opening on session resume—fixed
- Numpad keys outputting escape sequences in Kitty protocol—resolved
- Option+Return newline insertion in Kitty protocol—fixed
- Corrupted config backup files eliminated
- `mcp list` and `mcp get` leaving orphaned processes—resolved
- Visual artifacts in ink2 mode with `display:none` nodes—fixed

#### Improvements
- External CLAUDE.md imports approval dialog enhanced
- `/tasks` dialog improved to show details directly for single background tasks
- @ autocomplete enhanced with icons and single-line formatting
- "Help improve Claude" setting fetch improved
- Task notification display capped at 3 lines with overflow summary
- Terminal title set to "Claude Code" on startup

#### Changes
- @-mention MCP servers to enable/disable deprecated
- VSCode usage indicator updated after manual compact

---

## Changes Potentially Relevant to Phantom Reads Investigation

The following changes across these versions may be relevant to understanding or reproducing the Phantom Reads bug:

### Context Management Changes
1. **2.1.20, 2.1.10**: Fixed session compaction issues that could cause resume to load full history instead of compact summary
2. **2.1.14**: Fixed regression where context window blocking limit was calculated too aggressively (~65% instead of ~98%)
3. **2.1.9, 2.1.7**: Context window blocking limit calculation corrected
4. **2.1.16**: Fixed OOM crashes when resuming sessions with heavy subagent usage

### File Reading/Tool Execution Changes
1. **2.1.21**: Improved read/search progress indicators; Improved Claude to prefer file operation tools (Read, Edit, Write) over bash equivalents
2. **2.1.20**: Changed read/search groups to show present/past tense based on completion status

### Memory Management Changes
1. **2.1.14**: Fixed memory leak in long-running sessions where stream resources were not cleaned up
2. **2.1.16**: Fixed OOM crashes when resuming sessions with heavy subagent usage
3. **2.1.9**: Known severe memory issues (100% CPU, 7-30GB RAM usage)

### MCP/Tool Changes
1. **2.1.11**: Fixed excessive MCP connection requests
2. **2.1.9**: MCP tool search auto mode enabled by default; context usage reduced significantly
3. **2.1.9**: MCP server reconnection no longer hangs with unresolved cached promises

---

## References

- [GitHub Releases](https://github.com/anthropics/claude-code/releases)
- [CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [Bug Report: 2.1.9 Unusable](https://github.com/anthropics/claude-code/issues/18559)
- [Bug Report: 2.1.9 Complete Freeze](https://github.com/anthropics/claude-code/issues/18532)
- [Bug Report: Startup Regression](https://github.com/anthropics/claude-code/issues/18479)
