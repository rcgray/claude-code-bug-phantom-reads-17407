#!/usr/bin/env python
"""
Parse a trial session JSONL file and extract structured data for trial_data.json.

This script extracts:
- Token progression (cache_read_input_tokens)
- Context resets (drops > 10,000 tokens)
- File reads (Read tool_use blocks)
- User inputs with methodology phase detection
"""

import json
import sys
from pathlib import Path


def parse_session_file(jsonl_path: Path) -> dict:
    """
    Parse a session JSONL file and extract trial data.

    Args:
        jsonl_path: Path to the .jsonl session file

    Returns:
        Dictionary with extracted data
    """
    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []
    timeline = []

    prev_cache_tokens = 0
    line_number = 0
    sequence = 0
    batch_id = 0
    errors = 0

    current_batch_line = None

    with jsonl_path.open("r") as f:
        for line in f:
            line_number += 1
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                errors += 1
                continue

            msg_type = entry.get("type")

            # Track assistant messages with usage data
            if msg_type == "assistant":
                message = entry.get("message", {})
                usage = message.get("usage", {})
                cache_tokens = usage.get("cache_read_input_tokens", 0)

                if cache_tokens and cache_tokens > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_tokens,
                        "session_line": line_number
                    })

                    # Detect context reset (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_tokens) > 10000:
                        resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_tokens,
                            "session_line": line_number
                        })
                        timeline.append({
                            "sequence": sequence,
                            "type": "context_reset",
                            "session_line": line_number,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_tokens
                        })

                    prev_cache_tokens = cache_tokens

                # Extract Read tool_use blocks
                content = message.get("content", [])
                reads_in_batch = []

                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        if block.get("name") == "Read":
                            tool_input = block.get("input", {})
                            file_path = tool_input.get("file_path", "")
                            tool_id = block.get("id", "")

                            # New batch if different line
                            if current_batch_line != line_number:
                                batch_id += 1
                                current_batch_line = line_number

                            read_entry = {
                                "sequence": len(file_reads) + 1,
                                "batch_id": batch_id,
                                "file_path": file_path,
                                "session_line": line_number,
                                "tool_use_id": tool_id
                            }
                            file_reads.append(read_entry)
                            reads_in_batch.append(read_entry)

                if reads_in_batch:
                    timeline.append({
                        "sequence": sequence,
                        "type": "tool_batch",
                        "session_line": line_number,
                        "tool_type": "Read",
                        "count": len(reads_in_batch),
                        "files": [r["file_path"] for r in reads_in_batch]
                    })

            # Track human messages
            elif msg_type == "human":
                message = entry.get("message", {})
                content = message.get("content", "")

                if isinstance(content, list):
                    # Extract text from content blocks
                    content = " ".join(
                        block.get("text", "") for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    )

                content_preview = content[:100] if content else ""

                # Detect methodology phase
                phase = None
                content_lower = content.lower()
                if "/wsd:init" in content_lower:
                    phase = "init"
                elif "/refine-plan" in content_lower:
                    phase = "trigger"
                elif "phantom read" in content_lower or "persisted-output" in content_lower:
                    phase = "inquiry"

                sequence += 1
                user_input = {
                    "sequence": sequence,
                    "session_line": line_number,
                    "content_preview": content_preview,
                    "phase": phase
                }
                user_inputs.append(user_input)

                timeline.append({
                    "sequence": sequence,
                    "type": "user_input",
                    "session_line": line_number,
                    "phase": phase,
                    "content_preview": content_preview[:50]
                })

    # Get unique files
    unique_files = list(set(r["file_path"] for r in file_reads if r["file_path"]))

    return {
        "token_progression": token_progression,
        "resets": resets,
        "file_reads": file_reads,
        "unique_file_list": unique_files,
        "user_inputs": user_inputs,
        "timeline": timeline,
        "stats": {
            "total_lines": line_number,
            "assistant_messages_with_usage": len(token_progression),
            "read_operations": len(file_reads),
            "read_batches": batch_id,
            "context_resets": len(resets),
            "parse_errors": errors
        }
    }


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_trial_session.py <jsonl_path>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    if not jsonl_path.exists():
        print(f"Error: File not found: {jsonl_path}")
        sys.exit(1)

    result = parse_session_file(jsonl_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
