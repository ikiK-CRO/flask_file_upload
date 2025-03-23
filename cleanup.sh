#!/bin/bash
# Script to clean up the system for a fresh start

# Parse command-line arguments
CLEAN_DB=false
CLEAN_FILES=false
CLEAN_LOGS=false
CLEAN_ALL=false
FULL_CLEANUP=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Clean up the system for a fresh start"
    echo
    echo "Options:"
    echo "  --db        Clean database records"
    echo "  --files     Clean uploaded files"
    echo "  --logs      Clean log files"
    echo "  --all       Clean database, files, and logs (default if no option provided)"
    echo "  --full      Complete cleanup including volumes (requires Docker)"
    echo "  --help      Display this help message"
    echo
    echo "If no option is provided, --all is assumed"
}

# If no arguments, assume clean all
if [ $# -eq 0 ]; then
    CLEAN_ALL=true
fi

# Parse arguments
while [ "$1" != "" ]; do
    case $1 in
        --db )          CLEAN_DB=true
                        ;;
        --files )       CLEAN_FILES=true
                        ;;
        --logs )        CLEAN_LOGS=true
                        ;;
        --all )         CLEAN_ALL=true
                        ;;
        --full )        FULL_CLEANUP=true
                        ;;
        --help )        usage
                        exit
                        ;;
        * )             usage
                        exit 1
    esac
    shift
done

# If --all is specified, set all flags
if [ "$CLEAN_ALL" = true ]; then
    CLEAN_DB=true
    CLEAN_FILES=true
    CLEAN_LOGS=true
fi

# If --full is specified, we'll do a complete rebuild
if [ "$FULL_CLEANUP" = true ]; then
    echo "========================================="
    echo "  PERFORMING COMPLETE SYSTEM REBUILD"
    echo "========================================="
    echo "This will stop Docker, remove volumes, and rebuild everything"
    echo "Press CTRL+C within 5 seconds to cancel"
    sleep 5
    
    # Stop containers
    echo "Stopping Docker containers..."
    docker-compose down
    
    # Remove the database volume
    echo "Removing database volume..."
    docker volume rm flask_file_upload_postgres_data
    
    # Rebuild containers from scratch
    echo "Rebuilding containers with no cache..."
    docker-compose build --no-cache
    
    # Start with a fresh state
    echo "Starting containers with a fresh state..."
    docker-compose up -d
    
    echo "Complete rebuild finished! System should now be in a fresh state."
    exit 0
fi

# Directory paths
UPLOAD_DIR="./uploads"
LOG_DIR="./logs"

# Clean database
if [ "$CLEAN_DB" = true ]; then
    echo "========================================="
    echo "  CLEANING DATABASE RECORDS"
    echo "========================================="
    
    # Set environment variable to indicate cleaning just the DB
    export ENABLE_STARTUP_CLEANUP=true
    export CLEANUP_STRATEGY=db
    
    # Trigger cleanup via a minimal Flask script
    python3 -c "
import os
os.environ['ENABLE_STARTUP_CLEANUP'] = 'true'
os.environ['CLEANUP_STRATEGY'] = 'db'
from app import app, cleanup_on_startup
with app.app_context():
    cleanup_on_startup()
print('Database cleanup completed')
"
    echo "Database cleanup complete"
fi

# Clean uploaded files
if [ "$CLEAN_FILES" = true ]; then
    echo "========================================="
    echo "  CLEANING UPLOADED FILES"
    echo "========================================="
    
    # Check if uploads directory exists
    if [ ! -d "$UPLOAD_DIR" ]; then
        mkdir -p "$UPLOAD_DIR"
        echo "Created uploads directory."
    else
        # Remove all files in the uploads directory
        rm -f "${UPLOAD_DIR}"/*
        echo "All files in uploads directory have been removed."
    fi
fi

# Clean logs
if [ "$CLEAN_LOGS" = true ]; then
    echo "========================================="
    echo "  CLEANING LOG FILES"
    echo "========================================="
    
    # Check if logs directory exists
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        echo "Created logs directory."
    else
        # For each log file, truncate it to just a header
        for logfile in "${LOG_DIR}"/*.log; do
            if [ -f "$logfile" ]; then
                echo "--- Log reset at $(date) ---" > "$logfile"
                echo "Reset log file: $(basename "$logfile")"
            fi
        done
        
        # Run log cleaning script to clean up log entries for non-existent files
        if [ -f "./clean_logs.sh" ]; then
            echo "Running specialized log cleaning script..."
            bash ./clean_logs.sh
        fi
    fi
fi

echo "========================================="
echo "  CLEANUP COMPLETE"
echo "========================================="
echo "The system has been cleaned according to your specifications."
echo "It's recommended to restart the application for a fresh start."

exit 0 