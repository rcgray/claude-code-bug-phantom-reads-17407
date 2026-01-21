#!/usr/bin/env python
"""
Extract structured trial data from Phantom Reads trial folder.

This script parses session JSONL files and chat exports to generate trial_data.json
with comprehensive metrics about context resets, file reads, and token analysis.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

def extract_trial_data(trial_folder: Path) -> dict[str, Any]:
    """Extract all trial data from a trial folder."""

    # Step 1: Validate and extract metadata
    workscope_id = trial_folder.name

    # Find chat export
    chat_files = list(trial_folder.glob("*.txt"))
    if not chat_files:
        raise FileNotFoundError(f"No chat export (.txt) found in {trial_folder}")
    chat_export_file = chat_files[0]

    # Find session file
    jsonl_files = list(trial_folder.glob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No session file (.jsonl) found in {trial_folder}")
    session_file = jsonl_files[0]
    session_uuid = session_file.stem

    # Check for subdirectory
    uuid_dir = trial_folder / session_uuid
    has_subagents = (uuid_dir / "subagents").exists() if uuid_dir.exists() else False
    has_tool_results = (uuid_dir / "tool-results").exists() if uuid_dir.exists() else False

    # Load token counts if available
    collection_dir = trial_folder.parent
    token_counts_file = collection_dir / "file_token_counts.json"
    token_counts_data = None
    if token_counts_file.exists():
        with token_counts_file.open() as f:
            token_counts_data = json.load(f)

    # Step 2: Parse session file
    print(f"Parsing session file ({session_file.stat().st_size // 1024}KB)...")

    token_progression = []
    resets = []
    file_reads = []
    timeline = []
    tool_results_map = {}

    sequence_counter = 0
    batch_id = 0
    last_cache_tokens = None
    prev_message_line = None
    current_batch_files = []

    with session_file.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            sequence_counter += 1

            # Track human messages (user inputs and tool results)
            if event.get("role") == "human":
                # Check for tool_result blocks
                content = event.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            tool_use_id = block.get("tool_use_id")
                            result_content = block.get("content", "")
                            tool_results_map[tool_use_id] = result_content

                # Add to timeline if it's a user input (text content)
                has_text = any(isinstance(b, dict) and b.get("type") == "text"
                              for b in content if isinstance(content, list))
                if has_text:
                    text_content = next((b.get("text", "") for b in content
                                       if isinstance(b, dict) and b.get("type") == "text"), "")
                    preview = text_content[:50]

                    # Detect phase
                    phase = None
                    if "/wsd:init" in text_content:
                        phase = "init"
                    elif "/refine-plan" in text_content:
                        phase = "trigger"
                    elif "phantom read" in text_content.lower() or "persisted-output" in text_content:
                        phase = "inquiry"

                    timeline.append({
                        "sequence": sequence_counter,
                        "type": "user_input",
                        "session_line": line_num,
                        "preview": preview,
                        "phase": phase
                    })

            # Track assistant messages
            elif event.get("role") == "assistant":
                usage = event.get("usage", {})
                cache_tokens = usage.get("cache_read_input_tokens")

                # Track token progression
                if cache_tokens and cache_tokens > 0:
                    token_progression.append({
                        "sequence": len(token_progression) + 1,
                        "cache_read_tokens": cache_tokens,
                        "session_line": line_num
                    })

                    # Detect resets
                    if last_cache_tokens is not None:
                        if last_cache_tokens - cache_tokens > 10000:
                            resets.append({
                                "from_tokens": last_cache_tokens,
                                "to_tokens": cache_tokens,
                                "session_line": line_num
                            })

                    last_cache_tokens = cache_tokens

                # Track Read operations
                content = event.get("content", [])
                if isinstance(content, list):
                    current_batch_files = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Read":
                                tool_input = block.get("input", {})
                                file_path = tool_input.get("file_path", "")
                                tool_use_id = block.get("id", "")

                                current_batch_files.append({
                                    "file_path": file_path,
                                    "session_line": line_num,
                                    "tool_use_id": tool_use_id,
                                    "batch_id": batch_id
                                })

                    # If we found reads in this message, add them
                    if current_batch_files:
                        file_reads.extend(current_batch_files)

                        # Add tool batch to timeline
                        timeline.append({
                            "sequence": sequence_counter,
                            "type": "tool_batch",
                            "session_line": line_num,
                            "read_count": len(current_batch_files),
                            "files": [f["file_path"] for f in current_batch_files]
                        })

                        batch_id += 1

    # Determine read success/failure
    for read in file_reads:
        tool_use_id = read["tool_use_id"]
        result_content = tool_results_map.get(tool_use_id, "")

        # Check for error marker
        if "<tool_use_error>" in result_content:
            read["success"] = False
            # Extract error message
            match = re.search(r"<tool_use_error>(.*?)</tool_use_error>", result_content, re.DOTALL)
            if match:
                read["error"] = match.group(1).strip()
            else:
                read["error"] = "Unknown error"
        else:
            read["success"] = True

    # Add sequence numbers to reads
    for idx, read in enumerate(file_reads, 1):
        read["sequence"] = idx

    print(f"  Processed {line_num} lines")
    print(f"  Found {len(token_progression)} assistant messages with usage data")
    successful_reads = sum(1 for r in file_reads if r["success"])
    failed_reads = sum(1 for r in file_reads if not r["success"])
    print(f"  Found {len(file_reads)} Read operations ({successful_reads} successful, {failed_reads} failed)")
    print(f"  Detected {len(resets)} context resets")

    # Step 3: Parse chat export
    print("Parsing chat export...")

    context_snapshots = []
    self_reported = "UNKNOWN"
    affected_files = []

    with chat_export_file.open() as f:
        chat_text = f.read()

        # Extract context snapshots
        for match in re.finditer(r"(\d+)K tokens \((\d+)%\)", chat_text):
            tokens = int(match.group(1)) * 1000
            percent = int(match.group(2))
            context_snapshots.append({"tokens": tokens, "percent": percent})

        # Determine outcome
        lower_chat = chat_text.lower()
        if "no phantom read" in lower_chat or "received inline" in lower_chat or "successfully read all" in lower_chat:
            self_reported = "SUCCESS"
        elif "phantom read" in lower_chat or "persisted-output" in lower_chat or "did not follow up" in lower_chat:
            self_reported = "FAILURE"

            # Try to extract affected files
            for match in re.finditer(r"docs/[a-zA-Z0-9_/-]+\.md", chat_text):
                file_path = match.group(0)
                if file_path not in affected_files:
                    affected_files.append(file_path)

    print(f"  Found {len(context_snapshots)} context snapshots")
    print(f"  Outcome: {self_reported}")

    # Step 4: Compute derived metrics
    print("Computing metrics...")

    # Find pre/post operation tokens
    pre_operation_tokens = None
    pre_operation_percent = None
    post_operation_tokens = None
    post_operation_percent = None

    trigger_event = next((e for e in timeline if e.get("phase") == "trigger"), None)
    if trigger_event and context_snapshots:
        # Find snapshot before trigger
        for snapshot in context_snapshots:
            if pre_operation_tokens is None:
                pre_operation_tokens = snapshot["tokens"]
                pre_operation_percent = snapshot["percent"]

        # Post-operation is the last snapshot
        if context_snapshots:
            post_operation_tokens = context_snapshots[-1]["tokens"]
            post_operation_percent = context_snapshots[-1]["percent"]

    headroom = (200000 - pre_operation_tokens) if pre_operation_tokens else None

    # Reset analysis
    total_events = sequence_counter
    for idx, reset in enumerate(resets, 1):
        reset["sequence_position"] = reset["session_line"]
        reset["total_events"] = total_events
        reset["position_percent"] = (reset["session_line"] / total_events) * 100

    reset_positions_percent = [r["position_percent"] for r in resets]

    # Pattern classification
    pattern = classify_reset_pattern(resets, total_events)

    # File read stats
    unique_files = list(set(r["file_path"] for r in file_reads if r["success"]))
    failed_read_list = [
        {
            "sequence": r["sequence"],
            "file_path": r["file_path"],
            "error": r.get("error", "Unknown error")
        }
        for r in file_reads if not r["success"]
    ]

    print(f"  Pattern: {pattern}")
    print(f"  Unique files: {len(unique_files)}")

    # Step 5: Token analysis
    token_analysis = {"available": False, "token_counts_file": None}

    if token_counts_data:
        print("Computing token analysis...")
        token_analysis = compute_token_analysis(
            file_reads, resets, token_counts_data,
            str(token_counts_file.relative_to(Path.cwd())),
            pre_operation_tokens or 0
        )
        print(f"  Matched {len([r for r in token_analysis['reads_with_tokens'] if r['token_count'] > 0])}/{len(file_reads)} files to token counts")

    # Step 6: Assemble output
    output = {
        "schema_version": "1.2",
        "generated_at": datetime.now().isoformat(),
        "metadata": {
            "workscope_id": workscope_id,
            "session_uuid": session_uuid,
            "chat_export_file": chat_export_file.name,
            "session_file": session_file.name,
            "has_subagents": has_subagents,
            "has_tool_results": has_tool_results
        },
        "outcome": {
            "self_reported": self_reported,
            "affected_files": affected_files,
            "notes": ""
        },
        "context_metrics": {
            "pre_operation_tokens": pre_operation_tokens,
            "pre_operation_percent": pre_operation_percent,
            "post_operation_tokens": post_operation_tokens,
            "post_operation_percent": post_operation_percent,
            "headroom_at_trigger": headroom,
            "context_window_size": 200000
        },
        "reset_analysis": {
            "total_resets": len(resets),
            "reset_positions_percent": reset_positions_percent,
            "pattern_classification": pattern,
            "resets": resets
        },
        "file_reads": {
            "total_operations": len(file_reads),
            "successful_operations": successful_reads,
            "failed_operations": failed_reads,
            "unique_files": len(unique_files),
            "unique_file_list": sorted(unique_files),
            "failed_reads": failed_read_list,
            "reads": file_reads
        },
        "timeline": timeline,
        "token_progression": token_progression,
        "token_analysis": token_analysis
    }

    return output


def classify_reset_pattern(resets: list[dict], total_events: int) -> str:
    """Classify the reset pattern."""
    if not resets:
        return "NO_RESETS"

    positions = [(r["session_line"] / total_events) * 100 for r in resets]

    if len(positions) == 1:
        if positions[0] < 50:
            return "SINGLE_EARLY"
        else:
            return "SINGLE_LATE"

    # All resets late
    if all(p > 80 for p in positions):
        return "LATE_CLUSTERED"

    # Early + late pattern
    if positions[0] < 50 and positions[-1] > 90:
        # Check for mid-session resets
        mid_resets = [p for p in positions[1:-1] if 50 <= p <= 90]
        if not mid_resets:
            return "EARLY_PLUS_LATE"
        else:
            return "EARLY_PLUS_MID_LATE"

    return "OTHER"


def compute_token_analysis(
    file_reads: list[dict],
    resets: list[dict],
    token_counts_data: dict,
    token_counts_file: str,
    pre_operation_tokens: int
) -> dict[str, Any]:
    """Compute token-based analysis."""

    project_files = token_counts_data.get("project_files", {})

    reads_with_tokens = []
    cumulative = pre_operation_tokens

    for read in file_reads:
        if not read["success"]:
            continue

        file_path = read["file_path"]

        # Normalize path
        rel_path = None
        for pattern in ["/Users/gray/Projects/claude-bug/", "/Users/gray/Projects/claude-code-bug-phantom-reads-17407/"]:
            if pattern in file_path:
                rel_path = file_path.split(pattern, 1)[1]
                break

        # Look up token count
        token_count = 0
        if rel_path and rel_path in project_files:
            token_count = project_files[rel_path]

        cumulative += token_count

        reads_with_tokens.append({
            "sequence": read["sequence"],
            "file_path": rel_path or file_path,
            "token_count": token_count,
            "cumulative_estimate": cumulative,
            "session_line": read["session_line"]
        })

    # Annotate resets with context
    resets_with_context = []
    for idx, reset in enumerate(resets, 1):
        reset_line = reset["session_line"]

        # Find last read before this reset
        last_read = None
        for read_with_tokens in reversed(reads_with_tokens):
            if read_with_tokens["session_line"] < reset_line:
                last_read = read_with_tokens
                break

        resets_with_context.append({
            "reset_sequence": idx,
            "session_line": reset_line,
            "cumulative_tokens_before": last_read["cumulative_estimate"] if last_read else pre_operation_tokens,
            "last_file_read": last_read["file_path"] if last_read else None,
            "last_file_tokens": last_read["token_count"] if last_read else None
        })

    # Compute statistics
    known_tokens = [r["token_count"] for r in reads_with_tokens if r["token_count"] > 0]

    total_tokens_read = sum(known_tokens)
    largest_file_tokens = max(known_tokens) if known_tokens else 0
    largest_file = None
    if largest_file_tokens > 0:
        largest_file = next((r["file_path"] for r in reads_with_tokens if r["token_count"] == largest_file_tokens), None)

    unknown_count = sum(1 for r in reads_with_tokens if r["token_count"] == 0)

    return {
        "available": True,
        "token_counts_file": token_counts_file,
        "statistics": {
            "total_tokens_read": total_tokens_read,
            "largest_file_tokens": largest_file_tokens,
            "largest_file_path": largest_file or "",
            "unknown_token_files": unknown_count
        },
        "reads_with_tokens": reads_with_tokens,
        "resets_with_context": resets_with_context
    }


def compare_data(existing: dict, new: dict) -> list[str]:
    """Compare existing and new data, return list of changes."""
    changes = []

    all_keys = set(existing.keys()) | set(new.keys())

    for key in sorted(all_keys):
        if key not in existing:
            changes.append(f"  - {key}: NEW")
        elif key not in new:
            changes.append(f"  - {key}: REMOVED")
        elif existing[key] != new[key]:
            # Provide specific details for some keys
            if key == "schema_version":
                changes.append(f"  - {key}: UPDATED ({existing[key]} → {new[key]})")
            elif key == "outcome":
                old_status = existing[key].get("self_reported", "UNKNOWN")
                new_status = new[key].get("self_reported", "UNKNOWN")
                if old_status != new_status:
                    changes.append(f"  - {key}: UPDATED (self_reported: {old_status} → {new_status})")
                else:
                    changes.append(f"  - {key}: UPDATED")
            elif key == "reset_analysis":
                old_resets = existing[key].get("total_resets", 0)
                new_resets = new[key].get("total_resets", 0)
                if old_resets != new_resets:
                    changes.append(f"  - {key}: UPDATED (total_resets: {old_resets} → {new_resets})")
                else:
                    changes.append(f"  - {key}: UPDATED")
            elif key == "token_analysis" and new[key].get("available"):
                reads = len(new[key].get("reads_with_tokens", []))
                resets = len(new[key].get("resets_with_context", []))
                changes.append(f"  - {key}: UPDATED ({reads} reads with tokens, {resets} resets with context)")
            else:
                changes.append(f"  - {key}: UPDATED")
        else:
            changes.append(f"  - {key}: UNCHANGED")

    return changes


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python extract_trial_data.py <trial-folder-path>")
        sys.exit(1)

    trial_folder = Path(sys.argv[1])

    if not trial_folder.exists():
        print(f"Error: Trial folder not found: {trial_folder}")
        sys.exit(1)

    print(f"Validating trial folder...")

    try:
        # Extract data
        new_data = extract_trial_data(trial_folder)

        # Check for existing file
        output_file = trial_folder / "trial_data.json"
        existing_data = None

        if output_file.exists():
            print(f"\nChecking for existing trial_data.json... Found")
            with output_file.open() as f:
                existing_data = json.load(f)
        else:
            print(f"\nChecking for existing trial_data.json... Not found")

        # Compare if existing
        if existing_data:
            print("\nChanges to trial_data.json:")
            changes = compare_data(existing_data, new_data)
            for change in changes:
                print(change)
        else:
            print("\nCreating new trial_data.json with all sections.")

        # Write output
        with output_file.open("w") as f:
            json.dump(new_data, f, indent=2)

        # Report summary
        metadata = new_data["metadata"]
        outcome = new_data["outcome"]
        context_metrics = new_data["context_metrics"]
        reset_analysis = new_data["reset_analysis"]
        file_reads_data = new_data["file_reads"]
        token_analysis = new_data["token_analysis"]

        print("\n" + "=" * 50)
        print("Trial Data Extraction Complete")
        print("=" * 50)
        print(f"Trial: {metadata['workscope_id']}")
        print(f"Session: {metadata['session_uuid']}")
        print()
        print(f"Outcome: {outcome['self_reported']}")
        print()
        print("Context Metrics:")
        if context_metrics["pre_operation_tokens"]:
            print(f"  Pre-operation:  {context_metrics['pre_operation_tokens'] // 1000}K tokens ({context_metrics['pre_operation_percent']}%)")
            print(f"  Post-operation: {context_metrics['post_operation_tokens'] // 1000}K tokens ({context_metrics['post_operation_percent']}%)")
            print(f"  Headroom:       {context_metrics['headroom_at_trigger'] // 1000}K tokens")
        else:
            print("  Not available")
        print()
        print("Reset Analysis:")
        print(f"  Total resets: {reset_analysis['total_resets']}")
        print(f"  Pattern: {reset_analysis['pattern_classification']}")
        if reset_analysis['reset_positions_percent']:
            positions = ", ".join(f"{p:.0f}%" for p in reset_analysis['reset_positions_percent'])
            print(f"  Positions: {positions}")
        print()
        print("File Reads:")
        print(f"  Total operations: {file_reads_data['total_operations']} ({file_reads_data['successful_operations']} successful, {file_reads_data['failed_operations']} failed)")
        print(f"  Unique files: {file_reads_data['unique_files']}")
        print()

        if token_analysis["available"]:
            stats = token_analysis["statistics"]
            print("Token Analysis: AVAILABLE")
            print(f"  Total tokens read: {stats['total_tokens_read']:,}")
            print(f"  Largest file: {stats['largest_file_path']} ({stats['largest_file_tokens']:,} tokens)")
            print(f"  Unknown files: {stats['unknown_token_files']}")
        else:
            print("Token Analysis: NOT AVAILABLE")
            print("  (No file_token_counts.json found in collection directory)")
        print()
        print(f"Timeline Events: {len(new_data['timeline'])}")
        print()
        print(f"Output: {output_file}")
        print(f"Status: {'UPDATED' if existing_data else 'CREATED'}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
