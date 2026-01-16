#!/usr/bin/env python
"""Claude Code Version Management Script.

Manages Claude Code version installation and auto-update settings through
a unified CLI interface. Provides commands for toggling auto-updates,
installing specific versions, and viewing current installation status.

This script serves as a convenience wrapper for the manual process documented
in Experiment-Methodology-01.md, enabling investigators to quickly configure
their Claude Code environment for phantom reads testing.

Features:
    - Toggle auto-update settings in ~/.claude/settings.json
    - Install specific Claude Code versions via npm
    - Display current version and auto-update status
    - Validate prerequisites (npm and claude availability)
    - Create backups before modifying settings

Usage:
    ./src/cc_version.py --status
    ./src/cc_version.py --disable-auto-update
    ./src/cc_version.py --install 2.0.58
    ./src/cc_version.py --reset
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def check_npm_available() -> bool:
    """Check if npm is available on the system.

    Executes 'npm --version' to verify npm is installed and accessible
    in the system PATH.

    Returns:
        True if npm command executes successfully, False otherwise.
    """
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_claude_available() -> bool:
    """Check if Claude Code CLI is available on the system.

    Executes 'claude --version' to verify Claude Code is installed and
    accessible in the system PATH.

    Returns:
        True if claude command executes successfully, False otherwise.
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def validate_prerequisites() -> bool:
    """Validate that all required tools are available.

    Checks for npm and claude CLI availability. Prints helpful error
    messages to stderr if either tool is missing.

    Returns:
        True if all prerequisites are met, False otherwise.
    """
    all_valid = True

    if not check_npm_available():
        print(
            "Error: npm is not installed or not in PATH.\n"
            "Please install Node.js and npm before using this script.",
            file=sys.stderr,
        )
        all_valid = False

    if not check_claude_available():
        print(
            "Error: Claude Code is not installed.\nRun: npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        all_valid = False

    return all_valid


def get_settings_path() -> Path:
    """Get the path to Claude Code settings file.

    Returns:
        Path to ~/.claude/settings.json
    """
    return Path.home() / ".claude" / "settings.json"


def create_backup(settings_path: Path) -> Path:
    """Create a timestamped backup of the settings file.

    Creates a backup with format: settings.json.YYYYMMDD_HHMMSS.cc_version_backup
    in the same directory as the original settings file.

    Args:
        settings_path: Path to the settings file to backup.

    Returns:
        Path to the created backup file.

    Raises:
        OSError: If backup file cannot be created.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"settings.json.{timestamp}.cc_version_backup"
    backup_path = settings_path.parent / backup_filename

    shutil.copy2(settings_path, backup_path)
    return backup_path


def read_settings() -> dict[str, Any]:
    """Read Claude Code settings from JSON file.

    Loads and parses the settings.json file from ~/.claude/ directory.
    Provides detailed error messages for various failure conditions.

    Returns:
        Dictionary containing settings data.

    Raises:
        FileNotFoundError: If settings file does not exist.
        ValueError: If settings file is empty or contains invalid JSON.
        OSError: If file cannot be read due to permissions.
    """
    settings_path = get_settings_path()

    if not settings_path.exists():
        raise FileNotFoundError(
            f"Settings file not found: {settings_path}\n"
            "Claude Code must be installed and have run at least once to create this file."
        )

    content = settings_path.read_text(encoding="utf-8")

    if not content.strip():
        raise ValueError(f"Settings file is empty: {settings_path}")

    try:
        settings = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Settings file contains invalid JSON: {settings_path}\nJSON error: {e}"
        ) from e

    if not isinstance(settings, dict):
        raise TypeError(f"Settings file must contain a JSON object, got {type(settings).__name__}")

    return settings


def write_settings(settings: dict[str, Any]) -> None:
    """Write settings to Claude Code settings file with backup.

    Creates a backup of the existing settings file before writing,
    then writes the new settings with consistent JSON formatting.

    Args:
        settings: Dictionary of settings to write.

    Raises:
        OSError: If backup cannot be created or file cannot be written.
        TypeError: If settings contains non-serializable values.
    """
    settings_path = get_settings_path()

    # Validate env structure if present
    if "env" in settings and not isinstance(settings["env"], dict):
        raise TypeError("Unexpected settings structure: 'env' is not a dictionary.")

    # Create backup before modifying
    if settings_path.exists():
        create_backup(settings_path)

    # Write with consistent formatting
    with settings_path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Trailing newline for POSIX compliance


def disable_auto_update() -> None:
    """Disable Claude Code auto-updates.

    Modifies ~/.claude/settings.json to set env.DISABLE_AUTOUPDATER to "1".
    Creates a timestamped backup before modification. Operation is idempotent -
    running when already disabled exits successfully with a message.

    Returns:
        None

    Raises:
        FileNotFoundError: If settings.json does not exist.
        ValueError: If settings.json is empty or contains invalid JSON.
        TypeError: If env key exists but is not a dictionary.
        OSError: If file cannot be read or written due to permissions.
    """
    settings = read_settings()

    # Check if already disabled - exit early with success if so
    if settings.get("env", {}).get("DISABLE_AUTOUPDATER") == "1":
        print("Auto-update is already disabled.")
        sys.exit(0)

    # Ensure 'env' key exists as a dict
    if "env" not in settings:
        settings["env"] = {}

    settings["env"]["DISABLE_AUTOUPDATER"] = "1"

    write_settings(settings)
    print("Auto-update disabled.")


def enable_auto_update() -> None:
    """Enable Claude Code auto-updates.

    Modifies ~/.claude/settings.json to remove env.DISABLE_AUTOUPDATER key.
    Creates a timestamped backup before modification. Operation is idempotent -
    running when already enabled exits successfully with a message. Cleans up
    empty env dict if no other keys remain.

    Returns:
        None

    Raises:
        FileNotFoundError: If settings.json does not exist.
        ValueError: If settings.json is empty or contains invalid JSON.
        TypeError: If env key exists but is not a dictionary.
        OSError: If file cannot be read or written due to permissions.
    """
    settings = read_settings()

    # Check if already enabled (key missing or not "1") - exit early with success if so
    if "env" not in settings or "DISABLE_AUTOUPDATER" not in settings["env"]:
        print("Auto-update is already enabled.")
        sys.exit(0)

    # Remove the key
    del settings["env"]["DISABLE_AUTOUPDATER"]

    # Clean up empty 'env' dict if no other keys remain
    if not settings["env"]:
        del settings["env"]

    write_settings(settings)
    print("Auto-update enabled.")
