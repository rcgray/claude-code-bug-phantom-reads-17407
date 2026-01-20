#!/usr/bin/env python3
"""
Parse session JSONL file for trial data extraction.
"""
import json
import sys
from pathlib import Path

def parse_session(session_path: Path):
    """Parse session JSONL and extract relevant data."""

    token_progression = []
    file_reads = []
    user_inputs = []
    context_resets = []

    prev_cache_tokens = 0
    sequence = 0
    batch_id = 0
    current_batch_line = -1

    line_num = 0
    errors = 0
    assistant_count = 0

    with open(session_path, 'r') as f:
        for line in f:
            line_num += 1
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                errors += 1
                continue

            msg_type = data.get('type')

            # Track user messages for user inputs
            if msg_type == 'user':
                content = ''
                if 'message' in data and 'content' in data['message']:
                    msg_content = data['message']['content']
                    if isinstance(msg_content, str):
                        content = msg_content
                    elif isinstance(msg_content, list):
                        for block in msg_content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                content = block.get('text', '')
                                break
                            elif isinstance(block, str):
                                content = block
                                break

                # Detect methodology phase
                phase = None
                content_lower = content.lower()
                if '/wsd:init' in content_lower:
                    phase = 'init'
                elif '/refine-plan' in content_lower:
                    phase = 'trigger'
                elif 'phantom read' in content_lower or 'persisted-output' in content_lower:
                    phase = 'inquiry'

                if phase:  # Only record if phase detected
                    user_inputs.append({
                        'session_line': line_num,
                        'content_preview': content[:100] if content else '',
                        'phase': phase
                    })

            # Track assistant messages for token progression and tool uses
            elif msg_type == 'assistant':
                assistant_count += 1

                # Extract usage/cache_read_input_tokens
                usage = data.get('message', {}).get('usage', {})
                cache_tokens = usage.get('cache_read_input_tokens', 0)

                if cache_tokens and cache_tokens > 0:
                    sequence += 1
                    token_progression.append({
                        'sequence': sequence,
                        'cache_read_tokens': cache_tokens,
                        'session_line': line_num
                    })

                    # Detect context reset (drop > 10000 tokens)
                    if prev_cache_tokens > 0 and (prev_cache_tokens - cache_tokens) > 10000:
                        context_resets.append({
                            'session_line': line_num,
                            'from_tokens': prev_cache_tokens,
                            'to_tokens': cache_tokens,
                            'sequence_position': sequence
                        })

                    prev_cache_tokens = cache_tokens

                # Extract tool uses (Read operations)
                content = data.get('message', {}).get('content', [])
                if isinstance(content, list):
                    reads_in_this_message = []
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'tool_use':
                            if block.get('name') == 'Read':
                                tool_input = block.get('input', {})
                                file_path = tool_input.get('file_path', '')
                                tool_id = block.get('id', '')
                                reads_in_this_message.append({
                                    'file_path': file_path,
                                    'tool_use_id': tool_id,
                                    'session_line': line_num
                                })

                    # Assign batch IDs
                    if reads_in_this_message:
                        if current_batch_line != line_num:
                            batch_id += 1
                            current_batch_line = line_num

                        for read in reads_in_this_message:
                            read['batch_id'] = batch_id
                            read['sequence'] = len(file_reads) + 1
                            file_reads.append(read)

    return {
        'token_progression': token_progression,
        'file_reads': file_reads,
        'user_inputs': user_inputs,
        'context_resets': context_resets,
        'stats': {
            'total_lines': line_num,
            'assistant_messages': assistant_count,
            'errors': errors
        }
    }

if __name__ == '__main__':
    session_path = Path('/Users/gray/Projects/claude-code-bug-phantom-reads-17407/dev/misc/wsd-dev-02/20260119-133027/a5b5f1c4-1945-4679-a252-62e1efe8295b.jsonl')
    result = parse_session(session_path)
    print(json.dumps(result, indent=2))
