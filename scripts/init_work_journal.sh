# Initialize a fresh Work Journal for a new agent session
# This script creates a new Work Journal directly in the archive location

# Accept Workscope ID as parameter
WORKSCOPE_ID=$1
if [ -z "$WORKSCOPE_ID" ]; then
    echo "Error: Workscope ID is required"
    echo "Usage: $0 <workscope-id>"
    exit 1
fi

# Get current timestamp for journal header
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# Ensure archive directory exists
mkdir -p dev/journal/archive

# Create Work Journal directly in archive location
JOURNAL_PATH="dev/journal/archive/Journal-Workscope-${WORKSCOPE_ID}.md"

# Initialize Work Journal with fresh header
echo "# Work Journal - $TIMESTAMP" > "$JOURNAL_PATH"
echo "## Workscope ID: Workscope-${WORKSCOPE_ID}" >> "$JOURNAL_PATH"
echo "" >> "$JOURNAL_PATH"

# Create symlink for Current-Journal.md (overwrites existing file)
# Use relative path from Current-Journal.md location to archive location
ln -sf "archive/Journal-Workscope-${WORKSCOPE_ID}.md" "dev/journal/Current-Journal.md"

# Output confirmation
echo "Work Journal initialized: $JOURNAL_PATH"
echo "Timestamp: $TIMESTAMP"
echo "Workscope ID: Workscope-${WORKSCOPE_ID}"
echo "Symlink created: dev/journal/Current-Journal.md -> archive/Journal-Workscope-${WORKSCOPE_ID}.md"

