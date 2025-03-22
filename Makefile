.PHONY: test test-flask test-react test-docker test-encryption clean

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

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose -f docker-compose.test.yml down
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 