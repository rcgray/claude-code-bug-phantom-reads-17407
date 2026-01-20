#!/usr/bin/env python
"""
Parse trial session file and extract structured data for trial_data.json.
Created for workscope 20260119-224743.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def parse_session_file(session_path: Path) -> dict:
    """Parse a session JSONL file and extract relevant data."""

    token_progression = []
    resets = []
    file_reads = []
    user_inputs = []
    timeline = []

    prev_cache_tokens = None
    sequence = 0
    batch_id = 0
    current_batch_line = None
    errors = 0

    with session_path.open('r') as f:
        for line_num, line in enumerate(f, start=1):
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
                    if prev_cache_tokens is not None:
                        if prev_cache_tokens - cache_read > 10000:
                            resets.append({
                                'sequence_position': sequence,
                                'from_tokens': prev_cache_tokens,
                                'to_tokens': cache_read,
                                'session_line': line_num
                            })

                    prev_cache_tokens = cache_read

                # Extract Read tool_use blocks from assistant content
                content = message.get('content', [])
                reads_in_message = []

                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        if block.get('name') == 'Read':
                            tool_input = block.get('input', {})
                            file_path = tool_input.get('file_path', '')
                            tool_id = block.get('id', '')

                            # Update batch tracking
                            if current_batch_line != line_num:
                                batch_id += 1
                                current_batch_line = line_num

                            reads_in_message.append({
                                'sequence': len(file_reads) + 1,
                                'batch_id': batch_id,
                                'file_path': file_path,
                                'session_line': line_num,
                                'tool_use_id': tool_id
                            })

                file_reads.extend(reads_in_message)

            # Track user/human messages
            elif msg_type == 'human':
                message = data.get('message', {})
                content = message.get('content', '')

                # Handle content as string or list
                if isinstance(content, list):
                    content_text = ''
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            content_text += block.get('text', '')
                        elif isinstance(block, str):
                            content_text += block
                    content = content_text

                preview = content[:50] if content else ''

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
                    'content_preview': preview,
                    'phase': phase
                })

    return {
        'token_progression': token_progression,
        'resets': resets,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'errors': errors,
        'total_lines': line_num
    }


def main():
    session_path = Path('/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260119-142117/4238e5fb-6bf4-479e-90dd-6fad78571fce.jsonl')

    result = parse_session_file(session_path)

    print(f"Processed {result['total_lines']} lines")
    print(f"Errors: {result['errors']}")
    print(f"\nToken progression entries: {len(result['token_progression'])}")
    print(f"Context resets: {len(result['resets'])}")
    print(f"File reads: {len(result['file_reads'])}")
    print(f"User inputs: {len(result['user_inputs'])}")

    print("\n=== TOKEN PROGRESSION ===")
    for tp in result['token_progression']:
        print(f"  Seq {tp['sequence']}: {tp['cache_read_tokens']:,} tokens (line {tp['session_line']})")

    print("\n=== CONTEXT RESETS ===")
    for r in result['resets']:
        print(f"  At seq {r['sequence_position']}: {r['from_tokens']:,} -> {r['to_tokens']:,} (line {r['session_line']})")

    print("\n=== FILE READS ===")
    for fr in result['file_reads']:
        print(f"  Batch {fr['batch_id']}: {fr['file_path']}")

    print("\n=== USER INPUTS ===")
    for ui in result['user_inputs']:
        phase_str = f" [{ui['phase']}]" if ui['phase'] else ""
        print(f"  Line {ui['session_line']}{phase_str}: {ui['content_preview'][:40]}...")

    # Output as JSON for further processing
    print("\n=== JSON OUTPUT ===")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
