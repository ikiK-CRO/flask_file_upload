# Secure File Sharing System Documentation

## Programming Languages and Technologies Used

### Programming Languages
- **Python**: Main backend language for server logic and data processing
- **JavaScript (ES6+)**: Frontend React application, AJAX for API communication
- **JSX**: React component templating
- **HTML**: Web page structure
- **CSS**: Web page styling

### Web Technologies
- **Flask**: Python web framework for backend API development
- **React**: Frontend JavaScript library for building user interfaces
- **React Router**: Routing and navigation for React applications
- **Axios**: HTTP client for API requests
- **React Dropzone**: Drag-and-drop file upload functionality
- **i18next**: Internationalization framework for React
- **SQLAlchemy**: ORM (Object-Relational Mapping) for database operations
- **Flask-Bcrypt**: Password hashing and validation
- **Flask-Babel**: Internationalization and localization support
- **Bootstrap**: Frontend framework for responsive design
- **Jest**: JavaScript testing framework for React components
- **pytest**: Python testing framework for backend code
- **CORS Support**: Cross-Origin Resource Sharing for API access
- **Docker Compose**: Multi-container environment definition
- **GitHub Actions**: CI/CD pipeline automation
- **Makefile**: Build automation and test orchestration
- **Cryptography**: Python library for secure encryption/decryption

### Databases
- **PostgreSQL**: Primary database used across all environments (local Docker, development, and production)

### Infrastructure and Deployment
- **Docker**: Application containerization for easy setup and deployment
- **npm**: Package manager for JavaScript dependencies
- **Heroku**: Cloud platform for application hosting (LIVE DEMO: https://uploadfile-47843913ee68.herokuapp.com/)

### Security and Validation
- **Werkzeug**: Utility library for security functions
- **Regular Expressions**: User input validation and sanitization
- **MIME Validation**: Verification of actual uploaded file types
- **Fernet Encryption**: Symmetric encryption for files and sensitive data
- **Password-based Key Derivation**: PBKDF2 for secure key generation

### Monitoring and Diagnostics
- **Python logging**: Structured activity logging
- **RotatingFileHandler**: Log file rotation for optimal space usage

## Table of Contents

1. [Technical Documentation](#technical-documentation)
   - [System Architecture](#system-architecture)
   - [Security Implementations](#security-implementations)
   - [Logging Implementation](#logging-implementation)
   - [Multilingual Support](#multilingual-support)
   - [Database Schema](#database-schema)
   - [API Endpoints](#api-endpoints)
   - [Error Handling](#error-handling)
   - [Technical Requirements](#technical-requirements)
   - [Testing Framework](#testing-framework)
   
2. [User Documentation](#user-documentation)
   - [Installation and Setup](#installation-and-setup)
   - [Using the Application](#using-the-application)
   - [Security Recommendations](#security-recommendations)
   - [Troubleshooting](#troubleshooting)

## Technical Documentation

### System Architecture

The secure file sharing system is implemented as a modern web application with a React frontend and Flask backend API:

- **Backend**: Flask-based RESTful API handling data operations and file management
- **Frontend**: React SPA (Single Page Application) providing a responsive and interactive user interface
- **Communication**: JSON-based API communication between frontend and backend

The main components of the system are:

1. **Backend API**: Flask application handling HTTP requests and API responses
2. **Frontend SPA**: React application for user interface and interaction
3. **Database**: PostgreSQL for storing metadata about uploaded files
4. **File System**: Local file system for storing uploaded files
5. **Logging System**: Structured logging of user and system activities
6. **Encryption Layer**: Fernet-based encryption for files and database fields

The application implements the following functional units:

- Secure file uploading with drag-and-drop support
- Password-protected file downloading
- Structured logging of all activities
- Activity log viewing with tabbed interface
- Internationalization with language switching
- End-to-end encryption for file contents and metadata

### Security Implementations

#### Input Validation and Sanitization

1. **File Type Validation**:
   - File extension checking against a whitelist of allowed types
   - Allowed formats: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip
   - Additional MIME type validation

2. **File Size Validation**:
   - File size limit set to 10MB
   - File size verification using `seek()` and `tell()` methods

3. **Filename Sanitization**:
   - Using Werkzeug's `secure_filename` function
   - Additional sanitization with regular expressions to remove potentially dangerous characters
   - UUID prefix to ensure file uniqueness

4. **File Content Validation**:
   - Checking the first 2048 bytes of the file for potentially dangerous content
   - Detection and blocking of script tags

#### Password Protection

1. **Password Hashing**:
   - Using Flask-Bcrypt for secure password hashing
   - Storing hash values in the database

2. **Password Verification During Download**:
   - Secure hash value verification without revealing the original password
   - Protection against brute-force attacks

#### Encryption System

1. **File Encryption**:
   - Fernet symmetric encryption for all uploaded files
   - Automatic encryption on upload and decryption on download
   - Secure key management with fallback mechanism

2. **Database Field Encryption**:
   - Transparent encryption of sensitive fields (filename, file path)
   - Encrypted at rest to protect from database breaches
   - Automatic decryption when fields are accessed

3. **Key Management**:
   - Master encryption key stored securely in environment variables
   - Fallback key generation with explicit warnings
   - Proper key format validation and correction

4. **Password-based Encryption**:
   - PBKDF2-based key derivation for password-protected operations
   - Salt generation and storage for secure key derivation
   - Protection against rainbow table attacks

#### Additional Security Measures

1. **Unique Identifiers**:
   - Using UUIDs for file identification
   - Prevention of predictable URLs

2. **Resource Cleanup**:
   - Automatic deletion of uploaded files in case of database errors
   - Prevention of orphaned files in the system
   
3. **Error Resilience**:
   - Graceful handling of encryption/decryption errors
   - Fallback mechanisms to ensure system availability
   - Detailed error logging for security monitoring

#### Token-Based Authentication

1. **JWT Authentication**:
   - JSON Web Tokens for secure API access
   - Role-based tokens (admin vs. regular access)
   - Short-lived access tokens with refresh capability
   - Secure token validation and verification

2. **Download Tokens**:
   - Single-use tokens for secure file downloads
   - Password verification embedded in token claims
   - Short expiration time (10 minutes) for download tokens
   - File-specific tokens that can't be reused for other files

3. **Token Management**:
   - Secure generation of cryptographically signed tokens
   - Token refresh mechanism for maintaining sessions
   - Protection against token reuse and replay attacks

### Logging Implementation

The logging system is implemented using Python's `logging` module with the goal of detailed activity tracking, diagnostics, and security monitoring.

#### Logging Structure

1. **Multiple Log Records**:
   - General application logs (`app.log`)
   - Security logs (`security.log`) for sensitive operations

2. **Log Rotation**:
   - Log file size limit set to 10MB
   - Maximum of 5 backup files to prevent excessive space usage

3. **Contextual Information in Logs**:
   - Timestamp
   - Log level (INFO, WARNING, ERROR)
   - Client IP address
   - Client user agent
   - Detailed activity messages

#### Logged Activities

1. **Basic Request Information**:
   - HTTP method
   - Path
   - Referrer

2. **Upload Activities**:
   - Upload attempts
   - Failed uploads with reasons
   - Successful uploads with file details

3. **Download Activities**:
   - Download page access
   - Failed authentication attempts
   - Successful downloads

4. **System Errors**:
   - Database interaction errors
   - File system operation errors
   - Unexpected exceptions

5. **Security Events**:
   - Invalid file types
   - Validation bypass attempts
   - Failed authentication attempts
   - Encryption/decryption events and errors

#### Log Viewing

1. Open the logs page (`/logs`)
2. View the table with data about uploaded files
3. Use tabs to view upload and download logs
4. Use the search field to filter logs

### Multilingual Support

The application implements internationalization and localization using Flask-Babel to provide a multilingual user interface:

#### Supported Languages
- **English (en)**: Default language
- **Croatian (hr)**: Complete translation of all user interface elements

#### Implementation Details
1. **Flask-Babel Integration**:
   - Configuration in `babel.cfg` for extracting translatable strings
   - Language detection from browser preferences and user selection
   - Persistence of language preference using browser cookies

2. **Translation Files**:
   - Structured as `translations/<language_code>/LC_MESSAGES/messages.po` 
   - Compiled `.mo` files for efficient runtime translation
   - Full coverage of all user-facing strings

3. **Language Switching**:
   - Language selector in the top-right corner of every page
   - Immediate language change without page refresh
   - Visual indication of currently selected language

4. **Fallback Mechanism**:
   - Falls back to default language (English) when translation is unavailable
   - Robust handling of translation edge cases

#### Translation Workflow
1. String extraction via `pybabel extract -F babel.cfg -o messages.pot .`
2. Translation initialization via `pybabel init -i messages.pot -d translations -l <language_code>`
3. Translation file updates via `pybabel update -i messages.pot -d translations`
4. Compilation via `pybabel compile -d translations`

### Database Schema

SQLAlchemy ORM with the `UploadedFile` model is used for storing file metadata:

| Field | Type | Description |
|-------|-----|------|
| id | String(36) | Primary key, UUID |
| _file_name | Text | Encrypted original filename |
| _file_path | Text | Encrypted file path in the system |
| password_hash | String(255) | Password hash value |
| password | String(255) | Password (for demonstration) |
| upload_date | DateTime | Upload date and time |
| download_count | Integer | Number of downloads |
| is_encrypted | Boolean | Flag indicating if the file is encrypted |
| encryption_salt | LargeBinary | Salt for encryption (if used) |

### API Endpoints

#### `/` (GET, POST)
- **GET**: Displays the home page with upload form
- **POST**: Processes file upload
  - Form parameters:
    - `file`: File to upload
    - `password`: Password to protect the file
  - Actions:
    - File validation
    - File storage
    - File encryption
    - Database record creation
    - Generation and return of download URL

#### `/get-file/<file_uuid>` (GET, POST)
- **GET**: Displays password entry page for download
- **POST**: Processes download request
  - Form parameters:
    - `password`: Password to access the file
  - Actions:
    - Password validation
    - Download count update
    - File decryption
    - File sending to client

#### `/api/download/<file_uuid>` (GET, OPTIONS)
- **GET**: Direct file download after authentication
  - Query parameters:
    - `authenticated`: Flag indicating successful authentication
  - Actions:
    - Authentication verification
    - File decryption if needed
    - Secure file delivery

#### `/api/upload` (GET, POST, OPTIONS)
- **GET**: Returns information about upload requirements
- **POST**: API endpoint for file upload
  - Form parameters:
    - `file`: File to upload
    - `password`: Password to protect the file
  - Actions:
    - File validation
    - File storage
    - File encryption
    - Database record creation
    - Return of JSON with file details and download URL

#### `/logs` (GET)
- **GET**: Displays activity logs
  - Actions:
    - Retrieving file list from database
    - Reading and parsing log files
    - Displaying table with data and logs

#### `/api/admin/check-files` (GET)
- **GET**: Admin endpoint to check and repair file system and database synchronization
  - Required Headers (choose one):
    - `X-Admin-Key`: Authentication key for admin access (default: "admin-key")
    - `Authorization`: Bearer token from admin token endpoint
  - Actions:
    - Checks for orphaned files (files in uploads directory but not in database)
    - Checks for missing files (records in database but files not on disk)
    - Automatically repairs orphaned files by creating database entries
    - Updates file paths in database if encrypted versions are found
    - Returns JSON with details about orphaned, missing, and repaired files

#### `/api/auth/admin-token` (POST)
- **POST**: Generates admin access and refresh tokens for API access
  - Required Headers:
    - `X-Admin-Key`: Authentication key for admin access (default: "admin-key")
  - Returns:
    - Access token (short-lived JWT for API operations)
    - Refresh token (long-lived JWT for obtaining new access tokens)
    - Token type and expiration information

#### `/api/auth/refresh` (POST)
- **POST**: Refreshes access tokens using a refresh token
  - Required Headers:
    - `Authorization`: Bearer token containing the refresh token
  - Returns:
    - New access token
    - Token type and expiration information

### Error Handling

The application has comprehensive error handling implemented:

1. **HTTP Errors**:
   - Custom pages for 404 errors (page not found)
   - Custom pages for 500 errors (internal server error)

2. **Validation Errors**:
   - Clear messages for invalid file types
   - Messages for file size exceeding limits
   - Messages for invalid filenames

3. **Authentication Errors**:
   - Messages for incorrect passwords
   - Messages for missing passwords

4. **Encryption Errors**:
   - Graceful handling of encryption failures
   - Fallback to unencrypted storage when necessary
   - Transparent error recovery during decryption

5. **System Errors**:
   - Database error handling
   - File system error handling
   - Detailed error logging

### Technical Requirements

- Python 3.6+
- Flask
- Flask-SQLAlchemy
- Flask-Bcrypt
- Werkzeug
- Cryptography
- PostgreSQL (primary database used across all environments)

## Testing Framework

The application includes a comprehensive testing framework to ensure reliability, security, and functionality of both frontend and backend components.

### Testing Technologies

- **Backend Testing**: 
  - pytest: Python testing framework
  - Flask Test Client: For testing Flask routes and API endpoints
  - Temporary SQLite database for test isolation
  
- **Frontend Testing**:
  - Jest: JavaScript testing framework
  - React Testing Library: For testing React components
  - Mock implementations for API calls and internationalization

- **Integration Testing**:
  - Docker Compose configuration for testing in isolated containers
  - End-to-end test workflow via GitHub Actions

### Test Structure

#### Backend Tests

1. **Basic Route Tests** (`tests/test_basic.py`):
   - Tests for the index route
   - Tests for the logs API route
   - Tests for 404 error handling

2. **File Operation Tests** (`tests/test_file_operations.py`):
   - Upload file functionality
   - Validation of file uploads without files
   - Validation of file uploads without passwords
   
3. **Encryption Tests** (`tests/test_encryption.py`):
   - Database field encryption and decryption
   - File encryption and decryption
   - Password-based encryption
   - Key management and validation

4. **Test Fixtures** (`tests/conftest.py`):
   - Flask application setup with test configuration
   - Test client creation
   - Database initialization and teardown

#### Frontend Tests

1. **Component Tests**:
   - File upload component tests
   - Navbar component tests
   - App component tests
   
2. **Mock Implementations**:
   - Mock i18n for internationalization testing
   - Mock API fetch calls for simulating server responses

### Running Tests

Different test commands are available via the Makefile to simplify test execution:

1. **Run All Tests**:
   ```bash
   make test
   ```

2. **Run Flask Backend Tests Only**:
   ```bash
   make test-flask
   ```

3. **Run React Frontend Tests Only**:
   ```bash
   make test-react
   ```

4. **Run Tests in Docker**:
   ```bash
   make test-docker
   ```

5. **Clean Test Environment**:
   ```bash
   make clean
   ```

### Test Coverage

The tests cover several critical aspects of the application:

1. **Security Tests**:
   - Password handling and protection
   - File validation and sanitization
   - Error handling for invalid inputs
   - Encryption and decryption functionality

2. **Functionality Tests**:
   - File upload and download workflows
   - API endpoint responses
   - Component rendering and interactions

3. **User Interface Tests**:
   - Component rendering
   - User interactions (click events, form submissions)
   - Internationalization

### Adding New Tests

When extending the application with new features, follow these guidelines for adding tests:

1. **Backend Tests**:
   - Add new test functions to the appropriate test file or create a new test file
   - Use the existing fixtures from conftest.py
   - Follow the naming convention `test_<feature_name>`

2. **Frontend Tests**:
   - Create new test files alongside component files
   - Use the naming convention `<ComponentName>.test.js`
   - Use React Testing Library's render and interaction utilities

## User Documentation

### Installation and Setup

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- Git for cloning the repository

#### Setup with Docker Compose (Recommended)

Docker Compose provides the easiest way to set up and run the entire application stack with the correct configuration:

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd flask_file_upload
   ```

2. **Configure Environment Variables (Optional)**
   
   The project includes default configuration in the `docker-compose.yml` file, but you can customize it by creating a `.env` file:
   ```bash
   # Example .env file contents
   MASTER_ENCRYPTION_KEY=your_secure_base64_key  # Optional: For production use
   ENABLE_STARTUP_CLEANUP=true                  # Enable cleanup on startup
   CLEANUP_STRATEGY=all                         # Options: all, db, files, logs or combinations
   ```

   Available cleanup strategies:
   - `all`: Clean everything (database, uploaded files, and logs)
   - `db`: Clean only database records
   - `files`: Clean only uploaded files
   - `logs`: Clean only log files
   - Comma-separated combinations: `db,logs` to clean database and logs
   
3. **Build and Start the Application**
   ```bash
   docker-compose up -d
   ```
   
   This command will:
   - Build the application container
   - Set up a PostgreSQL database container
   - Configure networking between containers
   - Mount necessary volumes
   - Start the application on http://localhost:5001

4. **Verify the Application is Running**
   
   Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

5. **View Logs (Optional)**
   ```bash
   docker-compose logs -f
   ```

6. **Stop the Application**
   ```bash
   docker-compose down
   ```

#### Cleaning Up the Project

The project includes several methods to ensure it starts with a clean state on restart:

1. **Automatic Cleanup on Startup**
   
   By default, the application is configured to clean database records, uploaded files, and logs on every restart. This behavior is controlled by environment variables in `docker-compose.yml`:
   ```yaml
   ENABLE_STARTUP_CLEANUP=true
   CLEANUP_STRATEGY=all
   ```

2. **Manual Cleanup Using Make Commands**
   
   The project includes several Make commands for managing the application state:
   ```bash
   # Start the application
   make start
   
   # Stop the application
   make stop
   
   # Clean everything and reset to initial state
   make clean
   
   # Clean everything and restart the application
   make clean-restart
   
   # Restart without cleaning (keeps existing data)
   make restart
   ```

3. **Using the Cleanup Script**
   
   For more fine-grained control, use the included cleanup script:
   ```bash
   # Show help
   ./cleanup.sh
   
   # Clean everything (database, uploads, logs)
   ./cleanup.sh --all
   
   # Clean only database
   ./cleanup.sh --db
   
   # Clean only uploaded files
   ./cleanup.sh --files
   
   # Clean only log files
   ./cleanup.sh --logs
   
   # Clean everything and restart
   ./cleanup.sh --restart
   ```

4. **Complete System Rebuild**

   If you need a completely fresh start with no persistence of old data:
   ```bash
   # Complete rebuild - removes all volumes, rebuilds containers, starts fresh
   make full-cleanup
   ```
   
   This command:
   - Stops all containers
   - Removes the database volume
   - Rebuilds all Docker images without cache
   - Starts the system completely fresh
   - Ensures no old data remains anywhere

5. **Cleaning Log Entries for Missing Files**

   If you've deleted files but still see them in the logs page, use the log cleaning script:
   ```bash
   # Using the dedicated script
   ./clean_logs.sh
   
   # Or using make
   make clean-logs
   ```
   
   This will remove log entries for files that no longer exist in the uploads directory.

#### Testing the Application

The application includes automated tests that you can run to verify functionality:

##### Testing with Docker Compose

1. **Run All Tests in Docker Environment**
   ```bash
   docker-compose -f docker-compose.test.yml up --build
   ```
   This will build a test container and run both backend and frontend tests.

2. **Run Only Backend Tests**
   ```bash
   docker-compose exec web python -m pytest tests/
   ```

3. **Run Specific Test Modules**
   ```bash
   docker-compose exec web python -m pytest tests/test_encryption.py -v
   ```

##### Testing Without Docker

If you're using the manual setup:

1. **Install Test Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run All Tests**
   ```bash
   make test
   ```

3. **Run Only Backend Tests**
   ```bash
   make test-flask
   ```

4. **Run Only Frontend Tests**
   ```bash
   make test-react
   ```

The test output will show if all components are functioning correctly. If any tests fail, the error messages can help identify the issue.

### Using the Application

The application will be available at `http://localhost:5000`

## Cleanup Functionality

The application includes comprehensive cleanup functionality to ensure a clean state on every installation and restart:

### Automatic Cleanup

- **Startup Cleanup**: On application startup, the system can automatically clean the database, uploads folder, and logs based on environment variables.
- **Environment Configuration**:
  - `ENABLE_STARTUP_CLEANUP`: Set to `true` to enable cleanup on startup (default: `true`)
  - `CLEANUP_STRATEGY`: Set to `all`, `files`, `db`, or `logs` to control what gets cleaned (default: `all`)

### Manual Cleanup

Several commands are available for cleaning the system:

```bash
# Clean log entries for missing files
make clean-logs

# Clean all uploaded files
make clean-files

# Clean database records
make clean-db

# Clean all and restart the application
make clean-restart

# Full cleanup with volume reset and complete rebuild
make full-cleanup
```

### Cleanup Scripts

- `clean_logs.sh`: Removes log entries for files that no longer exist in the uploads directory
- `cleanup.sh`: Main cleanup script with options for targeted cleaning:
  ```bash
  ./cleanup.sh --db     # Clean database only
  ./cleanup.sh --files  # Clean uploads only
  ./cleanup.sh --logs   # Clean logs only
  ./cleanup.sh --all    # Clean everything (default)
  ./cleanup.sh --full   # Complete system rebuild
  ```

### Complete Rebuild

For a fresh start with a completely clean state:

```bash
make full-cleanup
```

This command:
1. Stops all containers
2. Removes the database volume
3. Rebuilds containers from scratch
4. Starts the application with a clean state