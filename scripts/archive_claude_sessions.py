"""Claude Code Session Archive Script.

Archives Claude Code session files from ~/.claude/projects/ to ~/ccarchives/
to preserve them before they are automatically purged by Claude Code.

Features:
- Creates ~/ccarchives/ directory if it doesn't exist
- Preserves the project directory organization from Claude Code
- Only copies files that have been modified since last archive (incremental)
- Handles removed session files gracefully
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_claude_sessions_dir() -> Path:
    """Get the Claude Code sessions directory path.

    Returns:
        Path to ~/.claude/projects directory.
    """
    return Path.home() / ".claude" / "projects"


def get_archive_dir() -> Path:
    """Get the archive directory path.

    Returns:
        Path to ~/ccarchives directory.
    """
    return Path.home() / "ccarchives"


def encode_project_path(project_path: Path) -> str:
    """Convert a project path to Claude Code's directory naming convention.

    Claude Code stores session files under ~/.claude/projects/ using a path-based
    naming convention where the absolute path has all '/' characters replaced with '-'.

    Args:
        project_path: Absolute path to the project directory.

    Returns:
        Encoded directory name (e.g., '/Users/gray/Projects/foo' -> '-Users-gray-Projects-foo').
    """
    return str(project_path).replace("/", "-")


def get_current_project_sessions_dir() -> Path | None:
    """Locate the current project's session directory under ~/.claude/projects/.

    Uses the current working directory to determine which Claude Code session
    directory corresponds to this project.

    Returns:
        Path to the project's session directory if it exists, None otherwise.
    """
    sessions_dir = get_claude_sessions_dir()
    if not sessions_dir.exists():
        return None

    encoded_name = encode_project_path(Path.cwd())
    project_sessions_dir = sessions_dir / encoded_name

    if project_sessions_dir.exists() and project_sessions_dir.is_dir():
        return project_sessions_dir

    return None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace with 'all' boolean attribute.
    """
    parser = argparse.ArgumentParser(
        description="Archive Claude Code session files to preserve them before automatic purge.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="archive_all",
        help="Archive sessions for all projects (default: current project only)",
    )

    return parser.parse_args()


def ensure_archive_dir_exists(archive_dir: Path) -> None:
    """Create the archive directory if it doesn't exist.

    Args:
        archive_dir: Path to archive directory to create.
    """
    archive_dir.mkdir(parents=True, exist_ok=True)
    print(f"Archive directory ready: {archive_dir}")


def should_copy_file(source: Path, dest: Path) -> bool:
    """Determine if a file should be copied based on modification time.

    Args:
        source: Source file path to check.
        dest: Destination file path to compare against.

    Returns:
        True if destination doesn't exist or source is newer than destination.
    """
    if not dest.exists():
        return True

    source_mtime = source.stat().st_mtime
    dest_mtime = dest.stat().st_mtime

    return source_mtime > dest_mtime


def archive_sessions(project_dirs: list[Path]) -> tuple[int, int, int]:
    """Archive Claude Code session files for specified project directories.

    Args:
        project_dirs: List of project session directories to archive.

    Returns:
        Tuple of (copied_count, skipped_count, error_count).
    """
    archive_dir = get_archive_dir()
    ensure_archive_dir_exists(archive_dir)

    copied_count = 0
    skipped_count = 0
    error_count = 0

    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue

        # Create corresponding archive project directory
        archive_project_dir = archive_dir / project_dir.name
        archive_project_dir.mkdir(parents=True, exist_ok=True)

        # Archive all .jsonl session files in this project
        for session_file in project_dir.glob("*.jsonl"):
            try:
                dest_file = archive_project_dir / session_file.name

                if should_copy_file(session_file, dest_file):
                    shutil.copy2(session_file, dest_file)
                    copied_count += 1
                    print(f"✓ Archived: {project_dir.name}/{session_file.name}")
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                print(f"✗ Error archiving {session_file}: {e}", file=sys.stderr)

    return copied_count, skipped_count, error_count


def main() -> int:
    """Archive Claude Code session files to preserve them.

    By default, archives only the current project's sessions. Use --all to archive
    sessions for all projects.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    args = parse_args()

    print("Claude Code Session Archiver")
    print("=" * 50)

    try:
        # Determine which project directories to archive
        if args.archive_all:
            sessions_dir = get_claude_sessions_dir()
            if not sessions_dir.exists():
                print(f"Claude Code sessions directory not found: {sessions_dir}")
                print("No sessions to archive.")
                return 0

            project_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
            print(f"Archiving all projects ({len(project_dirs)} found)")
        else:
            current_project_dir = get_current_project_sessions_dir()
            if current_project_dir is None:
                sessions_dir = get_claude_sessions_dir()
                expected_path = sessions_dir / encode_project_path(Path.cwd())
                print(
                    "Error: No Claude Code session directory found for this project.",
                    file=sys.stderr,
                )
                print(f"Expected: {expected_path}", file=sys.stderr)
                print("Use --all to archive sessions for all projects.", file=sys.stderr)
                return 1

            project_dirs = [current_project_dir]
            print(f"Archiving current project: {current_project_dir.name}")

        print()

        copied, skipped, errors = archive_sessions(project_dirs)

        print()
        print("=" * 50)
        print("Summary:")
        print(f"  Files copied: {copied}")
        print(f"  Files skipped (unchanged): {skipped}")
        print(f"  Errors: {errors}")

        if errors > 0:
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nArchive interrupted by user.", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\n\nFatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
