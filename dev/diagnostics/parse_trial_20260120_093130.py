#!/usr/bin/env python
"""
Parse trial session file for 20260120-093130 and extract structured data.

This script extracts token progression, context resets, file reads, and other
metrics from a Claude Code session .jsonl file.
"""

import json
from pathlib import Path
from datetime import datetime

TRIAL_DIR = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260120-093130")
SESSION_FILE = TRIAL_DIR / "1cb17063-b50f-4059-bd3c-180225452204.jsonl"

def main() -> None:
    """Parse the session file and output extracted data."""

    token_progression = []
    file_reads = []
    user_inputs = []
    resets = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    read_sequence = 0
    current_batch_line = -1

    with SESSION_FILE.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # Track token progression from assistant messages
            if msg_type == "assistant":
                usage = data.get("message", {}).get("usage", {})
                cache_read = usage.get("cache_read_input_tokens", 0)

                if cache_read > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_read,
                        "session_line": line_num
                    })

                    # Detect context resets (drop of more than 10k tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read) > 10000:
                        resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_read,
                            "session_line": line_num
                        })

                    prev_cache_tokens = cache_read

                # Extract Read tool uses from assistant messages
                content = data.get("message", {}).get("content", [])
                reads_in_this_msg = []
                for block in content:
                    if block.get("type") == "tool_use" and block.get("name") == "Read":
                        read_sequence += 1
                        file_path = block.get("input", {}).get("file_path", "")
                        tool_id = block.get("id", "")
                        reads_in_this_msg.append({
                            "sequence": read_sequence,
                            "file_path": file_path,
                            "session_line": line_num,
                            "tool_use_id": tool_id
                        })

                # Assign batch ID
                if reads_in_this_msg:
                    if current_batch_line != line_num:
                        batch_id += 1
                        current_batch_line = line_num
                    for r in reads_in_this_msg:
                        r["batch_id"] = batch_id
                        file_reads.append(r)

            # Track user inputs
            elif msg_type == "user":
                content = data.get("message", {}).get("content", "")
                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    content = " ".join(text_parts)

                preview = content[:100].replace("\n", " ").strip()

                phase = "unknown"
                if "/wsd:init" in content:
                    phase = "init"
                elif "/refine-plan" in content:
                    phase = "trigger"
                elif "phantom read" in content.lower() or "persisted-output" in content.lower():
                    phase = "inquiry"

                user_inputs.append({
                    "preview": preview,
                    "phase": phase,
                    "session_line": line_num
                })

    # Output results
    print("=" * 60)
    print("TOKEN PROGRESSION")
    print("=" * 60)
    for t in token_progression:
        print(f"  Seq {t['sequence']:3d}: {t['cache_read_tokens']:,} tokens (line {t['session_line']})")

    print("\n" + "=" * 60)
    print("CONTEXT RESETS")
    print("=" * 60)
    if resets:
        for r in resets:
            drop = r['from_tokens'] - r['to_tokens']
            print(f"  Seq {r['sequence_position']:3d}: {r['from_tokens']:,} -> {r['to_tokens']:,} (drop of {drop:,}, line {r['session_line']})")
    else:
        print("  No resets detected")

    print("\n" + "=" * 60)
    print("FILE READS")
    print("=" * 60)
    for r in file_reads:
        print(f"  Batch {r['batch_id']:2d}, Seq {r['sequence']:3d}: {r['file_path']}")

    print("\n" + "=" * 60)
    print("USER INPUTS")
    print("=" * 60)
    for u in user_inputs:
        print(f"  [{u['phase']:10s}] {u['preview'][:60]}...")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total assistant messages with usage: {len(token_progression)}")
    print(f"  Total Read operations: {len(file_reads)}")
    print(f"  Unique files: {len(set(r['file_path'] for r in file_reads))}")
    print(f"  Total context resets: {len(resets)}")
    print(f"  User input phases: {[u['phase'] for u in user_inputs]}")

    # Output JSON structure for trial_data.json
    unique_files = list(set(r['file_path'] for r in file_reads))

    # Calculate context metrics
    pre_op_tokens = None
    post_op_tokens = None
    for i, u in enumerate(user_inputs):
        if u['phase'] == 'trigger':
            # Find token count right before trigger
            trigger_line = u['session_line']
            for t in token_progression:
                if t['session_line'] < trigger_line:
                    pre_op_tokens = t['cache_read_tokens']
                elif t['session_line'] > trigger_line and post_op_tokens is None:
                    post_op_tokens = t['cache_read_tokens']
            break

    # Use last token count if post_op not found
    if post_op_tokens is None and token_progression:
        post_op_tokens = token_progression[-1]['cache_read_tokens']

    print(f"\n  Pre-operation tokens: {pre_op_tokens:,}" if pre_op_tokens else "\n  Pre-operation tokens: N/A")
    print(f"  Post-operation tokens: {post_op_tokens:,}" if post_op_tokens else "  Post-operation tokens: N/A")

    # Calculate reset positions as percentages
    total_events = len(token_progression)
    reset_positions = []
    for r in resets:
        pos_pct = (r['sequence_position'] / total_events) * 100 if total_events > 0 else 0
        reset_positions.append(round(pos_pct, 1))
        r['total_events'] = total_events
        r['position_percent'] = round(pos_pct, 1)

    # Pattern classification
    if not resets:
        pattern = "NO_RESETS"
    elif len(resets) == 1:
        if reset_positions[0] < 50:
            pattern = "SINGLE_EARLY"
        else:
            pattern = "SINGLE_LATE"
    elif all(p > 80 for p in reset_positions):
        pattern = "LATE_CLUSTERED"
    elif reset_positions[0] < 50 and not any(50 <= p <= 90 for p in reset_positions) and reset_positions[-1] > 90:
        pattern = "EARLY_PLUS_LATE"
    elif reset_positions[0] < 50 and any(50 <= p <= 90 for p in reset_positions):
        pattern = "EARLY_PLUS_MID_LATE"
    else:
        pattern = "OTHER"

    print(f"  Reset positions: {reset_positions}")
    print(f"  Pattern: {pattern}")

if __name__ == "__main__":
    main()
