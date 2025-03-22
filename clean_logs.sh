#!/bin/bash

# Script to clean log entries for files that no longer exist in the uploads directory
# Usage: ./clean_logs.sh

# Set colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting log cleanup for missing files...${NC}"

# Get path to logs
LOGS_DIR="./logs"

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${RED}Error: Logs directory not found at $LOGS_DIR${NC}"
    exit 1
fi

# Path to app log
APP_LOG="$LOGS_DIR/app.log"

# Get list of UUIDs from logs
echo -e "${YELLOW}Searching for file UUIDs in logs...${NC}"
UUIDS=$(grep -Eo "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" "$APP_LOG" | sort | uniq)

if [ -z "$UUIDS" ]; then
    echo -e "${GREEN}No UUIDs found in logs. Nothing to clean.${NC}"
    exit 0
fi

# Get list of files in uploads directory
UPLOADS_DIR="./uploads"
if [ ! -d "$UPLOADS_DIR" ]; then
    echo -e "${RED}Warning: Uploads directory not found at $UPLOADS_DIR${NC}"
    mkdir -p "$UPLOADS_DIR"
    echo -e "${GREEN}Created uploads directory${NC}"
fi

echo -e "${YELLOW}Checking each UUID against files in uploads directory...${NC}"

# Temporary file for new logs
TEMP_LOG=$(mktemp)

# Keep track of UUIDs that were removed from logs
REMOVED_UUIDS=""

# Process each UUID
for uuid in $UUIDS; do
    # Check if any file with this UUID exists in uploads
    if ! ls "$UPLOADS_DIR"/${uuid}* >/dev/null 2>&1; then
        echo -e "${YELLOW}UUID $uuid has no corresponding file in uploads directory${NC}"
        REMOVED_UUIDS="$REMOVED_UUIDS $uuid"
    fi
done

if [ -z "$REMOVED_UUIDS" ]; then
    echo -e "${GREEN}All UUIDs in logs have corresponding files. No cleanup needed.${NC}"
    rm "$TEMP_LOG"
    exit 0
fi

echo -e "${YELLOW}Cleaning log entries for missing files...${NC}"

# Filter out lines containing removed UUIDs
for uuid in $REMOVED_UUIDS; do
    grep -v "$uuid" "$APP_LOG" > "$TEMP_LOG"
    mv "$TEMP_LOG" "$APP_LOG"
    echo -e "${GREEN}Removed log entries for UUID $uuid${NC}"
done

echo -e "${GREEN}Log cleanup completed successfully${NC}"

# Clean backup temp file
if [ -f "$TEMP_LOG" ]; then
    rm "$TEMP_LOG"
fi

exit 0
