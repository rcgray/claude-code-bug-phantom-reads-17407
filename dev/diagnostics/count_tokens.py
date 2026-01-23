#!/usr/bin/env python3
"""Count tokens in a text file using tiktoken."""

import sys
import tiktoken

def count_tokens(filepath):
    """Count tokens in file using cl100k_base encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(content)
    return len(tokens)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: count_tokens.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    token_count = count_tokens(filepath)
    print(f"{token_count}")
