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

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any


def check_npm_available(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> bool:
    """Check if npm is available on the system.

    Executes 'npm --version' to verify npm is installed and accessible
    in the system PATH.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.

    Returns:
        True if npm command executes successfully, False otherwise.
    """
    runner = run_command if run_command is not None else subprocess.run

    try:
        result = runner(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_claude_available(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> bool:
    """Check if Claude Code CLI is available on the system.

    Executes 'claude --version' to verify Claude Code is installed and
    accessible in the system PATH.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.

    Returns:
        True if claude command executes successfully, False otherwise.
    """
    runner = run_command if run_command is not None else subprocess.run

    try:
        result = runner(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def validate_prerequisites(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> bool:
    """Validate that all required tools are available.

    Checks for npm and claude CLI availability. Prints helpful error
    messages to stderr if either tool is missing.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Passed through to
            check_npm_available() and check_claude_available().

    Returns:
        True if all prerequisites are met, False otherwise.
    """
    all_valid = True

    if not check_npm_available(run_command=run_command):
        print(
            "Error: npm is not installed or not in PATH.\n"
            "Please install Node.js and npm before using this script.",
            file=sys.stderr,
        )
        all_valid = False

    if not check_claude_available(run_command=run_command):
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


def create_backup(settings_path: Path, timestamp: str | None = None) -> Path:
    """Create a timestamped backup of the settings file.

    Creates a backup with format: settings.json.YYYYMMDD_HHMMSS.cc_version_backup
    in the same directory as the original settings file.

    Args:
        settings_path: Path to the settings file to backup.
        timestamp: Optional timestamp string in YYYYMMDD_HHMMSS format for testing.
            If None, generates current timestamp.

    Returns:
        Path to the created backup file.

    Raises:
        OSError: If backup file cannot be created.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_filename = f"settings.json.{timestamp}.cc_version_backup"
    backup_path = settings_path.parent / backup_filename

    shutil.copy2(settings_path, backup_path)
    return backup_path


def read_settings(settings_path: Path | None = None) -> dict[str, Any]:
    """Read Claude Code settings from JSON file.

    Loads and parses the settings.json file. Provides detailed error messages
    for various failure conditions.

    Args:
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        Dictionary containing settings data.

    Raises:
        FileNotFoundError: If settings file does not exist.
        ValueError: If settings file is empty or contains invalid JSON.
        OSError: If file cannot be read due to permissions.
    """
    if settings_path is None:
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


def write_settings(settings: dict[str, Any], settings_path: Path | None = None) -> None:
    """Write settings to Claude Code settings file with backup.

    Creates a backup of the existing settings file before writing,
    then writes the new settings with consistent JSON formatting.

    Args:
        settings: Dictionary of settings to write.
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Raises:
        OSError: If backup cannot be created or file cannot be written.
        TypeError: If settings contains non-serializable values.
    """
    if settings_path is None:
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


def disable_auto_update(
    settings_path: Path | None = None,
) -> None:
    """Disable Claude Code auto-updates.

    Modifies ~/.claude/settings.json to set env.DISABLE_AUTOUPDATER to "1".
    Creates a timestamped backup before modification. Operation is idempotent -
    running when already disabled exits successfully with a message.

    Args:
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        None

    Raises:
        FileNotFoundError: If settings.json does not exist.
        ValueError: If settings.json is empty or contains invalid JSON.
        TypeError: If env key exists but is not a dictionary.
        OSError: If file cannot be read or written due to permissions.
    """
    settings = read_settings(settings_path=settings_path)

    # Check if already disabled - exit early with success if so
    if settings.get("env", {}).get("DISABLE_AUTOUPDATER") == "1":
        print("Auto-update is already disabled.")
        sys.exit(0)

    # Ensure 'env' key exists as a dict
    if "env" not in settings:
        settings["env"] = {}

    settings["env"]["DISABLE_AUTOUPDATER"] = "1"

    write_settings(settings, settings_path=settings_path)
    print("Auto-update disabled.")


def enable_auto_update(
    settings_path: Path | None = None,
) -> None:
    """Enable Claude Code auto-updates.

    Modifies ~/.claude/settings.json to remove env.DISABLE_AUTOUPDATER key.
    Creates a timestamped backup before modification. Operation is idempotent -
    running when already enabled exits successfully with a message. Cleans up
    empty env dict if no other keys remain.

    Args:
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        None

    Raises:
        FileNotFoundError: If settings.json does not exist.
        ValueError: If settings.json is empty or contains invalid JSON.
        TypeError: If env key exists but is not a dictionary.
        OSError: If file cannot be read or written due to permissions.
    """
    settings = read_settings(settings_path=settings_path)

    # Check if already enabled (key missing or not "1") - exit early with success if so
    if "env" not in settings or "DISABLE_AUTOUPDATER" not in settings["env"]:
        print("Auto-update is already enabled.")
        sys.exit(0)

    # Remove the key
    del settings["env"]["DISABLE_AUTOUPDATER"]

    # Clean up empty 'env' dict if no other keys remain
    if not settings["env"]:
        del settings["env"]

    write_settings(settings, settings_path=settings_path)
    print("Auto-update enabled.")


def list_versions(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> None:
    """List all available Claude Code versions from npm registry.

    Executes 'npm view @anthropic-ai/claude-code versions' and passes
    the human-readable output directly to stdout. This provides users
    with a quick view of all available versions without JSON parsing.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.

    Returns:
        None

    Raises:
        SystemExit: If npm command fails, exits with code 1.
    """
    runner = run_command if run_command is not None else subprocess.run
    result = runner(
        ["npm", "view", "@anthropic-ai/claude-code", "versions"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(
            f"Error: npm command failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
        if result.stderr:
            print(f"npm output: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    print(result.stdout, end="")


def get_auto_update_status(
    settings_path: Path | None = None,
) -> str:
    """Get the current auto-update status from settings.

    Reads ~/.claude/settings.json and checks if env.DISABLE_AUTOUPDATER
    is set to "1".

    Args:
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        "Disabled" if auto-update is disabled, "Enabled" otherwise.

    Raises:
        FileNotFoundError: If settings.json does not exist.
        ValueError: If settings.json is empty or contains invalid JSON.
        TypeError: If env key exists but is not a dictionary.
    """
    settings = read_settings(settings_path=settings_path)
    if settings.get("env", {}).get("DISABLE_AUTOUPDATER") == "1":
        return "Disabled"
    return "Enabled"


def get_installed_version(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> str:
    """Get the currently installed Claude Code version.

    Executes 'claude --version' and parses the output to extract
    the version number. Expected output format: "2.1.3 (Claude Code)"

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.

    Returns:
        Version string (e.g., "2.1.3").

    Raises:
        RuntimeError: If claude command fails or output cannot be parsed.
    """
    runner = run_command if run_command is not None else subprocess.run
    result = runner(
        ["claude", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to get Claude Code version. Exit code: {result.returncode}\n"
            f"stderr: {result.stderr.strip() if result.stderr else '(none)'}"
        )

    # Parse version from output like "2.1.3 (Claude Code)"
    output = result.stdout.strip()
    if not output:
        raise RuntimeError("Claude version command returned empty output.")

    # Extract version number (first space-separated token)
    version = output.split()[0]
    return version


def get_available_versions(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> list[str]:
    """Fetch all available Claude Code versions from npm registry.

    Queries the npm registry for @anthropic-ai/claude-code package and
    returns the complete list of available versions for validation and
    installation purposes.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.

    Returns:
        List of version strings sorted by npm (oldest to newest).

    Raises:
        RuntimeError: If npm command fails or output cannot be parsed.
    """
    runner = run_command if run_command is not None else subprocess.run
    result = runner(
        ["npm", "view", "@anthropic-ai/claude-code", "versions", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to fetch versions from npm. Exit code: {result.returncode}\n"
            f"npm output: {result.stderr.strip() if result.stderr else '(none)'}"
        )

    try:
        versions = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse npm JSON output: {e}") from e

    if not isinstance(versions, list) or not versions:
        raise RuntimeError("npm returned empty or invalid versions list.")

    return [str(v) for v in versions]


def get_latest_version(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> str:
    """Get the latest available Claude Code version from npm.

    Fetches the complete version list and returns the last element,
    which represents the most recent release.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Passed through to
            get_available_versions().

    Returns:
        Latest version string (e.g., "2.1.6").

    Raises:
        RuntimeError: If npm command fails or output cannot be parsed.
    """
    versions = get_available_versions(run_command=run_command)
    return versions[-1]


def validate_version(
    version: str,
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> bool:
    """Validate that a version string exists in available npm versions.

    Checks the requested version against the list of versions available
    in the npm registry for @anthropic-ai/claude-code package.

    Args:
        version: Version string to validate (e.g., "2.0.58").
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Passed through to
            get_available_versions().

    Returns:
        True if version exists in available versions, False otherwise.

    Raises:
        RuntimeError: If npm command fails during version fetch.
    """
    available_versions = get_available_versions(run_command=run_command)
    return version in available_versions


def install_version(
    version: str,
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    settings_path: Path | None = None,
) -> None:
    """Install a specific Claude Code version.

    Orchestrates npm commands to install the specified version: uninstalls
    current version, cleans npm cache, installs target version, and verifies
    installation success.

    Args:
        version: Version string to install (e.g., "2.0.58").
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Must accept same
            signature as subprocess.run.
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json. Currently unused but accepted for
            interface consistency with other command functions.

    Returns:
        None

    Raises:
        SystemExit: If version validation fails or any npm command fails.
    """
    # settings_path is accepted for interface consistency but not used directly
    # by this function (it doesn't modify settings)
    _ = settings_path

    runner = run_command if run_command is not None else subprocess.run

    # Validate version exists before attempting installation
    print(f"Validating version {version}...")
    try:
        if not validate_version(version, run_command=run_command):
            print(
                f"Error: Version '{version}' not found.\nUse --list to see available versions.",
                file=sys.stderr,
            )
            sys.exit(1)
    except RuntimeError as e:
        print(f"Error validating version: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Uninstall current version
    print("Uninstalling current Claude Code version...")
    result = runner(
        ["npm", "uninstall", "-g", "@anthropic-ai/claude-code"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Error: npm uninstall failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
        if result.stderr:
            print(f"npm output: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Clean npm cache
    print("Cleaning npm cache...")
    result = runner(
        ["npm", "cache", "clean", "--force"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Error: npm cache clean failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
        if result.stderr:
            print(f"npm output: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Install specified version
    print(f"Installing Claude Code version {version}...")
    result = runner(
        ["npm", "install", "-g", f"@anthropic-ai/claude-code@{version}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Error: npm install failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
        if result.stderr:
            print(f"npm output: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Step 4: Verify installation
    print("Verifying installation...")
    try:
        installed = get_installed_version(run_command=run_command)
        if installed == version:
            print(f"Successfully installed Claude Code version {version}.")
        else:
            print(
                f"Warning: Requested version {version}, but {installed} is installed.",
                file=sys.stderr,
            )
            sys.exit(1)
    except RuntimeError as e:
        print(f"Error verifying installation: {e}", file=sys.stderr)
        sys.exit(1)


def reset_to_defaults(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    settings_path: Path | None = None,
) -> None:
    """Reset Claude Code to Anthropic-intended default state.

    Performs two operations in sequence:
    1. Enables auto-updates by removing env.DISABLE_AUTOUPDATER from settings
    2. Installs the latest available version

    This restores the system to the state Anthropic intends for normal operation.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Passed through to
            get_latest_version() and install_version().
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        None

    Raises:
        SystemExit: If any operation fails.
    """
    # Step 1: Enable auto-updates
    print("Enabling auto-updates...")
    try:
        settings = read_settings(settings_path=settings_path)

        # Only modify if auto-update is currently disabled
        if settings.get("env", {}).get("DISABLE_AUTOUPDATER") == "1":
            del settings["env"]["DISABLE_AUTOUPDATER"]
            if not settings["env"]:
                del settings["env"]
            write_settings(settings, settings_path=settings_path)
            print("Auto-update enabled.")
        else:
            print("Auto-update is already enabled.")

    except (FileNotFoundError, ValueError, TypeError) as e:
        print(f"Error enabling auto-update: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Install latest version
    print("Installing latest version...")
    try:
        latest = get_latest_version(run_command=run_command)
        print(f"Latest version is {latest}.")
    except RuntimeError as e:
        print(f"Error getting latest version: {e}", file=sys.stderr)
        sys.exit(1)

    install_version(latest, run_command=run_command, settings_path=settings_path)
    print("Reset to defaults complete.")


def show_status(
    run_command: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    settings_path: Path | None = None,
) -> None:
    """Display current Claude Code installation status.

    Shows auto-updater state, installed version, and latest available
    version in a clear, readable format.

    Args:
        run_command: Optional command execution function for testing. If None,
            uses subprocess.run with default settings. Passed through to
            get_installed_version() and get_latest_version().
        settings_path: Optional path to settings file for testing. If None,
            uses ~/.claude/settings.json.

    Returns:
        None

    Raises:
        SystemExit: If any status check fails, exits with code 1.
    """
    try:
        auto_update_status = get_auto_update_status(settings_path=settings_path)
    except (FileNotFoundError, ValueError, TypeError) as e:
        print(f"Error checking auto-update status: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        installed_version = get_installed_version(run_command=run_command)
    except RuntimeError as e:
        print(f"Error getting installed version: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        latest_version = get_latest_version(run_command=run_command)
    except RuntimeError as e:
        print(f"Error getting latest version: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Auto-update: {auto_update_status}")
    print(f"Installed version: {installed_version}")
    print(f"Latest version: {latest_version}")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.

    Builds an ArgumentParser with mutually exclusive command flags for
    all supported operations. Only one command may be specified per
    invocation.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Manage Claude Code version installation and auto-update settings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    commands = parser.add_mutually_exclusive_group(required=True)

    commands.add_argument(
        "--disable-auto-update",
        action="store_true",
        help='Set env.DISABLE_AUTOUPDATER to "1" in ~/.claude/settings.json',
    )

    commands.add_argument(
        "--enable-auto-update",
        action="store_true",
        help="Remove env.DISABLE_AUTOUPDATER from ~/.claude/settings.json",
    )

    commands.add_argument(
        "--list",
        action="store_true",
        dest="list_versions",
        help="List available Claude Code versions from npm registry (human-readable output)",
    )

    commands.add_argument(
        "--status",
        action="store_true",
        help="Show auto-updater state, currently installed version, and latest available version",
    )

    commands.add_argument(
        "--install",
        metavar="VERSION",
        help="Install specific Claude Code version (validates against available versions first)",
    )

    commands.add_argument(
        "--reset",
        action="store_true",
        help="Restore defaults: enable auto-update and install latest version",
    )

    return parser


def main() -> int:
    """Main entry point for the cc_version CLI.

    Validates prerequisites, parses command-line arguments, and dispatches
    to the appropriate handler function based on the selected command.

    Returns:
        Exit code (0 for success, 1 for any error).
    """
    if not validate_prerequisites():
        return 1

    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.disable_auto_update:
            disable_auto_update()
        elif args.enable_auto_update:
            enable_auto_update()
        elif args.list_versions:
            list_versions()
        elif args.status:
            show_status()
        elif args.install:
            install_version(args.install)
        elif args.reset:
            reset_to_defaults()
    except (FileNotFoundError, ValueError, TypeError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
