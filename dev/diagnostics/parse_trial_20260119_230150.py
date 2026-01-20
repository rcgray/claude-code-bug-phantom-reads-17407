#!/usr/bin/env python3
"""
Parse a trial session JSONL file to extract structured data for trial_data.json.

This diagnostic script extracts:
- Token progression (cache_read_input_tokens)
- Context resets (drops > 10,000 tokens)
- File read operations
- User inputs and methodology phases
"""

import json
import sys
from pathlib import Path


def parse_session_file(jsonl_path: Path) -> dict:
    """Parse session JSONL and extract relevant data."""

    token_progression = []
    file_reads = []
    user_inputs = []
    resets = []

    sequence = 0
    prev_tokens = 0
    batch_id = 0
    current_batch_line = -1

    malformed_count = 0

    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                malformed_count += 1
                continue

            msg_type = data.get('type')

            # Track token progression from assistant messages
            if msg_type == 'assistant':
                message = data.get('message', {})
                usage = message.get('usage', {})
                cache_tokens = usage.get('cache_read_input_tokens', 0)

                if cache_tokens > 0:
                    sequence += 1
                    token_progression.append({
                        'sequence': sequence,
                        'cache_read_tokens': cache_tokens,
                        'session_line': line_num
                    })

                    # Detect context reset (drop > 10,000)
                    if prev_tokens > 0 and (prev_tokens - cache_tokens) > 10000:
                        resets.append({
                            'sequence_position': sequence,
                            'from_tokens': prev_tokens,
                            'to_tokens': cache_tokens,
                            'session_line': line_num
                        })

                    prev_tokens = cache_tokens

                # Extract tool_use blocks for Read operations
                content = message.get('content', [])
                if isinstance(content, list):
                    reads_in_batch = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                tool_input = block.get('input', {})
                                file_path = tool_input.get('file_path', '')
                                tool_id = block.get('id', '')

                                # Determine batch
                                if line_num != current_batch_line:
                                    batch_id += 1
                                    current_batch_line = line_num

                                reads_in_batch.append({
                                    'sequence': len(file_reads) + 1,
                                    'batch_id': batch_id - 1,
                                    'file_path': file_path,
                                    'session_line': line_num,
                                    'tool_use_id': tool_id
                                })

                    file_reads.extend(reads_in_batch)

            # Track user inputs
            elif msg_type == 'human':
                message = data.get('message', {})
                content = message.get('content', '')
                if isinstance(content, str):
                    preview = content[:50]

                    # Detect methodology phase
                    phase = None
                    if '/wsd:init' in content:
                        phase = 'init'
                    elif '/refine-plan' in content:
                        phase = 'trigger'
                    elif 'phantom read' in content.lower() or 'persisted-output' in content.lower():
                        phase = 'inquiry'

                    user_inputs.append({
                        'session_line': line_num,
                        'preview': preview,
                        'phase': phase
                    })

    # Calculate total events for reset positioning
    total_events = sequence if sequence > 0 else len(token_progression)
    for reset in resets:
        reset['total_events'] = total_events
        reset['position_percent'] = round((reset['sequence_position'] / total_events) * 100, 2)

    return {
        'token_progression': token_progression,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'resets': resets,
        'malformed_count': malformed_count,
        'total_lines': line_num if 'line_num' in dir() else 0
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_trial.py <session.jsonl>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    if not jsonl_path.exists():
        print(f"Error: File not found: {jsonl_path}")
        sys.exit(1)

    print(f"Parsing session file: {jsonl_path}")
    print(f"File size: {jsonl_path.stat().st_size / 1024:.1f}KB")

    result = parse_session_file(jsonl_path)

    print(f"\nProcessed {result['total_lines']} lines")
    if result['malformed_count'] > 0:
        print(f"Malformed lines skipped: {result['malformed_count']}")

    print(f"\nToken progression entries: {len(result['token_progression'])}")
    print(f"File read operations: {len(result['file_reads'])}")
    print(f"User inputs: {len(result['user_inputs'])}")
    print(f"Context resets detected: {len(result['resets'])}")

    # Output as JSON for further processing
    output = {
        'token_progression': result['token_progression'],
        'file_reads': result['file_reads'],
        'user_inputs': result['user_inputs'],
        'resets': result['resets'],
        'stats': {
            'total_lines': result['total_lines'],
            'malformed_count': result['malformed_count'],
            'unique_files': len(set(r['file_path'] for r in result['file_reads']))
        }
    }

    print("\n--- JSON OUTPUT ---")
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
