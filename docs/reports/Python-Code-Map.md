# Python API Structure

*Generated: 2026-01-19 10:39:52*
*Configuration: [tool.wsd].check_dirs from pyproject.toml*

## Modules

### `src.__init__`

Source package for claude-code-bug-phantom-reads project.

### `src.cc_version`

Claude Code Version Management Script.

**Functions:**

- `check_npm_available()`: Check if npm is available on the system.
- `check_claude_available()`: Check if Claude Code CLI is available on the system.
- `validate_prerequisites()`: Validate that all required tools are available.
- `get_settings_path()`: Get the path to Claude Code settings file.
- `create_backup()`: Create a timestamped backup of the settings file.
- `read_settings()`: Read Claude Code settings from JSON file.
- `write_settings()`: Write settings to Claude Code settings file with backup.
- `disable_auto_update()`: Disable Claude Code auto-updates.
- `enable_auto_update()`: Enable Claude Code auto-updates.
- `list_versions()`: List all available Claude Code versions from npm registry.
- `get_auto_update_status()`: Get the current auto-update status from settings.
- `get_installed_version()`: Get the currently installed Claude Code version.
- `get_available_versions()`: Fetch all available Claude Code versions from npm registry.
- `get_latest_version()`: Get the latest available Claude Code version from npm.
- `validate_version()`: Validate that a version string exists in available npm versions.
- `install_version()`: Install a specific Claude Code version.
- `reset_to_defaults()`: Reset Claude Code to Anthropic-intended default state.
- `show_status()`: Display current Claude Code installation status.
- `create_parser()`: Create and configure the argument parser for the CLI.
- `main()`: Main entry point for the cc_version CLI.

### `src.collect_trials`

Collect Trials Script.

**Classes:**

- `CollectionResult`: Results from collecting a single trial.

**Functions:**

- `encode_project_path()`: Convert project path to Claude Code's directory naming convention.
- `derive_session_directory()`: Derive Claude Code session directory from current working directory.
- `validate_directory()`: Validate that a directory exists and is accessible.
- `scan_exports()`: Scan exports directory for chat export files and extract Workscope IDs.
- `find_session_file()`: Search session files for Workscope ID and return the Session UUID.
- `file_contains_session_id()`: Check if an agent file belongs to a specific session.
- `copy_session_files()`: Copy session files using unified algorithm for all structures.
- `collect_single_trial()`: Collect all artifacts for a single trial.
- `create_parser()`: Create and configure the argument parser for the CLI.
- `print_summary()`: Print collection summary report.
- `main()`: Main entry point for the collect_trials CLI.


---

## Related Documentation

- [Python Standards](../read-only/standards/Python-Standards.md) - Python coding conventions for this project
- [Coding Standards](../read-only/standards/Coding-Standards.md) - General coding guidelines
- [Python Document Generator](../features/python-document-generator/Python-Document-Generator-Overview.md) - Tool specification
