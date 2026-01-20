#!/usr/bin/env python
"""
Parse a Claude Code session .jsonl file to extract:
- Token progression (cache_read_input_tokens)
- Context resets (drops > 10,000 tokens)
- File reads (Read tool_use blocks)
- User inputs and methodology phases
"""

import json
import sys
from pathlib import Path


def parse_session(session_path: Path) -> dict:
    """Parse session file and extract structured data."""

    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []

    prev_tokens = None
    sequence = 0
    batch_id = 0
    read_sequence = 0
    current_message_line = None
    current_batch_files = []

    with session_path.open('r') as f:
        for line_num, line in enumerate(f, start=1):
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            msg_type = data.get('type')

            # Track user inputs
            if msg_type == 'human':
                content = data.get('message', {}).get('content', '')
                if isinstance(content, list):
                    content = ' '.join(
                        c.get('text', '') for c in content if isinstance(c, dict)
                    )

                phase = None
                if '/wsd:init' in content:
                    phase = 'init'
                elif '/refine-plan' in content:
                    phase = 'trigger'
                elif 'phantom read' in content.lower() or 'persisted-output' in content.lower():
                    phase = 'inquiry'

                user_inputs.append({
                    'line': line_num,
                    'preview': content[:50] if content else '',
                    'phase': phase
                })

            # Track assistant messages with usage data
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

                    # Check for context reset
                    if prev_tokens is not None:
                        drop = prev_tokens - cache_tokens
                        if drop > 10000:
                            resets.append({
                                'sequence': sequence,
                                'from_tokens': prev_tokens,
                                'to_tokens': cache_tokens,
                                'session_line': line_num
                            })

                    prev_tokens = cache_tokens

                # Track Read tool_use blocks
                content = message.get('content', [])
                if isinstance(content, list):
                    reads_in_message = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                read_sequence += 1
                                file_path = block.get('input', {}).get('file_path', '')
                                reads_in_message.append({
                                    'sequence': read_sequence,
                                    'file_path': file_path,
                                    'session_line': line_num,
                                    'tool_use_id': block.get('id', '')
                                })

                    if reads_in_message:
                        batch_id += 1
                        for read in reads_in_message:
                            read['batch_id'] = batch_id
                            file_reads.append(read)

    return {
        'token_progression': token_progression,
        'resets': resets,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'total_events': sequence
    }


def main():
    session_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not session_path or not session_path.exists():
        print("Usage: python parse_session.py <session.jsonl>")
        sys.exit(1)

    result = parse_session(session_path)

    print(f"Lines processed: {result['total_events']} token events")
    print(f"Token progression entries: {len(result['token_progression'])}")
    print(f"Context resets: {len(result['resets'])}")
    print(f"File reads: {len(result['file_reads'])}")
    print(f"User inputs: {len(result['user_inputs'])}")

    # Print resets
    print("\n=== RESETS ===")
    for r in result['resets']:
        pct = (r['sequence'] / result['total_events']) * 100
        print(f"  Seq {r['sequence']} (line {r['session_line']}): {r['from_tokens']} -> {r['to_tokens']} ({pct:.1f}%)")

    # Print user input phases
    print("\n=== USER INPUTS ===")
    for u in result['user_inputs']:
        phase = f" [{u['phase']}]" if u['phase'] else ""
        print(f"  Line {u['line']}{phase}: {u['preview'][:40]}...")

    # Print file reads summary
    print("\n=== FILE READS ===")
    unique_files = set()
    for r in result['file_reads']:
        unique_files.add(r['file_path'])
    print(f"  Total operations: {len(result['file_reads'])}")
    print(f"  Unique files: {len(unique_files)}")

    # Output JSON for further processing
    print("\n=== JSON OUTPUT ===")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
