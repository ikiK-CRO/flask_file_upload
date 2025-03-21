import os
import uuid
import re
import logging
from logging.handlers import RotatingFileHandler
import datetime
import functools
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import mimetypes
from flask_babel import Babel, _

from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your-secret-key'  # Change this in production

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

# Define allowed file extensions and max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

db = SQLAlchemy(app)

# Define the database model
class UploadedFile(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID4 as string
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Store hashed password
    password = db.Column(db.String(255), nullable=False)  # This might be the missing column
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)

# Create database tables (if they don't exist)
with app.app_context():
    try:
        # Drop all tables and recreate them to ensure schema is up to date
        db.drop_all()
        db.create_all()
        app.logger.info("Database tables dropped and recreated successfully")
    except Exception as e:
        app.logger.error(f"Error recreating database tables: {e}")
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
                db.drop_all()
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

@app.route('/get-file/<file_uuid>', methods=['GET', 'POST'])
def get_file(file_uuid):
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
                return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
            except Exception as e:
                app.logger.error(f"File send error: {str(e)} - Path: {file_record.file_path}")
                return jsonify({'success': False, 'message': _("Error downloading file")}), 500
        else:
            app.logger.warning(f"Incorrect password attempt for file: {file_uuid}")
            return jsonify({'success': False, 'message': _("Incorrect password!")}), 403
    
    # For GET requests, redirect to the main React app with the file UUID as a parameter
    # Since we're now serving React at the root (/), redirect there with the file UUID parameter
    return redirect(f'/?file={file_uuid}')

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
@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    # Mostly same logic as upload_file but returns JSON
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _("No file part in the request")})
            
    uploaded_file = request.files.get('file')
    password = request.form.get('password')
    
    if not uploaded_file or uploaded_file.filename == '':
        return jsonify({'success': False, 'message': _("No file selected")})
        
    if not password:
        return jsonify({'success': False, 'message': _("Password is required")})
    
    app.logger.info(f"API Upload attempt: {uploaded_file.filename}")
        
    if not allowed_file(uploaded_file.filename):
        message = f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        return jsonify({'success': False, 'message': message})
        
    # File Size Validation
    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)
    
    if file_size > MAX_CONTENT_LENGTH:
        message = f"File size exceeds the {MAX_CONTENT_LENGTH // (1024 * 1024)}MB limit!"
        return jsonify({'success': False, 'message': message})
        
    # MIME type validation
    if not validate_mime_type(uploaded_file):
        return jsonify({'success': False, 'message': "Invalid file content or MIME type"})

    # Input Validation and Sanitization
    filename = secure_filename(uploaded_file.filename)
    if filename == '':
        return jsonify({'success': False, 'message': "Invalid file name after sanitization"})
        
    # Additional sanitization
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_{filename}")
    
    try:
        uploaded_file.save(file_path)
        app.logger.info(f"File saved: {file_path} - Size: {file_size/1024/1024:.2f}MB")
    except Exception as e:
        app.logger.error(f"File save error: {str(e)} - Path: {file_path}")
        return jsonify({'success': False, 'message': "Error saving file"})

    # Hash the password
    try:
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    except Exception as e:
        app.logger.error(f"Password hashing error: {str(e)}")
        return jsonify({'success': False, 'message': "Password hashing failed!"})
    
    # Create the new_file instance
    new_file = UploadedFile(
        id=file_uuid,
        file_name=filename,
        file_path=file_path,
        password_hash=password_hash,
        password=password
    )
    
    # Save file metadata in the database
    db.session.add(new_file)
    try:
        db.session.commit()
        app.logger.info(f"File metadata saved to database: {file_uuid} - {filename}")
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        
        # Delete the uploaded file if database operation failed
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                app.logger.info(f"Cleaned up file after database error: {file_path}")
            except Exception as cleanup_error:
                app.logger.error(f"Error cleaning up file: {str(cleanup_error)} - Path: {file_path}")
            
        return jsonify({'success': False, 'message': "An error occurred while saving the file."})

    # Return the download URL to the user
    file_url = url_for('get_file', file_uuid=file_uuid, _external=True)
    return jsonify({
        'success': True, 
        'message': _("File uploaded successfully! You will need the password you provided to access it at: {}").format(file_url),
        'file_url': file_url
    })

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
        
        # Return the direct download URL
        download_url = url_for('download_file_direct', file_uuid=file_uuid, _external=True)
        app.logger.info(f"API: Password verified, returning download URL: {download_url}")
        
        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': file_record.file_name
        })
    else:
        app.logger.warning(f"API: Incorrect password attempt for file: {file_uuid}")
        return jsonify({'success': False, 'message': _("Incorrect password!")}), 403

@app.route('/api/download/<file_uuid>', methods=['GET'])
def download_file_direct(file_uuid):
    # This route would handle the actual file download after auth is completed
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        app.logger.warning(f"File not found for direct download: {file_uuid}")
        return "File not found", 404
        
    try:
        directory, stored_file = os.path.split(file_record.file_path)
        app.logger.info(f"Direct file download: {file_uuid} - {file_record.file_name}")
        return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
    except Exception as e:
        app.logger.error(f"Error during direct file download: {str(e)} for file {file_uuid}")
        return "Error downloading file", 500

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    try:
        files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).all()
        
        # Convert file objects to dictionaries
        file_list = []
        for file in files:
            file_list.append({
                'id': file.id,
                'file_name': file.file_name,
                'upload_date': file.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
                'download_count': file.download_count
            })
        
        # Get upload logs
        upload_logs = []
        download_logs = []
        
        # Read app.log for upload and download logs
        log_path = os.path.join(os.getcwd(), 'logs', 'app.log')
        try:
            with open(log_path, 'r') as log_file:
                for line in log_file:
                    if "File metadata saved to database:" in line:
                        upload_logs.append(line.strip())
                    elif "File download successful:" in line:
                        download_logs.append(line.strip())
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


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
