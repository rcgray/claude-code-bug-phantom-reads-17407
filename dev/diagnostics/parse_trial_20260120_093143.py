#!/usr/bin/env python
"""
Temporary script to parse trial session data for 20260120-093143.
Extracts token progression, context resets, file reads, and user inputs.
"""

import json
from pathlib import Path

TRIAL_PATH = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260120-093143")
SESSION_FILE = TRIAL_PATH / "683ca24f-7e5e-4e77-a203-0ec9e9318625.jsonl"

def parse_session() -> dict:
    """Parse the session JSONL file and extract relevant data."""
    token_progression = []
    file_reads = []
    user_inputs = []
    resets = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    current_batch_line = -1
    errors = 0

    with SESSION_FILE.open() as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                errors += 1
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

                # Extract file reads from tool_use blocks
                content = message.get("content", [])
                if isinstance(content, list):
                    batch_has_reads = False
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Read":
                                if not batch_has_reads or current_batch_line != line_num:
                                    batch_id += 1
                                    current_batch_line = line_num
                                    batch_has_reads = True

                                file_path = block.get("input", {}).get("file_path", "")
                                tool_use_id = block.get("id", "")
                                file_reads.append({
                                    "sequence": len(file_reads) + 1,
                                    "batch_id": batch_id,
                                    "file_path": file_path,
                                    "session_line": line_num,
                                    "tool_use_id": tool_use_id
                                })

            # Track user inputs
            elif msg_type == "human":
                message = data.get("message", {})
                content = message.get("content", "")
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
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

    # Compute unique files
    unique_files = list(set(r["file_path"] for r in file_reads))

    return {
        "token_progression": token_progression,
        "file_reads": file_reads,
        "user_inputs": user_inputs,
        "resets": resets,
        "unique_files": unique_files,
        "errors": errors,
        "total_lines": line_num
    }


if __name__ == "__main__":
    result = parse_session()

    print(f"Parsed {result['total_lines']} lines")
    print(f"Parse errors: {result['errors']}")
    print(f"\nToken progression points: {len(result['token_progression'])}")
    print(f"File reads: {len(result['file_reads'])}")
    print(f"Unique files: {len(result['unique_files'])}")
    print(f"User inputs: {len(result['user_inputs'])}")
    print(f"Context resets: {len(result['resets'])}")

    if result['resets']:
        print("\nResets:")
        for r in result['resets']:
            print(f"  Line {r['session_line']}: {r['from_tokens']} -> {r['to_tokens']} (drop: {r['from_tokens'] - r['to_tokens']})")

    if result['user_inputs']:
        print("\nUser inputs with phases:")
        for u in result['user_inputs']:
            if u['phase']:
                print(f"  Line {u['session_line']}: phase={u['phase']}, preview={u['preview'][:50]}...")

    # Output full data as JSON for further processing
    print("\n--- JSON DATA ---")
    print(json.dumps(result, indent=2))
