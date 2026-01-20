#!/usr/bin/env python
"""
Diagnostic script to parse trial session data for workscope 20260119-142117.

This script extracts:
- Token progression (cache_read_input_tokens)
- Context resets (drops > 10,000 tokens)
- File Read operations
- User inputs and phases
"""

import json
from pathlib import Path

TRIAL_PATH = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260119-142117")
SESSION_FILE = TRIAL_PATH / "4238e5fb-6bf4-479e-90dd-6fad78571fce.jsonl"

def parse_session():
    """Parse the session JSONL file."""
    token_progression = []
    file_reads = []
    user_inputs = []
    context_resets = []

    prev_tokens = None
    sequence = 0
    read_sequence = 0
    batch_id = 0
    last_batch_line = -1

    with SESSION_FILE.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"  Skipping malformed JSON at line {line_num}")
                continue

            msg_type = data.get("type")

            # Track assistant messages with usage data
            if msg_type == "assistant":
                usage = data.get("message", {}).get("usage", {})
                cache_tokens = usage.get("cache_read_input_tokens", 0)

                if cache_tokens > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_tokens,
                        "session_line": line_num
                    })

                    # Detect context reset (drop > 10,000 tokens)
                    if prev_tokens is not None and (prev_tokens - cache_tokens) > 10000:
                        context_resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_tokens,
                            "to_tokens": cache_tokens,
                            "session_line": line_num
                        })

                    prev_tokens = cache_tokens

                # Extract Read tool_use blocks
                content = data.get("message", {}).get("content", [])
                batch_reads = []
                for block in content:
                    if block.get("type") == "tool_use" and block.get("name") == "Read":
                        read_sequence += 1
                        # Check if same batch (same assistant message)
                        if line_num != last_batch_line:
                            batch_id += 1
                            last_batch_line = line_num

                        file_path = block.get("input", {}).get("file_path", "")
                        tool_use_id = block.get("id", "")

                        file_reads.append({
                            "sequence": read_sequence,
                            "batch_id": batch_id,
                            "file_path": file_path,
                            "session_line": line_num,
                            "tool_use_id": tool_use_id
                        })

            # Track human messages (user inputs)
            elif msg_type == "human":
                content = data.get("message", {}).get("content", [])
                text_content = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_content = block.get("text", "")[:100]
                        break
                    elif isinstance(block, str):
                        text_content = block[:100]
                        break

                # Detect phase
                phase = "unknown"
                if "/wsd:init" in text_content:
                    phase = "init"
                elif "/refine-plan" in text_content:
                    phase = "trigger"
                elif "phantom read" in text_content.lower() or "persisted-output" in text_content.lower():
                    phase = "inquiry"

                user_inputs.append({
                    "session_line": line_num,
                    "phase": phase,
                    "content_preview": text_content[:50]
                })

    return {
        "token_progression": token_progression,
        "file_reads": file_reads,
        "user_inputs": user_inputs,
        "context_resets": context_resets,
        "total_events": sequence
    }


def main():
    """Main entry point."""
    print(f"Parsing session file: {SESSION_FILE}")
    print(f"File size: {SESSION_FILE.stat().st_size / 1024:.1f} KB")
    print()

    results = parse_session()

    print(f"Token Progression: {len(results['token_progression'])} data points")
    print(f"File Reads: {len(results['file_reads'])} operations")
    print(f"User Inputs: {len(results['user_inputs'])} messages")
    print(f"Context Resets: {len(results['context_resets'])} detected")
    print()

    # Show context resets
    if results['context_resets']:
        print("Context Resets:")
        total = results['total_events']
        for reset in results['context_resets']:
            pos_pct = (reset['sequence_position'] / total) * 100
            print(f"  Line {reset['session_line']}: {reset['from_tokens']:,} -> {reset['to_tokens']:,} "
                  f"(position: {reset['sequence_position']}/{total} = {pos_pct:.1f}%)")
    print()

    # Show file reads
    print("File Reads:")
    unique_files = set()
    for read in results['file_reads']:
        unique_files.add(read['file_path'])
        print(f"  [{read['sequence']}] Batch {read['batch_id']}, Line {read['session_line']}: "
              f"{Path(read['file_path']).name}")
    print()
    print(f"Unique files: {len(unique_files)}")

    # Show user inputs with phases
    print()
    print("User Inputs (phases):")
    for inp in results['user_inputs']:
        print(f"  Line {inp['session_line']}: [{inp['phase']}] {inp['content_preview'][:40]}...")

    # Output JSON for verification
    print()
    print("=" * 60)
    print("JSON Output for verification:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
