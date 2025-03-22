.PHONY: test test-flask test-react test-docker test-encryption clean start stop clean restart clean-restart clean-logs help full-cleanup

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
	docker-compose up -d

# Stop the application
stop:
	docker-compose down

# Clean everything - database volume, uploads, logs
clean:
	docker-compose down -v
	@echo "Removed database volume"
	@echo "The next start will be fresh with clean data"

# Restart with clean state
clean-restart: clean start
	@echo "Project restarted with clean state"

# Restart the application (keeps data)
restart:
	docker-compose restart

# Clean log entries for missing files
clean-logs:
	@echo "Cleaning log entries for missing files..."
	./clean_logs.sh

# Complete cleanup - removes volumes, rebuilds containers and starts clean
full-cleanup:
	@echo "Performing complete cleanup including database volumes..."
	docker-compose down -v
	docker volume rm flask_file_upload_postgres_data 2>/dev/null || echo "Volume already removed"
	@echo "Rebuilding containers from scratch..."
	docker-compose build --no-cache
	@echo "Starting with completely clean state..."
	docker-compose up -d
	@echo "Complete cleanup finished - application started with fresh database"

# Help command
help:
	@echo "Available commands:"
	@echo "  make start         - Start the application"
	@echo "  make stop          - Stop the application"
	@echo "  make restart       - Restart the application (keeps data)"
	@echo "  make clean         - Stop and clean all data (DB, uploads, logs)"
	@echo "  make clean-restart - Clean all data and restart"
	@echo "  make clean-logs    - Clean log entries for missing files"
	@echo "  make full-cleanup  - Complete rebuild with fresh database (removes all data)"