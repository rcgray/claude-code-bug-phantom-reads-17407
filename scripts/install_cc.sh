#!/bin/bash

# Check if version parameter is provided
if [ -z "$1" ]; then
    echo "Error: no version specified"
    exit 1
fi

VERSION="$1"

# Get current version
CURRENT_VERSION=$(claude --version 2>/dev/null)

# Uninstall current version
npm uninstall -g @anthropic-ai/claude-code >/dev/null 2>&1

echo "Removed: $CURRENT_VERSION"

# Clean npm cache
npm cache clean --force >/dev/null 2>&1

# Install specified version
npm install -g @anthropic-ai/claude-code@"$VERSION" >/dev/null 2>&1

# Get and display new version
NEW_VERSION=$(claude --version 2>/dev/null)
echo "Installed: $NEW_VERSION"
