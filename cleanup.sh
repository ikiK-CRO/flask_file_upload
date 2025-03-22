#!/bin/bash

# Cleanup script for the Flask File Upload project
# This script allows manual cleanup of the project data

print_help() {
    echo "Cleanup script for Flask File Upload project"
    echo ""
    echo "Usage: ./cleanup.sh [option]"
    echo ""
    echo "Options:"
    echo "  --all          Clean everything (database, uploads, logs)"
    echo "  --db           Clean only the database (removes database volume)"
    echo "  --files        Clean only uploaded files"
    echo "  --logs         Clean only log files"
    echo "  --restart      Clean everything and restart the application"
    echo "  --full         Complete rebuild with fresh database (removes all data and volumes)"
    echo "  --help         Show this help message"
    echo ""
}

clean_database() {
    echo "Cleaning database..."
    docker-compose down -v
    docker-compose up -d db
    echo "Database has been reset."
}

clean_uploads() {
    echo "Cleaning uploaded files..."
    docker-compose exec web rm -rf /app/uploads/*
    echo "Upload directory cleaned."
}

clean_logs() {
    echo "Cleaning log files..."
    docker-compose exec web bash -c "truncate -s 0 /app/logs/*.log 2>/dev/null || echo 'No log files found'"
    
    # Also clean log entries for deleted files
    if [ -f ./clean_logs.sh ]; then
        echo "Cleaning log entries for missing files..."
        ./clean_logs.sh
    fi
    
    echo "Log files cleaned."
}

clean_all() {
    echo "Cleaning everything..."
    clean_database
    clean_uploads
    clean_logs
    echo "All data has been cleaned."
}

restart_app() {
    echo "Restarting application..."
    docker-compose restart web
    echo "Application restarted."
}

full_cleanup() {
    echo "Performing complete cleanup including database volumes..."
    docker-compose down -v
    echo "Removing database volume..."
    docker volume rm flask_file_upload_postgres_data 2>/dev/null || echo "Volume already removed or not found"
    echo "Rebuilding containers from scratch..."
    docker-compose build --no-cache
    echo "Starting with completely clean state..."
    docker-compose up -d
    echo "Complete cleanup finished - application started with fresh database"
}

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    print_help
    exit 0
fi

# Parse arguments
case "$1" in
    --all)
        clean_all
        ;;
    --db)
        clean_database
        ;;
    --files)
        clean_uploads
        ;;
    --logs)
        clean_logs
        ;;
    --restart)
        clean_all
        restart_app
        ;;
    --full)
        full_cleanup
        ;;
    --help)
        print_help
        ;;
    *)
        echo "Unknown option: $1"
        print_help
        exit 1
        ;;
esac

exit 0
