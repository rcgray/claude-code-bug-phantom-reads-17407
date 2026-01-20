#!/usr/bin/env python3
"""
Parse a trial session .jsonl file to extract token progression, context resets, and file reads.
"""

import json
import sys
from pathlib import Path

def parse_session_file(jsonl_path: Path) -> dict:
    """Parse session file and extract key metrics."""

    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []

    prev_tokens = 0
    sequence = 0
    read_sequence = 0
    batch_id = 0
    last_read_line = -1

    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get('type')

            # Track user inputs
            if msg_type == 'human':
                content = data.get('message', {}).get('content', '')
                if isinstance(content, list):
                    content = ' '.join([c.get('text', '') for c in content if isinstance(c, dict)])
                elif not isinstance(content, str):
                    content = str(content)

                phase = None
                if '/wsd:init' in content:
                    phase = 'init'
                elif '/refine-plan' in content:
                    phase = 'trigger'
                elif 'phantom read' in content.lower() or 'persisted-output' in content.lower():
                    phase = 'inquiry'

                user_inputs.append({
                    'session_line': line_num,
                    'preview': content[:50] if content else '',
                    'phase': phase
                })

            # Track assistant messages with usage data
            if msg_type == 'assistant':
                usage = data.get('message', {}).get('usage', {})
                cache_read = usage.get('cache_read_input_tokens', 0)

                if cache_read and cache_read > 0:
                    sequence += 1
                    token_progression.append({
                        'sequence': sequence,
                        'cache_read_tokens': cache_read,
                        'session_line': line_num
                    })

                    # Detect resets (drop > 10000 tokens)
                    if prev_tokens > 0 and (prev_tokens - cache_read) > 10000:
                        resets.append({
                            'sequence_position': sequence,
                            'from_tokens': prev_tokens,
                            'to_tokens': cache_read,
                            'session_line': line_num
                        })

                    prev_tokens = cache_read

                # Track file reads
                message = data.get('message', {})
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                            if item.get('name') == 'Read':
                                read_sequence += 1

                                # Determine batch - same line = same batch
                                if line_num != last_read_line:
                                    batch_id += 1
                                    last_read_line = line_num

                                input_data = item.get('input', {})
                                file_path = input_data.get('file_path', '')

                                file_reads.append({
                                    'sequence': read_sequence,
                                    'batch_id': batch_id,
                                    'file_path': file_path,
                                    'session_line': line_num,
                                    'tool_use_id': item.get('id', '')
                                })

    # Compute total events for position percentages
    total_events = len(token_progression)
    for reset in resets:
        reset['total_events'] = total_events
        reset['position_percent'] = round((reset['sequence_position'] / total_events) * 100, 1)

    return {
        'token_progression': token_progression,
        'resets': resets,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'total_events': total_events
    }


def main():
    jsonl_path = Path('/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260119-140906/5a48a54e-4455-438d-b0df-5933149d2c78.jsonl')

    print(f"Parsing session file: {jsonl_path}")
    print(f"File size: {jsonl_path.stat().st_size / 1024:.1f} KB")

    results = parse_session_file(jsonl_path)

    print(f"\n=== Token Progression ===")
    print(f"Total data points: {len(results['token_progression'])}")

    print(f"\n=== Context Resets ===")
    print(f"Total resets: {len(results['resets'])}")
    for reset in results['resets']:
        print(f"  Line {reset['session_line']}: {reset['from_tokens']} -> {reset['to_tokens']} ({reset['position_percent']}%)")

    print(f"\n=== File Reads ===")
    print(f"Total operations: {len(results['file_reads'])}")
    unique_files = list(set(r['file_path'] for r in results['file_reads']))
    print(f"Unique files: {len(unique_files)}")

    print(f"\n=== User Inputs ===")
    for inp in results['user_inputs']:
        phase_str = f" [{inp['phase']}]" if inp['phase'] else ""
        print(f"  Line {inp['session_line']}{phase_str}: {inp['preview'][:60]}")

    # Output as JSON for comparison
    print(f"\n=== JSON Output ===")
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
