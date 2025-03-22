import os
import uuid
import re
import logging
from logging.handlers import RotatingFileHandler
import datetime
import functools
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, jsonify, Response, after_this_request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import mimetypes
from flask_babel import Babel, _
from urllib.parse import quote
from auth_utils import TokenManager, token_required, admin_token_required, download_token_required

from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Content-Disposition", "Authorization", "X-Requested-With"],
    "expose_headers": ["Content-Disposition", "Content-Type", "Content-Length", "X-Content-Transfer-Id"],
    "supports_credentials": True,
    "max_age": 86400
}})  # Enhanced CORS for all routes
app.secret_key = 'your-secret-key'  # Change this in production

# Initialize our TokenManager
token_manager = TokenManager(app)

# Add JWT_SECRET_KEY to app config if not already set
app.config.setdefault('JWT_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'))
app.config.setdefault('ADMIN_KEY', os.environ.get('ADMIN_KEY', 'admin-key'))

# Force HTTPS middleware - only on production
@app.before_request
def force_https():
    # Only force HTTPS on Heroku or other production environments using X-Forwarded-Proto
    # Skip this in Docker or local environments
    if request.headers.get('X-Forwarded-Proto') == 'http' and not request.host.startswith('127.0.0.1') and not request.host.startswith('localhost') and 'herokuapp.com' in request.host:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# Add middleware to set security headers for all responses
@app.after_request
def add_security_headers(response):
    # Only add these headers in production, not in Docker or local dev
    if not request.host.startswith('127.0.0.1') and not request.host.startswith('localhost') and 'herokuapp.com' in request.host:
        response.headers['Content-Security-Policy'] = "upgrade-insecure-requests"
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set log level
    app.logger.setLevel(logging.INFO)
    
    # Create a filter to add IP and user agent to log records
    class RequestFilter(logging.Filter):
        def filter(self, record):
            # Safely check for request context
            from flask import has_request_context
            
            if has_request_context():
                record.ip = request.remote_addr
                record.user_agent = request.user_agent.string if hasattr(request, 'user_agent') else 'N/A'
            else:
                record.ip = 'N/A'
                record.user_agent = 'N/A'
            return True
    
    # Log formatting
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(ip)s - %(user_agent)s - %(message)s'
    )
    
    # File handler for general logs (rotating to keep file size manageable)
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.addFilter(RequestFilter())
    file_handler.setLevel(logging.INFO)
    
    # Security-specific file handler
    security_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setFormatter(log_formatter)
    security_handler.setLevel(logging.WARNING)
    security_handler.addFilter(RequestFilter())
    
    # Add handlers to app.logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(security_handler)
    
    # If in development, also log to console
    if os.environ.get('FLASK_ENV') == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.addFilter(RequestFilter())
        app.logger.addHandler(console_handler)

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

# Initialize Flask-Babel
babel = Babel(app)

# Define the default locale
@babel.localeselector
def get_locale():
    # Make sure we prioritize the cookie language
    lang = request.cookies.get('lang')
    if lang in ['hr', 'en']:
        return lang
    return request.accept_languages.best_match(['hr', 'en'], default='hr')

# Modify your database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Heroku PostgreSQL URL format (if needed)
    database_url = re.sub(r'^postgres:', 'postgresql:', database_url)
    
    # Check if psycopg2 is available
    try:
        import psycopg2
        app.logger.info("PostgreSQL support available, using PostgreSQL database")
    except ImportError:
        app.logger.warning("PostgreSQL support not available, falling back to SQLite")
        # Use SQLite for fallback
        database_path = os.path.join(os.getcwd(), 'fileupload.db')
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
        database_url = f'sqlite:///{database_path}'
else:
    # Use SQLite for demonstration
    database_path = os.path.join(os.getcwd(), 'fileupload.db')
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
    database_url = f'sqlite:///{database_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define upload folder – using an absolute path within the container.
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
# Ensure the uploads folder exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.logger.info(f"Uploads directory created at {UPLOAD_FOLDER}")
except Exception as e:
    app.logger.error(f"Error creating uploads directory: {e}")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize logging
setup_logging()

# Clean up function for fresh start
def cleanup_on_startup():
    """
    Cleans up database records, uploaded files, and logs on application startup
    based on environment variables.
    """
    # Check if cleanup is enabled via environment variable (default to disabled)
    cleanup_enabled = os.environ.get('ENABLE_STARTUP_CLEANUP', 'false').lower() == 'true'
    
    if not cleanup_enabled:
        app.logger.info("Startup cleanup is disabled. Set ENABLE_STARTUP_CLEANUP=true to enable.")
        return
    
    app.logger.info("Starting application cleanup process...")
    
    # Determine cleanup strategy from environment variable
    # Options: all, db, files, logs, or comma-separated combinations
    cleanup_strategy = os.environ.get('CLEANUP_STRATEGY', 'all').lower()
    strategies = [s.strip() for s in cleanup_strategy.split(',')]
    
    # Clean database if specified
    if 'all' in strategies or 'db' in strategies:
        try:
            # Ensure database tables exist before cleaning
            with app.app_context():
                db.create_all()
                app.logger.info("Ensured database tables exist")
                
                # Count existing records before deletion
                file_count = UploadedFile.query.count()
                
                # Delete all records
                UploadedFile.query.delete()
                db.session.commit()
                
                # Verify deletion
                remaining = UploadedFile.query.count()
                app.logger.info(f"Cleaned up {file_count} records from database, {remaining} remaining")
                
                if remaining > 0:
                    app.logger.warning(f"Some records could not be deleted ({remaining} remaining)")
                    # Try more aggressive approach
                    try:
                        db.session.execute('TRUNCATE TABLE uploaded_file RESTART IDENTITY CASCADE')
                        db.session.commit()
                        app.logger.info("Used TRUNCATE as fallback to clean database")
                    except Exception as truncate_error:
                        app.logger.error(f"Error during TRUNCATE: {str(truncate_error)}")
                        # If TRUNCATE fails, try with raw DELETE
                        try:
                            db.session.execute('DELETE FROM uploaded_file')
                            db.session.commit()
                            app.logger.info("Used raw DELETE as fallback to clean database")
                        except Exception as delete_error:
                            app.logger.error(f"Error during raw DELETE: {str(delete_error)}")
        except Exception as e:
            app.logger.error(f"Error cleaning database: {str(e)}")
    
    # Clean uploaded files if specified
    if 'all' in strategies or 'files' in strategies:
        try:
            # Ensure uploads directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # First approach: Use glob to find all files
            import glob
            file_paths = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
            files_removed = 0
            
            for file_path in file_paths:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        files_removed += 1
                except Exception as e:
                    app.logger.error(f"Error removing file {file_path}: {str(e)}")
            
            app.logger.info(f"Cleaned up {files_removed}/{len(file_paths)} files from uploads directory")
            
            # Second approach: Check if files remain and use additional methods
            remaining_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
            if remaining_files:
                app.logger.warning(f"Found {len(remaining_files)} files still in uploads directory")
                # Try alternative approach with direct system command
                try:
                    import subprocess
                    # Use rm -f to force removal without confirmation
                    result = subprocess.run(['rm', '-f', os.path.join(app.config['UPLOAD_FOLDER'], '*')], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        app.logger.info("Used system command to clean uploads directory")
                    else:
                        app.logger.error(f"System command failed: {result.stderr}")
                except Exception as cmd_error:
                    app.logger.error(f"Error using system command: {str(cmd_error)}")
        except Exception as e:
            app.logger.error(f"Error cleaning uploads directory: {str(e)}")
    
    # Clean logs if specified
    if 'all' in strategies or 'logs' in strategies:
        try:
            logs_dir = os.path.join(os.getcwd(), 'logs')
            log_files = ['app.log', 'security.log']
            
            for log_file in log_files:
                log_path = os.path.join(logs_dir, log_file)
                if os.path.exists(log_path):
                    # Option 1: Delete log files
                    # os.remove(log_path)
                    
                    # Option 2: Empty log files but keep them (better)
                    open(log_path, 'w').close()
            
            app.logger.info(f"Cleaned up log files in {logs_dir}")
        except Exception as e:
            app.logger.error(f"Error cleaning log files: {str(e)}")

    # Add an explicit log cleanup to prevent showing old file records in logs page
    try:
        # Reset upload and download logs in memory
        app.config.setdefault('upload_logs', [])
        app.config.setdefault('download_logs', [])
        app.logger.info("Reset in-memory log references")
    except Exception as e:
        app.logger.error(f"Error resetting in-memory logs: {str(e)}")

    app.logger.info("Application cleanup process completed")

# Run cleanup on startup
cleanup_on_startup()

# Define allowed file extensions and max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

db = SQLAlchemy(app)

# Define the database model
class UploadedFile(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID4 as string
    _file_name = db.Column('file_name_encrypted', db.Text, nullable=False)  # Encrypted filename
    _file_path = db.Column('file_path_encrypted', db.Text, nullable=False)  # Encrypted filepath
    password_hash = db.Column(db.String(255), nullable=False)  # Store hashed password
    password = db.Column(db.String(255), nullable=False)  # This might be the missing column
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)
    is_encrypted = db.Column(db.Boolean, default=True)  # Flag to indicate if file is encrypted
    encryption_salt = db.Column(db.LargeBinary, nullable=True)  # Salt for encryption (if used)
    
    @property
    def file_name(self):
        """Get decrypted file name"""
        try:
            from crypto_utils import decrypt_db_field
            if self.is_encrypted and self._file_name:
                decrypted = decrypt_db_field(self._file_name)
                if decrypted:
                    return decrypted
                app.logger.warning(f"Failed to decrypt file_name, using raw value for: {self.id}")
            return self._file_name
        except Exception as e:
            app.logger.error(f"Error in file_name getter: {str(e)} for file: {self.id}")
            return self._file_name or "unknown_file"
        
    @file_name.setter
    def file_name(self, value):
        """Set encrypted file name"""
        try:
            from crypto_utils import encrypt_db_field
            if value and self.is_encrypted:
                encrypted = encrypt_db_field(value)
                if encrypted:
                    self._file_name = encrypted
                else:
                    app.logger.warning(f"Failed to encrypt file_name, using raw value for: {value}")
                    self._file_name = value
            else:
                self._file_name = value
        except Exception as e:
            app.logger.error(f"Error in file_name setter: {str(e)}")
            self._file_name = value
    
    @property
    def file_path(self):
        """Get decrypted file path"""
        try:
            from crypto_utils import decrypt_db_field
            if self.is_encrypted and self._file_path:
                decrypted = decrypt_db_field(self._file_path)
                if decrypted:
                    return decrypted
                app.logger.warning(f"Failed to decrypt file_path, using raw value for: {self.id}")
            return self._file_path
        except Exception as e:
            app.logger.error(f"Error in file_path getter: {str(e)} for file: {self.id}")
            return self._file_path
        
    @file_path.setter
    def file_path(self, value):
        """Set encrypted file path"""
        try:
            from crypto_utils import encrypt_db_field
            if value and self.is_encrypted:
                encrypted = encrypt_db_field(value)
                if encrypted:
                    self._file_path = encrypted
                else:
                    app.logger.warning(f"Failed to encrypt file_path, using raw value for: {value}")
                    self._file_path = value
            else:
                self._file_path = value
        except Exception as e:
            app.logger.error(f"Error in file_path setter: {str(e)}")
            self._file_path = value

# Create database tables (if they don't exist)
with app.app_context():
    try:
        # Only create tables if they don't exist, don't drop tables
        # db.drop_all()  # Removed to prevent data loss
        db.create_all()
        app.logger.info("Database tables created successfully (if they didn't exist)")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")
        # If we're using PostgreSQL and it fails, try to fall back to SQLite
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
            try:
                app.logger.warning("Attempting to fall back to SQLite database")
                # Switch to SQLite
                database_path = os.path.join(os.getcwd(), 'fileupload.db')
                app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
                # Recreate the engine with the new connection string
                db.engine.dispose()
                db.get_engine(app, bind=None)
                # Try again with SQLite
                # db.drop_all()  # Removed to prevent data loss
                db.create_all()
                app.logger.info("Database tables created successfully with SQLite fallback")
            except Exception as inner_e:
                app.logger.error(f"Error creating SQLite fallback database: {inner_e}")

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to validate file MIME type
def validate_mime_type(file):
    # Read the first 2048 bytes to determine MIME type
    file_head = file.read(2048)
    file.seek(0)  # Reset file pointer
    
    # Get MIME type from the file
    mime_type = mimetypes.guess_type(file.filename)[0]
    
    # List of allowed MIME types
    allowed_mime_types = [
        'text/plain', 'application/pdf', 'image/png', 'image/jpeg', 'image/gif',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/zip'
    ]
    
    if mime_type not in allowed_mime_types:
        return False
    
    # Additional check for potential malicious content
    if b'<script' in file_head.lower():
        return False
        
    return True

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content

@app.before_request
def log_request_info():
    # Log basic request information
    app.logger.info(
        f"Request: {request.method} {request.path} - "
        f"Referrer: {request.referrer}"
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle API POST requests for file upload
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file part"})
        # Rest of your file upload logic...
    else:
        # Serve React app for GET requests
        return render_template('minimal_react.html')

@app.route('/get-file/<file_uuid>', methods=['GET', 'POST', 'OPTIONS'])
def get_file(file_uuid):
    # Add support for preflight OPTIONS requests
    if request.method == 'OPTIONS':
        resp = jsonify({'success': True})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Content-Disposition, X-Requested-With'
        return resp
        
    app.logger.info(f"File download page accessed: {file_uuid}")
    
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        app.logger.warning(f"File not found: {file_uuid}")
        return jsonify({'success': False, 'message': _("File not found")}), 404

    if request.method == 'POST':
        entered_password = request.form.get('password')
        
        if not entered_password:
            app.logger.warning(f"Download attempt without password: {file_uuid}")
            return jsonify({'success': False, 'message': _("Password is required")}), 400
        
        if bcrypt.check_password_hash(file_record.password_hash, entered_password):
            # Update download count
            file_record.download_count += 1
            try:
                db.session.commit()
                app.logger.info(f"Download count updated: {file_uuid} - New count: {file_record.download_count}")
            except Exception as e:
                app.logger.error(f"Error updating download count: {str(e)} - UUID: {file_uuid}")
                return jsonify({'success': False, 'message': _("Error updating download count")}), 500
            
            # Send the file as a download
            directory, stored_file = os.path.split(file_record.file_path)
            app.logger.info(f"File download successful: {file_uuid} - {file_record.file_name}")
            
            try:
                response = send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
                
                # Add headers for cross-browser compatibility, especially for Chrome
                response.headers["Content-Disposition"] = f"attachment; filename=\"{file_record.file_name}\"; filename*=UTF-8''{quote(file_record.file_name)}"
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                
                # Enhanced cross-origin headers for Chrome on HTTPS
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Content-Disposition, X-Requested-With"
                response.headers["Access-Control-Expose-Headers"] = "Content-Disposition, Content-Length, X-Content-Transfer-Id"
                response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
                
                # Only add these security headers in production
                if 'herokuapp.com' in request.host:
                    response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
                    response.headers["Feature-Policy"] = "downloads *"
                
                # Ensure temp file is deleted after sending
                @after_this_request
                def cleanup_temp_file(response):
                    app.logger.info(f"Cleaning up temp file: {directory}/{stored_file}")
                    if os.path.exists(os.path.join(directory, stored_file)):
                        try:
                            os.remove(os.path.join(directory, stored_file))
                            app.logger.info(f"Temp file removed: {os.path.join(directory, stored_file)}")
                        except Exception as e:
                            app.logger.error(f"Error removing temp file: {e}")
                    return response
                
                return response
            except Exception as e:
                app.logger.error(f"File send error: {str(e)} - Path: {file_record.file_path}")
                return jsonify({'success': False, 'message': _("Error downloading file")}), 500
        else:
            app.logger.warning(f"Incorrect password attempt for file: {file_uuid}")
            return jsonify({'success': False, 'message': _("Incorrect password!")}), 403
    
    # For GET requests, redirect to the main React app with the file UUID as a parameter
    scheme = request.scheme
    # Force HTTPS only on Heroku
    if 'herokuapp.com' in request.host and request.headers.get('X-Forwarded-Proto') == 'https':
        scheme = 'https'
    host = request.host
    return redirect(f'{scheme}://{host}/?file={file_uuid}')

@app.route('/logs')
def view_logs():
    """Redirect to the React app's logs page."""
    return redirect(url_for('serve_react') + '#/logs')

@app.errorhandler(404)
def page_not_found(e):
    app.logger.warning(f"404 error: {request.path}")
    return jsonify({'success': False, 'message': _("Page not found")}), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return jsonify({'success': False, 'message': _("Internal server error")}), 500

@app.route('/set_language/<lang>')
def set_language(lang):
    response = redirect(request.referrer or url_for('serve_react'))
    response.set_cookie('lang', lang)
    return response

@app.route('/react')
def serve_react():
    return render_template('minimal_react.html')

# API endpoints for React
@app.route('/api/upload', methods=['GET', 'POST', 'OPTIONS'])
def api_upload_endpoint():
    """API endpoint for file uploads"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    # For GET, return instructions
    if request.method == 'GET':
    return jsonify({
            "success": True,
            "message": "Upload files via POST with multipart/form-data",
            "required_fields": ["file", "password"]
        })
        
    # For POST, handle file upload
    return api_upload_file()

@app.route('/api/files/<file_uuid>', methods=['POST'])
def api_get_file(file_uuid):
    app.logger.info(f"API file access attempt: {file_uuid}")
    
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        app.logger.warning(f"API: File not found: {file_uuid}")
        return jsonify({'success': False, 'message': _("File not found")}), 404

    # Try to get password from JSON body first, then form data
    entered_password = None
    if request.is_json:
        app.logger.info(f"API: Processing JSON request for file: {file_uuid}")
        entered_password = request.json.get('password')
    else:
        app.logger.info(f"API: Processing form request for file: {file_uuid}")
        entered_password = request.form.get('password')
    
    if not entered_password:
        app.logger.warning(f"API: Download attempt without password: {file_uuid}")
        return jsonify({'success': False, 'message': _("Password is required")}), 400
    
    app.logger.info(f"API: Verifying password for file: {file_uuid}")
    
    if bcrypt.check_password_hash(file_record.password_hash, entered_password):
        # Do not update download count here as it will be updated during the actual download
        app.logger.info(f"API: Password verified for file: {file_uuid}")
        
        # Generate a download token with password verification
        download_token = token_manager.generate_download_token(
            file_uuid=file_uuid, 
            password_verified=True,
            file_type=mimetypes.guess_type(file_record.file_name)[0]
        )
        
        # Return the direct download URL with the token
        scheme = request.scheme
        # Force HTTPS only on Heroku
        if 'herokuapp.com' in request.host:
            scheme = 'https'
        host = request.host
        download_url = f"{scheme}://{host}/api/download/{file_uuid}?token={download_token}"
        app.logger.info(f"API: Password verified, returning download URL with token: {download_url}")
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': file_record.file_name,
            'download_token': download_token
        })
    else:
        app.logger.warning(f"API: Incorrect password attempt for file: {file_uuid}")
        return jsonify({'success': False, 'message': _("Incorrect password!")}), 403

@app.route('/api/download/<file_uuid>', methods=['GET', 'OPTIONS'])
@download_token_required(token_manager)
def download_file_direct(file_uuid):
    app.logger.info(f"Direct download attempt for file: {file_uuid}")
    
    # Token is already verified by the decorator
    # The decorator also ensures the file_uuid in the token matches the URL
    
    # Get file from database
    file_record = UploadedFile.query.get(file_uuid)
    if not file_record:
        app.logger.warning(f"Download attempt for non-existent file: {file_uuid}")
        
        # Check if file exists in uploads directory despite not being in database
        import glob
        matching_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_*"))
        if matching_files:
            app.logger.warning(f"Found orphaned file for {file_uuid} not in database: {matching_files}")
        
        return jsonify({"success": False, "message": "File not found in database"}), 404
    
    try:
        # Get the file path and create the response
        file_path = file_record.file_path  # This uses the decryption getter
        original_filename = file_record.file_name  # This uses the decryption getter
        
        # Check if file_path is None or empty
        if not file_path:
            app.logger.error(f"File path is None or empty for UUID: {file_uuid}")
            return jsonify({"success": False, "message": "File path is missing or corrupted"}), 404
            
        app.logger.info(f"Preparing to serve file: {original_filename} from path: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            app.logger.error(f"File not found on disk: {file_path} for UUID: {file_uuid}")
            
            # Check if there's an alternative file that matches
            import glob
            matching_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_*"))
            
            if matching_files:
                app.logger.warning(f"Found alternative file: {matching_files[0]} for {file_uuid}")
                file_path = matching_files[0]
            else:
                return jsonify({"success": False, "message": "File not available on disk"}), 404
        
        # Determine if file needs decryption
        serve_path = None
        temp_path = None
        
        if file_record.is_encrypted:
            app.logger.info(f"File is encrypted, decrypting: {file_uuid}")
            # Create a temporary file to hold the decrypted content
            import tempfile
            from crypto_utils import decrypt_file
            
            # Create temp file with original extension
            _, file_ext = os.path.splitext(original_filename)
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_path = temp_file.name
            app.logger.info(f"Created temp file for decryption: {temp_path}")
            
            # Decrypt the file to the temporary location
            decrypt_result = decrypt_file(file_path, temp_path)
            if decrypt_result:
                app.logger.info(f"File decrypted successfully to: {decrypt_result}")
                # Set this as the path to serve
                serve_path = decrypt_result
            else:
                app.logger.error(f"File decryption failed for: {file_uuid}")
                return jsonify({"success": False, "message": "Decryption failed"}), 500
        else:
            # No decryption needed
            app.logger.info(f"File is not encrypted, serving directly: {file_uuid}")
            serve_path = file_path
        
        # Update download count
        file_record.download_count += 1
        db.session.commit()
        app.logger.info(f"Download count updated for {file_uuid}, new count: {file_record.download_count}")
        
        # Log the download
        app.logger.info(f"File downloaded: {original_filename} (UUID: {file_uuid})")
        
        # Clear the logs cache to ensure fresh data on next log retrieval
        app.config.pop('upload_logs', None)
        app.config.pop('download_logs', None)
        
        # If we have a temporary file, ensure it's deleted after sending
        if temp_path:
            @after_this_request
            def cleanup_temp_file(response):
                app.logger.info(f"Cleaning up temp file: {temp_path}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        app.logger.info(f"Temp file removed: {temp_path}")
                    except Exception as e:
                        app.logger.error(f"Error removing temp file: {e}")
        return response
        
        # Send the file with original filename
        return send_from_directory(
            directory=os.path.dirname(serve_path),
            path=os.path.basename(serve_path),
            as_attachment=True,
            download_name=original_filename,
            mimetype=mimetypes.guess_type(original_filename)[0]
        )
        
    except Exception as e:
        app.logger.error(f"Error during file download: {str(e)} for UUID: {file_uuid}")
        return jsonify({"success": False, "message": f"Error processing file download: {str(e)}"}), 500

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    try:
        # Force a refresh of the cached logs
        app.config.pop('upload_logs', None)
        app.config.pop('download_logs', None)
        
        files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).all()
        
        # Filter files to only include those that exist on disk
        valid_files = []
        for file in files:
            try:
                file_path = file.file_path
                # Check both regular file path and encrypted file path
                if file_path and (os.path.exists(file_path) or os.path.exists(f"{file_path}.encrypted")):
                    valid_files.append(file)
                else:
                    app.logger.warning(f"File not found on disk for id {file.id}, excluding from logs")
            except Exception as e:
                app.logger.error(f"Error checking file existence: {str(e)}")
        
        # Convert file objects to dictionaries
        file_list = []
        for file in valid_files:
            file_list.append({
                'id': file.id,
                'file_name': file.file_name,
                'upload_date': file.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'download_count': file.download_count
            })
        
        # Get upload logs from our stored cache or log file
        upload_logs = []
        download_logs = []
        
        # Read app.log for upload and download logs
        log_path = os.path.join(os.getcwd(), 'logs', 'app.log')
        try:
            with open(log_path, 'r') as log_file:
                for line in log_file:
                    if "File metadata saved to database:" in line or "File uploaded successfully:" in line:
                        # Include log entries for all valid files
                        for file in valid_files:
                            if file.id in line:
                        upload_logs.append(line.strip())
                                break
                            
                    elif "File downloaded:" in line or "File download successful:" in line or "Download count updated" in line:
                        # Include log entries for all valid files
                        for file in valid_files:
                            if file.id in line:
                        download_logs.append(line.strip())
                                break
        except Exception as e:
            app.logger.error(f"Error reading log file: {str(e)}")
            
        # Cache the logs we just read
        app.config['upload_logs'] = upload_logs
        app.config['download_logs'] = download_logs
            
        return jsonify({
            'success': True,
            'files': file_list,
            'upload_logs': upload_logs,
            'download_logs': download_logs
        })
    except Exception as e:
        app.logger.error(f"Error loading logs: {str(e)}")
        return jsonify({'success': False, 'message': f"Could not load logs: {str(e)}"})

def api_upload_file():
    """Handle file upload from API"""
    # Mostly same logic as upload_file but returns JSON
    if 'file' not in request.files:
        app.logger.warning("Upload attempt with no file part")
        return jsonify({"success": False, "message": _("No file part")})
    
    file = request.files['file']
    if file.filename == '':
        app.logger.warning("Upload attempt with empty filename")
        return jsonify({"success": False, "message": _("No file selected")})
    
    password = request.form.get('password', '')
    if not password:
        app.logger.warning("Upload attempt with no password")
        return jsonify({"success": False, "message": _("No password provided")})
    
    if file and allowed_file(file.filename):
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_CONTENT_LENGTH:
            app.logger.warning(f"Upload attempt with too large file: {file_size} bytes, max is {MAX_CONTENT_LENGTH}")
            return jsonify({
                "success": False, 
                "message": _("File too large, max 10MB allowed")
            })
        
        # Validate MIME type
        if not validate_mime_type(file):
            app.logger.warning(f"Upload attempt with invalid MIME type for file: {file.filename}")
            return jsonify({
                "success": False, 
                "message": _("Invalid file type")
            })
        
        # Create a secure filename
        original_filename = secure_filename(file.filename)
        file_uuid = str(uuid.uuid4())
        
        # Create unique filename with UUID
        secure_filename_with_uuid = f"{file_uuid}_{original_filename}"
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename_with_uuid)
        
        # Save the file temporarily
        try:
            app.logger.info(f"Attempting to save file to {temp_file_path}")
            file.save(temp_file_path)
            app.logger.info(f"File temporarily saved at: {temp_file_path}")
            
            # Verify the file was saved correctly
            if not os.path.exists(temp_file_path):
                app.logger.error(f"Failed to save file at: {temp_file_path}")
                return jsonify({
                    "success": False,
                    "message": _("Failed to save uploaded file")
                })
            
            # Encrypt the file
            app.logger.info(f"Attempting to encrypt file: {temp_file_path}")
            try:
                from crypto_utils import encrypt_file
                encrypted_file_path = encrypt_file(temp_file_path)
                app.logger.info(f"File encrypted: {encrypted_file_path}")
                
                # Delete the original unencrypted file if encryption was successful
                if encrypted_file_path != temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    app.logger.info(f"Removed original unencrypted file: {temp_file_path}")
            except Exception as e:
                app.logger.error(f"Encryption error: {str(e)}")
                # If encryption fails, continue with the unencrypted file
                encrypted_file_path = temp_file_path
                app.logger.warning(f"Continuing with unencrypted file: {encrypted_file_path}")
            
            # Generate password hash
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            try:
                # Store file information in database
                is_encrypted = encrypted_file_path != temp_file_path
                new_file = UploadedFile(
                    id=file_uuid,
                    file_name=original_filename,  # This will be encrypted by the setter
                    file_path=encrypted_file_path,  # This will be encrypted by the setter
                    password=password,  # Raw password for demonstration purposes
                    password_hash=password_hash,
                    is_encrypted=is_encrypted
                )
                db.session.add(new_file)
                db.session.commit()
                
                # Log the successful upload
                app.logger.info(f"File uploaded successfully: {original_filename} (UUID: {file_uuid})")
                
                # Create file URL for download
                file_url = url_for('get_file', file_uuid=file_uuid, _external=True)
                
                return jsonify({
                    "success": True, 
                    "message": _("File uploaded successfully!"),
                    "file_uuid": file_uuid,
                    "file_url": file_url
                })
                
            except Exception as e:
                # If database error, delete the uploaded file to avoid orphaned files
                if os.path.exists(encrypted_file_path):
                    try:
                        os.remove(encrypted_file_path)
                        app.logger.info(f"Removed file after database error: {encrypted_file_path}")
                    except Exception as remove_error:
                        app.logger.error(f"Error removing file: {str(remove_error)}")
                
                app.logger.error(f"Database error during file upload: {str(e)}")
                return jsonify({
                    "success": False, 
                    "message": _("An error occurred while saving the file information.")
                })
                
        except Exception as e:
            app.logger.error(f"File system error during upload: {str(e)}")
            return jsonify({
                "success": False, 
                "message": _("An error occurred while saving the file.")
            })
    
    else:
        # Handle invalid file type
        allowed_extensions = ', '.join(ALLOWED_EXTENSIONS)
        app.logger.warning(f"Upload attempt with invalid file type: {file.filename}")
        return jsonify({
            "success": False, 
            "message": _("Invalid file type. Allowed types: %(types)s", types=allowed_extensions)
        })

@app.route('/api/admin/check-files', methods=['GET'])
@admin_token_required(token_manager)
def check_files():
    """Admin endpoint to check and repair orphaned files"""
    # This is now protected by the admin_token_required decorator
    # The old key-based authentication is kept for backward compatibility
    # Check for the old style authentication (X-Admin-Key header)
    if not hasattr(request, 'token_payload') and request.headers.get('X-Admin-Key') != app.config.get('ADMIN_KEY'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        # Get all files in the uploads directory
        import glob
        all_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*'))
        app.logger.info(f"Found {len(all_files)} files in uploads directory: {app.config['UPLOAD_FOLDER']}")
        
        # Log the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI']
        app.logger.info(f"Using database: {db_path}")
        
        # Get all file UUIDs from the database
        try:
            db_files = UploadedFile.query.all()
            app.logger.info(f"Found {len(db_files)} files in database")
            db_uuids = [f.id for f in db_files]
        except Exception as e:
            app.logger.error(f"Database query error: {str(e)}")
            db_files = []
            db_uuids = []
        
        orphaned_files = []
        missing_files = []
        repaired_files = []
        
        # Check for orphaned files (files in directory but not in database)
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            app.logger.info(f"Checking file: {file_name}")
            
            # Extract UUID from filename
            uuid_match = file_name.split('_')[0] if '_' in file_name else None
            
            if uuid_match and uuid_match not in db_uuids:
                app.logger.info(f"Found orphaned file: {file_path} with UUID: {uuid_match}")
                orphaned_files.append({
                    "file_path": file_path,
                    "uuid": uuid_match
                })
                
                # Try to repair by adding to database
                try:
                    # Extract original filename from the path
                    original_filename = file_name.split('_', 1)[1] if '_' in file_name else file_name
                    
                    # Remove .encrypted extension for display
                    if original_filename.endswith('.encrypted'):
                        display_filename = original_filename[:-10]  # Remove '.encrypted'
                    else:
                        display_filename = original_filename
                        
                    app.logger.info(f"Creating database entry for {uuid_match} with name {display_filename}")
                    
                    # Create a new database entry
                    new_file = UploadedFile(
                        id=uuid_match,
                        file_name=display_filename,
                        file_path=file_path,
                        password="recovered",  # Default password for recovered files
                        password_hash=bcrypt.generate_password_hash("recovered").decode('utf-8'),
                        is_encrypted=file_path.endswith('.encrypted')
                    )
                    db.session.add(new_file)
                    db.session.commit()
                    repaired_files.append(uuid_match)
                    app.logger.info(f"Repaired orphaned file: {file_path}")
                except Exception as e:
                    app.logger.error(f"Failed to repair orphaned file {file_path}: {str(e)}")
        
        # Check for missing files (files in database but not in directory)
        for db_file in db_files:
            if not os.path.exists(db_file.file_path):
                app.logger.warning(f"File in database but not on disk: {db_file.id} - {db_file.file_path}")
                
                # Try to find the file with .encrypted extension if it exists
                encrypted_path = f"{db_file.file_path}.encrypted"
                if os.path.exists(encrypted_path):
                    app.logger.info(f"Found encrypted version of file: {encrypted_path}")
                    # Update the database record
                    db_file.file_path = encrypted_path
                    db_file.is_encrypted = True
                    db.session.commit()
                    app.logger.info(f"Updated file path in database: {db_file.id}")
                else:
                    missing_files.append({
                        "uuid": db_file.id,
                        "file_name": db_file.file_name,
                        "expected_path": db_file.file_path
                    })
        
        return jsonify({
            "success": True,
            "orphaned_files": len(orphaned_files),
            "missing_files": len(missing_files),
            "repaired_files": len(repaired_files),
            "uploads_dir": app.config['UPLOAD_FOLDER'],
            "database_path": db_path,
            "details": {
                "orphaned": orphaned_files,
                "missing": missing_files,
                "repaired": repaired_files
            }
        })
    except Exception as e:
        app.logger.error(f"Error checking files: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# New routes for token management

@app.route('/api/auth/admin-token', methods=['POST'])
def get_admin_token():
    """
    Generate an admin access token for API access
    Requires admin key for authentication
    """
    # Get admin key from request
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key or admin_key != app.config.get('ADMIN_KEY'):
        app.logger.warning(f"Invalid admin key used for token generation")
        return jsonify({"success": False, "message": "Invalid admin key"}), 401
    
    # Generate admin token
    try:
        access_token = token_manager.generate_access_token(admin=True)
        refresh_token = token_manager.generate_refresh_token()
        
        app.logger.info(f"Admin token generated successfully")
        
        return jsonify({
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 1800)
        })
    except Exception as e:
        app.logger.error(f"Error generating admin token: {str(e)}")
        return jsonify({"success": False, "message": f"Error generating token: {str(e)}"}), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """
    Generate a new access token using a refresh token
    """
    # Get refresh token from request
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Refresh token is missing"}), 401
    
    refresh_token = auth_header.split(' ')[1]
    
    # Verify refresh token
    payload = token_manager.verify_token(refresh_token, 'refresh')
    if not payload:
        app.logger.warning(f"Invalid refresh token used")
        return jsonify({"success": False, "message": "Invalid or expired refresh token"}), 401
    
    # Generate new access token
    try:
        # Pass admin claim if it was in the original token
        new_access_token = token_manager.generate_access_token(admin=payload.get('admin', False))
        
        app.logger.info(f"Access token refreshed successfully")
        
        return jsonify({
            "success": True,
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 1800)
        })
    except Exception as e:
        app.logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({"success": False, "message": f"Error refreshing token: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
