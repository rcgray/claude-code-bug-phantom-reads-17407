"""Script to manage prompt files using symlinks to timestamped archives.

All actual prompt files are created in archive/ with timestamps.
Prompts-Current.md and Prompts-Previous.md are symlinks pointing to archive files.
"""

import shutil
from datetime import datetime
from pathlib import Path

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "dev" / "prompts"
ARCHIVE_DIR = PROMPTS_DIR / "archive"
TEMPLATE_FILE = PROMPTS_DIR / "Prompts-Template.md"
CURRENT_LINK = PROMPTS_DIR / "Prompts-Current.md"
PREVIOUS_LINK = PROMPTS_DIR / "Prompts-Previous.md"


def get_timestamp() -> str:
    """Generate a timestamp string in ISO 8601 format with underscores.

    Returns:
        str: Timestamp in format YYYY-MM-DD_HHMMSS
    """
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def ensure_archive_exists() -> None:
    """Ensure the archive directory exists."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Archive directory ready: {ARCHIVE_DIR}")


def create_timestamped_archive_file() -> Path:
    """Create a new timestamped file in archive/ from template or empty.

    Returns:
        Path: Path to the newly created archive file
    """
    timestamp = get_timestamp()
    new_filename = f"Prompts-{timestamp}.txt"
    archive_path = ARCHIVE_DIR / new_filename

    if TEMPLATE_FILE.exists():
        shutil.copy2(str(TEMPLATE_FILE), str(archive_path))
        print(f"Created archive file from template: {archive_path}")
    else:
        archive_path.touch()
        print(f"Created empty archive file (template not found): {archive_path}")

    return archive_path


def update_symlink(link_path: Path, target_path: Path) -> bool:
    """Create or update a symlink to point to target.

    Uses relative paths for portability.

    Args:
        link_path: Path where the symlink should exist
        target_path: Absolute path to the target file

    Returns:
        bool: True if successful, False otherwise
    """
    # Calculate relative path from link to target
    try:
        # Both are in same parent directory, so relative path is just archive/filename
        relative_target = Path("archive") / target_path.name

        # Remove existing symlink or file
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
            print(f"Removed existing symlink/file: {link_path.name}")

        # Create new symlink
        link_path.symlink_to(relative_target)
        print(f"Created symlink: {link_path.name} -> {relative_target}")
        return True
    except Exception as e:
        print(f"Error updating symlink {link_path}: {e}")
        return False


def get_symlink_target(link_path: Path) -> Path | None:
    """Get the target of a symlink if it exists and is valid.

    Args:
        link_path: Path to the potential symlink

    Returns:
        Optional[Path]: Absolute path to target if valid, None otherwise
    """
    if not link_path.is_symlink():
        return None

    try:
        # Resolve the symlink to absolute path
        return link_path.resolve(strict=True)
    except (OSError, RuntimeError):
        # Broken symlink or circular reference
        return None


def validate_symlink_target(link_path: Path) -> bool:
    """Check if symlink points to a valid file in archive/.

    Args:
        link_path: Path to the symlink

    Returns:
        bool: True if symlink is valid and points to archive/, False otherwise
    """
    target = get_symlink_target(link_path)
    if target is None:
        return False

    # Check if target is in archive directory
    try:
        target.relative_to(ARCHIVE_DIR)
        return True
    except ValueError:
        print(f"Warning: {link_path.name} points outside archive/: {target}")
        return False


def cleanup_broken_symlink(link_path: Path) -> None:
    """Remove a broken or invalid symlink.

    Args:
        link_path: Path to the symlink to clean up
    """
    if link_path.is_symlink():
        link_path.unlink()
        print(f"Cleaned up broken/invalid symlink: {link_path.name}")


def main() -> None:
    """Manage prompt files using symlink architecture."""
    print("\nStarting prompt file management (symlink-based)...")

    # Ensure archive directory exists
    ensure_archive_exists()

    # Check current state
    current_exists = CURRENT_LINK.exists()
    current_is_symlink = CURRENT_LINK.is_symlink()
    previous_exists = PREVIOUS_LINK.exists()
    previous_is_symlink = PREVIOUS_LINK.is_symlink()

    print(f"Current symlink exists: {current_exists}")
    print(f"Previous symlink exists: {previous_exists}")

    # Handle broken or invalid symlinks
    if current_is_symlink and not validate_symlink_target(CURRENT_LINK):
        cleanup_broken_symlink(CURRENT_LINK)
        current_exists = False
        current_is_symlink = False

    if previous_is_symlink and not validate_symlink_target(PREVIOUS_LINK):
        cleanup_broken_symlink(PREVIOUS_LINK)
        previous_exists = False
        previous_is_symlink = False

    # Handle regular files (shouldn't exist after migration, but handle gracefully)
    if current_exists and not current_is_symlink:
        print(f"Warning: {CURRENT_LINK.name} is a regular file, not a symlink")
        print("Please remove it manually or re-run after migration")
        return

    if previous_exists and not previous_is_symlink:
        print(f"Warning: {PREVIOUS_LINK.name} is a regular file, not a symlink")
        print("Please remove it manually or re-run after migration")
        return

    # Create new timestamped file in archive
    new_archive_file = create_timestamped_archive_file()

    # Case 1: Brand new project (nothing exists)
    if not current_exists and not previous_exists:
        print("\nCase 1: Brand new project - creating initial Current symlink")
        update_symlink(CURRENT_LINK, new_archive_file)
        print("Initial setup complete!")
        return

    # Case 2: Only Current exists
    if current_exists and not previous_exists:
        print("\nCase 2: Only Current exists - creating Previous and updating Current")
        old_current_target = get_symlink_target(CURRENT_LINK)
        if old_current_target:
            update_symlink(PREVIOUS_LINK, old_current_target)
        update_symlink(CURRENT_LINK, new_archive_file)
        print("Rotation complete!")
        return

    # Case 3: Both symlinks exist (normal operation)
    if current_exists and previous_exists:
        print("\nCase 3: Normal operation - rotating both symlinks")
        old_current_target = get_symlink_target(CURRENT_LINK)
        if old_current_target:
            update_symlink(PREVIOUS_LINK, old_current_target)
        update_symlink(CURRENT_LINK, new_archive_file)
        print("Full rotation complete!")
        return

    # This shouldn't happen, but handle it gracefully
    print("Unexpected state. Please check your prompt files manually.")


if __name__ == "__main__":
    main()
