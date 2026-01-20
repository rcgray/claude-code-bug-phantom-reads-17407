#!/usr/bin/env python
"""
Parse trial session JSONL file to extract structured data for trial_data.json.

This diagnostic script processes the session file and chat export to extract:
- Token progression and context resets
- File read operations
- User input phases
- Timeline events
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def parse_session_file(session_path: Path) -> dict:
    """
    Parse JSONL session file to extract token progression, resets, and reads.

    Args:
        session_path: Path to the session .jsonl file

    Returns:
        Dictionary containing extracted data
    """
    token_progression = []
    file_reads = []
    user_inputs = []
    line_number = 0
    prev_tokens = 0
    sequence = 0
    read_sequence = 0
    batch_id = 0
    prev_message_id = None

    with session_path.open("r") as f:
        for line in f:
            line_number += 1
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # Track user inputs
            if msg_type == "user":
                content = ""
                if isinstance(data.get("message"), dict):
                    msg_content = data["message"].get("content", "")
                    if isinstance(msg_content, list):
                        for block in msg_content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                content += block.get("text", "")
                    elif isinstance(msg_content, str):
                        content = msg_content
                elif isinstance(data.get("message"), str):
                    content = data["message"]

                # Determine phase
                phase = None
                content_lower = content.lower()
                if "/wsd:init" in content_lower or "wsd:init" in content:
                    phase = "init"
                elif "/refine-plan" in content_lower or "refine-plan" in content:
                    phase = "trigger"
                elif "phantom read" in content_lower or "persisted-output" in content_lower:
                    phase = "inquiry"

                user_inputs.append({
                    "session_line": line_number,
                    "phase": phase,
                    "preview": content[:50] if content else ""
                })

            # Track assistant messages with usage data
            if msg_type == "assistant":
                message = data.get("message", {})
                usage = message.get("usage", {})
                cache_read = usage.get("cache_read_input_tokens", 0)

                if cache_read > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_read,
                        "session_line": line_number
                    })

                    # Check for content blocks with tool_use
                    content = message.get("content", [])
                    message_id = message.get("id", line_number)

                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                if block.get("name") == "Read":
                                    read_sequence += 1
                                    # New batch if different message
                                    if message_id != prev_message_id:
                                        batch_id += 1
                                        prev_message_id = message_id

                                    input_data = block.get("input", {})
                                    file_path = input_data.get("file_path", "")

                                    file_reads.append({
                                        "sequence": read_sequence,
                                        "batch_id": batch_id,
                                        "file_path": file_path,
                                        "session_line": line_number,
                                        "tool_use_id": block.get("id", "")
                                    })

                    prev_tokens = cache_read

    return {
        "token_progression": token_progression,
        "file_reads": file_reads,
        "user_inputs": user_inputs,
        "total_lines": line_number
    }


def detect_resets(token_progression: list, threshold: int = 10000) -> list:
    """
    Detect context resets where tokens drop significantly.

    Args:
        token_progression: List of token progression entries
        threshold: Minimum drop to consider a reset

    Returns:
        List of reset events
    """
    resets = []
    prev_tokens = 0

    for entry in token_progression:
        current_tokens = entry["cache_read_tokens"]
        if prev_tokens > 0 and (prev_tokens - current_tokens) > threshold:
            resets.append({
                "sequence_position": entry["sequence"],
                "total_events": len(token_progression),
                "position_percent": round((entry["sequence"] / len(token_progression)) * 100, 1),
                "from_tokens": prev_tokens,
                "to_tokens": current_tokens,
                "session_line": entry["session_line"]
            })
        prev_tokens = current_tokens

    return resets


def classify_pattern(resets: list, total_events: int) -> str:
    """
    Classify the reset pattern.

    Args:
        resets: List of reset events
        total_events: Total number of events

    Returns:
        Pattern classification string
    """
    if not resets:
        return "NO_RESETS"

    positions = [r["position_percent"] for r in resets]

    if len(resets) == 1:
        if positions[0] < 50:
            return "SINGLE_EARLY"
        else:
            return "SINGLE_LATE"

    # Check if all resets are late (>80%)
    if all(p > 80 for p in positions):
        return "LATE_CLUSTERED"

    # Check for EARLY_PLUS_LATE pattern
    first_early = positions[0] < 50
    mid_range_exists = any(50 <= p <= 90 for p in positions)
    last_late = positions[-1] > 90

    if first_early and not mid_range_exists and last_late:
        return "EARLY_PLUS_LATE"

    if first_early and mid_range_exists:
        return "EARLY_PLUS_MID_LATE"

    return "OTHER"


def parse_chat_export(chat_path: Path) -> dict:
    """
    Parse chat export for context snapshots and outcome.

    Args:
        chat_path: Path to the chat export .txt file

    Returns:
        Dictionary with snapshots and outcome data
    """
    snapshots = []
    outcome = "UNKNOWN"
    affected_files = []
    notes = ""

    content = chat_path.read_text()

    # Look for token snapshots (pattern like "123,456 tokens (62%)")
    import re
    token_pattern = r"([\d,]+)\s*tokens?\s*\((\d+)%\)"
    matches = re.findall(token_pattern, content)
    for match in matches:
        tokens = int(match[0].replace(",", ""))
        percent = int(match[1])
        snapshots.append({"tokens": tokens, "percent": percent})

    # Determine outcome
    content_lower = content.lower()
    if "no phantom read" in content_lower or "received inline" in content_lower or "successfully read" in content_lower:
        outcome = "SUCCESS"
    elif "phantom read" in content_lower or "<persisted-output>" in content_lower or "did not follow up" in content_lower:
        outcome = "FAILURE"

        # Try to extract affected files
        persisted_pattern = r"<persisted-output>.*?saved to:.*?/([^/\s]+\.(?:md|py|txt))"
        file_matches = re.findall(persisted_pattern, content, re.IGNORECASE)
        if file_matches:
            affected_files = list(set(file_matches))

    return {
        "snapshots": snapshots,
        "outcome": outcome,
        "affected_files": affected_files,
        "notes": notes
    }


def build_timeline(user_inputs: list, resets: list) -> list:
    """
    Build unified timeline of events.

    Args:
        user_inputs: List of user input events
        resets: List of reset events

    Returns:
        Sorted timeline of events
    """
    timeline = []
    seq = 0

    # Add user inputs
    for inp in user_inputs:
        if inp["phase"]:  # Only include phase-relevant inputs
            seq += 1
            timeline.append({
                "sequence": seq,
                "type": "user_input",
                "session_line": inp["session_line"],
                "phase": inp["phase"],
                "preview": inp["preview"]
            })

    # Add resets
    for reset in resets:
        seq += 1
        timeline.append({
            "sequence": seq,
            "type": "context_reset",
            "session_line": reset["session_line"],
            "from_tokens": reset["from_tokens"],
            "to_tokens": reset["to_tokens"]
        })

    # Sort by session line
    timeline.sort(key=lambda x: x["session_line"])

    # Reassign sequence numbers
    for i, event in enumerate(timeline):
        event["sequence"] = i + 1

    return timeline


def main() -> None:
    """Main entry point."""
    trial_folder = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260119-140145")
    session_file = trial_folder / "b1d6c71c-b872-4dd5-b75b-0e848e7ece41.jsonl"
    chat_file = trial_folder / "20260119-140145.txt"

    print(f"Parsing session file: {session_file.name}")
    session_data = parse_session_file(session_file)

    print(f"  Processed {session_data['total_lines']} lines")
    print(f"  Found {len(session_data['token_progression'])} token progression entries")
    print(f"  Found {len(session_data['file_reads'])} Read operations")
    print(f"  Found {len(session_data['user_inputs'])} user inputs")

    # Detect resets
    resets = detect_resets(session_data["token_progression"])
    print(f"  Detected {len(resets)} context resets")

    # Classify pattern
    pattern = classify_pattern(resets, len(session_data["token_progression"]))
    print(f"  Pattern: {pattern}")

    # Parse chat export
    print(f"\nParsing chat export: {chat_file.name}")
    chat_data = parse_chat_export(chat_file)
    print(f"  Outcome: {chat_data['outcome']}")
    print(f"  Found {len(chat_data['snapshots'])} token snapshots")

    # Build timeline
    timeline = build_timeline(session_data["user_inputs"], resets)
    print(f"\nTimeline events: {len(timeline)}")

    # Calculate unique files
    unique_files = list(set(r["file_path"] for r in session_data["file_reads"]))

    # Output summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Token progression entries: {len(session_data['token_progression'])}")
    print(f"File reads: {len(session_data['file_reads'])} total, {len(unique_files)} unique")
    print(f"Resets: {len(resets)}")
    if resets:
        print(f"  Positions: {[r['position_percent'] for r in resets]}")
    print(f"Pattern: {pattern}")
    print(f"Outcome: {chat_data['outcome']}")

    # Output JSON structure for verification
    output = {
        "token_progression": session_data["token_progression"],
        "file_reads": session_data["file_reads"],
        "resets": resets,
        "pattern": pattern,
        "timeline": timeline,
        "unique_files": unique_files,
        "outcome": chat_data["outcome"]
    }

    output_file = trial_folder / "parsed_data_debug.json"
    with output_file.open("w") as f:
        json.dump(output, f, indent=2)
    print(f"\nDebug output written to: {output_file}")


if __name__ == "__main__":
    main()
