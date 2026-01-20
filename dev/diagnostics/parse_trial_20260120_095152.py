#!/usr/bin/env python
"""
Parse trial session data for 20260120-095152.

This script extracts structured data from a Phantom Reads trial session,
including token progression, context resets, file reads, and timeline events.
"""

import json
from pathlib import Path
from datetime import datetime

TRIAL_PATH = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260120-095152")
SESSION_FILE = TRIAL_PATH / "8cbb3e89-6e98-47ee-aad0-3f9caa5d17e5.jsonl"
CHAT_EXPORT = TRIAL_PATH / "20260120-095152.txt"

def parse_session_file() -> dict:
    """Parse the JSONL session file and extract relevant data."""
    token_progression = []
    file_reads = []
    resets = []
    timeline = []
    user_inputs = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    current_batch_line = -1

    with SESSION_FILE.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

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
                        "session_line": line_num
                    })

                    # Detect context resets (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read) > 10000:
                        resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_read,
                            "session_line": line_num
                        })

                    prev_cache_tokens = cache_read

                # Extract tool uses (file reads)
                content = message.get("content", [])
                if isinstance(content, list):
                    batch_has_reads = False
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Read":
                                if line_num != current_batch_line:
                                    batch_id += 1
                                    current_batch_line = line_num
                                    batch_has_reads = True

                                input_data = block.get("input", {})
                                file_path = input_data.get("file_path", "")
                                tool_id = block.get("id", "")

                                file_reads.append({
                                    "sequence": len(file_reads) + 1,
                                    "batch_id": batch_id,
                                    "file_path": file_path,
                                    "session_line": line_num,
                                    "tool_use_id": tool_id
                                })

            # Track human/user messages
            elif msg_type == "human":
                message = data.get("message", {})
                content = message.get("content", "")
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = " ".join(text_parts)

                preview = content[:100] if content else ""

                # Detect methodology phases
                phase = None
                content_lower = content.lower() if content else ""
                if "/wsd:init" in content_lower:
                    phase = "init"
                elif "/refine-plan" in content_lower:
                    phase = "trigger"
                elif "phantom read" in content_lower or "persisted-output" in content_lower:
                    phase = "inquiry"

                user_inputs.append({
                    "session_line": line_num,
                    "preview": preview,
                    "phase": phase
                })

    return {
        "token_progression": token_progression,
        "file_reads": file_reads,
        "resets": resets,
        "user_inputs": user_inputs,
        "total_lines": line_num
    }


def parse_chat_export() -> dict:
    """Parse the chat export TXT file for context snapshots and outcome."""
    context_snapshots = []
    outcome = "UNKNOWN"
    affected_files = []
    notes = ""

    content = CHAT_EXPORT.read_text()
    lines = content.split('\n')

    for line in lines:
        # Look for context snapshots with token info
        if "tokens" in line.lower() and "%" in line:
            # Try to extract token count and percentage
            import re
            match = re.search(r'(\d[\d,]*)\s*tokens?\s*\((\d+)%\)', line, re.IGNORECASE)
            if match:
                tokens = int(match.group(1).replace(',', ''))
                pct = int(match.group(2))
                context_snapshots.append({"tokens": tokens, "percent": pct})

    # Determine outcome from content
    content_lower = content.lower()

    # Success indicators
    if any(phrase in content_lower for phrase in [
        "no phantom reads",
        "received inline",
        "successfully read all",
        "all files were read correctly",
        "no issues with file reading",
        "content was received directly"
    ]):
        outcome = "SUCCESS"

    # Failure indicators
    elif any(phrase in content_lower for phrase in [
        "phantom read",
        "persisted-output",
        "did not follow up",
        "failed to read",
        "old tool result content cleared"
    ]):
        outcome = "FAILURE"

        # Try to extract affected file paths
        import re
        # Look for file paths mentioned near phantom read discussion
        path_matches = re.findall(r'[/\w-]+\.(?:md|py|json|txt|yaml|yml)', content)
        affected_files = list(set(path_matches))[:10]  # Limit to 10

    return {
        "context_snapshots": context_snapshots,
        "outcome": outcome,
        "affected_files": affected_files,
        "notes": notes
    }


def classify_reset_pattern(resets: list, total_events: int) -> str:
    """Classify the reset pattern based on positions."""
    if not resets:
        return "NO_RESETS"

    positions = [(r["sequence_position"] / total_events) * 100 for r in resets]

    if len(positions) == 1:
        if positions[0] < 50:
            return "SINGLE_EARLY"
        else:
            return "SINGLE_LATE"

    # Multiple resets
    if all(p > 80 for p in positions):
        return "LATE_CLUSTERED"

    first = positions[0]
    last = positions[-1]
    mid_resets = [p for p in positions if 50 <= p <= 90]

    if first < 50 and not mid_resets and last > 90:
        return "EARLY_PLUS_LATE"

    if first < 50 and mid_resets:
        return "EARLY_PLUS_MID_LATE"

    return "OTHER"


def main():
    print("Parsing session file...")
    session_data = parse_session_file()

    print(f"  Processed {session_data['total_lines']} lines")
    print(f"  Found {len(session_data['token_progression'])} assistant messages with usage data")
    print(f"  Found {len(session_data['file_reads'])} Read operations")
    print(f"  Detected {len(session_data['resets'])} context resets")

    print("\nParsing chat export...")
    chat_data = parse_chat_export()
    print(f"  Found {len(chat_data['context_snapshots'])} context snapshots")
    print(f"  Outcome: {chat_data['outcome']}")

    # Compute derived metrics
    total_events = len(session_data['token_progression'])
    resets = session_data['resets']

    # Update reset data with totals and percentages
    for reset in resets:
        reset["total_events"] = total_events
        reset["position_percent"] = round((reset["sequence_position"] / total_events) * 100, 1) if total_events > 0 else 0

    pattern = classify_reset_pattern(resets, total_events)
    reset_positions = [r["position_percent"] for r in resets]

    # Get unique files
    unique_files = list(set(r["file_path"] for r in session_data['file_reads']))

    # Find pre/post operation tokens
    pre_op_tokens = 0
    post_op_tokens = 0

    # Look for trigger phase in user inputs
    trigger_line = None
    for ui in session_data['user_inputs']:
        if ui['phase'] == 'trigger':
            trigger_line = ui['session_line']
            break

    if trigger_line and session_data['token_progression']:
        # Find token count just before trigger
        for tp in session_data['token_progression']:
            if tp['session_line'] < trigger_line:
                pre_op_tokens = tp['cache_read_tokens']
            else:
                if post_op_tokens == 0:
                    post_op_tokens = tp['cache_read_tokens']

        # If we didn't find post, use the last one
        if post_op_tokens == 0 and session_data['token_progression']:
            post_op_tokens = session_data['token_progression'][-1]['cache_read_tokens']
    elif session_data['token_progression']:
        # No trigger found, use first and last
        pre_op_tokens = session_data['token_progression'][0]['cache_read_tokens']
        post_op_tokens = session_data['token_progression'][-1]['cache_read_tokens']

    # Build timeline
    timeline = []
    seq = 0

    for ui in session_data['user_inputs']:
        seq += 1
        timeline.append({
            "sequence": seq,
            "type": "user_input",
            "session_line": ui['session_line'],
            "phase": ui['phase'],
            "preview": ui['preview'][:50]
        })

    for reset in resets:
        seq += 1
        timeline.append({
            "sequence": seq,
            "type": "context_reset",
            "session_line": reset['session_line'],
            "from_tokens": reset['from_tokens'],
            "to_tokens": reset['to_tokens']
        })

    # Sort timeline by session_line
    timeline.sort(key=lambda x: x['session_line'])
    for i, item in enumerate(timeline, 1):
        item['sequence'] = i

    # Assemble output
    output = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "metadata": {
            "workscope_id": "20260120-095152",
            "session_uuid": "8cbb3e89-6e98-47ee-aad0-3f9caa5d17e5",
            "chat_export_file": "20260120-095152.txt",
            "session_file": "8cbb3e89-6e98-47ee-aad0-3f9caa5d17e5.jsonl",
            "has_subagents": True,
            "has_tool_results": False
        },
        "outcome": {
            "self_reported": chat_data['outcome'],
            "affected_files": chat_data['affected_files'],
            "notes": chat_data['notes']
        },
        "context_metrics": {
            "pre_operation_tokens": pre_op_tokens,
            "pre_operation_percent": round((pre_op_tokens / 200000) * 100, 1),
            "post_operation_tokens": post_op_tokens,
            "post_operation_percent": round((post_op_tokens / 200000) * 100, 1),
            "headroom_at_trigger": 200000 - pre_op_tokens,
            "context_window_size": 200000
        },
        "reset_analysis": {
            "total_resets": len(resets),
            "reset_positions_percent": reset_positions,
            "pattern_classification": pattern,
            "resets": resets
        },
        "file_reads": {
            "total_operations": len(session_data['file_reads']),
            "unique_files": len(unique_files),
            "reads": session_data['file_reads'],
            "unique_file_list": unique_files
        },
        "timeline": timeline,
        "token_progression": session_data['token_progression']
    }

    # Write output
    output_path = TRIAL_PATH / "trial_data.json"
    with output_path.open('w') as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput written to: {output_path}")

    # Print summary
    print(f"""
Trial Data Extraction Complete
==============================
Trial: 20260120-095152
Session: 8cbb3e89-6e98-47ee-aad0-3f9caa5d17e5

Outcome: {chat_data['outcome']}

Context Metrics:
  Pre-operation:  {pre_op_tokens // 1000}K tokens ({round((pre_op_tokens / 200000) * 100, 1)}%)
  Post-operation: {post_op_tokens // 1000}K tokens ({round((post_op_tokens / 200000) * 100, 1)}%)
  Headroom:       {(200000 - pre_op_tokens) // 1000}K tokens

Reset Analysis:
  Total resets: {len(resets)}
  Pattern: {pattern}
  Positions: {reset_positions}

File Reads:
  Total operations: {len(session_data['file_reads'])}
  Unique files: {len(unique_files)}

Timeline Events: {len(timeline)}

Output: {output_path}
Status: CREATED
""")


if __name__ == "__main__":
    main()
