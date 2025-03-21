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

### Monitoring and Diagnostics
- **Python logging**: Structured activity logging
- **RotatingFileHandler**: Log file rotation for optimal space usage

## Table of Contents

1. [Technical Documentation](#technical-documentation)
   - [System Architecture](#system-architecture)
   - [Security Implementations](#security-implementations)
   - [Logging Implementation](#logging-implementation)
   - [Database Schema](#database-schema)
   - [API Endpoints](#api-endpoints)
   - [Error Handling](#error-handling)
   - [Technical Requirements](#technical-requirements)
   
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

The application implements the following functional units:

- Secure file uploading with drag-and-drop support
- Password-protected file downloading
- Structured logging of all activities
- Activity log viewing with tabbed interface
- Internationalization with language switching

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

#### Additional Security Measures

1. **Unique Identifiers**:
   - Using UUIDs for file identification
   - Prevention of predictable URLs

2. **Resource Cleanup**:
   - Automatic deletion of uploaded files in case of database errors
   - Prevention of orphaned files in the system

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
| file_name | String(255) | Original filename |
| file_path | String(255) | File path in the system |
| password_hash | String(255) | Password hash value |
| password | String(255) | Password (for demonstration) |
| upload_date | DateTime | Upload date and time |
| download_count | Integer | Number of downloads |

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
    - File sending to client

#### `/logs` (GET)
- **GET**: Displays activity logs
  - Actions:
    - Retrieving file list from database
    - Reading and parsing log files
    - Displaying table with data and logs

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

4. **System Errors**:
   - Database error handling
   - File system error handling
   - Detailed error logging

### Technical Requirements

- Python 3.6+
- Flask
- Flask-SQLAlchemy
- Flask-Bcrypt
- Werkzeug
- SQLite (for demonstration) or PostgreSQL (for production)

## User Documentation

### Installation and Setup

#### Prerequisites
- Python 3.6 or newer
- pip (Python package manager)

#### Installation Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd flask_file_upload
   ```

2. **Install Required Packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Optional: Set environment variables
   export FLASK_ENV=development # for development
   # or
   export FLASK_ENV=production # for production
   
   # For using PostgreSQL database
   export DATABASE_URL=postgresql://username:password@localhost/database_name
   ```

4. **Start the Application**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`

#### Docker Installation

1. **Build Docker Image**
   ```bash
   docker build -t flask_file_upload .
   ```

2. **Run Docker Container**
   ```bash
   docker run -p 5000:5000 flask_file_upload
   ```

### Using the Application

#### Uploading a File

1. Open the application's home page (`/`)
2. Click "Choose file" and select a file to upload
   - Supported formats: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip
   - Maximum size: 10MB
3. Enter a password that will be required for downloading the file
4. Click "Upload"
5. After successful upload, you'll receive a unique URL to access the file

#### Downloading a File

1. Open the file download link (`/get-file/<file_uuid>`)
2. Enter the password that was set during upload
3. Click "Download"
4. The file will be downloaded to your computer

#### Viewing Activity Logs

1. Open the logs page (`/logs`)
2. View the table with data about uploaded files
3. Use tabs to view upload and download logs
4. Use the search field to filter logs

### Security Recommendations

1. **Use strong passwords** to protect your files.
2. **Don't share download URLs** through insecure channels.
3. **Regularly delete unnecessary files** from the system.
4. **Check files for viruses** before upload and after download.
5. **Don't upload sensitive data** without additional encryption.

### Troubleshooting

#### File Upload Error

- **Problem**: "An error occurred while saving the file."
- **Solution**: 
  - Check if the application has sufficient permissions to write to the `uploads` directory.
  - Check if the file size is below 10MB.
  - Check if the file type is allowed.

#### File Download Error

- **Problem**: "Incorrect password!"
- **Solution**: 
  - Check if you've entered the correct password.
  - Be careful about uppercase/lowercase letters in the password.

#### Log Access Error

- **Problem**: "Could not load logs"
- **Solution**: 
  - Check if the `logs` directory exists and if the application has sufficient permissions to read and write.
  - If necessary, manually create the `logs` directory in the application's root directory.

#### "File not found" Error

- **Problem**: "File not found" when trying to download
- **Solution**: 
  - Check if you've entered the correct download URL.
  - If the file has been deleted, it will no longer be available for download.

#### Language Selection Not Working

- **Problem**: "Language isn't changing when I click on the language button."
- **Solution**: 
  - Check if cookies are enabled in your browser.
  - Try clearing your browser cache and cookies.
  - Ensure the page is fully reloaded after language selection.

## Frontend Architecture

The frontend is built using React with the following component structure:

### Components
- **App**: Main application component and routing
- **Navbar**: Navigation bar with language selection
- **FileUpload**: Drag-and-drop file upload functionality
- **FileDownload**: Password-protected file download
- **ActivityLog**: Tabbed interface for viewing upload/download logs

### State Management
- Component-level state using React hooks (useState, useEffect)
- Context API for global state (language settings)

### Internationalization
- i18next integration for multilingual support
- Language detection from browser settings and cookies
- Language switching with persistent selection

### API Integration
- Axios for HTTP requests to the Flask backend
- JSON-based data exchange
- Form data handling for file uploads

### Styling
- Bootstrap 5 for responsive layout
- Custom CSS for theming and component styling
- Responsive design for mobile and desktop views 