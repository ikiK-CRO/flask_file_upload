#!/bin/bash
# Script to clean log entries for files that no longer exist in the uploads directory

# Directory paths
LOG_DIR="./logs"
UPLOAD_DIR="./uploads"
LOG_FILE="${LOG_DIR}/app.log"
TEMP_LOG="${LOG_DIR}/temp_app.log"

echo "=== Starting log cleanup process ==="
echo "$(date): Running log cleanup" >> "${LOG_DIR}/maintenance.log"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "Log file $LOG_FILE does not exist. Nothing to clean."
    exit 0
fi

# Check if uploads directory exists
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "Uploads directory $UPLOAD_DIR does not exist."
    mkdir -p "$UPLOAD_DIR"
    echo "Created uploads directory."
fi

# Extract UUIDs from log lines
echo "Extracting UUIDs from logs..."
UUIDS=$(grep -o -E "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" "$LOG_FILE" | sort | uniq)

# Count of UUIDs found
UUID_COUNT=$(echo "$UUIDS" | wc -l)
echo "Found $UUID_COUNT unique UUIDs in logs"

# Initialize counters
MISSING_COUNT=0
KEPT_LINES=0
TOTAL_LINES=$(wc -l < "$LOG_FILE")

# Create a temporary file
touch "$TEMP_LOG"

# Start with a log reset header
echo "--- Log cleaned at $(date) ---" > "$TEMP_LOG"

# Check each UUID to see if a corresponding file exists
echo "Checking for missing files..."
MISSING_UUIDS=""

for uuid in $UUIDS; do
    # Check if any file with this UUID exists in the uploads directory
    if ! ls "${UPLOAD_DIR}/${uuid}_"* 1>/dev/null 2>&1 && ! ls "${UPLOAD_DIR}/${uuid}*" 1>/dev/null 2>&1; then
        MISSING_UUIDS="$MISSING_UUIDS|$uuid"
        MISSING_COUNT=$((MISSING_COUNT+1))
        echo "UUID $uuid: No matching file found"
    fi
done

# Remove leading pipe if it exists
MISSING_UUIDS=${MISSING_UUIDS#|}

# If there are missing UUIDs, filter the logs
if [ -n "$MISSING_UUIDS" ]; then
    echo "Filtering out log entries for $MISSING_COUNT missing UUIDs..."
    
    # Grep line by line to avoid issues with long patterns
    while IFS= read -r line; do
        match=false
        for uuid in $(echo "$MISSING_UUIDS" | tr '|' ' '); do
            if echo "$line" | grep -q "$uuid"; then
                match=true
                break
            fi
        done
        
        if [ "$match" = false ]; then
            echo "$line" >> "$TEMP_LOG"
            KEPT_LINES=$((KEPT_LINES+1))
        fi
    done < "$LOG_FILE"
else
    echo "No missing UUIDs found. All files exist."
    cp "$LOG_FILE" "$TEMP_LOG"
    KEPT_LINES=$TOTAL_LINES
fi

# Backup the original log file
cp "$LOG_FILE" "${LOG_FILE}.bak"

# Replace the log file with our filtered version
mv "$TEMP_LOG" "$LOG_FILE"

echo "=== Log cleanup complete ==="
echo "Total lines in original log: $TOTAL_LINES"
echo "Lines kept in new log: $KEPT_LINES"
echo "Lines removed: $((TOTAL_LINES - KEPT_LINES))"
echo "Missing UUIDs: $MISSING_COUNT"
echo "$(date): Log cleanup completed. Removed $((TOTAL_LINES - KEPT_LINES)) lines for $MISSING_COUNT missing UUIDs" >> "${LOG_DIR}/maintenance.log"

exit 0 