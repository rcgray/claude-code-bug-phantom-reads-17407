#!/usr/bin/env python
"""
Update trial_data.json from schema 1.1 to 1.2 by adding success/failure tracking.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_tool_results_map(session_file: Path) -> dict[str, dict]:
    """Run extract_tool_results.py to get the tool results map."""
    result = subprocess.run(
        ["python", "dev/diagnostics/extract_tool_results.py", str(session_file)],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)


def update_trial_data(trial_folder: Path) -> None:
    """Update trial_data.json to schema 1.2."""
    trial_data_path = trial_folder / "trial_data.json"

    # Read existing trial_data
    with trial_data_path.open() as f:
        data = json.loads(f.read())

    # Check schema version
    if data.get("schema_version") == "1.2":
        print(f"Already at schema 1.2, no update needed")
        return

    # Get session file
    session_uuid = data["metadata"]["session_uuid"]
    session_file = trial_folder / f"{session_uuid}.jsonl"

    if not session_file.exists():
        print(f"ERROR: Session file not found: {session_file}")
        sys.exit(1)

    # Get tool results map
    print(f"Extracting tool_result success/failure data...")
    tool_results_map = get_tool_results_map(session_file)

    # Update schema version
    data["schema_version"] = "1.2"
    data["generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Update file_reads with success/failure tracking
    successful_count = 0
    failed_count = 0
    failed_reads = []

    for read in data["file_reads"]["reads"]:
        tool_use_id = read["tool_use_id"]

        if tool_use_id in tool_results_map:
            result_info = tool_results_map[tool_use_id]
            read["success"] = result_info["success"]

            if result_info["success"]:
                successful_count += 1
            else:
                failed_count += 1
                read["error"] = result_info["error"]
                failed_reads.append({
                    "sequence": read["sequence"],
                    "file_path": read["file_path"],
                    "error": result_info["error"]
                })
        else:
            # Tool use ID not found in results - mark as unknown
            read["success"] = False
            read["error"] = "Tool result not found in session"
            failed_count += 1
            failed_reads.append({
                "sequence": read["sequence"],
                "file_path": read["file_path"],
                "error": "Tool result not found in session"
            })

    # Update aggregate counts
    data["file_reads"]["successful_operations"] = successful_count
    data["file_reads"]["failed_operations"] = failed_count

    # Recalculate unique_files from successful reads only
    successful_files = set()
    for read in data["file_reads"]["reads"]:
        if read.get("success", False):
            successful_files.add(read["file_path"])

    data["file_reads"]["unique_files"] = len(successful_files)
    data["file_reads"]["unique_file_list"] = sorted(list(successful_files))

    # Add failed_reads section
    data["file_reads"]["failed_reads"] = failed_reads

    # Write updated data
    with trial_data_path.open("w") as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated trial_data.json to schema 1.2")
    print(f"  Successful operations: {successful_count}")
    print(f"  Failed operations: {failed_count}")
    print(f"  Unique files (successful only): {len(successful_files)}")


if __name__ == "__main__":
    trial_folder = Path(sys.argv[1])
    update_trial_data(trial_folder)
