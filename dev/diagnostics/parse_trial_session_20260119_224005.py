#!/usr/bin/env python
"""
Parse a Claude Code session .jsonl file to extract trial data.

This script extracts:
- Token progression (cache_read_input_tokens)
- Context resets (drops > 10,000 tokens)
- File read operations
- User inputs and methodology phases
- Timeline events
"""

import json
import sys
from pathlib import Path


def parse_session_file(session_path: Path) -> dict:
    """Parse session .jsonl file and extract trial data."""
    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []
    timeline = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    current_batch_line = -1
    malformed_lines = 0

    with session_path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                malformed_lines += 1
                continue

            msg_type = data.get("type")

            # Track assistant messages with usage data
            if msg_type == "assistant":
                message = data.get("message", {})
                usage = message.get("usage", {})
                cache_read = usage.get("cache_read_input_tokens", 0)

                if cache_read and cache_read > 0:
                    sequence += 1
                    token_progression.append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_read,
                        "session_line": line_num
                    })

                    # Detect context resets
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read) > 10000:
                        resets.append({
                            "sequence_position": sequence,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_read,
                            "session_line": line_num
                        })

                    prev_cache_tokens = cache_read

                # Extract tool_use blocks for Read operations
                content = message.get("content", [])
                if isinstance(content, list):
                    reads_in_message = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Read":
                                tool_input = block.get("input", {})
                                file_path = tool_input.get("file_path", "")
                                tool_id = block.get("id", "")
                                reads_in_message.append({
                                    "file_path": file_path,
                                    "tool_use_id": tool_id,
                                    "session_line": line_num
                                })

                    # Assign batch IDs
                    if reads_in_message:
                        if line_num != current_batch_line:
                            batch_id += 1
                            current_batch_line = line_num
                        for read in reads_in_message:
                            read["batch_id"] = batch_id
                            read["sequence"] = len(file_reads) + 1
                            file_reads.append(read)

            # Track human/user messages
            elif msg_type in ("human", "user"):
                message = data.get("message", {})
                content = message.get("content", "")

                # Handle content as string or list
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = " ".join(text_parts)

                preview = content[:100] if content else ""

                # Detect methodology phase
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
        "resets": resets,
        "file_reads": file_reads,
        "user_inputs": user_inputs,
        "malformed_lines": malformed_lines,
        "total_lines": line_num
    }


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_trial_session.py <session_file.jsonl>")
        sys.exit(1)

    session_path = Path(sys.argv[1])
    if not session_path.exists():
        print(f"Error: File not found: {session_path}")
        sys.exit(1)

    result = parse_session_file(session_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
