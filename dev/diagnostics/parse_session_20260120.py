#!/usr/bin/env python
"""
Parse a Claude Code session .jsonl file to extract trial data metrics.

This script extracts token progression, context resets, file reads, and user inputs
from a session file for phantom reads analysis.
"""

import json
import sys
from pathlib import Path


def parse_session_file(session_path: Path) -> dict:
    """
    Parse a session .jsonl file and extract relevant metrics.

    Args:
        session_path: Path to the session .jsonl file

    Returns:
        Dictionary containing extracted metrics
    """
    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []

    prev_cache_tokens = 0
    sequence = 0
    read_sequence = 0
    batch_id = 0
    last_assistant_line = -1
    errors = 0

    with session_path.open('r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                errors += 1
                continue

            msg_type = data.get('type')

            # Track assistant messages with usage data
            if msg_type == 'assistant':
                message = data.get('message', {})
                usage = message.get('usage', {})
                cache_read = usage.get('cache_read_input_tokens', 0)

                if cache_read and cache_read > 0:
                    sequence += 1
                    token_progression.append({
                        'sequence': sequence,
                        'cache_read_tokens': cache_read,
                        'session_line': line_num
                    })

                    # Detect context resets (drop > 10000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read) > 10000:
                        resets.append({
                            'sequence_position': sequence,
                            'from_tokens': prev_cache_tokens,
                            'to_tokens': cache_read,
                            'session_line': line_num
                        })

                    prev_cache_tokens = cache_read

                # Extract file reads from tool_use blocks
                content = message.get('content', [])
                if isinstance(content, list):
                    current_batch_has_reads = False
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                if last_assistant_line != line_num:
                                    batch_id += 1
                                    last_assistant_line = line_num

                                read_sequence += 1
                                inp = block.get('input', {})
                                file_reads.append({
                                    'sequence': read_sequence,
                                    'batch_id': batch_id,
                                    'file_path': inp.get('file_path', ''),
                                    'session_line': line_num,
                                    'tool_use_id': block.get('id', '')
                                })

            # Track human messages
            elif msg_type == 'human':
                message = data.get('message', {})
                content = message.get('content', '')
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = ' '.join(text_parts)

                preview = content[:100] if content else ''

                # Detect methodology phases
                phase = None
                content_lower = content.lower() if content else ''
                if '/wsd:init' in content_lower:
                    phase = 'init'
                elif '/refine-plan' in content_lower:
                    phase = 'trigger'
                elif 'phantom read' in content_lower or 'persisted-output' in content_lower:
                    phase = 'inquiry'

                user_inputs.append({
                    'session_line': line_num,
                    'preview': preview,
                    'phase': phase
                })

    return {
        'token_progression': token_progression,
        'resets': resets,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'total_lines': line_num,
        'errors': errors
    }


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python parse_session_20260120.py <session_file>")
        sys.exit(1)

    session_path = Path(sys.argv[1])
    if not session_path.exists():
        print(f"Error: File not found: {session_path}")
        sys.exit(1)

    result = parse_session_file(session_path)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
