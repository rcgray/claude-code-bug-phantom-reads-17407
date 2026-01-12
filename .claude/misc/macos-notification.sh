#!/bin/bash
# Process transcript and send macOS notification with logging
# Usage: macos-notification.sh [title]
# If title is provided as argument, it overrides the default

TRANSCRIPT=$(jq -r .transcript_path)
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
LOG_FILE="$XDG_DATA_HOME/ccnotify/notifications.log"
LOG_DIR="$XDG_DATA_HOME/ccnotify"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log function
log_notification() {
  local level="$1"
  local message="$2"
  local details="$3"
  echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\",\"level\":\"$level\",\"type\":\"macos\",\"message\":\"$message\",\"details\":$details}" >> "$LOG_FILE"
}

# Get title from argument or use default
DEFAULT_TITLE="Claude Code"
MAIN_TITLE="${1:-$DEFAULT_TITLE}"

# Get latest assistant message
LATEST_MSG=$(tail -1 "$TRANSCRIPT" | jq -r '.message.content[0].text // empty')

# Get latest user message using a temporary file for portability
USER_MSG=""
TEMP_FILE=$(mktemp)
tac "$TRANSCRIPT" > "$TEMP_FILE"
while IFS= read -r line; do
  TYPE=$(echo "$line" | jq -r '.type // empty')
  if [ "$TYPE" = "user" ]; then
    ROLE=$(echo "$line" | jq -r '.message.role // empty')
    if [ "$ROLE" = "user" ]; then
      CONTENT=$(echo "$line" | jq -r '.message.content // empty')
      # Only use content if it's a string and doesn't start with [
      if [ -n "$CONTENT" ] && [ "${CONTENT:0:1}" != "[" ]; then
        USER_MSG="$CONTENT"
        break
      fi
    fi
  fi
done < "$TEMP_FILE"
rm -f "$TEMP_FILE"

# Log notification start
log_notification "INFO" "Starting macOS notification" "{\"title\":\"$MAIN_TITLE\",\"transcriptPath\":\"$TRANSCRIPT\"}"

# Send notification only if assistant message is not empty
if [ -n "$LATEST_MSG" ]; then
  # Use user message as subtitle (truncated to 256 chars for macOS limit)
  SUBTITLE="${USER_MSG:0:256}"

  # Use assistant message as body (truncated to 1000 chars for macOS limit)
  NOTIFICATION_BODY="${LATEST_MSG:0:1000}"

  START_TIME=$(date +%s)

  # Display macOS notification using terminal-notifier
  terminal-notifier -title "$MAIN_TITLE" -subtitle "$SUBTITLE" -message "$NOTIFICATION_BODY" -sound "Glass"

  END_TIME=$(date +%s)
  EXECUTION_TIME=$((END_TIME - START_TIME))

  # Check if terminal-notifier command was successful
  if [ $? -eq 0 ]; then
    log_notification "INFO" "macOS notification sent successfully" "{\"title\":\"$MAIN_TITLE\",\"executionTime\":$EXECUTION_TIME}"
  else
    log_notification "ERROR" "macOS notification failed" "{\"title\":\"$MAIN_TITLE\",\"executionTime\":$EXECUTION_TIME,\"error\":\"terminal-notifier command failed\"}"
  fi
else
  log_notification "DEBUG" "macOS notification skipped" "{\"title\":\"$MAIN_TITLE\",\"reason\":\"No assistant message found\"}"
fi
