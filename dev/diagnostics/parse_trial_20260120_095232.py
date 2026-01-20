#!/usr/bin/env python3
"""
Parse trial session data for 20260120-095232.
Extracts token progression, context resets, file reads, and user inputs.
"""

import json
import sys
from pathlib import Path

TRIAL_FOLDER = Path("/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260120-095232")
SESSION_FILE = TRIAL_FOLDER / "ea44ab3c-a774-4c46-a4fb-73dcbea0f653.jsonl"

def parse_session():
    token_progression = []
    context_resets = []
    file_reads = []
    user_inputs = []

    prev_cache_tokens = 0
    current_batch_id = 0
    read_sequence = 0
    event_sequence = 0

    with open(SESSION_FILE, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get('type')

            # Track user inputs
            if msg_type == 'human':
                event_sequence += 1
                content = data.get('message', {}).get('content', '')
                if isinstance(content, list):
                    # Extract text from content blocks
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    content = ' '.join(text_parts)

                preview = content[:100] if content else ''

                # Detect phase
                phase = None
                content_lower = content.lower() if content else ''
                if '/wsd:init' in content_lower:
                    phase = 'init'
                elif '/refine-plan' in content_lower:
                    phase = 'trigger'
                elif 'phantom read' in content_lower or 'persisted-output' in content_lower:
                    phase = 'inquiry'

                user_inputs.append({
                    'sequence': event_sequence,
                    'session_line': line_num,
                    'preview': preview,
                    'phase': phase
                })

            # Track assistant messages with usage data
            if msg_type == 'assistant':
                event_sequence += 1
                message = data.get('message', {})
                usage = message.get('usage', {})
                cache_read = usage.get('cache_read_input_tokens', 0)

                if cache_read and cache_read > 0:
                    token_progression.append({
                        'sequence': event_sequence,
                        'cache_read_tokens': cache_read,
                        'session_line': line_num
                    })

                    # Detect context reset (drop > 10,000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_read) > 10000:
                        context_resets.append({
                            'sequence': event_sequence,
                            'session_line': line_num,
                            'from_tokens': prev_cache_tokens,
                            'to_tokens': cache_read
                        })

                    prev_cache_tokens = cache_read

                # Extract file reads from tool_use blocks
                content = message.get('content', [])
                if isinstance(content, list):
                    batch_has_reads = False
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                if not batch_has_reads:
                                    current_batch_id += 1
                                    batch_has_reads = True

                                read_sequence += 1
                                file_path = block.get('input', {}).get('file_path', '')
                                tool_use_id = block.get('id', '')

                                file_reads.append({
                                    'sequence': read_sequence,
                                    'batch_id': current_batch_id,
                                    'file_path': file_path,
                                    'session_line': line_num,
                                    'tool_use_id': tool_use_id
                                })

    return {
        'token_progression': token_progression,
        'context_resets': context_resets,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'total_events': event_sequence
    }

if __name__ == '__main__':
    results = parse_session()

    print(f"Parsed session file ({SESSION_FILE.stat().st_size // 1024}KB)")
    print(f"  Found {len(results['token_progression'])} assistant messages with usage data")
    print(f"  Found {len(results['file_reads'])} Read operations in {max([r['batch_id'] for r in results['file_reads']], default=0)} batches")
    print(f"  Detected {len(results['context_resets'])} context resets")
    print(f"  Found {len(results['user_inputs'])} user inputs")

    print("\n--- Token Progression (first 10) ---")
    for tp in results['token_progression'][:10]:
        print(f"  Line {tp['session_line']}: {tp['cache_read_tokens']:,} tokens")

    print("\n--- Context Resets ---")
    for cr in results['context_resets']:
        print(f"  Line {cr['session_line']}: {cr['from_tokens']:,} -> {cr['to_tokens']:,}")

    print("\n--- User Inputs ---")
    for ui in results['user_inputs']:
        phase_str = f" [{ui['phase']}]" if ui['phase'] else ""
        print(f"  Line {ui['session_line']}{phase_str}: {ui['preview'][:60]}...")

    print("\n--- File Reads ---")
    for fr in results['file_reads']:
        print(f"  Batch {fr['batch_id']}, Line {fr['session_line']}: {fr['file_path']}")

    # Output JSON for further processing
    print("\n\n=== JSON OUTPUT ===")
    print(json.dumps(results, indent=2))
