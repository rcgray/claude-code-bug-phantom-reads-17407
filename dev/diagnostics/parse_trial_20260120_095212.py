#!/usr/bin/env python
"""
Parse trial session data for trial 20260120-095212.

This script extracts token progression, context resets, and file reads
from a Claude Code session .jsonl file.
"""

import json
from pathlib import Path


def parse_session_file(session_path: Path) -> dict:
    """Parse the session .jsonl file and extract relevant data."""
    token_progression = []
    file_reads = []
    user_inputs = []
    resets = []

    prev_cache_tokens = 0
    sequence = 0
    read_sequence = 0
    batch_id = 0
    current_batch_line = -1

    with session_path.open('r') as f:
        for line_num, line in enumerate(f, 1):
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
                    'sequence': sequence,
                    'content_preview': content[:100] if content else '',
                    'phase': phase,
                    'session_line': line_num
                })
                sequence += 1

            # Track assistant messages with usage data
            if msg_type == 'assistant':
                message = data.get('message', {})
                usage = message.get('usage', {})
                cache_tokens = usage.get('cache_read_input_tokens', 0)

                if cache_tokens and cache_tokens > 0:
                    token_progression.append({
                        'sequence': sequence,
                        'cache_read_tokens': cache_tokens,
                        'session_line': line_num
                    })

                    # Detect context resets (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_tokens) > 10000:
                        resets.append({
                            'sequence_position': sequence,
                            'from_tokens': prev_cache_tokens,
                            'to_tokens': cache_tokens,
                            'session_line': line_num
                        })

                    prev_cache_tokens = cache_tokens

                # Extract file reads from tool_use blocks
                content = message.get('content', [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                # Update batch_id if this is a new message
                                if line_num != current_batch_line:
                                    batch_id += 1
                                    current_batch_line = line_num

                                input_data = block.get('input', {})
                                file_path = input_data.get('file_path', '')

                                file_reads.append({
                                    'sequence': read_sequence,
                                    'batch_id': batch_id,
                                    'file_path': file_path,
                                    'session_line': line_num,
                                    'tool_use_id': block.get('id', '')
                                })
                                read_sequence += 1

                sequence += 1

    # Calculate unique files
    unique_files = list(set(r['file_path'] for r in file_reads if r['file_path']))

    return {
        'token_progression': token_progression,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'resets': resets,
        'unique_file_list': unique_files,
        'total_lines': line_num
    }


def main() -> None:
    """Main entry point."""
    trial_path = Path('/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260120-095212')
    session_file = trial_path / 'b2b36cd7-fe3f-41b0-93be-01d8e257e7dc.jsonl'

    print(f"Parsing session file ({session_file.stat().st_size // 1024}KB)...")

    result = parse_session_file(session_file)

    print(f"  Processed {result['total_lines']} lines")
    print(f"  Found {len(result['token_progression'])} assistant messages with usage data")
    print(f"  Found {len(result['file_reads'])} Read operations in {max((r['batch_id'] for r in result['file_reads']), default=0)} batches")
    print(f"  Detected {len(result['resets'])} context resets")
    print(f"  Found {len(result['user_inputs'])} user inputs")

    # Output as JSON for further processing
    output = {
        'token_progression': result['token_progression'],
        'file_reads': result['file_reads'],
        'user_inputs': result['user_inputs'],
        'resets': result['resets'],
        'unique_file_list': result['unique_file_list'],
        'stats': {
            'total_lines': result['total_lines'],
            'total_reads': len(result['file_reads']),
            'unique_files': len(result['unique_file_list']),
            'total_resets': len(result['resets']),
            'total_batches': max((r['batch_id'] for r in result['file_reads']), default=0)
        }
    }

    print("\n--- JSON OUTPUT ---")
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
