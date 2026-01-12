#!/usr/bin/env python
"""Workscope-Dev Runner (wsd.py) - Unified task runner for all Workscope-Dev projects.

This script provides a consistent command-line interface across Python, TypeScript,
JavaScript, and mixed-language projects. Commands like `ws test`, `ws lint`, and
`ws format` work identically regardless of the underlying technology stack, with
the runner transparently mapping to appropriate tools.

Core Philosophy:
- Command homogenization: Same commands work everywhere
- Project type auto-detection: No manual configuration needed
- Universal coverage: 29 commands covering common development tasks
- Workscope-Dev integration: Core workflow commands always available

Usage:
    ./wsd.py <command> [args...]
    python wsd.py <command> [args...]

Script-Level Flags:
    --help, -h      Display all available commands and exit
    --version, -V   Display WSD version and exit

Examples:
    ./wsd.py test           # Runs pytest or jest based on project type
    ./wsd.py lint           # Runs ruff or eslint based on project type
    ./wsd.py health         # Runs Workscope-Dev health check
    ./wsd.py health:clean   # Health check with fresh cache (deterministic)
    ./wsd.py                # Shows all available commands
    ./wsd.py --version      # Shows WSD version

For shell convenience, create an alias:
    alias wsd='./wsd.py'
"""

import datetime
import errno
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn


# Import language detection utilities from scripts directory
_scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(_scripts_dir))
from wsd_utils import (  # noqa: E402
    WsdCollectionError,
    _is_binary_file,
    calculate_file_hash,
    collect_wsd_files,
    detect_package_manager,
    detect_project_languages,
)


# Configure logging for tag preservation warnings and verbose output
logger = logging.getLogger(__name__)

# Global verbose flag for detailed operation logging
_verbose_mode = False


def set_verbose_mode(enabled: bool) -> None:
    """Enable or disable verbose output mode.

    When verbose mode is enabled, detailed operation logging is printed
    to stderr to help users troubleshoot installation and update issues.

    Args:
        enabled: True to enable verbose output, False to disable
    """
    global _verbose_mode  # noqa: PLW0603
    _verbose_mode = enabled
    if enabled:
        # Configure logging to show INFO level messages
        logging.basicConfig(
            level=logging.INFO,
            format="[VERBOSE] %(message)s",
            stream=sys.stderr,
        )


def verbose_log(message: str) -> None:
    """Log a message if verbose mode is enabled.

    Prints detailed operation information to stderr when verbose mode
    is active. Messages are prefixed with [VERBOSE] for easy filtering.

    Args:
        message: The message to log
    """
    if _verbose_mode:
        print(f"[VERBOSE] {message}", file=sys.stderr)


# Type alias for command structures
Command = list[str] | list[list[str]]


def cmd(*args: str) -> list[str]:
    """Build a command array from arguments.

    Args:
        *args: Command components as strings

    Returns:
        list[str]: Command array suitable for subprocess.run()
    """
    return list(args)


def lang_cmd(python_cmd: list[str], node_cmd: list[str]) -> list[str]:
    """Return appropriate command based on detected project type.

    This function enables command homogenization by selecting the
    language-appropriate implementation at runtime. Uses detect_project_languages()
    internally, prioritizing Node.js languages when multiple languages detected.

    Args:
        python_cmd: Command to use for Python projects.
        node_cmd: Command to use for Node.js projects (TypeScript and JavaScript).

    Returns:
        Command array for the detected project type, or warning message if no
        languages detected. Node.js languages take priority in multi-language projects.
    """
    languages = detect_project_languages()

    # Node.js languages (TypeScript/JavaScript) take priority in multi-language projects
    if "typescript" in languages or "javascript" in languages:
        return node_cmd
    if "python" in languages:
        return python_cmd
    # No languages detected - return helpful warning
    warning = "⚠️  No languages detected. Add pyproject.toml or package.json to enable task runner."
    return cmd("echo", warning)


def multi_lang_cmd(
    python_cmd: list[str] | None = None, node_cmd: list[str] | None = None
) -> list[list[str]]:
    """Return commands for all detected project languages.

    This function enables multi-language command execution by returning
    commands for each detected language in the project. Commands execute
    sequentially (Python first, then Node.js) with fail-fast behavior.

    Args:
        python_cmd: Command to use for Python. None to skip Python even if detected.
        node_cmd: Command to use for Node.js projects (TypeScript and JavaScript).
                  None to skip Node.js languages even if detected.

    Returns:
        List of command arrays, one per detected language. Returns warning command
        if no languages detected or all language commands are None. Empty list never
        returned - always at least one command (may be warning message).
    """
    languages = detect_project_languages()
    commands = []

    # Build commands for detected languages (Python first, then Node.js)
    if "python" in languages and python_cmd is not None:
        commands.append(python_cmd)

    # Both TypeScript and JavaScript use the same Node.js tooling
    if ("typescript" in languages or "javascript" in languages) and node_cmd is not None:
        commands.append(node_cmd)

    # No valid commands - return warning
    if not commands:
        warning = (
            "⚠️  No languages detected. Add pyproject.toml or package.json to enable task runner."
        )
        commands.append(cmd("echo", warning))

    return commands


def execute_multi_lang_task(
    _task_name: str, commands: list[list[str]], extra_args: list[str]
) -> int:
    """Execute commands for multiple languages sequentially with fail-fast behavior.

    Validates that all command components are strings before execution. If any
    command contains None (indicating a missing package manager), prints an error
    with installation instructions and returns exit code 1.

    Args:
        _task_name: Name of the task being executed (reserved for future use)
        commands: List of commands to execute (one per language)
        extra_args: Additional arguments to forward to each command

    Returns:
        int: Exit code - 0 for success, 1 for missing package manager,
            or non-zero from first failing command
    """
    for command in commands:
        # Validate command components - check for None values indicating
        # a missing package manager (PKG_MANAGER is None for Node.js projects
        # without a lock file)
        if any(arg is None for arg in command):
            _exit_missing_package_manager()

        # Build complete command with extra arguments
        full_command = command + extra_args

        # Run the command
        print(f"🚀 Running: {' '.join(full_command)}")
        print("-" * 70)
        result = subprocess.run(full_command, check=False)

        # Fail-fast: return immediately on first failure
        if result.returncode != 0:
            return result.returncode

    # All commands succeeded
    return 0


def get_check_dirs() -> list[str]:
    """Read check directories from pyproject.toml [tool.wsd] configuration.

    Lazy-loaded only when config-dependent commands (lint, format, type, security)
    are executed. Uses tomllib (Python 3.11+) or tomli fallback for parsing.

    Returns:
        List of directory paths to check (e.g., ["src", "tests"]). Can be empty list.

    Raises:
        SystemExit: With code 1 if pyproject.toml or [tool.wsd] configuration is missing
            or if check_dirs is not a list type.
    """
    # Lazy import - only load when config needed
    try:
        import tomllib  # type: ignore[import-not-found]  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # noqa: PLC0415

    pyproject_path = Path("pyproject.toml")

    # Validate pyproject.toml exists
    if not pyproject_path.exists():
        print("❌ ERROR: pyproject.toml not found in project root.", file=sys.stderr)
        print(
            "\nWorkscope-Dev requires pyproject.toml with [tool.wsd] configuration.",
            file=sys.stderr,
        )
        print("\nAdd this to your pyproject.toml:", file=sys.stderr)
        print("\n[tool.wsd]", file=sys.stderr)
        print('check_dirs = ["src", "tests"]', file=sys.stderr)
        sys.exit(1)

    # Parse TOML file
    try:
        with pyproject_path.open("rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse pyproject.toml: {e}", file=sys.stderr)
        print("\nEnsure your pyproject.toml is valid TOML format.", file=sys.stderr)
        sys.exit(1)

    # Extract [tool.wsd] configuration
    wsd_config = config.get("tool", {}).get("wsd", {})

    # Validate configuration exists
    if not wsd_config or "check_dirs" not in wsd_config:
        print(
            "❌ ERROR: [tool.wsd] configuration missing or incomplete in pyproject.toml.",
            file=sys.stderr,
        )
        print("\nAdd this to your pyproject.toml:", file=sys.stderr)
        print("\n[tool.wsd]", file=sys.stderr)
        print('check_dirs = ["src", "tests"]', file=sys.stderr)
        print("\nFor config-dependent commands (lint, format, type, security).", file=sys.stderr)
        sys.exit(1)

    # Validate check_dirs type
    check_dirs = wsd_config["check_dirs"]
    if not isinstance(check_dirs, list):
        print("❌ ERROR: check_dirs must be a list in pyproject.toml", file=sys.stderr)
        print('\nExample: check_dirs = ["src", "tests"]', file=sys.stderr)
        sys.exit(1)
    return check_dirs


# Detect project context
PROJECT_LANGUAGES = detect_project_languages()
# Detect package manager for Node.js projects (both TypeScript and JavaScript)
PKG_MANAGER = (
    detect_package_manager()
    if ("typescript" in PROJECT_LANGUAGES or "javascript" in PROJECT_LANGUAGES)
    else None
)

# Commands that require [tool.wsd] configuration
CONFIG_DEPENDENT_COMMANDS = {
    "lint",
    "lint:fix",
    "lint:aggressive",
    "lint:docs",
    "lint:docs:fix",
    "format",
    "format:check",
    "type",
    "security",
}


def _exit_missing_package_manager() -> NoReturn:
    """Print error message and exit when no Node.js package manager is detected.

    Called when PKG_MANAGER is None but a Node.js command is required.
    Provides clear instructions for installing a package manager and creating
    a lock file, following Design Decision 1 (Explicit Configuration Over
    Implicit Defaults).

    Raises:
        SystemExit: Always exits with code 1.
    """
    print("❌ ERROR: No Node.js package manager detected.", file=sys.stderr)
    print(file=sys.stderr)
    print("WSD requires a package manager lock file to run Node.js commands.", file=sys.stderr)
    print(
        "Create one by running your preferred package manager's install command:", file=sys.stderr
    )
    print(file=sys.stderr)
    print("  pnpm install  → creates pnpm-lock.yaml", file=sys.stderr)
    print("  npm install   → creates package-lock.json", file=sys.stderr)
    print("  yarn install  → creates yarn.lock", file=sys.stderr)
    print("  bun install   → creates bun.lockb", file=sys.stderr)
    sys.exit(1)


def build_config_command(task_name: str) -> list[list[str]]:
    """Build command for config-dependent tasks that require check_dirs.

    This function implements lazy loading by calling get_check_dirs() only when
    a config-dependent command is actually being executed, not at module import time.
    Supports multi-language projects by building commands for all detected languages.

    Args:
        task_name: Name of the config-dependent task (lint, format, type, security, etc.)

    Returns:
        List of command arrays to execute, one per detected language. For single-language
        projects returns single-item list. For multi-language projects returns multiple
        commands to execute sequentially.
    """
    # Lazy-load configuration only when needed
    check_dirs = get_check_dirs()
    # Append trailing slash for directory arguments (e.g., "src" -> "src/")
    dir_args = [f"{d}/" for d in check_dirs]

    def node_script(script: str) -> list[str]:
        """Build Node.js command using detected package manager.

        Uses the PKG_MANAGER global (pnpm/npm/yarn/bun) detected from lock files.
        If no package manager is detected (PKG_MANAGER is None), prints an error
        with installation instructions and exits with code 1.

        Args:
            script: npm script name to execute (e.g., "lint", "test", "build")

        Returns:
            Command array like ["pnpm", "run", "lint"]

        Raises:
            SystemExit: With code 1 if no package manager is detected.
        """
        if PKG_MANAGER is None:
            _exit_missing_package_manager()
        return cmd(PKG_MANAGER, "run", script)

    def node_audit_cmd() -> list[str]:
        """Build Node.js audit command using detected package manager.

        Security audit commands differ slightly between package managers but all
        support the "audit" subcommand. If no package manager is detected
        (PKG_MANAGER is None), prints an error with installation instructions
        and exits with code 1.

        Returns:
            Audit command array like ["pnpm", "audit"]

        Raises:
            SystemExit: With code 1 if no package manager is detected.
        """
        if PKG_MANAGER is None:
            _exit_missing_package_manager()
        return cmd(PKG_MANAGER, "audit")

    # Command mapping - reduces function complexity (PLR0911)
    command_map: dict[str, list[list[str]]] = {
        "lint": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "check", *dir_args),
            node_cmd=node_script("lint"),
        ),
        "lint:fix": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "check", "--fix", *dir_args),
            node_cmd=node_script("lint:fix"),
        ),
        "lint:aggressive": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "check", "--fix", "--unsafe-fixes", *dir_args),
            node_cmd=node_script("lint:aggressive"),
        ),
        "lint:docs": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "check", "--select", "D", *dir_args),
            node_cmd=None,
        ),
        "lint:docs:fix": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "check", "--select", "D", "--fix", *dir_args),
            node_cmd=None,
        ),
        "format": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "format", *dir_args),
            node_cmd=node_script("format"),
        ),
        "format:check": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "ruff", "format", "--check", *dir_args),
            node_cmd=node_script("format:check"),
        ),
        "type": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "mypy", *dir_args),
            node_cmd=node_script("typecheck"),
        ),
        "security": multi_lang_cmd(
            python_cmd=cmd("uv", "run", "bandit", "-r", *dir_args, "-f", "screen", "-ll"),
            node_cmd=node_audit_cmd(),
        ),
    }

    # Return command from map or error if not found
    return command_map.get(
        task_name, [cmd("echo", f"ERROR: Unknown config-dependent command '{task_name}'")]
    )


# Task definitions with command homogenization
TASKS: dict[str, Command] = {
    # === WORKSCOPE-DEV CORE COMMANDS ===
    # These commands are fundamental to the Workscope-Dev workflow
    # and are always available regardless of project type
    "prompt": cmd("uv", "run", "python", "scripts/new_prompt.py"),
    "health": multi_lang_cmd(
        python_cmd=cmd("uv", "run", "python", "scripts/health_check.py"),
        node_cmd=cmd("node", "scripts/health_check.js"),
    ),
    "health:aggressive": multi_lang_cmd(
        python_cmd=cmd("uv", "run", "python", "scripts/health_check.py", "--aggressive"),
        node_cmd=cmd("node", "scripts/health_check.js", "--aggressive"),
    ),
    "health:clean": multi_lang_cmd(
        python_cmd=cmd("uv", "run", "python", "scripts/health_check.py", "--clean"),
        node_cmd=cmd("node", "scripts/health_check.js", "--clean"),
    ),
    "archive": cmd("uv", "run", "python", "scripts/archive_claude_sessions.py"),
    "docs:update": cmd("uv", "run", "python", "scripts/update_docs.py"),
    "docs:full": cmd("uv", "run", "python", "scripts/update_docs.py", "--full"),
    # === UNIVERSAL DEVELOPMENT COMMANDS ===
    # These commands adapt automatically to your project type
    # Use the same commands in Python, TypeScript, or mixed projects
    # Testing & Quality Assurance
    "test": multi_lang_cmd(
        python_cmd=cmd("uv", "run", "pytest"),
        node_cmd=cmd(PKG_MANAGER, "test"),  # type: ignore[arg-type]
    ),
    "test:watch": lang_cmd(
        cmd("uv", "run", "pytest-watch"),
        cmd(PKG_MANAGER, "run", "test:watch"),  # type: ignore[arg-type]
    ),
    "test:coverage": lang_cmd(
        cmd("uv", "run", "pytest", "--cov", "--cov-report=html"),
        cmd(PKG_MANAGER, "run", "test:coverage"),  # type: ignore[arg-type]
    ),
    "validate": lang_cmd(
        cmd("bash", "-c", "./wsd.py lint && ./wsd.py type && ./wsd.py format:check"),
        cmd(PKG_MANAGER, "run", "validate"),  # type: ignore[arg-type]
    ),
    # Build & Development
    "build": multi_lang_cmd(
        python_cmd=cmd("uv", "build"),
        node_cmd=cmd(PKG_MANAGER, "run", "build"),  # type: ignore[arg-type]
    ),
    "dev": lang_cmd(
        cmd("uv", "run", "python", "-m", "uvicorn", "app.main:app", "--reload"),
        cmd(PKG_MANAGER, "run", "dev"),  # type: ignore[arg-type]
    ),
    "serve": lang_cmd(
        cmd("uv", "run", "python", "-m", "http.server", "8000"),
        cmd(PKG_MANAGER, "run", "serve"),  # type: ignore[arg-type]
    ),
    "watch": lang_cmd(
        cmd("uv", "run", "watchmedo", "shell-command", "-R", "-p", "*.py", "-c", "pytest"),
        cmd(PKG_MANAGER, "run", "watch"),  # type: ignore[arg-type]
    ),
    "clean": lang_cmd(
        cmd(
            "rm",
            "-rf",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "*.egg-info",
        ),
        cmd("rm", "-rf", "node_modules", "dist", ".next", ".vite", "build"),
    ),
    # Dependencies & Security
    "sync": multi_lang_cmd(
        python_cmd=cmd("uv", "sync"),
        node_cmd=cmd(PKG_MANAGER, "install"),  # type: ignore[arg-type]
    ),
    "audit": lang_cmd(
        cmd("uv", "run", "pip-audit"),
        cmd(PKG_MANAGER, "audit"),  # type: ignore[arg-type]
    ),
    "audit:fix": lang_cmd(
        cmd("uv", "run", "pip-audit", "--fix"),
        cmd(PKG_MANAGER, "audit", "fix"),  # type: ignore[arg-type]
    ),
}


def _display_commands(task_name: str, commands: list[list[str]]) -> None:
    """Display one or more commands for a task.

    Args:
        task_name: Name of the task
        commands: List of command lists to display
    """
    if len(commands) > 1:
        # Multi-language: show all commands
        for i, cmd in enumerate(commands):
            cmd_str = " ".join(cmd)
            if i == 0:
                print(f"  {task_name:<20} → {cmd_str}")
            else:
                print(f"  {'':<20}   {cmd_str}")
    else:
        # Single language or error: show one command
        cmd_str = " ".join(commands[0]) if commands else "[no command]"
        print(f"  {task_name:<20} → {cmd_str}")


def _display_task_command(task_name: str) -> None:
    """Display command for a single task.

    Args:
        task_name: Name of the task to display
    """
    if task_name == "install":
        # Special install command with flags
        print(f"  {task_name:<20} → wsd.py install [--dry-run] [--force] <target-path>")
    elif task_name == "update":
        # Special update command with flags
        print(f"  {task_name:<20} → wsd.py update [--dry-run] <target-path>")
    elif task_name in CONFIG_DEPENDENT_COMMANDS:
        # Build config command for display (may fail if config missing)
        try:
            commands = build_config_command(task_name)
            _display_commands(task_name, commands)
        except SystemExit:
            # Config missing - show placeholder
            print(f"  {task_name:<20} → [requires [tool.wsd] configuration]")
    elif task_name in TASKS:
        command = TASKS[task_name]
        # Check if multi-language command (list of lists)
        if command and len(command) > 0 and isinstance(command[0], list):
            # Show ALL commands from multi-language list
            multi_cmd: list[list[str]] = command  # type: ignore[assignment]
            _display_commands(task_name, multi_cmd)
        else:
            # Single command
            single_cmd: list[str] = command  # type: ignore[assignment]
            _display_commands(task_name, [single_cmd])


def show_help() -> None:
    """Display all available tasks with their commands.

    Organized by category for easy discovery. Shows the actual
    command that will be executed for the current project type.

    For multi-language projects, displays all language-specific commands
    to show users exactly what will run for each detected language.
    """
    print("Workscope-Dev Runner - Available Commands")
    if PROJECT_LANGUAGES:
        lang_str = ", ".join(sorted(PROJECT_LANGUAGES)).upper()
        print(f"Project Languages: {lang_str}")
    else:
        print("Project Languages: NONE DETECTED")
    if ("typescript" in PROJECT_LANGUAGES or "javascript" in PROJECT_LANGUAGES) and PKG_MANAGER:
        print(f"Package Manager: {PKG_MANAGER}")
    print("=" * 70)
    print()

    categories = {
        "Workscope-Dev Core": [
            "install",
            "update",
            "prompt",
            "health",
            "health:aggressive",
            "health:clean",
            "archive",
            "docs:update",
            "docs:full",
        ],
        "Testing & Quality": [
            "test",
            "test:watch",
            "test:coverage",
            "lint",
            "lint:fix",
            "lint:aggressive",
            "lint:docs",
            "lint:docs:fix",
            "format",
            "format:check",
            "type",
            "validate",
            "security",
        ],
        "Build & Development": ["build", "dev", "serve", "watch", "clean"],
        "Dependencies & Security": ["sync", "audit", "audit:fix"],
    }

    for category, task_names in categories.items():
        print(f"{category}:")
        for task_name in task_names:
            _display_task_command(task_name)
        print()

    print("Usage:")
    print("  ./wsd.py <command> [args...]")
    print("  python wsd.py <command> [args...]")
    print()
    print("For convenience, create a shell alias:")
    print("  alias wsd='./wsd.py'")
    print()


def show_version() -> NoReturn:
    """Display WSD Runtime version and exit.

    Looks up version information from .wsd manifest (installed projects)
    or wsd.json metadata (source context). Prints version to stdout and
    exits with code 0 on success, exits with code 1 if neither file exists.

    The lookup hierarchy is:
    1. Check for .wsd manifest in the same directory as wsd.py
    2. Fall back to wsd.json in the same directory
    3. If neither exists, error and exit

    Raises:
        SystemExit: Always exits after displaying version or error
    """
    script_dir = Path(__file__).parent

    # Check for .wsd manifest (installed project)
    manifest_path = script_dir / ".wsd"
    if manifest_path.exists():
        manifest = read_manifest(manifest_path)
        print(manifest["version"])
        sys.exit(0)

    # Fall back to wsd.json (source context)
    wsd_json_path = script_dir / "wsd.json"
    if wsd_json_path.exists():
        metadata = read_wsd_metadata(script_dir)
        print(metadata.version)
        sys.exit(0)

    # Neither found - error condition
    print("Error: Cannot determine WSD version", file=sys.stderr)
    print("No .wsd manifest or wsd.json found", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Run the Workscope-Dev Runner.

    Parse command-line arguments, validate the requested task,
    and execute the appropriate command with argument forwarding.
    """
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    # Handle script-level flags before command routing
    if len(sys.argv) >= 2:
        flag = sys.argv[1]
        if flag in ("--help", "-h"):
            show_help()
            sys.exit(0)
        if flag in ("--version", "-V"):
            show_version()

    task_name = sys.argv[1]
    extra_args = sys.argv[2:]

    # Handle special install and update commands
    if task_name == "install":
        handle_install_command(extra_args)
        return

    if task_name == "update":
        handle_update_command(extra_args)
        return

    # Validate task exists (either in TASKS or in config-dependent commands)
    if task_name not in TASKS and task_name not in CONFIG_DEPENDENT_COMMANDS:
        print(f"Error: Unknown task '{task_name}'", file=sys.stderr)
        print("\nRun './wsd.py' with no arguments to see all available commands.", file=sys.stderr)
        print("\nDid you mean one of these?", file=sys.stderr)
        # Show a few similar command names as suggestions
        all_commands = set(TASKS.keys()).union(CONFIG_DEPENDENT_COMMANDS)
        similar = [cmd for cmd in sorted(all_commands) if task_name[:2] in cmd][:5]
        if similar:
            for suggestion in similar:
                print(f"  - {suggestion}", file=sys.stderr)
        sys.exit(1)

    # Build command - lazy load configuration for config-dependent commands
    if task_name in CONFIG_DEPENDENT_COMMANDS:
        commands = build_config_command(task_name)
        exit_code = execute_multi_lang_task(task_name, commands, extra_args)
        sys.exit(exit_code)

    # Get command from TASKS
    command = TASKS[task_name]

    # Check if this is a multi-language command (list of lists)
    if command and len(command) > 0 and isinstance(command[0], list):
        # Multi-language command - must be list[list[str]]
        assert all(isinstance(cmd, list) for cmd in command)  # Type narrowing
        multi_lang_command: list[list[str]] = command  # type: ignore[assignment]
        exit_code = execute_multi_lang_task(task_name, multi_lang_command, extra_args)
        sys.exit(exit_code)

    # Single command - must be list[str]
    assert isinstance(command, list)  # Type narrowing for mypy

    # Validate command components - check for None values indicating
    # a missing package manager (PKG_MANAGER is None for Node.js projects
    # without a lock file)
    if any(arg is None for arg in command):
        _exit_missing_package_manager()

    assert all(isinstance(x, str) for x in command)  # Type narrowing
    single_command: list[str] = command  # type: ignore[assignment]
    full_command = single_command + extra_args
    print(f"🚀 Running: {' '.join(full_command)}")
    print("-" * 70)
    result = subprocess.run(full_command, check=False)
    sys.exit(result.returncode)


# ==============================================================================
# WSD METADATA UTILITIES
# ==============================================================================


@dataclass
class WsdMetadata:
    r"""WSD Runtime metadata from wsd.json file.

    This class represents the parsed and validated metadata from a wsd.json file
    located at the WSD Runtime root. It contains version information, file protection
    policies, executable permission lists, installation exclusions, required directories,
    and content hashes.

    Attributes:
        version: Semantic version string (e.g., "1.0.0"). Must match pattern ^\d+\.\d+\.\d+$
        installation_only: Files excluded from installation. Relative paths from WSD Runtime root.
            Empty list if not specified in wsd.json.
        no_overwrite: Files protected from updates. Relative paths from WSD Runtime root.
            Empty list if not specified in wsd.json.
        executable: Files requiring +x permission. Relative paths from WSD Runtime root.
            Empty list if not specified in wsd.json.
        required_directories: Directories that must exist in installed projects. Relative paths
            from project root. These directories will be created during installation, and
            .wsdkeep placeholder files will be added to any that are empty. Empty list if not
            specified in wsd.json.
        file_hashes: SHA-256 content hashes for files in WSD Runtime. Dictionary mapping
            relative file paths to hash strings in format 'sha256:<hex_digest>'.
            Empty dict if not specified in wsd.json.
    """

    version: str
    installation_only: list[str]
    no_overwrite: list[str]
    executable: list[str]
    required_directories: list[str]
    file_hashes: dict[str, str]


def read_wsd_metadata(runtime_path: Path) -> WsdMetadata:
    """Read and validate WSD Runtime metadata from wsd.json file.

    Reads the wsd.json file at the specified WSD Runtime path, validates its structure
    and content, applies default values for optional fields, and validates that files
    referenced in no_overwrite and executable arrays exist.

    Note: Files in installation_only are NOT validated for existence because they may
    be generated at build time (e.g., __init__.py for PyPI packages) rather than
    existing in the source directory.

    Args:
        runtime_path: Path to WSD Runtime root directory containing wsd.json

    Returns:
        WsdMetadata: Parsed and validated metadata with all fields populated

    Raises:
        FileNotFoundError: If wsd.json does not exist at runtime_path
        json.JSONDecodeError: If wsd.json is not valid JSON
        ValueError: If wsd.json validation fails (missing required fields, invalid format,
            or files in no_overwrite/executable arrays don't exist)
    """
    wsd_json_path = runtime_path / "wsd.json"

    # Check if wsd.json exists
    if not wsd_json_path.exists():
        error_msg = f"wsd.json not found at {wsd_json_path}"
        raise FileNotFoundError(error_msg)

    # Read and parse JSON
    try:
        with wsd_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"wsd.json is not valid JSON: {e}"
        raise json.JSONDecodeError(error_msg, e.doc, e.pos) from e

    # Validate required fields
    if "version" not in data:
        error_msg = "wsd.json missing required field: version"
        raise ValueError(error_msg)

    version = data["version"]

    # Validate version format (semantic version: major.minor.patch)
    version_pattern = r"^\d+\.\d+\.\d+$"
    if not re.match(version_pattern, version):
        error_msg = (
            f"version field must match semantic version pattern (e.g., '1.0.0'), got: {version}"
        )
        raise ValueError(error_msg)

    # Apply defaults for optional fields
    installation_only = data.get("installation_only", [])
    no_overwrite = data.get("no_overwrite", [])
    executable = data.get("executable", [])
    required_directories = data.get("required_directories", [])
    file_hashes = data.get("file_hashes", {})

    # Validate array types
    if not isinstance(installation_only, list):
        error_msg = "installation_only must be an array"
        raise ValueError(error_msg)

    if not isinstance(no_overwrite, list):
        error_msg = "no_overwrite must be an array"
        raise ValueError(error_msg)

    if not isinstance(executable, list):
        error_msg = "executable must be an array"
        raise ValueError(error_msg)

    if not isinstance(required_directories, list):
        error_msg = "required_directories must be an array"
        raise ValueError(error_msg)

    if not isinstance(file_hashes, dict):
        error_msg = "file_hashes must be an object"
        raise ValueError(error_msg)

    # Validate file references exist in WSD Runtime
    # Note: installation_only is exempt because it may contain build-time generated files
    # that don't exist in the source directory but will be created during packaging
    fields_requiring_existence = {
        "no_overwrite": no_overwrite,
        "executable": executable,
    }

    for field_name, file_list in fields_requiring_existence.items():
        for file_path_str in file_list:
            file_path = runtime_path / file_path_str
            if not file_path.exists():
                error_msg = f"File referenced in {field_name} does not exist: {file_path_str}"
                raise ValueError(error_msg)

    return WsdMetadata(
        version=version,
        installation_only=installation_only,
        no_overwrite=no_overwrite,
        executable=executable,
        required_directories=required_directories,
        file_hashes=file_hashes,
    )


# ============================================================================
# WSD Manifest Utilities (.wsd file)
# ============================================================================


def read_manifest(path: Path) -> dict[str, Any]:
    """Read and parse WSD manifest from .wsd file.

    Reads the .wsd manifest file at the specified path, parses its JSON content,
    and returns the manifest data for validation and processing.

    Args:
        path: Path to .wsd manifest file

    Returns:
        Parsed manifest data as dictionary with keys: version, created, updated,
        files, tags

    Raises:
        FileNotFoundError: If .wsd manifest file doesn't exist at path
        json.JSONDecodeError: If .wsd manifest contains invalid JSON
        UnicodeDecodeError: If .wsd manifest is not UTF-8 encoded
    """
    # Check if manifest file exists
    if not path.exists():
        error_msg = f"Manifest file not found: {path}"
        raise FileNotFoundError(error_msg)

    # Read and parse JSON with UTF-8 encoding
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        error_msg = f"Manifest file contains invalid JSON: {e.msg}"
        raise json.JSONDecodeError(error_msg, e.doc, e.pos) from e
    except UnicodeDecodeError as e:
        error_msg = f"Manifest file is not UTF-8 encoded: {path}"
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, error_msg) from e


def validate_manifest(data: dict[str, Any]) -> bool:  # noqa: PLR0912, PLR0915
    """Validate WSD manifest structure and content.

    Performs comprehensive validation of manifest data including:
    - Required fields presence
    - Version format (semantic versioning)
    - Timestamp formats (ISO 8601)
    - Files array structure and constraints
    - Tags array structure and constraints
    - Referential integrity (tag files in files array)
    - Logical constraints (created <= updated)

    Note: Function complexity (21 branches, 64 statements) is justified by the
    comprehensive validation requirements of the WSD Manifest Schema. Each check
    validates a specific aspect of the manifest structure and provides clear
    error messages for debugging.

    Args:
        data: Manifest data dictionary to validate

    Returns:
        True if manifest is valid

    Raises:
        ValueError: If validation fails with specific error describing what's wrong
    """
    # Validate all required fields are present
    required_fields = ["version", "created", "updated", "files", "tags"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Manifest missing required field: {field}"
            raise ValueError(error_msg)

    # Validate version format (semantic version: major.minor.patch)
    version = data["version"]
    if not isinstance(version, str):
        error_msg = f"version must be a string, got: {type(version).__name__}"
        raise ValueError(error_msg)

    version_pattern = r"^\d+\.\d+\.\d+$"
    if not re.match(version_pattern, version):
        error_msg = f"version must match semantic version pattern (e.g., '1.0.0'), got: {version}"
        raise ValueError(error_msg)

    # Validate timestamp formats (ISO 8601)
    for timestamp_field in ["created", "updated"]:
        timestamp = data[timestamp_field]
        if not isinstance(timestamp, str):
            error_msg = f"{timestamp_field} must be a string, got: {type(timestamp).__name__}"
            raise ValueError(error_msg)

        # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
        iso8601_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        if not re.match(iso8601_pattern, timestamp):
            error_msg = (
                f"{timestamp_field} must be ISO 8601 format "
                f"(YYYY-MM-DDTHH:MM:SSZ), got: {timestamp}"
            )
            raise ValueError(error_msg)

    # Validate logical constraint: created <= updated
    created = data["created"]
    updated = data["updated"]
    if created > updated:
        error_msg = f"created timestamp ({created}) cannot be after updated timestamp ({updated})"
        raise ValueError(error_msg)

    # Validate files array
    files = data["files"]
    if not isinstance(files, list):
        error_msg = f"files must be an array, got: {type(files).__name__}"
        raise ValueError(error_msg)

    if len(files) == 0:
        error_msg = "files array cannot be empty (must have at least 1 item)"
        raise ValueError(error_msg)

    # Validate all files are strings
    for i, file_path in enumerate(files):
        if not isinstance(file_path, str):
            error_msg = f"files[{i}] must be a string, got: {type(file_path).__name__}"
            raise ValueError(error_msg)

    # Validate files are unique
    if len(files) != len(set(files)):
        error_msg = "files array must contain unique paths (duplicates found)"
        raise ValueError(error_msg)

    # Validate tags array
    tags = data["tags"]
    if not isinstance(tags, list):
        error_msg = f"tags must be an array, got: {type(tags).__name__}"
        raise ValueError(error_msg)

    # Validate each tag object structure
    for i, tag in enumerate(tags):
        if not isinstance(tag, dict):
            error_msg = f"tags[{i}] must be an object, got: {type(tag).__name__}"
            raise ValueError(error_msg)

        # Validate tag has exactly two fields: id and file
        if set(tag.keys()) != {"id", "file"}:
            error_msg = (
                f"tags[{i}] must have exactly two fields (id, file), got: {', '.join(tag.keys())}"
            )
            raise ValueError(error_msg)

        tag_id = tag["id"]
        tag_file = tag["file"]

        # Validate tag id is string
        if not isinstance(tag_id, str):
            error_msg = f"tags[{i}].id must be a string, got: {type(tag_id).__name__}"
            raise ValueError(error_msg)

        # Validate tag id matches kebab-case pattern
        tag_id_pattern = r"^[a-z0-9]([a-z0-9-]{1,48}[a-z0-9])?$"
        if not re.match(tag_id_pattern, tag_id):
            error_msg = (
                f"tags[{i}].id must match kebab-case pattern "
                f"(3-50 chars, lowercase alphanumeric with hyphens), got: {tag_id}"
            )
            raise ValueError(error_msg)

        # Validate tag file is string
        if not isinstance(tag_file, str):
            error_msg = f"tags[{i}].file must be a string, got: {type(tag_file).__name__}"
            raise ValueError(error_msg)

        # Validate referential integrity: tag file must exist in files array
        if tag_file not in files:
            error_msg = f"tags[{i}].file references '{tag_file}' which is not in files array"
            raise ValueError(error_msg)

    return True


def create_manifest(
    version: str,
    files: list[str],
    tags: list[dict[str, str]],
    created: str,
    updated: str,
) -> dict[str, Any]:
    """Create valid WSD manifest data structure.

    Constructs a manifest dictionary from provided components and validates
    the result before returning. This ensures all created manifests conform
    to the WSD Manifest Schema.

    Args:
        version: Semantic version string (e.g., "1.0.0")
        files: List of relative file paths managed by WSD
        tags: List of tag objects with 'id' and 'file' keys
        created: ISO 8601 timestamp of initial installation
        updated: ISO 8601 timestamp of most recent update

    Returns:
        Valid manifest dictionary with all required fields

    Raises:
        ValueError: If any inputs are invalid or resulting manifest fails validation
    """
    manifest = {
        "version": version,
        "created": created,
        "updated": updated,
        "files": files,
        "tags": tags,
    }

    # Validate the constructed manifest
    validate_manifest(manifest)

    return manifest


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    """Write WSD manifest to .wsd file with proper formatting.

    Writes manifest data to the specified path with UTF-8 encoding and
    proper JSON formatting (2-space indentation). Validates manifest before
    writing to ensure only valid manifests are written to disk.

    Args:
        manifest: Manifest data dictionary to write
        path: Path where .wsd manifest file should be written

    Raises:
        ValueError: If manifest is invalid and cannot be written
        OSError: If write operation fails (permissions, disk full, etc.)
    """
    # Validate manifest before writing
    validate_manifest(manifest)

    # Write manifest with UTF-8 encoding and proper formatting
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")  # Add trailing newline
    except OSError as e:
        error_msg = f"Failed to write manifest to {path}: {e}"
        raise OSError(error_msg) from e


@dataclass
class InstallationMode:
    """Installation mode information from update detection.

    This class represents the result of detecting whether the target directory
    requires a fresh installation or an update operation, along with extracted
    manifest data for update operations.

    Attributes:
        mode: Installation mode - "fresh" for new installation, "update" for existing installation
        manifest_data: Parsed manifest from target .wsd file. None for fresh installations.
        version: Version from installed manifest. None for fresh installations.
        files: List of file paths from installed manifest. None for fresh installations.
    """

    mode: str
    manifest_data: dict[str, Any] | None
    version: str | None
    files: list[str] | None


@dataclass
class RollbackPoint:
    """Rollback point for update operations.

    Captures the state before update operations begin to enable recovery
    if errors occur during file operations or manifest writing.

    Attributes:
        manifest_state: Complete manifest data before update operations.
        timestamp: ISO 8601 timestamp when rollback point created.
        vcs_commit_hash: Git commit hash if repository available, None otherwise.
        manifest_path: Path to .wsd manifest file for restoration.
    """

    manifest_state: dict[str, Any]
    timestamp: str
    vcs_commit_hash: str | None
    manifest_path: Path


def create_rollback_point(
    manifest_data: dict[str, Any],
    manifest_path: Path,
    target_dir: Path,
) -> RollbackPoint:
    """Create rollback point before update operations begin.

    Records current manifest state, timestamp, and VCS commit hash (if available)
    to enable recovery if update operations fail.

    Args:
        manifest_data: Current manifest data to preserve.
        manifest_path: Path to .wsd manifest file.
        target_dir: Path to target directory for VCS detection.

    Returns:
        RollbackPoint containing all information needed for recovery.
    """
    # Record current timestamp in ISO 8601 format
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Attempt to record VCS commit hash if available
    vcs_commit_hash = get_vcs_commit_hash(target_dir)

    return RollbackPoint(
        manifest_state=manifest_data,
        timestamp=timestamp,
        vcs_commit_hash=vcs_commit_hash,
        manifest_path=manifest_path,
    )


def get_vcs_commit_hash(directory: Path) -> str | None:
    """Attempt to get current VCS commit hash from directory.

    Checks if directory is a git repository and retrieves current commit hash.
    Returns None if not a git repository or git command fails.

    Args:
        directory: Path to directory to check for git repository.

    Returns:
        Commit hash string if git repository detected, None otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def restore_manifest_on_error(rollback_point: RollbackPoint) -> None:
    """Restore manifest to pre-update state after error.

    Writes the original manifest state back to disk and provides manual
    recovery instructions to the user including git checkout guidance.

    Args:
        rollback_point: Rollback point containing original manifest state.
    """
    # Restore manifest to pre-update state
    try:
        write_manifest(rollback_point.manifest_state, rollback_point.manifest_path)
    except OSError as e:
        # If we can't restore manifest, provide critical error message
        print(
            f"\n⚠️  CRITICAL: Failed to restore manifest after update error: {e}",
            file=sys.stderr,
        )
        print(
            "Manifest state may be inconsistent. Manual recovery required.",
            file=sys.stderr,
        )

    # Provide manual recovery instructions
    print("\n" + "=" * 60, file=sys.stderr)
    print("UPDATE ROLLBACK - MANUAL RECOVERY REQUIRED", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(
        f"\nUpdate operation failed at {rollback_point.timestamp}",
        file=sys.stderr,
    )
    print("Manifest has been restored to pre-update state.", file=sys.stderr)

    if rollback_point.vcs_commit_hash:
        print(
            f"\nYour repository was at commit: {rollback_point.vcs_commit_hash[:12]}",
            file=sys.stderr,
        )
        print("\nTo restore all WSD files to pre-update state:", file=sys.stderr)
        commit_hash = rollback_point.vcs_commit_hash[:12]
        print(
            f"  git checkout {commit_hash} -- .claude/ docs/ scripts/ dev/ wsd.py",
            file=sys.stderr,
        )
        print("\nOr restore entire working directory:", file=sys.stderr)
        print(f"  git reset --hard {rollback_point.vcs_commit_hash[:12]}", file=sys.stderr)
    else:
        print("\nTo restore WSD files to pre-update state:", file=sys.stderr)
        print("  git checkout HEAD -- .claude/ docs/ scripts/ dev/ wsd.py", file=sys.stderr)
        print("\nOr restore entire working directory:", file=sys.stderr)
        print("  git reset --hard HEAD", file=sys.stderr)
        print(
            "\nNote: VCS commit hash was not available at update time.",
            file=sys.stderr,
        )

    print("\nAfter restoring files, retry the update operation.", file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)


def detect_installation_mode(target_dir: Path) -> InstallationMode:
    """Detect whether target requires fresh install or update operation.

    Implements update detection logic from Update-System.md § Update Detection.
    Checks target directory existence, .wsd manifest presence, and extracts
    manifest data for update operations.

    Decision flow:
    1. If target directory does not exist → "fresh" mode
    2. If target exists but no .wsd manifest → "fresh" mode
    3. If target exists with valid .wsd manifest → "update" mode
       - Parses manifest using read_manifest()
       - Validates structure using validate_manifest()
       - Extracts version information
       - Extracts file metadata list

    Args:
        target_dir: Path to target installation directory

    Returns:
        InstallationMode object containing:
        - mode: "fresh" or "update"
        - manifest_data: Parsed manifest dict (None for fresh)
        - version: Installed version string (None for fresh)
        - files: List of installed file paths (None for fresh)

    Raises:
        json.JSONDecodeError: If manifest exists but contains invalid JSON
        ValueError: If manifest exists but fails validation
    """
    # Check if target directory exists
    if not target_dir.exists():
        return InstallationMode(
            mode="fresh",
            manifest_data=None,
            version=None,
            files=None,
        )

    # Check for .wsd manifest file indicating existing WSD installation
    manifest_path = target_dir / ".wsd"
    if not manifest_path.exists():
        return InstallationMode(
            mode="fresh",
            manifest_data=None,
            version=None,
            files=None,
        )

    # Manifest exists - parse and extract data for update operation
    manifest_data = read_manifest(manifest_path)

    # Validate manifest structure before extracting fields
    validate_manifest(manifest_data)

    # Extract version and files list (guaranteed present after validation)
    version = manifest_data["version"]
    files = manifest_data["files"]

    # Return update mode with extracted manifest data
    return InstallationMode(
        mode="update",
        manifest_data=manifest_data,
        version=version,
        files=files,
    )


# ==============================================================================
# VERSION COMPARISON UTILITIES
# ==============================================================================


@dataclass
class SemanticVersion:
    """Parsed semantic version components.

    This class represents a semantic version string parsed into its major,
    minor, and patch components for comparison operations.

    Attributes:
        major: Major version number (breaking changes)
        minor: Minor version number (backward-compatible features)
        patch: Patch version number (backward-compatible bug fixes)
        original: Original version string that was parsed
    """

    major: int
    minor: int
    patch: int
    original: str


def parse_semantic_version(version_str: str) -> SemanticVersion:
    """Parse semantic version string into components.

    Parses a semantic version string in major.minor.patch format into
    individual integer components for comparison operations.

    Args:
        version_str: Semantic version string (e.g., "1.2.3")

    Returns:
        SemanticVersion object with major, minor, patch components

    Raises:
        ValueError: If version string doesn't match semantic version pattern
            or if any component is not a valid positive integer
    """
    # Validate version pattern
    version_pattern = r"^\d+\.\d+\.\d+$"
    if not re.match(version_pattern, version_str):
        error_msg = (
            f"Version must match semantic version pattern (major.minor.patch), got: {version_str}"
        )
        raise ValueError(error_msg)

    # Split into components
    parts = version_str.split(".")

    # Parse components as integers
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
    except ValueError as e:
        error_msg = f"Version components must be valid integers: {version_str}"
        raise ValueError(error_msg) from e

    # Validate non-negative
    if major < 0 or minor < 0 or patch < 0:
        error_msg = f"Version components must be non-negative: {version_str}"
        raise ValueError(error_msg)

    return SemanticVersion(
        major=major,
        minor=minor,
        patch=patch,
        original=version_str,
    )


def compare_versions(version1: str, version2: str) -> str:
    """Compare two semantic version strings.

    Compares version strings to determine upgrade, downgrade, or same version
    relationships. Uses semantic versioning comparison rules (major > minor > patch).

    Args:
        version1: First version string to compare (e.g., "1.2.3")
        version2: Second version string to compare (e.g., "2.0.0")

    Returns:
        Comparison result:
        - "upgrade" if version2 > version1 (version2 is newer)
        - "downgrade" if version2 < version1 (version2 is older)
        - "same" if version2 == version1 (identical versions)

    Raises:
        ValueError: If either version string is invalid
    """
    # Parse both versions
    v1 = parse_semantic_version(version1)
    v2 = parse_semantic_version(version2)

    # Compare major, minor, and patch in order
    for v1_component, v2_component in [
        (v1.major, v2.major),
        (v1.minor, v2.minor),
        (v1.patch, v2.patch),
    ]:
        if v2_component > v1_component:
            return "upgrade"
        if v2_component < v1_component:
            return "downgrade"

    # All components equal
    return "same"


def check_version_compatibility(installed_version: str, update_version: str) -> bool:
    """Check if update version is compatible with installed version.

    Determines whether an update from installed_version to update_version is
    allowed based on version comparison rules. In v1, only upgrades and
    same-version reinstalls are compatible.

    Args:
        installed_version: Currently installed WSD version (e.g., "1.0.0")
        update_version: Version to update to (e.g., "1.1.0")

    Returns:
        True if update is compatible (upgrade or same version),
        False if incompatible (downgrade)

    Raises:
        ValueError: If either version string is invalid
    """
    comparison = compare_versions(installed_version, update_version)
    # Upgrades and same-version reinstalls are compatible, downgrades are not
    return comparison in ("upgrade", "same")


def format_downgrade_warning(installed_version: str, update_version: str) -> str:
    """Format warning message for downgrade attempts.

    Creates a comprehensive warning message explaining downgrade risks and
    requiring explicit user confirmation.

    Args:
        installed_version: Currently installed version (e.g., "1.1.0")
        update_version: Version attempting to downgrade to (e.g., "1.0.0")

    Returns:
        Formatted warning message with downgrade details and risks
    """
    warning = f"""
WARNING: Version Downgrade Detected
====================================

Installed Version: {installed_version}
Update Version:    {update_version}

This operation would downgrade your WSD installation to an older version.

Downgrade operations are not officially supported and may cause:
  - Loss of newer features and improvements
  - Incompatibility issues with existing customizations
  - Potential data loss in WORKSCOPE-DEV tags
  - Manifest inconsistencies

Recommendation: Use version control to revert specific files if needed,
rather than downgrading the entire WSD installation.
"""
    return warning.strip()


def confirm_downgrade(installed_version: str, update_version: str) -> bool:
    """Prompt user for explicit confirmation of downgrade operation.

    Displays downgrade warning and requires explicit user confirmation before
    proceeding with a downgrade operation.

    Args:
        installed_version: Currently installed version
        update_version: Version attempting to downgrade to

    Returns:
        True if user explicitly confirms downgrade, False otherwise
    """
    # Display warning
    warning = format_downgrade_warning(installed_version, update_version)
    print(warning, file=sys.stderr)
    print(file=sys.stderr)

    # Prompt for confirmation
    print("Proceed with downgrade? [y/N]: ", end="", file=sys.stderr)
    sys.stderr.flush()

    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Treat EOF or interrupt as "no"
        print(file=sys.stderr)
        return False

    # Only explicit "y" or "yes" confirms
    return response in ("y", "yes")


# ==============================================================================
# EDGE CASE DETECTION
# ==============================================================================


def detect_concurrent_update(manifest_path: Path) -> bool:
    """Detect if another update may be in progress based on manifest modification time.

    Checks if the .wsd manifest file was modified recently (< 5 minutes ago),
    which may indicate another update operation is running concurrently.

    Args:
        manifest_path: Path to .wsd manifest file

    Returns:
        True if manifest modified within last 5 minutes, False otherwise
    """
    if not manifest_path.exists():
        return False

    try:
        # Get manifest modification time
        mtime = manifest_path.stat().st_mtime

        # Get current time
        current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()

        # Check if modified within last 5 minutes (300 seconds)
        time_since_modification = current_time - mtime

        return time_since_modification < 300

    except OSError:
        # If we can't stat the file, assume no concurrent update
        return False


def warn_concurrent_update() -> None:
    """Display concurrent update warning to user.

    Warns that another update may be in progress based on recent manifest
    modification, and explains potential conflicts.
    """
    print("\nWarning: Another update may be in progress", file=sys.stderr)
    print("Evidence: .wsd file modified recently (< 5 minutes ago)", file=sys.stderr)
    print("Action: Ensure no other update operations are running.", file=sys.stderr)
    print("        Conflicts may occur with concurrent updates.", file=sys.stderr)
    print(file=sys.stderr)


def confirm_concurrent_update() -> bool:
    """Prompt user for confirmation to proceed with potentially concurrent update.

    Asks user whether to proceed with update despite evidence of recent
    manifest modification that may indicate concurrent update.

    Returns:
        True if user explicitly confirms proceeding, False otherwise
    """
    print("Proceed? [y/N]: ", end="", file=sys.stderr)
    sys.stderr.flush()

    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Treat EOF or interrupt as "no"
        print(file=sys.stderr)
        return False

    # Only explicit "y" or "yes" confirms
    return response in ("y", "yes")


def has_temp_update_files(target_dir: Path) -> bool:
    """Check for temporary update files in target directory.

    Scans for temporary files that may indicate an incomplete or interrupted
    update operation. This is an informational check only and does not block
    update operations.

    Args:
        target_dir: Path to target directory to scan for temp files

    Returns:
        True if any temporary update files are found, False otherwise.
    """
    temp_patterns = [
        ".wsd.tmp",
        ".wsd.bak",
        ".update-in-progress",
    ]

    for pattern in temp_patterns:
        temp_path = target_dir / pattern
        if temp_path.exists():
            return True

    return False


def warn_temp_update_files(target_dir: Path) -> None:
    """Display informational warning about temporary update files.

    Warns the user about the presence of temporary files that may indicate
    a previous incomplete update. This is informational only and does not
    block the current operation.

    Args:
        target_dir: Path to target directory containing temp files
    """
    print("\nNote: Temporary update files detected in target directory", file=sys.stderr)
    print(f"Location: {target_dir}", file=sys.stderr)
    print("These files may indicate a previous incomplete operation.", file=sys.stderr)
    print("The current update will proceed normally.", file=sys.stderr)
    print(file=sys.stderr)


def check_large_file(file_path: Path, threshold_mb: int = 100) -> tuple[bool, int]:
    """Check if file exceeds size threshold for special handling.

    Determines if a file is large enough to require streaming copy instead
    of loading into memory for tag preservation.

    Args:
        file_path: Path to file to check
        threshold_mb: Size threshold in megabytes (default: 100)

    Returns:
        Tuple of (is_large, size_mb) where is_large is True if file exceeds
        threshold, False otherwise, and size_mb is the file size in megabytes
    """
    if not file_path.exists():
        return (False, 0)

    try:
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        return (size_mb > threshold_mb, int(size_mb))

    except OSError:
        # If we can't stat the file, assume not large
        return (False, 0)


def warn_large_file(file_path: str, size_mb: int) -> None:
    """Display warning about large file being processed.

    Warns user that a large file may cause memory issues and explains
    that binary files will be copied without tag preservation.

    Args:
        file_path: Relative path to large file
        size_mb: File size in megabytes
    """
    print("\nWarning: Large file detected", file=sys.stderr)
    print(f"File: {file_path}", file=sys.stderr)
    print(f"Size: {size_mb} MB", file=sys.stderr)
    print("Action: Files over 100 MB may cause memory issues.", file=sys.stderr)
    print("        Binary files are copied without tag preservation.", file=sys.stderr)
    print(file=sys.stderr)


def confirm_large_file_processing() -> bool:
    """Prompt user for confirmation to process large file.

    Asks user whether to proceed with processing a large file that may
    cause memory issues.

    Returns:
        True if user explicitly confirms proceeding, False otherwise
    """
    print("Proceed? [y/N]: ", end="", file=sys.stderr)
    sys.stderr.flush()

    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Treat EOF or interrupt as "no"
        print(file=sys.stderr)
        return False

    # Only explicit "y" or "yes" confirms
    return response in ("y", "yes")


def is_binary_file(file_path: Path) -> bool:
    """Determine if file is binary by checking for null bytes in initial content.

    Reads first 8192 bytes and checks for null byte presence, which
    indicates binary file format.

    Args:
        file_path: Path to file to check

    Returns:
        True if file appears to be binary, False if appears to be text
    """
    if not file_path.exists():
        return False

    try:
        with file_path.open("rb") as f:
            # Read first 8KB
            chunk = f.read(8192)
            # Binary files contain null bytes
            return b"\x00" in chunk

    except OSError:
        # If we can't read the file, assume text (will fail later if truly problematic)
        return False


def streaming_copy_file(source_path: Path, dest_path: Path, chunk_size: int = 1024 * 1024) -> None:
    """Copy file using streaming to avoid loading entire file into memory.

    Uses chunk-based copying for large files to prevent memory exhaustion.

    Args:
        source_path: Path to source file
        dest_path: Path to destination file
        chunk_size: Size of chunks to copy in bytes (default: 1 MB)

    Raises:
        FileNotFoundError: If source file does not exist
        OSError: If copy operation fails
    """
    # Create parent directory if needed
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Stream copy in chunks
    with source_path.open("rb") as src, dest_path.open("wb") as dst:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            dst.write(chunk)


# ==============================================================================
# FILE COMPARISON AND CATEGORIZATION
# ==============================================================================


@dataclass
class FileCategorization:
    """Categorized file lists for update operations.

    This class holds the results of comparing installed files against update files,
    categorizing them into actions needed for the update operation (delete, add,
    update, or skip).

    Attributes:
        to_delete: Files to remove (installed - update). Files present in installed
            manifest but not in update source.
        to_add: Files to copy to target (update - installed). Files present in
            update source but not in installed manifest.
        to_update: Files to overwrite with preservation (installed ∩ update, content differs).
            Files present in both with different content that are not protected.
        to_skip: Files to preserve unchanged (installed ∩ update, protected by no_overwrite).
            Files present in both that are protected by no_overwrite policy.
        to_skip_unchanged: Files to preserve unchanged (installed ∩ update, content identical).
            Files present in both with identical content based on hash comparison.
    """

    to_delete: list[str]
    to_add: list[str]
    to_update: list[str]
    to_skip: list[str]
    to_skip_unchanged: list[str]


def check_file_writable(file_path: Path) -> bool:
    """Check if file is writable (not locked or read-only).

    Attempts to open file in append mode to verify write access without
    modifying content. Returns True if writable, False if locked or read-only.

    Args:
        file_path: Path to file to check

    Returns:
        True if file is writable, False otherwise
    """
    if not file_path.exists():
        # File doesn't exist, check parent directory
        return os.access(file_path.parent, os.W_OK)

    try:
        # Try to open in append mode (doesn't modify file)
        with file_path.open("a"):
            pass
        return True
    except (OSError, PermissionError):
        return False


def detect_file_locks(file_paths: list[str], base_dir: Path) -> list[str]:
    """Detect which files are locked or not writable.

    Checks each file for write access to identify files that would fail
    during update operations due to locks or permissions.

    Args:
        file_paths: List of relative file paths to check
        base_dir: Base directory for resolving relative paths

    Returns:
        List of relative paths for files that are locked or not writable
    """
    locked_files = []

    for relative_path in file_paths:
        full_path = base_dir / relative_path
        if not check_file_writable(full_path):
            locked_files.append(relative_path)

    return locked_files


def validate_update_preconditions(  # noqa: PLR0912, PLR0915
    categorization: FileCategorization,
    target_dir: Path,
    source_dir: Path,
) -> None:
    """Validate update preconditions before any filesystem modifications.

    Performs comprehensive pre-update validation as specified in
    Update-System.md § Pre-Update Validation Requirements:
    - Manifest validity (already validated during load)
    - File permissions for all operations
    - Sufficient disk space
    - File lock detection where possible

    Validation is atomic - all checks performed before any modifications.
    If any check fails, update aborts with clear error message and
    actionable recovery steps.

    Args:
        categorization: Categorized file lists from update comparison
        target_dir: Path to target directory (project root)
        source_dir: Path to WSD Runtime root directory (for disk space calculation)

    Raises:
        SystemExit: If validation fails (exits with code 1)
    """
    # Check write permissions for files to be deleted
    if categorization.to_delete:
        unwritable_deletes = []
        for relative_path in categorization.to_delete:
            file_path = target_dir / relative_path
            if file_path.exists() and not os.access(file_path, os.W_OK):
                unwritable_deletes.append(relative_path)

        if unwritable_deletes:
            error_msg = "Insufficient permissions for update"
            details = "The following files need to be deleted but are not writable:\n" + "\n".join(
                f"  - {f}" for f in unwritable_deletes[:5]
            )
            if len(unwritable_deletes) > 5:
                details += f"\n  ... and {len(unwritable_deletes) - 5} more"

            recovery_steps = [
                f"Grant write permissions: chmod u+w {' '.join(unwritable_deletes[:3])}",
                "Or run with appropriate privileges",
                "Then retry update",
            ]
            report_installation_error(error_msg, details, recovery_steps)

    # Check write permissions for files to be updated
    if categorization.to_update:
        unwritable_updates = []
        for relative_path in categorization.to_update:
            file_path = target_dir / relative_path
            if file_path.exists() and not os.access(file_path, os.W_OK):
                unwritable_updates.append(relative_path)

        if unwritable_updates:
            error_msg = "Insufficient permissions for update"
            details = "The following files need to be updated but are not writable:\n" + "\n".join(
                f"  - {f}" for f in unwritable_updates[:5]
            )
            if len(unwritable_updates) > 5:
                details += f"\n  ... and {len(unwritable_updates) - 5} more"

            recovery_steps = [
                f"Grant write permissions: chmod u+w {' '.join(unwritable_updates[:3])}",
                "Or run with appropriate privileges",
                "Then retry update",
            ]
            report_installation_error(error_msg, details, recovery_steps)

    # Check write permissions for manifest file
    manifest_path = target_dir / ".wsd"
    if manifest_path.exists() and not os.access(manifest_path, os.W_OK):
        error_msg = "Cannot update manifest file"
        details = f"Manifest file is not writable: {manifest_path}"
        recovery_steps = [
            f"Grant write permission: chmod u+w {manifest_path}",
            "Then retry update",
        ]
        report_installation_error(error_msg, details, recovery_steps)

    # Check write permissions for new directories
    if categorization.to_add:
        # Get unique parent directories for new files
        new_dirs = set()
        for relative_path in categorization.to_add:
            file_path = target_dir / relative_path
            parent = file_path.parent
            # Check each parent in hierarchy
            while parent != target_dir and not parent.exists():
                new_dirs.add(parent)
                parent = parent.parent

        # Check that we can create directories
        for directory in new_dirs:
            existing_parent = directory
            while not existing_parent.exists():
                existing_parent = existing_parent.parent

            if not os.access(existing_parent, os.W_OK):
                error_msg = "Insufficient permissions for update"
                details = f"Cannot create new directories under: {existing_parent}"
                recovery_steps = [
                    f"Grant write permission: chmod u+w {existing_parent}",
                    "Or run with appropriate privileges",
                    "Then retry update",
                ]
                report_installation_error(error_msg, details, recovery_steps)

    # Validate sufficient disk space
    try:
        # Calculate space needed for new and updated files
        required_bytes = 0

        # Add space for new files
        for relative_path in categorization.to_add:
            source_path = source_dir / relative_path
            if source_path.exists():
                required_bytes += source_path.stat().st_size

        # Add space for updated files (approximate - actual may be less after tag preservation)
        for relative_path in categorization.to_update:
            source_path = source_dir / relative_path
            if source_path.exists():
                required_bytes += source_path.stat().st_size

        # Check available space
        available_bytes = get_available_disk_space(target_dir)

        if available_bytes < required_bytes:
            required_mb = required_bytes / (1024 * 1024)
            available_mb = available_bytes / (1024 * 1024)
            shortfall_mb = (required_bytes - available_bytes) / (1024 * 1024)

            error_msg = "Insufficient disk space for update"
            details = (
                f"Required: {required_mb:.1f} MB\n"
                f"Available: {available_mb:.1f} MB\n"
                f"Shortfall: {shortfall_mb:.1f} MB"
            )
            recovery_steps = [
                f"Free up at least {shortfall_mb:.1f} MB of disk space",
                "Then retry update",
            ]
            report_installation_error(error_msg, details, recovery_steps)

    except OSError:
        # If we can't check disk space, log warning but don't block
        # Actual operations will fail if space is truly insufficient
        print(
            "Warning: Unable to verify disk space availability",
            file=sys.stderr,
        )

    # Detect file locks
    files_to_check = categorization.to_delete + categorization.to_update
    if files_to_check:
        locked_files = detect_file_locks(files_to_check, target_dir)

        if locked_files:
            # Warning only - file locks may be transient
            print("Warning: Some files may be locked by other processes:", file=sys.stderr)
            for locked_file in locked_files[:5]:
                print(f"  - {locked_file}", file=sys.stderr)
            if len(locked_files) > 5:
                print(f"  ... and {len(locked_files) - 5} more", file=sys.stderr)
            print(
                "\nClose applications using these files and retry if update fails.", file=sys.stderr
            )
            print(file=sys.stderr)


def categorize_update_files(
    installed_files: list[str],
    update_source_dir: Path,
    update_metadata: WsdMetadata,
    target_dir: Path,
) -> FileCategorization:
    """Categorize files for update operation based on set operations, protection, and hashes.

    Implements file comparison algorithm from Update-System.md § File Comparison Algorithm
    with content hash comparison from Content-Hashing-Overview.md. Compares installed files
    against update source files, performs set operations to determine which files need to be
    deleted/added/updated, applies no_overwrite protection policies, and uses content hash
    comparison to skip files with identical content.

    This function returns ALL files in their natural categories. Note that .wsdkeep
    files are no longer tracked in file_hashes; directory requirements are declared
    via the required_directories field in wsd.json. The update workflow filters out
    .wsdkeep files from these categories and handles directories separately.

    Algorithm:
    1. Read installation_only list from UPDATE's wsd.json
    2. Extract file paths from installed manifest
    3. Collect all update files and filter out installation_only files
    4. Perform set operations (delete = installed - update)
    5. Perform set operations (add = update - installed)
    6. Identify files in both (in_both = installed ∩ update)
    7. Read no_overwrite list from UPDATE's wsd.json
    8. Read file_hashes from UPDATE's wsd.json for content comparison
    9. Filter in_both files:
       - Protected by no_overwrite → to_skip
       - Content hash matches → to_skip_unchanged
       - Content differs or hash missing → to_update
    10. Return categorized file lists (including .wsdkeep files)

    Args:
        installed_files: List of file paths from installed manifest
        update_source_dir: Path to WSD Runtime root directory containing update files
        update_metadata: Parsed wsd.json from update source containing protection policies
        target_dir: Path to target directory where WSD is installed (for directory checks)

    Returns:
        FileCategorization object with categorized file lists:
            - to_delete: Files to remove from target (includes .wsdkeep)
            - to_add: Files to copy to target (includes .wsdkeep)
            - to_update: Files to overwrite with tag preservation (content differs)
            - to_skip: Files to leave unchanged (no_overwrite protected)
            - to_skip_unchanged: Files to leave unchanged (content identical)

    Raises:
        FileNotFoundError: If update_source_dir does not exist
        WsdCollectionError: If invalid content found in update source
    """
    # Read installation_only list from UPDATE's wsd.json
    installation_only = update_metadata.installation_only
    installation_only_set = set(installation_only)

    # Extract file paths from installed manifest
    installed_set = set(installed_files)

    # Collect all update files and filter out installation_only files
    all_update_files = collect_wsd_files(update_source_dir)
    # Convert to strings and filter out installation_only files
    update_files = {str(p) for p in all_update_files if str(p) not in installation_only_set}

    # Perform set operations (delete = installed - update)
    to_delete_set = installed_set - update_files

    # Perform set operations (add = update - installed)
    to_add_set = update_files - installed_set

    # Identify files in both (in_both = installed ∩ update)
    in_both = installed_set & update_files

    # Read no_overwrite list from UPDATE's wsd.json
    no_overwrite = set(update_metadata.no_overwrite)

    # Read file_hashes from UPDATE's wsd.json for content comparison
    source_hashes = update_metadata.file_hashes

    # Filter in_both files using protection policies and content hash comparison
    to_skip_list: list[str] = []
    to_skip_unchanged_list: list[str] = []
    to_update_list: list[str] = []

    for file_path in in_both:
        if file_path in no_overwrite:
            # Protected by no_overwrite policy - skip updating regardless of content
            to_skip_list.append(file_path)
        else:
            # Not protected - check content hash to determine if update needed
            target_file_path = target_dir / file_path
            source_hash = source_hashes.get(file_path)

            if source_hash is None:
                # Missing hash indicates manifest out of sync - halt per DD-12
                error_msg = (
                    f"Missing hash for '{file_path}' in wsd.json manifest. "
                    "The manifest may be out of sync with source files. "
                    "Regenerate wsd.json with pre_staging.py."
                )
                raise ValueError(error_msg)

            if target_file_path.exists():
                try:
                    target_hash = calculate_file_hash(target_file_path)
                    if target_hash == source_hash:
                        # Content identical - skip update
                        to_skip_unchanged_list.append(file_path)
                        continue
                except OSError:
                    # Cannot read target file - fail-safe to update
                    pass

            # Content differs or read error - update needed
            to_update_list.append(file_path)

    # Return categorized file lists
    # The update workflow filters out .wsdkeep and handles directories via required_directories
    return FileCategorization(
        to_delete=sorted(to_delete_set),
        to_add=sorted(to_add_set),
        to_update=sorted(to_update_list),
        to_skip=sorted(to_skip_list),
        to_skip_unchanged=sorted(to_skip_unchanged_list),
    )


@dataclass
class UpdateStatistics:
    """Statistics for update file operations.

    Tracks counts of files processed in each category during update operations.
    Used for reporting update results to user and for logging purposes.

    Attributes:
        deleted: Number of files successfully deleted from target
        added: Number of files successfully copied to target
        updated: Number of files successfully updated with preservation
        skipped: Number of files skipped due to no_overwrite protection
    """

    deleted: int
    added: int
    updated: int
    skipped: int


def execute_file_deletions(
    to_delete: list[str],
    target_dir: Path,
) -> int:
    """Execute file deletion operations for update process.

    Deletes files in "to_delete" category using shared delete_file() utility with error
    handling, logging, and statistics tracking.

    Args:
        to_delete: List of relative file paths to delete from target
        target_dir: Path to target directory (project root)

    Returns:
        int: Count of files successfully deleted

    Raises:
        OSError: If deletion fails due to permissions or file locks
        IsADirectoryError: If path is a directory (should not happen)
    """
    deleted_count = 0

    verbose_log(f"Deleting {len(to_delete)} obsolete files")

    for relative_path in to_delete:
        file_path = target_dir / relative_path

        try:
            verbose_log(f"Deleting: {relative_path}")
            delete_file(file_path)
            logger.info(f"Deleted: {relative_path}")
            deleted_count += 1

        except (OSError, IsADirectoryError) as e:
            error_msg = (
                f"Error: Cannot delete file during update\n"
                f"\n"
                f"File: {relative_path}\n"
                f"Reason: {e}\n"
                f"\n"
                f"Action: Update halted. No changes made.\n"
                f"        Grant write permission to file or parent directory.\n"
                f"        Retry update after resolving permission issue."
            )
            print(error_msg, file=sys.stderr)
            raise

    return deleted_count


def execute_file_additions(
    to_add: list[str],
    update_source_dir: Path,
    target_dir: Path,
    executable_files: list[str],
) -> int:
    """Execute file addition operations for update process.

    Copies files in "to_add" category using shared copy_file() utility with error handling,
    permission setting, logging, and statistics tracking.

    Args:
        to_add: List of relative file paths to copy to target
        update_source_dir: Path to WSD Runtime root directory (update source)
        target_dir: Path to target directory (project root)
        executable_files: List of files requiring executable permission from wsd.json

    Returns:
        int: Count of files successfully added

    Raises:
        FileNotFoundError: If source file does not exist
        OSError: If copy operation fails (permissions, disk full, etc.)
    """
    added_count = 0
    executable_set = set(executable_files)

    verbose_log(f"Adding {len(to_add)} new files")

    for relative_path in to_add:
        source_path = update_source_dir / relative_path
        dest_path = target_dir / relative_path

        try:
            verbose_log(f"Adding: {relative_path}")
            copy_file(source_path, dest_path)

            if relative_path in executable_set:
                set_executable(dest_path)

            logger.info(f"Added: {relative_path}")
            added_count += 1

        except FileNotFoundError:
            error_msg = (
                f"Error: Cannot create new file during update\n"
                f"\n"
                f"File: {relative_path}\n"
                f"Reason: Source file not found\n"
                f"\n"
                f"Action: Update halted. Partial changes rolled back.\n"
                f"        This appears to be a WSD source corruption issue.\n"
                f"        Re-download WSD source and retry."
            )
            print(error_msg, file=sys.stderr)
            raise
        except OSError as e:
            # Determine specific error type for better messaging
            error_reason = str(e)
            if "disk quota" in error_reason.lower() or "no space" in error_reason.lower():
                error_msg = (
                    f"Error: Cannot create new file during update\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: Disk quota exceeded\n"
                    f"\n"
                    f"Action: Update halted. Partial changes rolled back.\n"
                    f"        Free disk space and retry update."
                )
            elif "permission denied" in error_reason.lower():
                error_msg = (
                    f"Error: Cannot create new file during update\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: Permission denied\n"
                    f"\n"
                    f"Action: Update halted. Partial changes rolled back.\n"
                    f"        Grant write permission to target directory.\n"
                    f"        Retry update after resolving permission issue."
                )
            else:
                error_msg = (
                    f"Error: Cannot create new file during update\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: {e}\n"
                    f"\n"
                    f"Action: Update halted. Partial changes rolled back.\n"
                    f"        Check file system status and retry update."
                )
            print(error_msg, file=sys.stderr)
            raise

    return added_count


def execute_file_updates(  # noqa: PLR0912, PLR0915
    to_update: list[str],
    update_source_dir: Path,
    target_dir: Path,
    executable_files: list[str],
) -> int:
    """Execute file update operations with tag preservation.

    Updates files in "to_update" category by checking for WORKSCOPE-DEV tags and
    applying appropriate update strategy (preservation or simple copy).

    Args:
        to_update: List of relative file paths to update in target
        update_source_dir: Path to WSD Runtime root directory (update source)
        target_dir: Path to target directory (project root)
        executable_files: List of files requiring executable permission from wsd.json

    Returns:
        int: Count of files successfully updated

    Raises:
        FileNotFoundError: If source file does not exist
        OSError: If file operations fail
        UnicodeDecodeError: If files are not UTF-8 encoded
    """
    updated_count = 0
    executable_set = set(executable_files)

    verbose_log(f"Updating {len(to_update)} existing files")

    for relative_path in to_update:
        source_path = update_source_dir / relative_path
        dest_path = target_dir / relative_path

        try:
            verbose_log(f"Updating: {relative_path}")
            # Check for large files
            is_large, size_mb = check_large_file(source_path)

            if is_large:
                # Warn about large file
                warn_large_file(relative_path, size_mb)

                # Prompt for confirmation
                if not confirm_large_file_processing():
                    print(f"\nSkipping large file: {relative_path}", file=sys.stderr)
                    continue

                # Check if binary file
                if is_binary_file(source_path):
                    # Use streaming copy for large binary files (skip tag preservation)
                    streaming_copy_file(source_path, dest_path)
                    logger.info(f"Updated (streaming): {relative_path}")
                else:
                    # Large text file - still use streaming copy to avoid memory issues
                    streaming_copy_file(source_path, dest_path)
                    logger.info(f"Updated (streaming, tag preservation skipped): {relative_path}")

            else:
                # Normal-sized file - check for WORKSCOPE-DEV tags
                try:
                    source_content = source_path.read_text(encoding="utf-8")
                    tags_in_file = find_tag_pairs(source_content, source_path)
                except (OSError, UnicodeDecodeError):
                    tags_in_file = []

                if tags_in_file:
                    # Tags present - use preservation algorithm
                    preserved_content = preserve_tag_content(source_path, dest_path)
                    dest_path.write_text(preserved_content, encoding="utf-8")
                else:
                    # No tags - perform simple file copy
                    copy_file(source_path, dest_path)

                logger.info(f"Updated: {relative_path}")

            # Set executable permissions from wsd.json if applicable
            if relative_path in executable_set:
                set_executable(dest_path)

            updated_count += 1

        except FileNotFoundError:
            error_msg = (
                f"Error: Cannot update file\n"
                f"\n"
                f"File: {relative_path}\n"
                f"Reason: Source file not found\n"
                f"\n"
                f"Action: Update halted. Changes rolled back.\n"
                f"        This appears to be a WSD source corruption issue.\n"
                f"        Re-download WSD source and retry update."
            )
            print(error_msg, file=sys.stderr)
            raise
        except UnicodeDecodeError:
            error_msg = (
                f"Error: Cannot update file\n"
                f"\n"
                f"File: {relative_path}\n"
                f"Reason: File is not UTF-8 encoded\n"
                f"\n"
                f"Action: Update halted. Changes rolled back.\n"
                f"        Convert file to UTF-8 encoding or skip this update.\n"
                f"        Restore installation from version control if needed."
            )
            print(error_msg, file=sys.stderr)
            raise
        except OSError as e:
            # Determine specific error type for better messaging
            error_reason = str(e)
            if "permission denied" in error_reason.lower():
                error_msg = (
                    f"Error: Cannot update file\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: Permission denied\n"
                    f"\n"
                    f"Action: Update halted. Changes rolled back.\n"
                    f"        Grant write permission to file.\n"
                    f"        Retry update after resolving permission issue."
                )
            elif "locked" in error_reason.lower() or "being used" in error_reason.lower():
                error_msg = (
                    f"Error: Cannot update file\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: File is locked by another process\n"
                    f"\n"
                    f"Action: Update halted. Changes rolled back.\n"
                    f"        Close applications using this file and retry."
                )
            else:
                error_msg = (
                    f"Error: Cannot update file\n"
                    f"\n"
                    f"File: {relative_path}\n"
                    f"Reason: {e}\n"
                    f"\n"
                    f"Action: Update halted. Changes rolled back.\n"
                    f"        Check file system status and retry update."
                )
            print(error_msg, file=sys.stderr)
            raise

    return updated_count


def execute_file_skips(
    to_skip: list[str],
) -> int:
    """Log and track files skipped during update due to no_overwrite protection.

    Processes files in "to_skip" category by logging them with reason and tracking
    statistics. These files remain in manifest but are not modified on filesystem.

    Note: Manifest handling is performed by the update command that calls this function.
    This function only handles logging and statistics.

    Args:
        to_skip: List of relative file paths skipped due to no_overwrite protection

    Returns:
        int: Count of files skipped
    """
    skipped_count = 0

    for relative_path in to_skip:
        logger.info(f"Skipped (no_overwrite): {relative_path}")
        skipped_count += 1

    return skipped_count


def generate_dry_run_preview(  # noqa: PLR0912, PLR0915
    categorization: FileCategorization,
    current_version: str,
    update_version: str,
    target_path: Path,
    installed_files: list[str],
    required_directories: list[str],
) -> None:
    """Generate and print dry-run preview report for update operation.

    Implements dry-run output format from Update-System.md § Dry-Run Mode (lines 776-822).
    Displays version information, categorized file lists with symbols, statistics summary,
    required directories to ensure, and instructions for proceeding without making any
    filesystem modifications.

    Output format:
    - Header with "WSD Update Preview (--dry-run)"
    - Version info showing current → update
    - Changes summary with counts for each category
    - Categorized file lists with symbols (-, +, ~, =)
    - Required directories to ensure (from update source metadata)
    - Statistics summary (current count, updated count, total changes)
    - Instructions for proceeding

    Args:
        categorization: File categorization results from categorize_update_files()
        current_version: Version from installed manifest
        update_version: Version from update source's wsd.json
        target_path: Path to target directory (for display in instructions)
        installed_files: List of currently installed files for statistics calculation
        required_directories: List of directory paths that must exist from update source
    """
    # Filter out .wsdkeep files from all categories (handled via required_directories)
    effective_to_delete = [f for f in categorization.to_delete if Path(f).name != ".wsdkeep"]
    effective_to_add = [f for f in categorization.to_add if Path(f).name != ".wsdkeep"]
    effective_to_update = [f for f in categorization.to_update if Path(f).name != ".wsdkeep"]

    print("WSD Update Preview (--dry-run)")
    print("=" * 30)
    print()

    # Version information (current → update)
    print(f"Current Version: {current_version}")
    print(f"Update Version:  {update_version}")
    print()

    # Changes summary with counts (using filtered lists for accurate preview)
    total_skipped = len(categorization.to_skip) + len(categorization.to_skip_unchanged)
    print("Changes Summary")
    print("-" * 30)
    print(f"Files to delete:  {len(effective_to_delete)}")
    print(f"Files to add:     {len(effective_to_add)}")
    print(f"Files to update:  {len(effective_to_update)}")
    print(
        f"Files to skip:    {total_skipped} "
        f"({len(categorization.to_skip_unchanged)} unchanged, "
        f"{len(categorization.to_skip)} protected)"
    )
    print()

    # Files to delete (with - symbol)
    if effective_to_delete:
        print("Files to Delete")
        print("-" * 30)
        for file_path in effective_to_delete:
            print(f"  - {file_path}")
        print()

    # Files to add (with + symbol)
    if effective_to_add:
        print("Files to Add")
        print("-" * 30)
        for file_path in effective_to_add:
            print(f"  + {file_path}")
        print()

    # Files to update with preservation (with ~ symbol)
    if effective_to_update:
        print("Files to Update (with content preservation)")
        print("-" * 30)
        # Show first 10 files, then indicate if there are more
        display_count = min(10, len(effective_to_update))
        for file_path in effective_to_update[:display_count]:
            print(f"  ~ {file_path}")

        remaining = len(effective_to_update) - display_count
        if remaining > 0:
            print(f"  [... {remaining} more files ...]")
        print()

    # Files to skip due to no_overwrite (with = symbol)
    if categorization.to_skip:
        print("Files to Skip (protected by no_overwrite)")
        print("-" * 30)
        for file_path in categorization.to_skip:
            print(f"  = {file_path} (user-owned content)")
        print()

    # Files to skip due to content unchanged (with ≡ symbol)
    if categorization.to_skip_unchanged:
        print("Files to Skip (content unchanged)")
        print("-" * 30)
        # Show first 10 files, then indicate if there are more
        display_count = min(10, len(categorization.to_skip_unchanged))
        for file_path in categorization.to_skip_unchanged[:display_count]:
            print(f"  ≡ {file_path}")

        remaining = len(categorization.to_skip_unchanged) - display_count
        if remaining > 0:
            print(f"  [... {remaining} more files ...]")
        print()

    # Required directories to ensure
    if required_directories:
        print(f"Required directories to ensure: {len(required_directories)}")
        print("-" * 30)
        for dir_path in required_directories:
            print(f"  {dir_path}")
        print()

    # Statistics summary (using filtered lists for accurate preview)
    current_file_count = len(installed_files)
    updated_file_count = current_file_count - len(effective_to_delete) + len(effective_to_add)
    total_changes = len(effective_to_delete) + len(effective_to_add) + len(effective_to_update)

    print("Statistics")
    print("-" * 30)
    print(f"Current file count: {current_file_count}")
    print(f"Updated file count: {updated_file_count}")
    print(f"Total changes:      {total_changes}")
    print()

    # Instructions for proceeding
    print("To proceed with this update, run:")
    print(f"  wsd.py install {target_path}")
    print()
    print("To cancel, take no action.")


def create_updated_manifest(
    categorization: FileCategorization,
    original_manifest: dict[str, Any],
    update_version: str,
    target_dir: Path,
    actual_deleted: list[str] | None = None,
    actual_added: list[str] | None = None,
) -> dict[str, Any]:
    """Create updated manifest after applying update file operations.

    Implements manifest management for updates from Install-And-Update-Overview.md.
    Builds complete file list from update results, rescans all files for
    WORKSCOPE-DEV tags, preserves creation timestamp from original manifest,
    updates modification timestamp to current time, and sets version from update source.

    This function is called AFTER all file operations have completed. It generates
    the new manifest reflecting the updated installation state. The manifest
    excludes .wsdkeep files as they are structural artifacts managed at runtime.

    Args:
        categorization: File categorization results with to_delete, to_add, to_update, to_skip
        original_manifest: Original manifest data from target directory before update
        update_version: Version string from update source's wsd.json
        target_dir: Path to target directory where WSD is installed
        actual_deleted: List of files actually deleted (may differ from categorization
            after filtering). If None, uses categorization.to_delete.
        actual_added: List of files actually added (may differ from categorization
            after filtering). If None, uses categorization.to_add.

    Returns:
        Updated manifest dictionary ready to be written via write_manifest()

    Raises:
        ValueError: If original manifest is invalid or missing required fields
        OSError: If file scanning fails during tag rescan
    """
    # Use actual operations if provided, otherwise fall back to categorization
    deleted_files = actual_deleted if actual_deleted is not None else categorization.to_delete
    added_files = actual_added if actual_added is not None else categorization.to_add

    # Build file list from update results
    # Final file list = (original files - deleted files) + added files
    # Updated and skipped files remain in the list
    original_files_set = set(original_manifest["files"])

    # Remove deleted files
    files_after_delete = original_files_set - set(deleted_files)

    # Add new files
    final_files = files_after_delete | set(added_files)

    # Filter out .wsdkeep files from manifest (structural artifacts, not tracked)
    final_files = {f for f in final_files if Path(f).name != ".wsdkeep"}

    # Convert to sorted list for consistent ordering
    final_files_list = sorted(final_files)

    # Rescan all files for WORKSCOPE-DEV tags
    tags: list[dict[str, str]] = []

    for relative_path_str in final_files_list:
        absolute_file_path = target_dir / relative_path_str

        # Scan file for tags
        try:
            with absolute_file_path.open("r", encoding="utf-8") as f:
                content = f.read()

            # Extract tag IDs from opening tags using simple string search
            pos = 0
            while True:
                start = content.find(_TAG_OPEN_PREFIX, pos)
                if start == -1:
                    break

                # Find end of opening tag within bounded window
                end = content.find(">", start, start + MAX_OPENING_TAG_LENGTH)
                if end == -1:
                    # No closing bracket within window - malformed opening tag
                    line_num = _get_line_number(content, start)
                    logger.warning(
                        f"Malformed WORKSCOPE-DEV tag in {relative_path_str} "
                        f"at line {line_num}: Opening tag missing closing '>' within "
                        f"{MAX_OPENING_TAG_LENGTH} characters. Tag will be skipped."
                    )
                    pos = start + 1
                    continue

                tag_portion = content[start + 14 : end]
                tag_id = tag_portion.strip()

                # Validate tag ID using shared validation utility
                if _is_valid_tag_id(tag_id):
                    tags.append({"id": tag_id, "file": relative_path_str})

                pos = end + 1

        except (OSError, UnicodeDecodeError):
            # Skip binary or unreadable files
            pass

    # Preserve creation timestamp from original manifest
    created_timestamp = original_manifest["created"]

    # Update modification timestamp to current time
    # Format as ISO 8601 without microseconds: YYYY-MM-DDTHH:MM:SSZ
    updated_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Set version from update source and create manifest using shared utility
    return create_manifest(
        version=update_version,
        files=final_files_list,
        tags=tags,
        created=created_timestamp,
        updated=updated_timestamp,
    )


# ==============================================================================
# FILE OPERATION UTILITIES
# ==============================================================================


def copy_file(src: Path, dest: Path) -> None:
    """Copy file from source to destination preserving metadata.

    Uses shutil.copy2() to preserve file metadata including modification times
    and permissions. Creates parent directories for destination if needed.

    Args:
        src: Source file path to copy from
        dest: Destination file path to copy to

    Raises:
        FileNotFoundError: If source file does not exist
        OSError: If copy operation fails (permissions, disk full, etc.)
    """
    if not src.exists():
        error_msg = f"Source file does not exist: {src}"
        raise FileNotFoundError(error_msg)

    try:
        # Create parent directories if needed using helper function
        create_directories(dest.parent)
        # Copy file preserving metadata
        shutil.copy2(src, dest)
    except OSError as e:
        error_msg = f"Failed to copy {src} to {dest}: {e}"
        raise OSError(error_msg) from e


def create_directories(path: Path) -> None:
    """Create directory and all parent directories with exist_ok handling.

    Creates the specified directory and any missing parent directories.
    Does not raise an error if the directory already exists.

    Args:
        path: Directory path to create

    Raises:
        OSError: If directory creation fails (permissions, invalid path, etc.)
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        error_msg = f"Failed to create directory {path}: {e}"
        raise OSError(error_msg) from e


def set_executable(path: Path) -> None:
    """Add executable permission (+x) to file.

    Sets the executable bit for user, group, and other without modifying
    other permission bits. Uses conservative approach to avoid interfering
    with user's permission preferences.

    Args:
        path: File path to make executable

    Raises:
        FileNotFoundError: If file does not exist
        OSError: If permission modification fails
    """
    if not path.exists():
        error_msg = f"File does not exist: {path}"
        raise FileNotFoundError(error_msg)

    try:
        current_mode = path.stat().st_mode
        # Add execute permission for user, group, and other
        path.chmod(current_mode | 0o111)
    except OSError as e:
        error_msg = f"Failed to set executable permission on {path}: {e}"
        raise OSError(error_msg) from e


def delete_file(path: Path) -> None:
    """Delete file with error handling.

    Removes the specified file from the filesystem. Does not raise an error
    if the file doesn't exist (idempotent deletion).

    Args:
        path: File path to delete

    Raises:
        OSError: If deletion fails (permissions, file locked, etc.)
        IsADirectoryError: If path is a directory, not a file
    """
    if not path.exists():
        return  # Idempotent - already deleted

    if path.is_dir():
        error_msg = f"Path is a directory, not a file: {path}"
        raise IsADirectoryError(error_msg)

    try:
        path.unlink()
    except OSError as e:
        error_msg = f"Failed to delete file {path}: {e}"
        raise OSError(error_msg) from e


def _report_rollback_status(
    copied_files: list[Path],
    failed_deletions: list[tuple[Path, str]],
    removed_directories: int,
) -> None:
    """Report rollback cleanup status to stderr.

    Args:
        copied_files: List of files that were attempted to be deleted
        failed_deletions: List of (file_path, error_message) for files that couldn't be deleted
        removed_directories: Count of empty directories successfully removed
    """
    if not failed_deletions:
        # Complete rollback success
        file_plural = "s" if len(copied_files) != 1 else ""
        file_msg = f"Removed {len(copied_files)} partial installation file{file_plural}"
        if removed_directories > 0:
            dir_plural = "ies" if removed_directories != 1 else "y"
            dir_msg = f", {removed_directories} empty director{dir_plural}"
        else:
            dir_msg = ""
        print(f"\nRollback: {file_msg}{dir_msg}", file=sys.stderr)
    else:
        # Partial rollback - some files couldn't be removed
        successful_count = len(copied_files) - len(failed_deletions)
        print(
            f"\nRollback: Removed {successful_count} of {len(copied_files)} partial files",
            file=sys.stderr,
        )
        if removed_directories > 0:
            dir_plural = "ies" if removed_directories != 1 else "y"
            print(
                f"Removed {removed_directories} empty director{dir_plural}",
                file=sys.stderr,
            )
        print("\nWarning: Could not remove the following files:", file=sys.stderr)
        for failed_path, error_msg in failed_deletions:
            print(f"  - {failed_path}: {error_msg}", file=sys.stderr)
        print(
            "\nManual cleanup required for files listed above before retrying installation.",
            file=sys.stderr,
        )


def rollback_partial_installation(copied_files: list[Path]) -> None:
    """Remove partially copied files and empty directories after installation error.

    Performs best-effort cleanup of files and empty directories that were created
    during a failed installation, attempting to return the target directory to its
    pre-installation state. Deletion failures are handled gracefully with warnings
    rather than raising exceptions.

    This function implements the atomic operation guarantee by cleaning up after
    installation failures. It performs cleanup in two phases:
    1. Delete all copied files (in reverse order)
    2. Remove empty parent directories created during installation (bottom-up)

    Directories containing pre-existing files are preserved.

    Args:
        copied_files: List of file paths that were successfully copied before
            the error occurred. Files are deleted in reverse order.
            PRECONDITION: Must contain at least one file path (guaranteed by
            calling context - only called after copy operation failures).
    """
    # Delete files in reverse order (last copied first)
    failed_deletions: list[tuple[Path, str]] = []

    for file_path in reversed(copied_files):
        try:
            delete_file(file_path)
        except (OSError, IsADirectoryError) as e:
            # Best-effort cleanup - warn but don't fail rollback
            failed_deletions.append((file_path, str(e)))

    # Collect all unique parent directories from copied files
    directories_to_check: set[Path] = set()
    for file_path in copied_files:
        current_dir = file_path.parent
        while current_dir != current_dir.parent:  # Stop at filesystem root
            directories_to_check.add(current_dir)
            current_dir = current_dir.parent

    # Sort directories by depth (deepest first) for bottom-up removal
    sorted_directories = sorted(directories_to_check, key=lambda p: len(p.parts), reverse=True)

    # Remove empty directories bottom-up
    removed_directories = 0
    for directory in sorted_directories:
        try:
            # Check if directory exists, is a directory, and is empty
            if directory.exists() and directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
                removed_directories += 1
        except OSError:
            # Best-effort cleanup - if we can't remove directory, continue
            # This catches permission errors, directory not empty race conditions, etc.
            pass

    # Report rollback status
    _report_rollback_status(copied_files, failed_deletions, removed_directories)


def is_directory_empty(path: Path) -> bool:
    """Check if directory is empty or contains only .wsdkeep file.

    A directory is considered empty if it contains no files, or if it only
    contains a .wsdkeep placeholder file. This function is used to determine
    whether .wsdkeep files should be preserved or removed during updates.

    Args:
        path: Directory path to check

    Returns:
        True if directory is empty or contains only .wsdkeep, False otherwise

    Raises:
        FileNotFoundError: If directory does not exist
        NotADirectoryError: If path exists but is not a directory
        OSError: If directory listing fails (permissions, etc.)
    """
    if not path.exists():
        error_msg = f"Directory does not exist: {path}"
        raise FileNotFoundError(error_msg)

    if not path.is_dir():
        error_msg = f"Path is not a directory: {path}"
        raise NotADirectoryError(error_msg)

    try:
        # Get list of all items in directory
        items = list(path.iterdir())

        # Empty directory
        if len(items) == 0:
            return True

        # Only .wsdkeep file present, or directory has other content
        return len(items) == 1 and items[0].name == ".wsdkeep"

    except OSError as e:
        error_msg = f"Failed to check directory {path}: {e}"
        raise OSError(error_msg) from e


def _directory_needs_wsdkeep(target_dir: Path) -> bool:
    """Check if a directory needs a .wsdkeep placeholder file.

    Determines whether a .wsdkeep file should be added or restored to a directory.
    The .wsdkeep file exists to "hold" empty directories through distribution;
    once users populate a directory with content, .wsdkeep becomes unnecessary.

    Decision logic:
    - If directory does NOT exist → True (need .wsdkeep to create structure)
    - If directory exists but is empty → True (need .wsdkeep to maintain structure)
    - If directory has content (any files other than .wsdkeep) → False (no need)

    Args:
        target_dir: Directory path to check

    Returns:
        True if .wsdkeep should be added/restored, False if directory has content
    """
    # Directory doesn't exist - need .wsdkeep to create structure
    if not target_dir.exists():
        return True

    # Directory exists - check if it has content
    try:
        items = list(target_dir.iterdir())

        # Empty directory - needs .wsdkeep to maintain structure
        if len(items) == 0:
            return True

        # Only .wsdkeep file present - still needs .wsdkeep (preserve it)
        # Directory has other content - doesn't need .wsdkeep
        return len(items) == 1 and items[0].name == ".wsdkeep"

    except OSError:
        # Cannot read directory - fail-safe to adding .wsdkeep
        return True


# ==============================================================================
# TAG SCANNING UTILITIES
# ==============================================================================

# Maximum length of a valid opening tag: "<WORKSCOPE‑DEV " (15) + tag-id (50 max) + ">" (1) = 66
# Used to limit search window and prevent massive text capture from malformed tags
MAX_OPENING_TAG_LENGTH: int = 66

# Tag pattern constants - string concatenation prevents scanner from detecting its own patterns
_TAG_OPEN_PREFIX: str = "<" + "WORKSCOPE-DEV"
_TAG_CLOSE: str = "</" + "WORKSCOPE-DEV>"


class TagParsingError(Exception):
    """Exception raised when WORKSCOPE-DEV tag parsing encounters an error.

    This exception is raised for malformed tags that would compromise the integrity
    of install or update operations. Per Design Decision 12, all tag parsing errors
    must halt operations immediately rather than continuing with potentially
    corrupted or incomplete data.

    Attributes:
        message: Human-readable description of the parsing error.
        file_path: Path to the file containing the malformed tag (if known).
        line_number: Line number where the error occurred (if known).

    Examples of conditions that raise this exception:
        - Opening tag missing closing '>' bracket
        - Invalid tag ID (not kebab-case, wrong length)
        - Missing closing tag for an opening tag
    """

    def __init__(
        self,
        message: str,
        file_path: Path | str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Initialize TagParsingError with context information.

        Args:
            message: Description of the parsing error.
            file_path: Path to the file being parsed when error occurred.
            line_number: Line number in the file where error occurred.
        """
        self.file_path = file_path
        self.line_number = line_number

        # Build full message with context
        parts = []
        if file_path:
            parts.append(f"in {file_path}")
        if line_number:
            parts.append(f"at line {line_number}")

        full_message = f"{message} ({', '.join(parts)})" if parts else message

        super().__init__(full_message)


def scan_file_for_tags(file_path: Path) -> list[dict[str, str]]:
    """Scan file for WORKSCOPE-DEV tags and return tag objects.

    Scans a text file for WORKSCOPE-DEV opening tags and extracts their tag IDs.
    Binary files are skipped. Files are read with UTF-8 encoding. Returns a list
    of tag objects containing the tag ID and file path for each discovered tag.

    Tag syntax: <WORKSCOPE‑DEV tag-id> where tag-id is kebab-case (3-50 chars).
    Only opening tags are extracted; closing tags </WORKSCOPE‑DEV> are ignored.

    Args:
        file_path: RELATIVE path to file to scan (must not be absolute).

    Returns:
        List of tag objects, each containing:
        - id: Tag identifier from opening tag (kebab-case string)
        - file: Relative path to file containing tag (string)
        Returns empty list if file is binary or contains no tags.

    Raises:
        ValueError: If file_path is absolute (must be relative for manifest compatibility).
        TagParsingError: If any malformed tag is encountered:
            - Opening tag missing closing '>' bracket
            - Invalid tag ID (not kebab-case, not 3-50 chars)
        OSError: If file cannot be read.
        UnicodeDecodeError: If file is not valid UTF-8.
    """
    # Enforce relative path requirement for manifest compatibility
    if file_path.is_absolute():
        error_msg = (
            f"file_path must be relative for manifest compatibility, got absolute: {file_path}"
        )
        raise ValueError(error_msg)

    # Skip binary files
    if _is_binary_file(file_path):
        return []

    tags: list[dict[str, str]] = []

    # Read file with UTF-8 encoding (let exceptions propagate)
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Extract tag IDs from opening tags using simple string search
    # Search for opening tags: <WORKSCOPE‑DEV tag-id>
    pos = 0
    while True:
        # Find start of opening tag
        start = content.find(_TAG_OPEN_PREFIX, pos)
        if start == -1:
            break

        # Find end of opening tag within bounded window
        end = content.find(">", start, start + MAX_OPENING_TAG_LENGTH)
        if end == -1:
            # No closing bracket within window - malformed opening tag
            line_num = _get_line_number(content, start)
            raise TagParsingError(
                f"Opening tag missing closing '>' within {MAX_OPENING_TAG_LENGTH} characters. "
                "Fix the tag syntax and retry the operation.",
                file_path=file_path,
                line_number=line_num,
            )

        # Extract tag portion between markers
        tag_portion = content[start + 14 : end]  # Skip "<WORKSCOPE‑DEV"

        # Strip whitespace from tag portion
        tag_id = tag_portion.strip()

        # Validate tag ID format (kebab-case, 3-50 chars)
        if not _is_valid_tag_id(tag_id):
            display_id = _format_tag_id_for_display(tag_id)
            line_num = _get_line_number(content, start)
            raise TagParsingError(
                f"Invalid tag ID '{display_id}' (expected kebab-case, 3-50 chars). "
                "Fix the tag ID format and retry the operation.",
                file_path=file_path,
                line_number=line_num,
            )

        tags.append({"id": tag_id, "file": str(file_path)})

        # Move position past this tag
        pos = end + 1

    return tags


def _format_tag_id_for_display(tag_id: str, max_length: int = 50) -> str:
    """Format tag ID for display in warning messages.

    Sanitizes and truncates tag IDs for readable error output. Replaces
    newlines with literal escape sequences and truncates long content
    with an ellipsis suffix.

    Args:
        tag_id: Raw tag ID string that may contain newlines or excessive content
        max_length: Maximum length before truncation (default: 50)

    Returns:
        Sanitized and truncated tag ID suitable for single-line display
    """
    # Replace newlines with literal representation
    sanitized = tag_id.replace("\n", "\\n").replace("\r", "\\r")

    # Truncate if too long
    if len(sanitized) > max_length:
        return sanitized[:max_length] + "..."
    return sanitized


def _get_line_number(content: str, position: int) -> int:
    """Convert byte position to line number.

    Calculates the line number for a given character position by counting
    newlines in the content before that position.

    Args:
        content: Full file content string
        position: Character position in the content

    Returns:
        Line number (1-indexed) where the position occurs
    """
    return content[:position].count("\n") + 1


def find_tag_pairs(content: str, file_path: Path | None = None) -> list[dict[str, Any]]:
    """Find all WORKSCOPE-DEV tag pairs in file content.

    Searches content for matching opening and closing tag pairs using simple
    string search (no regex). Returns list of tag pair objects containing tag ID,
    start/end positions, and content between tags.

    Tag pair syntax:
    - Opening: <WORKSCOPE‑DEV tag-id>
    - Closing: </WORKSCOPE‑DEV>
    - Content: Any text between opening and closing tags

    Args:
        content: File content to search for tag pairs.
        file_path: Optional path to file being scanned (for error messages).

    Returns:
        List of tag pair objects, each containing:
        - id: Tag identifier from opening tag (string)
        - start: Character position of opening tag start (int)
        - end: Character position after closing tag (int)
        - content: Text between opening and closing tags (string)
        Returns empty list if no tag pairs found.

    Raises:
        TagParsingError: If any malformed tag is encountered:
            - Opening tag missing closing '>' bracket
            - Invalid tag ID (not kebab-case, not 3-50 chars)
            - Missing closing tag for an opening tag
    """
    pairs: list[dict[str, Any]] = []
    pos = 0

    while True:
        # Find opening tag start
        open_start = content.find(_TAG_OPEN_PREFIX, pos)
        if open_start == -1:
            break

        # Find opening tag end within bounded window
        open_end = content.find(">", open_start, open_start + MAX_OPENING_TAG_LENGTH)
        if open_end == -1:
            # No closing bracket within window - malformed opening tag
            line_num = _get_line_number(content, open_start)
            raise TagParsingError(
                f"Opening tag missing closing '>' within {MAX_OPENING_TAG_LENGTH} characters. "
                "Fix the tag syntax and retry the operation.",
                file_path=file_path,
                line_number=line_num,
            )

        # Extract and validate tag ID
        tag_portion = content[open_start + 14 : open_end]
        tag_id = tag_portion.strip()

        if not _is_valid_tag_id(tag_id):
            # Invalid tag ID format
            display_id = _format_tag_id_for_display(tag_id)
            line_num = _get_line_number(content, open_start)
            raise TagParsingError(
                f"Invalid tag ID '{display_id}' (expected kebab-case, 3-50 chars). "
                "Fix the tag ID format and retry the operation.",
                file_path=file_path,
                line_number=line_num,
            )

        # Find matching closing tag
        close_start = content.find(_TAG_CLOSE, open_end + 1)
        if close_start == -1:
            # No closing tag found - malformed
            display_id = _format_tag_id_for_display(tag_id)
            line_num = _get_line_number(content, open_start)
            raise TagParsingError(
                f"Missing closing tag for '{display_id}'. "
                "Add </WORKSCOPE-DEV> after the tag content and retry the operation.",
                file_path=file_path,
                line_number=line_num,
            )

        # Extract content between tags
        tag_content = content[open_end + 1 : close_start]

        # Store tag pair info
        pairs.append(
            {
                "id": tag_id,
                "start": open_start,
                "end": close_start + 16,  # Position after </WORKSCOPE-DEV>
                "content": tag_content,
            }
        )

        # Move position past this closing tag
        pos = close_start + 16

    return pairs


def extract_preserved_content(destination_file: Path, update_tag_ids: set[str]) -> dict[str, str]:
    """Extract user content from destination file for WORKSCOPE-DEV tags.

    This function implements Step 3 of the content preservation algorithm from
    Template-System.md. It reads the destination file, finds all WORKSCOPE-DEV
    tag pairs, and extracts the content between tags for tag IDs that exist in
    the update file.

    Content is preserved byte-for-byte including:
    - Exact whitespace and formatting
    - UTF-8 encoding
    - Multi-line content

    Handles file-level edge cases:
    - Very large files (logs warning but proceeds)
    - Symlinks (follows for reading)
    - File read errors (raises exception to halt operation)

    Args:
        destination_file: Path to existing file in user's project
        update_tag_ids: Set of tag IDs present in the update file

    Returns:
        dict[str, str]: Mapping of tag_id -> content for tags found in both
        destination and update files. Returns empty dict if:
        - Destination file doesn't exist
        - No matching tags found between destination and update

    Raises:
        PermissionError: If destination file cannot be read due to permissions.
            Includes file path and recovery instructions.
        UnicodeDecodeError: If destination file is not valid UTF-8.
            Includes file path and encoding details.
        OSError: If destination file cannot be accessed for other I/O reasons.
            Includes file path, error details, and recovery instructions.
    """
    # Return empty mapping if destination file doesn't exist
    if not destination_file.exists():
        return {}

    # Check file size and log warning for very large files
    try:
        file_size = destination_file.stat().st_size
        # Warn if file larger than 10 MB
        if file_size > 10 * 1024 * 1024:
            size_mb = file_size / (1024 * 1024)
            logger.warning(
                f"Very large file detected: {destination_file} ({size_mb:.1f} MB). "
                "Loading entire file into memory may cause performance issues."
            )
    except OSError:
        # Can't stat file, will fail on read anyway
        pass

    # Read destination file content (follows symlinks by default)
    try:
        with destination_file.open(encoding="utf-8") as f:
            content = f.read()
    except PermissionError as e:
        error_msg = (
            f"Cannot read destination file '{destination_file}' during content preservation: "
            f"Permission denied.\n"
            f"Action: Grant read permission with: chmod u+r {destination_file}\n"
            f"This operation is idempotent and safe to retry after fixing permissions."
        )
        raise PermissionError(error_msg) from e
    except UnicodeDecodeError as e:
        error_msg = (
            f"Cannot read destination file '{destination_file}' during content preservation: "
            f"Invalid UTF-8 encoding.\n"
            f"Details: {e}\n"
            f"Action: Fix file encoding or convert to UTF-8, then retry.\n"
            f"This operation is idempotent and safe to retry after fixing encoding."
        )
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, error_msg) from e
    except OSError as e:
        error_msg = (
            f"Cannot read destination file '{destination_file}' during content preservation: "
            f"{e}\n"
            f"Reason: {type(e).__name__}\n"
            f"Action: Resolve the file access issue and retry.\n"
            f"This operation is idempotent and safe to retry after fixing the issue."
        )
        raise OSError(error_msg) from e

    # Find all tag pairs in destination file
    tag_pairs = find_tag_pairs(content, destination_file)

    # Build preserved content mapping for tags that exist in update
    preserved: dict[str, str] = {}
    for pair in tag_pairs:
        tag_id = pair["id"]
        # Only preserve content if tag exists in update file
        if tag_id in update_tag_ids:
            preserved[tag_id] = pair["content"]

    return preserved


def preserve_tag_content(update_file: Path, destination_file: Path) -> str:
    """Preserve user customizations in WORKSCOPE-DEV tags during update.

    This function implements the complete 8-step content preservation algorithm from
    Template-System.md § Content Preservation Algorithm (lines 671-711). It reads both
    update and destination files, finds WORKSCOPE-DEV tags, and merges content such that:
    - Template context from update file is used
    - User content within tags is preserved from destination
    - New tags use initial content from update
    - Old tags removed from update are discarded

    Algorithm steps:
    1. Read update file completely into memory
    2. Read destination file if it exists
    3. Find all tags in update file
    4. Build tag ID list from update file
    5. Start with update file content as base
    6. Replace each tag's content with preserved user content
    7. Keep initial content for new tags not in destination
    8. Return final content (caller writes to destination)

    Args:
        update_file: Path to new template file from WSD Runtime
        destination_file: Path to existing file in user's project

    Returns:
        str: Updated content with preserved user customizations

    Raises:
        FileNotFoundError: If update_file does not exist.
        PermissionError: If update_file or destination_file cannot be read
            due to permissions.
        UnicodeDecodeError: If update_file or destination_file is not valid UTF-8.
        OSError: If file reading fails for other I/O reasons.
    """
    # Read update file completely into memory
    if not update_file.exists():
        error_msg = f"Update file does not exist: {update_file}"
        raise FileNotFoundError(error_msg)

    # Check file size and log warning for very large files
    try:
        file_size = update_file.stat().st_size
        # Warn if file larger than 10 MB
        if file_size > 10 * 1024 * 1024:
            logger.warning(
                f"Very large file detected: {update_file} ({file_size / (1024 * 1024):.1f} MB). "
                "Loading entire file into memory may cause performance issues."
            )
    except OSError as e:
        error_msg = (
            f"Cannot access update file {update_file}: {e}\n"
            f"Action: Grant read permission with: chmod u+r {update_file}"
        )
        raise OSError(error_msg) from e

    # Read update file (follows symlinks by default)
    try:
        with update_file.open(encoding="utf-8") as f:
            update_content = f.read()
    except UnicodeDecodeError as e:
        error_msg = f"Update file is not UTF-8 encoded: {update_file}"
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, error_msg) from e
    except PermissionError as e:
        error_msg = (
            f"Cannot read update file {update_file}: Permission denied\n"
            f"Action: Grant read permission with: chmod u+r {update_file}"
        )
        raise PermissionError(error_msg) from e
    except OSError as e:
        error_msg = f"Cannot read update file {update_file}: {e}\nReason: {type(e).__name__}"
        raise OSError(error_msg) from e

    # Find all tags in update file
    update_tag_pairs = find_tag_pairs(update_content, update_file)

    # Build tag ID list from update file
    update_tag_ids = {pair["id"] for pair in update_tag_pairs}

    # Extract preserved content from destination
    # Only extracts content for tags that exist in update
    preserved_content = extract_preserved_content(destination_file, update_tag_ids)

    # Start with update file content as base
    result_content = update_content

    # Replace each tag's content with preserved user content
    # Keep initial content for new tags not in destination
    for tag_id, user_content in preserved_content.items():
        result_content = _replace_tag_content(result_content, tag_id, user_content)

    # Return final content (caller writes to destination)
    return result_content


def _replace_tag_content(content: str, tag_id: str, new_content: str) -> str:
    """Replace content within a specific WORKSCOPE-DEV tag.

    Finds the tag pair with the specified ID and replaces the content between
    the opening and closing tags with new_content. Preserves the tag markers
    themselves and all surrounding context.

    Args:
        content: Full file content containing the tag
        tag_id: Tag identifier to find and replace
        new_content: New content to insert between tag markers

    Returns:
        str: Content with tag's inner content replaced

    Raises:
        ValueError: If tag_id is not found in content
    """
    # Find opening tag
    opening_pattern = f"{_TAG_OPEN_PREFIX} {tag_id}>"
    open_start = content.find(opening_pattern)

    if open_start == -1:
        error_msg = f"Tag '{tag_id}' not found in content"
        raise ValueError(error_msg)

    # Find end of opening tag
    open_end = open_start + len(opening_pattern)

    # Find matching closing tag
    close_start = content.find(_TAG_CLOSE, open_end)

    if close_start == -1:
        error_msg = f"Closing tag not found for '{tag_id}'"
        raise ValueError(error_msg)

    # Build new content: before tag + opening tag + new content + closing tag + after tag
    return content[:open_end] + new_content + content[close_start:]


def _find_opening_tags(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Find all opening WORKSCOPE-DEV tags in content.

    Args:
        content: File content to search

    Returns:
        Tuple containing:
        - List of opening tag objects with id and pos fields
        - List of warning messages for invalid tag IDs
    """
    opening_tags: list[dict[str, Any]] = []
    warnings: list[str] = []
    pos = 0

    while True:
        start = content.find(_TAG_OPEN_PREFIX, pos)
        if start == -1:
            break

        # Find end of opening tag within bounded window
        end = content.find(">", start, start + MAX_OPENING_TAG_LENGTH)
        if end == -1:
            # No closing bracket within window - malformed opening tag
            line_num = _get_line_number(content, start)
            warnings.append(
                f"Opening tag missing closing '>' at line {line_num} "
                f"(position {start}). Tag will be skipped."
            )
            pos = start + 1
            continue

        tag_portion = content[start + 14 : end]
        tag_id = tag_portion.strip()

        if _is_valid_tag_id(tag_id):
            opening_tags.append({"id": tag_id, "pos": start})
        else:
            warnings.append(
                f"Invalid tag ID format at line {_get_line_number(content, start)}: '{tag_id}' "
                "(must be kebab-case, 3-50 chars)"
            )

        pos = end + 1

    return opening_tags, warnings


def _find_closing_tags(content: str) -> list[int]:
    """Find all closing WORKSCOPE-DEV tag positions in content.

    Args:
        content: File content to search

    Returns:
        List of character positions where closing tags start
    """
    closing_tags: list[int] = []
    pos = 0

    while True:
        close_pos = content.find(_TAG_CLOSE, pos)
        if close_pos == -1:
            break
        closing_tags.append(close_pos)
        pos = close_pos + len(_TAG_CLOSE)

    return closing_tags


def _check_tag_counts(opening_count: int, closing_count: int) -> list[str]:
    """Check that opening and closing tag counts match.

    Args:
        opening_count: Number of opening tags found
        closing_count: Number of closing tags found

    Returns:
        List of error messages (empty if counts match)
    """
    if opening_count == closing_count:
        return []

    if opening_count > closing_count:
        return [
            f"Incomplete tags: {opening_count} opening tags but only {closing_count} closing tags"
        ]

    return [
        f"Orphaned closing tags: {closing_count} closing tags but only {opening_count} opening tags"
    ]


def _check_nested_tags(opening_tags: list[dict[str, Any]], closing_tags: list[int]) -> list[str]:
    """Check for nested WORKSCOPE-DEV tags.

    Args:
        opening_tags: List of opening tag objects with id and pos fields
        closing_tags: List of closing tag positions

    Returns:
        List of error messages for detected nested tags
    """
    errors: list[str] = []

    for i, opening in enumerate(opening_tags):
        if i >= len(closing_tags):
            break

        open_pos = opening["pos"]
        close_pos = closing_tags[i]

        # Check if any other opening tag appears between this pair
        for j, other_opening in enumerate(opening_tags):
            if j != i and open_pos < other_opening["pos"] < close_pos:
                errors.append(
                    f"Nested tag detected: tag '{other_opening['id']}' at position "
                    f"{other_opening['pos']} is nested within tag '{opening['id']}' "
                    f"at position {open_pos}"
                )

    return errors


def validate_tag_pairs(content: str, file_path: Path | None = None) -> dict[str, Any]:
    """Validate WORKSCOPE-DEV tag pairs in content.

    Performs comprehensive validation of tag pairs including:
    - Matching opening/closing tags
    - No nested tags
    - Tag completeness (all opened tags are closed)
    - Malformed tag detection

    Logs warnings for malformed tags:
    - Orphaned closing tags

    Args:
        content: File content to validate
        file_path: Optional path to file being validated (for warning messages)

    Returns:
        Validation result dictionary containing:
        - valid: True if all validations pass, False otherwise (bool)
        - errors: List of validation error messages (list[str])
        - warnings: List of non-fatal warnings (list[str])
        - tag_count: Number of valid tag pairs found (int)
    """
    # Find opening tags with warnings
    opening_tags, warnings = _find_opening_tags(content)

    # Find closing tags
    closing_tags = _find_closing_tags(content)

    # Check tag counts match
    count_errors = _check_tag_counts(len(opening_tags), len(closing_tags))

    # Log warning for orphaned closing tags
    if file_path and len(closing_tags) > len(opening_tags):
        orphan_count = len(closing_tags) - len(opening_tags)
        logger.warning(
            f"Malformed WORKSCOPE-DEV tags in {file_path}: "
            f"Found {orphan_count} orphaned closing tag(s) "
            f"({len(closing_tags)} closing vs {len(opening_tags)} opening). "
            "Orphaned closing tags will be treated as regular text. "
            "Check for missing opening tags or extra closing tags."
        )

    # Check for nested tags
    nesting_errors = _check_nested_tags(opening_tags, closing_tags)

    # Combine all errors
    errors = count_errors + nesting_errors

    # Get valid tag pairs
    valid_pairs = find_tag_pairs(content, file_path)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "tag_count": len(valid_pairs),
    }


def _is_valid_tag_id(tag_id: str) -> bool:
    """Validate tag ID matches kebab-case pattern (3-50 chars).

    Tag ID must:
    - Be 3-50 characters long
    - Start and end with lowercase letter or digit
    - Contain only lowercase letters, digits, and hyphens
    - Not have consecutive hyphens

    Args:
        tag_id: Tag identifier string to validate

    Returns:
        True if tag ID is valid kebab-case, False otherwise
    """
    # Check length constraints
    if len(tag_id) < 3 or len(tag_id) > 50:
        return False

    # Check start and end characters (must be lowercase alphanumeric)
    if not (tag_id[0].isalnum() and (not tag_id[0].isalpha() or tag_id[0].islower())):
        return False
    if not (tag_id[-1].isalnum() and (not tag_id[-1].isalpha() or tag_id[-1].islower())):
        return False

    # Check all characters are valid (lowercase alphanumeric or hyphen)
    return all(char.islower() or char.isdigit() or char == "-" for char in tag_id)


# ==============================================================================
# COLLISION DETECTION
# ==============================================================================


def detect_collisions(source_dir: Path, target_dir: Path) -> tuple[list[str], list[str]]:
    """Detect file collisions with hash-based categorization.

    Implements hash-based collision detection from Content-Hashing-Overview.md § Hash
    Comparison for Installation. Scans source directory for all files (excluding
    installation_only files), and categorizes path collisions as either true collisions
    (different content) or false positives (identical content).

    Special cases handled:
    - .wsd file presence indicates update scenario (not a collision)
    - installation_only files excluded from collision check

    Note: Directory structure requirements are handled separately via the
    required_directories field in wsd.json, not through collision detection.

    Args:
        source_dir: Path to WSD Runtime root directory (contains wsd.json)
        target_dir: Path to target installation directory to check for collisions

    Returns:
        tuple: (true_collisions, false_positives)
            - true_collisions: Files with path AND content conflict
            - false_positives: Files with matching content (safe to overwrite)

    Raises:
        FileNotFoundError: If source_dir or target_dir does not exist
        ValueError: If wsd.json is missing or invalid in source_dir
    """
    if not source_dir.exists():
        error_msg = f"Source directory does not exist: {source_dir}"
        raise FileNotFoundError(error_msg)

    if not target_dir.exists():
        error_msg = f"Target directory does not exist: {target_dir}"
        raise FileNotFoundError(error_msg)

    # Read WSD metadata to get installation_only list and file_hashes
    try:
        metadata = read_wsd_metadata(source_dir)
        installation_only = metadata.installation_only
        installation_only_set = set(installation_only)
        source_hashes = metadata.file_hashes
    except (FileNotFoundError, ValueError) as e:
        error_msg = f"Failed to read WSD metadata from {source_dir}: {e}"
        raise ValueError(error_msg) from e

    # Collect all source files and filter out installation_only files and .wsdkeep
    # (.wsdkeep files are structural artifacts handled via required_directories)
    all_source_files = collect_wsd_files(source_dir)
    source_files = [
        p for p in all_source_files if str(p) not in installation_only_set and p.name != ".wsdkeep"
    ]

    true_collisions: list[str] = []
    false_positives: list[str] = []

    # Check each source file against target directory
    for source_file in source_files:
        # Skip .wsd manifest file (indicates update scenario, not collision)
        if source_file.name == ".wsd":
            continue

        # Check if file exists in target directory
        target_file = target_dir / source_file
        if target_file.exists():
            # Path collision detected - check content hash
            relative_path_str = str(source_file)
            source_hash = source_hashes.get(relative_path_str)

            if source_hash is None:
                # Missing hash indicates manifest out of sync
                error_msg = (
                    f"Missing hash for '{relative_path_str}' in wsd.json manifest. "
                    "The manifest may be out of sync with source files. "
                    "Regenerate wsd.json with pre_staging.py."
                )
                raise ValueError(error_msg)

            # Calculate target file hash
            try:
                target_hash = calculate_file_hash(target_file)

                if target_hash == source_hash:
                    # Content identical - false positive collision
                    false_positives.append(relative_path_str)
                else:
                    # Content differs - true collision
                    true_collisions.append(relative_path_str)
            except (OSError, FileNotFoundError):
                # Cannot read target file - treat as true collision
                true_collisions.append(relative_path_str)

    return (true_collisions, false_positives)


# ==============================================================================
# COLLISION REPORTING
# ==============================================================================


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes as human-readable string.

    Converts raw byte counts to human-readable format with appropriate units
    (bytes, KB, MB, GB). Uses 1024 as the divisor for binary units.

    Args:
        size_bytes: File size in bytes

    Returns:
        Human-readable file size string. Examples: "244 bytes", "1.2 KB", "3.5 MB"
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    if size_bytes < 1024 * 1024:
        kb = size_bytes / 1024
        return f"{kb:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        mb = size_bytes / (1024 * 1024)
        return f"{mb:.1f} MB"
    gb = size_bytes / (1024 * 1024 * 1024)
    return f"{gb:.1f} GB"


def report_collision_error(
    true_collisions: list[str],
    target_dir: Path,
    retry_command: str,
) -> NoReturn:
    """Report file collision error and exit with error code.

    Implements hash-based collision reporting from Content-Hashing-Overview.md § User
    Communication. Reports true collisions (files with different content) and exits
    with error code to block installation.

    Args:
        true_collisions: Files with path AND content conflict (blocks installation)
        target_dir: Target installation directory path (for finding file sizes)
        retry_command: Command string to retry installation after resolving conflicts

    Raises:
        SystemExit: Always exits with code 1 after reporting collision error
    """
    # Print error header
    print("Error: Installation aborted due to file collisions.", file=sys.stderr)
    print(file=sys.stderr)
    print("The following files exist with different content:", file=sys.stderr)

    # List true collisions with sizes
    for collision_path in true_collisions:
        full_path = target_dir / collision_path
        try:
            size_bytes = full_path.stat().st_size
            size_str = format_file_size(size_bytes)
            print(
                f"  - {collision_path} ({size_str}) - content differs from WSD template",
                file=sys.stderr,
            )
        except (FileNotFoundError, OSError):
            # If we can't get size, still report the collision
            print(
                f"  - {collision_path} - content differs from WSD template",
                file=sys.stderr,
            )

    print(file=sys.stderr)

    # Provide actionable resolution steps
    print("Please resolve these conflicts before installing WSD:", file=sys.stderr)
    print("  1. Rename or move existing files", file=sys.stderr)
    print("  2. Delete files if they can be replaced by WSD templates", file=sys.stderr)
    print("  3. Use --force to overwrite all conflicting files", file=sys.stderr)
    print(file=sys.stderr)
    print("After resolving conflicts, retry:", file=sys.stderr)
    print(f"  {retry_command}", file=sys.stderr)

    # Exit with error code
    sys.exit(1)


# ==============================================================================
# INSTALLATION VALIDATION AND ERROR REPORTING
# ==============================================================================


def validate_target_is_directory(target_path: Path) -> None:
    """Validate that target path is a directory (not a file).

    Checks if target path exists and is a directory. If target exists but is
    a file (not directory), raises error with actionable message.

    Args:
        target_path: Path to validate as directory

    Raises:
        ValueError: If target_path exists but is a file, not a directory
    """
    if target_path.exists() and not target_path.is_dir():
        error_msg = (
            f"Error: Target path '{target_path}' is a file, not a directory.\n"
            "\n"
            "Specify a directory path for installation."
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def validate_source_directory_exists(source_dir: Path) -> None:
    """Validate that source directory exists.

    Args:
        source_dir: Path to WSD Runtime root directory to validate

    Raises:
        SystemExit: If source directory does not exist (exits with code 1)
    """
    if not source_dir.exists():
        error_msg = (
            "Error: WSD source directory not found.\n"
            "\n"
            "This appears to be a packaging issue. Please reinstall WSD."
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def calculate_required_disk_space(source_dir: Path, installation_only: list[str]) -> int:
    """Calculate total disk space required for installation.

    Scans source directory and sums file sizes for all files that will be
    installed (excluding installation_only files).

    Args:
        source_dir: Path to WSD Runtime root directory
        installation_only: List of files to exclude from installation

    Returns:
        Total bytes required for installation

    Raises:
        OSError: If file size calculation fails
        WsdCollectionError: If invalid content found in source directory
    """
    total_bytes = 0
    installation_only_set = set(installation_only)

    try:
        all_source_files = collect_wsd_files(source_dir)
        source_files = [p for p in all_source_files if str(p) not in installation_only_set]

        for relative_path in source_files:
            file_path = source_dir / relative_path
            if file_path.exists():
                total_bytes += file_path.stat().st_size

    except OSError as e:
        error_msg = f"Failed to calculate required disk space: {e}"
        raise OSError(error_msg) from e

    return total_bytes


def get_available_disk_space(path: Path) -> int:
    """Get available disk space at specified path.

    Args:
        path: Path to check available disk space (directory or file's parent)

    Returns:
        Available bytes on filesystem containing path

    Raises:
        OSError: If disk space check fails
    """
    try:
        stat_result = os.statvfs(path if path.is_dir() else path.parent)
        # Available space = fragment size * available fragments
        return stat_result.f_bavail * stat_result.f_frsize
    except OSError as e:
        error_msg = f"Failed to check available disk space: {e}"
        raise OSError(error_msg) from e


def validate_sufficient_disk_space(
    source_dir: Path, target_dir: Path, installation_only: list[str]
) -> None:
    """Validate that target has sufficient disk space for installation.

    Calculates space required for all files to be installed and compares
    against available space on target filesystem. Exits with error if
    insufficient space detected.

    Args:
        source_dir: Path to WSD Runtime root directory
        target_dir: Path to target installation directory (or its parent if not created)
        installation_only: List of files to exclude from installation

    Raises:
        SystemExit: If insufficient disk space (exits with code 1)
    """
    try:
        required_bytes = calculate_required_disk_space(source_dir, installation_only)

        # Check space on target (or parent if target doesn't exist yet)
        check_path = target_dir if target_dir.exists() else target_dir.parent
        available_bytes = get_available_disk_space(check_path)

        if available_bytes < required_bytes:
            required_mb = required_bytes / (1024 * 1024)
            available_mb = available_bytes / (1024 * 1024)

            error_msg = (
                "Error: Insufficient disk space for installation.\n"
                "\n"
                f"Required: {required_mb:.1f} MB\n"
                f"Available: {available_mb:.1f} MB\n"
                "\n"
                "Free up disk space and retry."
            )
            print(error_msg, file=sys.stderr)
            sys.exit(1)

    except OSError as e:
        # If we can't check disk space, log warning but don't block installation
        # The actual copy operations will fail if space is truly insufficient
        print(
            f"Warning: Unable to check disk space: {e}",
            file=sys.stderr,
        )


def report_permission_error(operation: str, path: Path, error: OSError) -> NoReturn:
    """Report permission denied error and exit.

    Formats permission error with actionable guidance and exits with code 1.

    Args:
        operation: Description of operation that failed (e.g., "creating directory")
        path: Path where permission was denied
        error: Original OSError that occurred

    Raises:
        SystemExit: Always exits with code 1 after reporting error
    """
    if "creating directory" in operation.lower():
        error_msg = (
            f"Error: Permission denied creating directory '{path}'\n"
            "\n"
            "Check that you have write permissions to the parent directory."
        )
    elif "writing" in operation.lower() or "copying" in operation.lower():
        error_msg = (
            f"Error: Permission denied writing to '{path}'\n"
            "\n"
            "Check that you have write permissions to this directory."
        )
    else:
        error_msg = (
            f"Error: Permission denied during {operation} for '{path}'\n"
            "\n"
            f"Details: {error}\n"
            "\n"
            "Check file and directory permissions and retry."
        )

    print(error_msg, file=sys.stderr)
    sys.exit(1)


def report_installation_error(
    message: str,
    details: str = "",
    recovery_steps: list[str] | None = None,
) -> NoReturn:
    """Report installation error with formatted message and exit.

    Prints error message to stderr following the standard error reporting format:
    - Brief error description
    - Detailed explanation
    - Actionable recovery steps

    Args:
        message: Brief error description
        details: Detailed explanation of the error (optional)
        recovery_steps: List of actionable steps to resolve (optional)

    Raises:
        SystemExit: Always exits with code 1 after reporting error
    """
    print(f"Error: {message}", file=sys.stderr)

    if details:
        print(file=sys.stderr)
        print(details, file=sys.stderr)

    if recovery_steps:
        print(file=sys.stderr)
        for i, step in enumerate(recovery_steps, 1):
            print(f"  {i}. {step}", file=sys.stderr)

    sys.exit(1)


# ==============================================================================
# INSTALLATION FILE OPERATIONS
# ==============================================================================


def install_files(source_dir: Path, target_dir: Path, force: bool = False) -> list[str]:  # noqa: PLR0912, PLR0915
    """Install WSD Runtime files from source to target directory.

    Implements installation file operations from Installation-System.md
    § File Copying Process with comprehensive error handling and atomic
    operation guarantees.

    Atomic operation guarantee (§ Atomic Operation Guarantee):
    1. All validation performed before any file operations
    2. Installation aborts immediately on first copy error
    3. Automatic rollback removes all partial files and empty directories
    4. .wsd manifest created only after successful file installation
    5. No partial installations - either completes fully or fails cleanly

    Rollback behavior (§ Rollback Mechanism):
    When a file copy operation fails, automatic rollback is performed:
    - All successfully copied files are deleted in reverse order
    - Empty directories created during installation are removed bottom-up
    - Directories containing pre-existing user files are preserved
    - Rollback status is reported to stderr before the error message
    - Rollback uses best-effort cleanup (continues if individual deletes fail)

    Error handling (§ Error Handling):
    - Detects permission errors on directory creation and file writing
    - Validates target is directory (not file)
    - Validates source directory exists
    - Checks for sufficient disk space
    - Performs rollback cleanup before reporting errors
    - Provides clear error messages with resolution steps
    - Exits with appropriate error codes

    Args:
        source_dir: Path to WSD Runtime root directory (contains wsd.json)
        target_dir: Path to target installation directory
        force: If True, bypass collision blocking and overwrite files with
            different content. Prints warning when collisions are overwritten.

    Returns:
        List of relative file paths for all installed files (excluding
        installation_only files). Paths are relative to target_dir.

    Raises:
        SystemExit: On any validation or installation error (exits with code 1).
            Rollback is performed before exit when errors occur during file copy.
    """
    # ========================================================================
    # PRE-VALIDATION (NO FILE MODIFICATIONS)
    # ========================================================================
    # Per Installation-System.md § Atomic Operation Guarantee:
    # "Perform all validation checks first"
    # "Only begin file copying after all checks pass"

    verbose_log(f"Starting installation from {source_dir} to {target_dir}")

    # Validate source directory exists
    validate_source_directory_exists(source_dir)
    verbose_log("Source directory validated")

    # Validate target path is directory (not file)
    validate_target_is_directory(target_dir)

    # Read WSD metadata before any file operations
    # (may raise FileNotFoundError or ValueError if wsd.json missing/invalid)
    try:
        metadata = read_wsd_metadata(source_dir)
    except (FileNotFoundError, ValueError) as e:
        report_installation_error(
            "Failed to read WSD metadata",
            f"Cannot read wsd.json from source directory: {e}",
            ["Verify WSD installation is complete", "Reinstall WSD if necessary"],
        )

    installation_only = metadata.installation_only
    executable_files = metadata.executable
    wsd_version = metadata.version

    # Detect file collisions with hash-based categorization
    verbose_log("Checking for file collisions...")
    true_collisions, false_positives_list = detect_collisions(source_dir, target_dir)

    # Convert to set for O(1) lookup during file copy loop
    false_positives = set(false_positives_list)

    # Report false positives (informational - these files will be skipped)
    if false_positives:
        print(file=sys.stderr)
        fp_count = len(false_positives)
        print(
            f"Found {fp_count} existing file(s) with identical content (will skip copying):",
            file=sys.stderr,
        )
        for fp_path in sorted(false_positives):
            print(f"  - {fp_path}", file=sys.stderr)
        print(file=sys.stderr)

    # Report and block on true collisions (unless force is specified)
    if true_collisions and not force:
        report_collision_error(true_collisions, target_dir, f"wsd.py install --force {target_dir}")
    elif true_collisions and force:
        print(
            f"Warning: --force specified, overwriting {len(true_collisions)} file(s) "
            "with different content",
            file=sys.stderr,
        )

    # Validate sufficient disk space before any file operations
    validate_sufficient_disk_space(source_dir, target_dir, installation_only)

    # ========================================================================
    # FILE OPERATIONS (WITH ABORT-ON-ERROR)
    # ========================================================================
    # Per Installation-System.md § Atomic Operation Guarantee:
    # "If any copy operation fails, abort immediately"

    # Create target directory with permission error detection
    if not target_dir.exists():
        try:
            create_directories(target_dir)
        except OSError as e:
            # Check if permission error
            if e.errno == errno.EACCES:  # Permission denied
                report_permission_error("creating directory", target_dir, e)
            else:
                report_installation_error(
                    f"Failed to create target directory '{target_dir}'",
                    f"Details: {e}",
                    ["Check parent directory permissions", "Verify path is valid"],
                )

    # Get list of files to install
    # (excluding .wsdkeep files which are handled via required_directories)
    installation_only_set = set(installation_only)
    try:
        all_source_files = collect_wsd_files(source_dir)
        # Filter out installation_only files AND .wsdkeep files (structural artifacts)
        source_files = [
            p
            for p in all_source_files
            if str(p) not in installation_only_set and p.name != ".wsdkeep"
        ]
    except (FileNotFoundError, WsdCollectionError, OSError) as e:
        report_installation_error(
            "Failed to scan source directory",
            f"Cannot read files from source directory: {e}",
            ["Verify WSD installation is complete", "Check source directory permissions"],
        )

    # Get required directories from metadata for post-file-copy processing
    required_directories = metadata.required_directories

    installed_files: list[str] = []
    copied_file_paths: list[Path] = []
    skipped_count = 0

    verbose_log(f"Found {len(source_files)} files to install")
    verbose_log(f"Required directories: {len(required_directories)}")

    # Two-stage installation with rollback-on-error behavior
    # Stage 1: Copy regular files (establishes directory state)
    # Stage 2: Process required_directories (create dirs and add .wsdkeep if empty)
    try:
        # ====================================================================
        # STAGE 1: Process regular files
        # ====================================================================
        for relative_path in source_files:
            relative_path_str = str(relative_path)

            # Check if this file already exists with matching content
            if relative_path_str in false_positives:
                # Skip copying - file already exists with identical content
                # Still track for manifest, but NOT for rollback (file wasn't copied)
                verbose_log(f"Skipping (identical content): {relative_path}")
                installed_files.append(relative_path_str)
                skipped_count += 1
                continue

            source_file = source_dir / relative_path
            target_file = target_dir / relative_path

            # Track target file path BEFORE attempting copy
            # This ensures rollback catches partially-written files even if
            # copy_file() succeeds in writing but then raises an exception
            copied_file_paths.append(target_file)

            verbose_log(f"Copying: {relative_path}")

            # Copy file (copy_file creates parent directories automatically)
            # May raise PermissionError or OSError
            copy_file(source_file, target_file)

            # Only track as installed if copy succeeded
            installed_files.append(relative_path_str)

        # ====================================================================
        # STAGE 2: Process required_directories
        # ====================================================================
        # Directory state now reflects regular file operations.
        # For each required directory, ensure it exists and add .wsdkeep if empty.
        for dir_path_str in required_directories:
            target_directory = target_dir / dir_path_str

            # Ensure directory exists
            if not target_directory.exists():
                try:
                    create_directories(target_directory)
                    verbose_log(f"Created required directory: {dir_path_str}")
                except OSError as e:
                    # Propagate to outer exception handler for rollback
                    raise OSError(
                        f"Failed to create required directory '{dir_path_str}': {e}"
                    ) from e

            # Check if directory needs .wsdkeep based on final state
            if not _directory_needs_wsdkeep(target_directory):
                verbose_log(f"Skipping .wsdkeep for {dir_path_str}: directory has content")
                continue

            # Create .wsdkeep file in the empty directory
            wsdkeep_file = target_directory / ".wsdkeep"

            # Track for rollback
            copied_file_paths.append(wsdkeep_file)

            verbose_log(f"Creating .wsdkeep in: {dir_path_str}")

            # Create empty .wsdkeep file
            try:
                wsdkeep_file.write_text("")
            except OSError as e:
                # Propagate to outer exception handler for rollback
                raise OSError(f"Failed to create .wsdkeep in '{dir_path_str}': {e}") from e

    except PermissionError as e:
        # Permission denied on file writing - rollback and report
        rollback_partial_installation(copied_file_paths)
        report_permission_error("copying file", target_file, e)
    except TagParsingError as e:
        # Tag parsing error - rollback and report with actionable message
        rollback_partial_installation(copied_file_paths)
        report_installation_error(
            "Installation failed due to malformed WORKSCOPE-DEV tag",
            str(e),
            [
                "Fix the malformed tag in the source file",
                f"Retry installation: wsd.py install {target_dir}",
            ],
        )
    except OSError as e:
        # Other OS errors (disk full, invalid path, etc.) - rollback and report
        rollback_partial_installation(copied_file_paths)

        if e.errno == errno.ENOSPC:  # No space left on device
            report_installation_error(
                "Insufficient disk space during installation",
                f"Ran out of disk space while copying '{relative_path}'",
                ["Free up disk space", "Retry installation"],
            )
        else:
            # Generic OS error
            report_installation_error(
                f"Installation failed while copying '{relative_path}'",
                f"Details: {e}",
                [
                    "Check file and directory permissions",
                    "Verify disk space is available",
                    "Retry installation",
                ],
            )

    # Report skipped files summary
    if skipped_count > 0:
        copied_count = len(installed_files) - skipped_count
        print(
            f"Skipped {skipped_count} file(s) with identical content, "
            f"copied {copied_count} file(s)",
            file=sys.stderr,
        )

    # Apply executable permissions to designated files
    for executable_file_str in executable_files:
        # Only apply permissions if file was actually installed (not in installation_only)
        if executable_file_str not in installation_only:
            target_file = target_dir / executable_file_str
            if target_file.exists():
                try:
                    set_executable(target_file)
                except (PermissionError, OSError) as e:
                    # Permission errors on chmod are not fatal, just warn
                    print(
                        f"Warning: Could not set executable permission "
                        f"on {executable_file_str}: {e}",
                        file=sys.stderr,
                    )

    # ========================================================================
    # MANIFEST CREATION (ONLY AFTER SUCCESSFUL INSTALLATION)
    # ========================================================================
    # Per Installation-System.md § Atomic Operation Guarantee:
    # "Do not create .wsd manifest if installation incomplete"

    if installed_files:
        # Format timestamp as ISO 8601 without microseconds: YYYY-MM-DDTHH:MM:SSZ
        current_timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        tags: list[dict[str, str]] = []

        # Scan all installed files for WORKSCOPE-DEV tags
        # Wrap in try/except to trigger rollback on any error during tag scanning
        try:
            for relative_path_str in installed_files:
                absolute_file_path = target_dir / relative_path_str

                # Skip binary files - they can't contain WORKSCOPE-DEV tags
                if _is_binary_file(absolute_file_path):
                    continue

                # Read file content - let exceptions propagate for rollback
                with absolute_file_path.open("r", encoding="utf-8") as f:
                    content = f.read()

                # Extract tag IDs from opening tags using simple string search
                pos = 0
                while True:
                    start = content.find(_TAG_OPEN_PREFIX, pos)
                    if start == -1:
                        break

                    # Find end of opening tag within bounded window
                    end = content.find(">", start, start + MAX_OPENING_TAG_LENGTH)
                    if end == -1:
                        # No closing bracket within window - malformed opening tag
                        # Per Design Decision 12: halt on any error
                        line_num = _get_line_number(content, start)
                        raise TagParsingError(
                            f"Opening tag missing closing '>' within "
                            f"{MAX_OPENING_TAG_LENGTH} characters",
                            file_path=relative_path_str,
                            line_number=line_num,
                        )

                    tag_portion = content[start + 14 : end]
                    tag_id = tag_portion.strip()

                    # Validate tag ID using shared validation utility
                    if _is_valid_tag_id(tag_id):
                        tags.append({"id": tag_id, "file": relative_path_str})

                    pos = end + 1

        except (TagParsingError, OSError, UnicodeDecodeError) as e:
            # Tag scanning error after files were copied - rollback and report
            rollback_partial_installation(copied_file_paths)
            if isinstance(e, TagParsingError):
                report_installation_error(
                    "Installation failed due to malformed WORKSCOPE-DEV tag",
                    str(e),
                    [
                        "Fix the malformed tag in the source file",
                        f"Retry installation: wsd.py install {target_dir}",
                    ],
                )
            else:
                report_installation_error(
                    "Installation failed while scanning files for tags",
                    str(e),
                    [
                        "Check file permissions and encoding",
                        f"Retry installation: wsd.py install {target_dir}",
                    ],
                )

        # Filter out .wsdkeep files from manifest (structural artifacts, not tracked)
        manifest_files = [f for f in installed_files if Path(f).name != ".wsdkeep"]

        # Create manifest structure
        manifest = create_manifest(
            version=wsd_version,
            files=manifest_files,
            tags=tags,
            created=current_timestamp,
            updated=current_timestamp,
        )

        # Write manifest to .wsd file
        try:
            manifest_path = target_dir / ".wsd"
            write_manifest(manifest, manifest_path)
        except (PermissionError, OSError) as e:
            report_installation_error(
                "Failed to create .wsd manifest file",
                f"Installation completed but manifest could not be written: {e}",
                [
                    "This may indicate a permission or disk space issue",
                    "Check directory permissions and available disk space",
                    "You may need to reinstall WSD after resolving the issue",
                ],
            )

    return installed_files


# ==============================================================================
# CLI COMMAND HANDLERS
# ==============================================================================


def handle_install_command(args: list[str]) -> None:  # noqa: PLR0912, PLR0915
    """Handle install command with argument parsing including --dry-run flag.

    Implements CLI command handling for `wsd.py install [OPTIONS] <target-path>`.
    Parses command-line arguments, validates options, detects installation mode
    (fresh vs update), and dispatches to appropriate installation or update logic
    with dry-run support.

    Command syntax:
        wsd.py install [--dry-run] [--force] [--verbose] <target-path>

    Args:
        args: Command-line arguments after 'install' (e.g., ['--dry-run', '.'])

    Raises:
        SystemExit: On invalid arguments, validation errors, or installation errors

    Note:
        Function complexity is acceptable for CLI handler orchestrating multiple operations.
    """
    # Parse arguments
    dry_run = False
    force = False
    verbose = False
    target_path_str = None

    for arg in args:
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--force":
            force = True
        elif arg in {"--verbose", "-v"}:
            verbose = True
        elif not arg.startswith("--") and arg != "-v":
            if target_path_str is not None:
                print("Error: Multiple target paths specified", file=sys.stderr)
                print(
                    "\nUsage: wsd.py install [--dry-run] [--force] [--verbose] <target-path>",
                    file=sys.stderr,
                )
                sys.exit(1)
            target_path_str = arg
        else:
            print(f"Error: Unknown option '{arg}'", file=sys.stderr)
            print(
                "\nUsage: wsd.py install [--dry-run] [--force] [--verbose] <target-path>",
                file=sys.stderr,
            )
            sys.exit(1)

    # Enable verbose mode if requested
    if verbose:
        set_verbose_mode(True)
        verbose_log("Verbose mode enabled for installation")

    # Validate target path provided
    if target_path_str is None:
        print("Error: Target path required", file=sys.stderr)
        print(
            "\nUsage: wsd.py install [--dry-run] [--force] [--verbose] <target-path>",
            file=sys.stderr,
        )
        print("\nExamples:", file=sys.stderr)
        print("  wsd.py install .", file=sys.stderr)
        print("  wsd.py install --verbose /path/to/project", file=sys.stderr)
        sys.exit(1)

    # Convert target path string to Path object
    target_path = Path(target_path_str).resolve()

    # Get source directory (directory containing this wsd.py script)
    source_dir = Path(__file__).parent.resolve()

    # Detect installation mode (fresh or update)
    mode_result = detect_installation_mode(target_path)

    # Handle update scenario (manifest exists)
    if mode_result.mode == "update" and not force:
        # Redirect to update logic, preserving flags
        update_args = []
        if dry_run:
            update_args.append("--dry-run")
        if verbose:
            update_args.append("--verbose")
        update_args.append(target_path_str)
        handle_update_command(update_args)
        return

    # Handle fresh installation or forced reinstall
    if dry_run:
        print("Error: --dry-run not supported for fresh installation", file=sys.stderr)
        print("\nThe --dry-run flag is only available for updates.", file=sys.stderr)
        print("For fresh installations, WSD performs collision detection", file=sys.stderr)
        print("and will abort if any files would be overwritten.", file=sys.stderr)
        sys.exit(1)

    # Perform fresh installation
    # (install_files handles collision detection and all validation)
    installed_file_list = install_files(source_dir, target_path, force=force)

    print(f"\n✅ WSD installed successfully to {target_path}")
    print(f"Installed {len(installed_file_list)} files")


def handle_update_command(args: list[str]) -> None:  # noqa: PLR0912, PLR0915
    """Handle update command with argument parsing including --dry-run flag.

    Implements CLI command handling for `wsd.py update [OPTIONS] <target-path>`.
    Parses command-line arguments, validates options, performs update detection,
    categorizes files, and either generates dry-run preview or executes update.

    Command syntax:
        wsd.py update [--dry-run] [--verbose] <target-path>

    Args:
        args: Command-line arguments after 'update' (e.g., ['--dry-run', '.'])

    Raises:
        SystemExit: On invalid arguments, validation errors, or update errors

    Note:
        Function complexity is acceptable for CLI handler orchestrating multiple operations.
    """
    # Parse arguments
    dry_run = False
    verbose = False
    target_path_str = None

    for arg in args:
        if arg == "--dry-run":
            dry_run = True
        elif arg in {"--verbose", "-v"}:
            verbose = True
        elif not arg.startswith("--") and arg != "-v":
            if target_path_str is not None:
                print("Error: Multiple target paths specified", file=sys.stderr)
                print(
                    "\nUsage: wsd.py update [--dry-run] [--verbose] <target-path>", file=sys.stderr
                )
                sys.exit(1)
            target_path_str = arg
        else:
            print(f"Error: Unknown option '{arg}'", file=sys.stderr)
            print("\nUsage: wsd.py update [--dry-run] [--verbose] <target-path>", file=sys.stderr)
            sys.exit(1)

    # Enable verbose mode if requested
    if verbose:
        set_verbose_mode(True)
        verbose_log("Verbose mode enabled for update")

    # Validate target path provided
    if target_path_str is None:
        print("Error: Target path required", file=sys.stderr)
        print("\nUsage: wsd.py update [--dry-run] [--verbose] <target-path>", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  wsd.py update .", file=sys.stderr)
        print("  wsd.py update --verbose /path/to/project", file=sys.stderr)
        sys.exit(1)

    # Convert target path string to Path object
    target_path = Path(target_path_str).resolve()

    # Get source directory (directory containing this wsd.py script)
    source_dir = Path(__file__).parent.resolve()

    # Detect installation mode - must be update mode
    mode_result = detect_installation_mode(target_path)

    if mode_result.mode != "update":
        print("Error: No WSD installation found", file=sys.stderr)
        print(f"\nTarget directory does not contain .wsd manifest: {target_path}", file=sys.stderr)
        print("\nTo install WSD, run:", file=sys.stderr)
        print(f"  wsd.py install {target_path_str}", file=sys.stderr)
        sys.exit(1)

    # Extract installed version and files from manifest
    assert mode_result.version is not None
    assert mode_result.files is not None
    assert mode_result.manifest_data is not None

    current_version = mode_result.version
    installed_files = mode_result.files
    original_manifest = mode_result.manifest_data

    # Read update source metadata
    try:
        update_metadata = read_wsd_metadata(source_dir)
    except (FileNotFoundError, ValueError) as e:
        print("Error: Failed to read WSD metadata from source", file=sys.stderr)
        print(f"\nCannot read wsd.json: {e}", file=sys.stderr)
        print("\nVerify you are running from a valid WSD source directory", file=sys.stderr)
        sys.exit(1)

    update_version = update_metadata.version

    # Edge case detection (concurrent updates, temp files)
    # Only perform these checks for actual updates, skip for dry-run
    if not dry_run:
        manifest_path = target_path / ".wsd"

        # Check for concurrent updates
        if detect_concurrent_update(manifest_path):
            warn_concurrent_update()
            if not confirm_concurrent_update():
                print("\nUpdate cancelled by user.", file=sys.stderr)
                sys.exit(0)

        # Check for temporary update files (informational only, non-blocking)
        if has_temp_update_files(target_path):
            warn_temp_update_files(target_path)

    # Categorize files for update
    categorization = categorize_update_files(
        installed_files=installed_files,
        update_source_dir=source_dir,
        update_metadata=update_metadata,
        target_dir=target_path,
    )

    # Pre-update validation (only for actual updates, skip for dry-run)
    if not dry_run:
        validate_update_preconditions(
            categorization=categorization,
            target_dir=target_path,
            source_dir=source_dir,
        )

    # Handle dry-run mode
    if dry_run:
        # Generate preview report and exit (no modifications)
        generate_dry_run_preview(
            categorization=categorization,
            current_version=current_version,
            update_version=update_version,
            target_path=target_path,
            installed_files=installed_files,
            required_directories=update_metadata.required_directories,
        )
        sys.exit(0)

    # Create rollback point before file operations
    manifest_path = target_path / ".wsd"
    rollback_point = create_rollback_point(
        manifest_data=original_manifest,
        manifest_path=manifest_path,
        target_dir=target_path,
    )

    # ========================================================================
    # TWO-STAGE UPDATE PROCESSING
    # ========================================================================
    # Stage 1: Process regular files (establishes directory state)
    # Stage 2: Process required_directories (create dirs, add .wsdkeep if empty)
    #
    # .wsdkeep files are no longer tracked in manifests or file lists. Instead,
    # required_directories declares which directories WSD needs, and .wsdkeep
    # files are generated locally based on directory state after file operations.

    # Filter out .wsdkeep files from all categories (they're handled via required_directories)
    files_to_delete = [f for f in categorization.to_delete if Path(f).name != ".wsdkeep"]
    files_to_add = [f for f in categorization.to_add if Path(f).name != ".wsdkeep"]
    files_to_update = [f for f in categorization.to_update if Path(f).name != ".wsdkeep"]

    # Get required directories from update source metadata
    required_directories = update_metadata.required_directories

    verbose_log(
        f"Update file counts: delete={len(files_to_delete)}, "
        f"add={len(files_to_add)}, update={len(files_to_update)}"
    )
    verbose_log(f"Required directories: {len(required_directories)}")

    # Track actual operations performed for manifest and statistics
    actual_deleted: list[str] = []
    actual_added: list[str] = []
    actual_updated: list[str] = []

    # Execute actual update (non-dry-run) with rollback capability
    try:
        # ====================================================================
        # STAGE 1: Process regular files (establishes directory state)
        # ====================================================================

        # Delete files
        for relative_path in files_to_delete:
            file_path = target_path / relative_path
            verbose_log(f"Deleting: {relative_path}")
            delete_file(file_path)
            logger.info(f"Deleted: {relative_path}")
            actual_deleted.append(relative_path)

        # Add files
        executable_set = set(update_metadata.executable)
        for relative_path in files_to_add:
            source_file = source_dir / relative_path
            target_file = target_path / relative_path
            verbose_log(f"Adding: {relative_path}")
            copy_file(source_file, target_file)
            if relative_path in executable_set:
                set_executable(target_file)
            logger.info(f"Added: {relative_path}")
            actual_added.append(relative_path)

        # Update files with tag preservation
        for relative_path in files_to_update:
            source_path = source_dir / relative_path
            dest_path = target_path / relative_path
            verbose_log(f"Updating: {relative_path}")

            # Check for WORKSCOPE-DEV tags
            try:
                source_content = source_path.read_text(encoding="utf-8")
                tags_in_file = find_tag_pairs(source_content, source_path)
            except (OSError, UnicodeDecodeError):
                tags_in_file = []

            if tags_in_file:
                # Tags present - use preservation algorithm
                preserved_content = preserve_tag_content(source_path, dest_path)
                dest_path.write_text(preserved_content, encoding="utf-8")
            else:
                # No tags - perform simple file copy
                copy_file(source_path, dest_path)

            if relative_path in executable_set:
                set_executable(dest_path)
            logger.info(f"Updated: {relative_path}")
            actual_updated.append(relative_path)

        # ====================================================================
        # STAGE 2: Process required_directories
        # ====================================================================
        # Directory state now reflects regular file operations.
        # For each required directory, ensure it exists and add .wsdkeep if empty.
        for dir_path_str in required_directories:
            target_directory = target_path / dir_path_str

            # Ensure directory exists (may be new in updated WSD version)
            if not target_directory.exists():
                try:
                    create_directories(target_directory)
                    verbose_log(f"Created required directory: {dir_path_str}")
                except OSError as e:
                    raise OSError(
                        f"Failed to create required directory '{dir_path_str}': {e}"
                    ) from e

            # Check if directory needs .wsdkeep based on final state
            if not _directory_needs_wsdkeep(target_directory):
                verbose_log(f"Skipping .wsdkeep for {dir_path_str}: directory has content")
                continue

            # Create or restore .wsdkeep file in the empty directory
            wsdkeep_file = target_directory / ".wsdkeep"
            verbose_log(f"Creating .wsdkeep in: {dir_path_str}")

            try:
                wsdkeep_file.write_text("")
            except OSError as e:
                raise OSError(f"Failed to create .wsdkeep in '{dir_path_str}': {e}") from e

        # Skip protected files (just logging, no filesystem changes)
        skipped_count = execute_file_skips(
            to_skip=categorization.to_skip,
        )

        # Calculate counts from actual operations
        deleted_count = len(actual_deleted)
        added_count = len(actual_added)
        updated_count = len(actual_updated)

        # Create updated manifest with actual operations performed
        updated_manifest = create_updated_manifest(
            categorization=categorization,
            original_manifest=original_manifest,
            update_version=update_version,
            target_dir=target_path,
            actual_deleted=actual_deleted,
            actual_added=actual_added,
        )

    except (
        OSError,
        FileNotFoundError,
        PermissionError,
        ValueError,
        UnicodeDecodeError,
        IsADirectoryError,
        TagParsingError,
    ) as e:
        # Print actionable error message with recovery instructions
        print("\nError: Update operation failed", file=sys.stderr)
        print(f"\n{e}", file=sys.stderr)
        print("\nOperation halted. No partial changes have been committed.", file=sys.stderr)
        print("Fix the issue above and retry: wsd.py update <target-path>", file=sys.stderr)

        # Restore manifest and provide recovery instructions
        restore_manifest_on_error(rollback_point)
        sys.exit(1)

    # Write updated manifest
    try:
        write_manifest(updated_manifest, manifest_path)
    except (PermissionError, OSError) as e:
        error_msg = "Cannot update manifest file after file operations"
        details = (
            f"Location: {manifest_path}\n"
            f"Reason: {e}\n"
            f"\n"
            f"Files updated successfully, but manifest not updated.\n"
            f"This may cause issues with future updates."
        )
        recovery_steps = [
            f"Grant write permission to .wsd: chmod u+w {manifest_path}",
            "Then re-run update to sync manifest",
        ]
        report_installation_error(error_msg, details, recovery_steps)

    # Report success
    print(f"\n✅ WSD updated successfully to version {update_version}")
    summary = (
        f"Deleted: {deleted_count}, Added: {added_count}, "
        f"Updated: {updated_count}, Skipped: {skipped_count}"
    )
    print(summary)


if __name__ == "__main__":
    main()
