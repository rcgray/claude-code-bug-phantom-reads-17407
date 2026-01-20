#!/usr/bin/env python3
"""
Parse a Claude Code session .jsonl file to extract trial data.

This script extracts token progression, context resets, file reads,
and user inputs from a session file for phantom reads analysis.
"""

import json
import sys
from pathlib import Path


def parse_session_file(session_path: Path) -> dict:
    """Parse session .jsonl file and extract relevant data."""
    results = {
        "token_progression": [],
        "resets": [],
        "file_reads": [],
        "user_inputs": [],
        "line_count": 0,
        "assistant_messages": 0,
        "errors": [],
    }

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    current_batch_line = -1
    read_sequence = 0

    with session_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            results["line_count"] += 1
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                results["errors"].append(f"Line {line_num}: JSON error - {e}")
                continue

            msg_type = data.get("type")

            # Track human messages (user inputs)
            if msg_type == "human":
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

                results["user_inputs"].append({
                    "sequence": sequence,
                    "session_line": line_num,
                    "content_preview": content_preview,
                    "phase": phase,
                })
                sequence += 1

            # Track assistant messages with usage data
            elif msg_type == "assistant":
                message = data.get("message", {})
                usage = message.get("usage", {})
                cache_read_tokens = usage.get("cache_read_input_tokens", 0)

                if cache_read_tokens and cache_read_tokens > 0:
                    results["assistant_messages"] += 1
                    results["token_progression"].append({
                        "sequence": sequence,
                        "cache_read_tokens": cache_read_tokens,
                        "session_line": line_num,
                    })

                    # Detect context reset (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read_tokens) > 10000:
                        results["resets"].append({
                            "sequence_position": sequence,
                            "session_line": line_num,
                            "from_tokens": prev_cache_tokens,
                            "to_tokens": cache_read_tokens,
                        })

                    prev_cache_tokens = cache_read_tokens

                # Extract tool_use blocks for Read operations
                content = message.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            if block.get("name") == "Read":
                                # New batch if different line
                                if line_num != current_batch_line:
                                    batch_id += 1
                                    current_batch_line = line_num

                                read_sequence += 1
                                input_data = block.get("input", {})
                                file_path = input_data.get("file_path", "")

                                results["file_reads"].append({
                                    "sequence": read_sequence,
                                    "batch_id": batch_id,
                                    "file_path": file_path,
                                    "session_line": line_num,
                                    "tool_use_id": block.get("id", ""),
                                })

                sequence += 1

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_trial_session.py <session_file.jsonl>")
        sys.exit(1)

    session_path = Path(sys.argv[1])
    if not session_path.exists():
        print(f"Error: File not found: {session_path}")
        sys.exit(1)

    results = parse_session_file(session_path)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
