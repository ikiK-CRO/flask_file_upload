.PHONY: test test-flask test-react test-docker test-encryption clean clean-logs clean-files clean-db clean-restart full-cleanup start stop restart help

# Run all tests locally
test: test-flask test-react test-encryption

# Run Flask tests
test-flask:
	@echo "Running Flask tests..."
	python -m pytest tests/ -v

# Run React tests
test-react:
	@echo "Running React tests..."
	cd react-src && npm test -- --watchAll=false

# Run encryption tests
test-encryption:
	@echo "Running encryption tests..."
	python -m pytest tests/test_encryption.py -v

# Run tests in Docker
test-docker:
	@echo "Running all tests in Docker..."
	docker-compose -f docker-compose.test.yml up --build

# Start the application
start:
	@echo "Starting the application..."
	docker-compose up -d

# Stop the application
stop:
	@echo "Stopping the application..."
	docker-compose down

# Basic cleanup (for test files, etc.)
clean:
	@echo "Cleaning up test files..."
	docker-compose -f docker-compose.test.yml down
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 

# Clean log entries
clean-logs:
	@echo "Cleaning log entries for missing files..."
	chmod +x clean_logs.sh
	./clean_logs.sh

# Clean uploaded files
clean-files:
	@echo "Cleaning uploaded files..."
	chmod +x cleanup.sh
	./cleanup.sh --files

# Clean database
clean-db:
	@echo "Cleaning database records..."
	chmod +x cleanup.sh
	./cleanup.sh --db

# Clean all and restart the application
clean-restart:
	@echo "Cleaning all data and restarting the application..."
	chmod +x cleanup.sh
	./cleanup.sh --all
	docker-compose restart

# Full cleanup with volume reset and complete rebuild
full-cleanup:
	@echo "Performing complete system rebuild..."
	chmod +x cleanup.sh
	./cleanup.sh --full

# Restart the application
restart:
	@echo "Restarting the application..."
	docker-compose restart

# Show help
help:
	@echo "Available commands:"
	@echo "  make start         - Start the application using docker-compose up -d"
	@echo "  make stop          - Stop the application using docker-compose down"
	@echo "  make restart       - Restart the application using docker-compose restart"
	@echo "  make clean         - Clean up test files and caches"
	@echo "  make clean-logs    - Clean log entries for files that no longer exist"
	@echo "  make clean-files   - Clean all uploaded files"
	@echo "  make clean-db      - Clean database records"
	@echo "  make clean-restart - Clean all data and restart the application"
	@echo "  make full-cleanup  - Perform complete system rebuild (stops, removes volumes, rebuilds, restarts)"
	@echo "  make test          - Run all tests locally"
	@echo "  make test-docker   - Run all tests in Docker" 