"""Claude Code Session Archive Script.

Archives Claude Code session files from ~/.claude/projects/ to ~/ccarchives/
to preserve them before they are automatically purged by Claude Code.

Features:
- Creates ~/ccarchives/ directory if it doesn't exist
- Preserves the project directory organization from Claude Code
- Only copies files that have been modified since last archive (incremental)
- Handles removed session files gracefully
"""

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


def archive_sessions() -> tuple[int, int, int]:
    """Archive all Claude Code session files.

    Returns:
        Tuple of (copied_count, skipped_count, error_count)
    """
    sessions_dir = get_claude_sessions_dir()
    archive_dir = get_archive_dir()

    if not sessions_dir.exists():
        print(f"Claude Code sessions directory not found: {sessions_dir}")
        print("No sessions to archive.")
        return 0, 0, 0

    ensure_archive_dir_exists(archive_dir)

    copied_count = 0
    skipped_count = 0
    error_count = 0

    # Iterate through all project directories
    for project_dir in sessions_dir.iterdir():
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

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    print("Claude Code Session Archiver")
    print("=" * 50)

    try:
        copied, skipped, errors = archive_sessions()

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
