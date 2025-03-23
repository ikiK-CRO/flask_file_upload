import os
import uuid
import re
import logging
import glob
import shutil
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

# Configuration for cleanup on startup/restart
ENABLE_STARTUP_CLEANUP = os.environ.get('ENABLE_STARTUP_CLEANUP', 'true').lower() == 'true'
CLEANUP_STRATEGY = os.environ.get('CLEANUP_STRATEGY', 'all')  # Options: all, files, db, logs

# Function to clean up on application startup
def cleanup_on_startup():
    """Performs cleanup based on environment settings"""
    if not ENABLE_STARTUP_CLEANUP:
        app.logger.info("Startup cleanup disabled via environment variable")
        return
    
    app.logger.info(f"Starting cleanup process with strategy: {CLEANUP_STRATEGY}")
    
    # Create required directories
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Clean database records
    if CLEANUP_STRATEGY in ['all', 'db']:
        try:
            with app.app_context():
                # Ensure database is initialized
                db.create_all()
                # Count records before deletion
                record_count = UploadedFile.query.count()
                if record_count > 0:
                    app.logger.info(f"Cleaning {record_count} records from database")
                    UploadedFile.query.delete()
                    db.session.commit()
                else:
                    app.logger.info("No database records to clean")
        except Exception as e:
            app.logger.error(f"Error cleaning database records: {str(e)}")
            try:
                # Rollback in case of error
                db.session.rollback()
            except:
                app.logger.error("Error rolling back session after database cleanup failure")
    
    # Clean uploaded files
    if CLEANUP_STRATEGY in ['all', 'files']:
        try:
            # First approach: Use glob to find all files
            import glob
            file_paths = glob.glob(os.path.join(uploads_dir, '*'))
            files_removed = 0
            
            for file_path in file_paths:
                try:
                    os.remove(file_path)
                    files_removed += 1
                except Exception as e:
                    app.logger.error(f"Error removing file {file_path}: {str(e)}")
            
            # If glob didn't find files or failed, try system commands as fallback
            if files_removed == 0:
                app.logger.info("Using alternative cleanup method for uploads directory")
                try:
                    # Alternative approach with system command
                    if os.name == 'nt':  # Windows
                        os.system(f'del /Q /F "{uploads_dir}\\*"')
                    else:  # Unix/Linux/Mac
                        os.system(f'rm -f {uploads_dir}/*')
                    app.logger.info("Alternative file cleanup completed")
                except Exception as e:
                    app.logger.error(f"Error in alternative file cleanup: {str(e)}")
            else:
                app.logger.info(f"Removed {files_removed} files from uploads directory")
        except Exception as e:
            app.logger.error(f"Error cleaning upload files: {str(e)}")
    
    # Clean logs
    if CLEANUP_STRATEGY in ['all', 'logs']:
        try:
            # Truncate log files instead of deleting them
            # This preserves the file handlers but clears content
            log_files = glob.glob(os.path.join(logs_dir, '*.log'))
            
            for log_file in log_files:
                try:
                    # Open file in write mode to truncate content
                    with open(log_file, 'w') as f:
                        f.write(f"--- Log reset at {datetime.datetime.now()} ---\n")
                    app.logger.info(f"Reset log file: {os.path.basename(log_file)}")
                except Exception as e:
                    app.logger.error(f"Error resetting log file {log_file}: {str(e)}")
        except Exception as e:
            app.logger.error(f"Error cleaning logs: {str(e)}")
    
    app.logger.info("Cleanup process completed")

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

# Call cleanup function at startup
if __name__ == '__main__':
    # Call cleanup function on startup when run directly
    with app.app_context():
        cleanup_on_startup()
        
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
else:  # When imported by WSGI server
    with app.app_context():
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

@app.route('/', methods=['GET', 'POST'], defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    app.logger.info(f"Root route called with method: {request.method}, path: {path}")
    
    # Handle some specific paths
    if path == 'favicon.ico':
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')
    
    # For API requests, handle them separately
    if path.startswith('api/'):
        return jsonify({"success": False, "message": "API endpoint not found"}), 404
        
    # List of known frontend routes
    known_frontend_routes = ['', 'logs', 'upload', 'files', 'admin']
    
    # Check if this is a frontend route we want to handle
    path_parts = path.split('/')
    first_part = path_parts[0] if path_parts else ''
    
    # For GET requests to known frontend routes, serve the React app
    if request.method == 'GET' and (not path or first_part in known_frontend_routes):
        app.logger.info("Serving React app")
        return render_template('minimal_react.html')
    
    # For paths that don't match any known pattern, return 404
    if request.method == 'GET' and first_part not in known_frontend_routes:
        app.logger.warning(f"Unknown route: {path}")
        return jsonify({"success": False, "message": "Page not found"}), 404
    
    # For POST requests to the root (likely a file upload from a non-React client)
    if request.method == 'POST':
        app.logger.info("Handling root POST request (likely file upload)")
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file part"}), 400
        # Handle file upload here

@app.route('/react')
def serve_react():
    """Legacy endpoint for backward compatibility"""
    app.logger.info("React route accessed, redirecting to root")
    return redirect(url_for('index'))

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
        # Update download count
        file_record.download_count += 1
        try:
            db.session.commit()
            app.logger.info(f"API: Download count updated: {file_uuid} - New count: {file_record.download_count}")
        except Exception as e:
            app.logger.error(f"API: Error updating download count: {str(e)} - UUID: {file_uuid}")
        
        # Return the direct download URL with HTTPS always forced
        scheme = request.scheme
        # Force HTTPS only on Heroku
        if 'herokuapp.com' in request.host:
            scheme = 'https'
        host = request.host
        download_url = f"{scheme}://{host}/api/download/{file_uuid}?authenticated=true"
        app.logger.info(f"API: Password verified, returning download URL: {download_url}")
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': file_record.file_name
        })
    else:
        app.logger.warning(f"API: Incorrect password attempt for file: {file_uuid}")
        return jsonify({'success': False, 'message': _("Incorrect password!")}), 403

@app.route('/api/download/<file_uuid>', methods=['GET', 'OPTIONS'])
def download_file_direct(file_uuid):
    app.logger.info(f"Direct download attempt for file: {file_uuid}")
    
    # Ensure we're only serving over HTTPS in production
    if request.headers.get('X-Forwarded-Proto') == 'http' and 'herokuapp.com' in request.host:
        https_url = url_for('download_file_direct', file_uuid=file_uuid, _external=True).replace('http://', 'https://')
        return redirect(https_url, code=301)
        
    # Add CORS headers for preflight requests
    if request.method == 'OPTIONS':
        return '', 200
    
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
    
    # User must have authenticated first
    authenticated = request.args.get('authenticated') == 'true'
    app.logger.info(f"Authentication parameter: {request.args.get('authenticated')} for file: {file_uuid}")
    
    if not authenticated:
        app.logger.warning(f"Download attempt without authentication: {file_uuid}")
        return jsonify({"success": False, "message": "Authentication required"}), 401
    
    try:
        # Get the file path and create the response
        file_path = file_record.file_path  # This uses the decryption getter
        original_filename = file_record.file_name  # This uses the decryption getter
        
        app.logger.info(f"Looking for file at path: {file_path}")
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            # Try to check if an encrypted version exists
            encrypted_file_path = file_path + '.encrypted'
            app.logger.info(f"File not found at {file_path}, checking for encrypted version at {encrypted_file_path}")
            
            if os.path.exists(encrypted_file_path):
                app.logger.info(f"Found encrypted version of file: {encrypted_file_path}")
                file_path = encrypted_file_path
            else:
                app.logger.error(f"File record exists but file not found on disk: {file_uuid} - {original_filename}")
                
                # Try one more location - check both by ID pattern
                alt_pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_*")
                alt_files = glob.glob(alt_pattern)
                
                if alt_files:
                    alt_file = alt_files[0]  # Take the first match
                    app.logger.info(f"Found alternative file location by UUID pattern: {alt_file}")
                    file_path = alt_file
                else:
                    # Clean up the database record if configured to do so
                    if ENABLE_STARTUP_CLEANUP and CLEANUP_STRATEGY in ['all', 'db']:
                        try:
                            db.session.delete(file_record)
                            db.session.commit()
                            app.logger.info(f"Removed database record for missing file: {file_uuid}")
                        except Exception as e:
                            app.logger.error(f"Error removing database record for missing file: {str(e)}")
                            db.session.rollback()
                    return jsonify({"success": False, "message": "File not found on disk"}), 404
        
        # For encrypted files, we need to decrypt them before sending
        is_encrypted = file_path.endswith('.encrypted') or file_record.is_encrypted
        temp_decrypted_path = None
        
        try:
            if is_encrypted:
                app.logger.info(f"Decrypting file for download: {file_path}")
                # Import decrypt_file from crypto_utils
                from crypto_utils import decrypt_file
                # Create a temporary file path for decrypted content
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_decrypted_path = os.path.join(temp_dir, f"decrypted_{os.path.basename(file_path).replace('.encrypted', '')}")
                
                # Decrypt the file to the temporary location
                decrypt_file(file_path, temp_decrypted_path)
                
                if os.path.exists(temp_decrypted_path):
                    app.logger.info(f"Successfully decrypted file to: {temp_decrypted_path}")
                    # Use the decrypted file for the response
                    directory, filename = os.path.split(temp_decrypted_path)
                else:
                    app.logger.error(f"Failed to decrypt file, decrypted file not found: {temp_decrypted_path}")
                    # Fall back to the original encrypted file
                    directory, filename = os.path.split(file_path)
                    app.logger.warning(f"Falling back to sending encrypted file directly: {file_path}")
            else:
                # For non-encrypted files, just use the original path
                directory, filename = os.path.split(file_path)
                
            app.logger.info(f"Sending file: directory={directory}, filename={filename}, original_name={original_filename}")
            
            # Register a callback to remove the temporary file after the response is sent
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                @after_this_request
                def remove_temp_file(response):
                    try:
                        if os.path.exists(temp_decrypted_path):
                            os.remove(temp_decrypted_path)
                            app.logger.info(f"Removed temporary decrypted file: {temp_decrypted_path}")
                    except Exception as e:
                        app.logger.error(f"Error removing temporary file: {str(e)}")
                    return response

            # Create a response using send_from_directory
            response = send_from_directory(
                directory, 
                filename, 
                as_attachment=True, 
                download_name=original_filename
            )
            
            # Set appropriate headers
            response.headers["Content-Disposition"] = f"attachment; filename=\"{original_filename}\"; filename*=UTF-8''{quote(original_filename)}"
            response.headers["Content-Type"] = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
            # Log successful download
            app.logger.info(f"File download successful: {file_uuid} - {original_filename}")
            
            return response
            
        except Exception as e:
            app.logger.error(f"Error sending file: {str(e)} - UUID: {file_uuid}, Path: {file_path}")
            
            # Clean up temp file if it exists
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                try:
                    os.remove(temp_decrypted_path)
                    app.logger.info(f"Cleaned up temporary file after error: {temp_decrypted_path}")
                except Exception as cleanup_error:
                    app.logger.error(f"Error cleaning up temporary file: {str(cleanup_error)}")
                    
            return jsonify({"success": False, "message": f"Error sending file: {str(e)}"}), 500
            
    except Exception as e:
        app.logger.error(f"Error in file download process: {str(e)} - UUID: {file_uuid}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    try:
        # Get all file records from the database
        files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).all()
        
        # Convert file objects to dictionaries, filtering out files that don't exist on disk
        file_list = []
        for file in files:
            file_path = file.file_path
            
            # Check both with and without .encrypted extension
            file_exists = os.path.exists(file_path) or os.path.exists(file_path + '.encrypted')
            
            # Include the file in list if it exists in either form
            if file_exists:
                file_list.append({
                    'id': file.id,
                    'file_name': file.file_name,
                    'upload_date': file.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'download_count': file.download_count
                })
            else:
                app.logger.warning(f"File record exists but file not found on disk: {file.id} - {file.file_name}")
        
        # Get upload logs
        upload_logs = []
        download_logs = []
        
        # Read app.log for upload and download logs, filtering by file existence
        log_path = os.path.join(os.getcwd(), 'logs', 'app.log')
        try:
            # Extract UUIDs from log lines for filtering
            uuid_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
            
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                with open(log_path, 'r') as log_file:
                    for line in log_file:
                        if "File metadata saved to database:" in line:
                            # Add all upload logs regardless of file existence
                            upload_logs.append(line.strip())
                            
                        elif "File download successful:" in line:
                            # Add all download logs regardless of file existence
                            download_logs.append(line.strip())
            else:
                app.logger.warning(f"Log file not found or empty: {log_path}")
        except Exception as e:
            app.logger.error(f"Error reading log file: {str(e)}")
            
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
                
                # Store the encrypted path directly (without decryption attempt)
                actual_file_path = encrypted_file_path
                
                # Delete the original unencrypted file if encryption was successful
                if encrypted_file_path != temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    app.logger.info(f"Removed original unencrypted file: {temp_file_path}")
            except Exception as e:
                app.logger.error(f"Encryption error: {str(e)}")
                # If encryption fails, continue with the unencrypted file
                encrypted_file_path = temp_file_path
                actual_file_path = temp_file_path
                app.logger.warning(f"Continuing with unencrypted file: {encrypted_file_path}")
            
            # Generate password hash
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            try:
                # Store file information in database
                is_encrypted = encrypted_file_path != temp_file_path
                new_file = UploadedFile(
                    id=file_uuid,
                    file_name=original_filename,  # This will be encrypted by the setter
                    file_path=actual_file_path,  # This will be encrypted by the setter
                    password=password,  # Raw password for demonstration purposes
                    password_hash=password_hash,
                    is_encrypted=is_encrypted
                )
                db.session.add(new_file)
                db.session.commit()
                
                # Log file upload success with the specific format needed for the logs page
                app.logger.info(f"File metadata saved to database: {file_uuid} - {original_filename}")
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
def check_files():
    """Admin endpoint to check and repair orphaned files"""
    # This would ideally have authentication, but it's simplified for this example
    
    if request.headers.get('X-Admin-Key') != app.config.get('ADMIN_KEY', 'admin-key'):
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
