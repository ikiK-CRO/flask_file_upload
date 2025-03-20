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

app = Flask(__name__)
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

# Modify your database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Heroku PostgreSQL URL format (if needed)
    database_url = re.sub(r'^postgres:', 'postgresql:', database_url)
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
def upload_file():
    if request.method == 'POST':
        # Check if the POST request has a file part
        if 'file' not in request.files:
            message = "No file part in the request"
            app.logger.warning(f"Upload failed: {message}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
            
        uploaded_file = request.files.get('file')
        password = request.form.get('password')
        
        # Check if a file was selected
        if not uploaded_file or uploaded_file.filename == '':
            message = "No file selected"
            app.logger.warning(f"Upload failed: {message}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
            
        # Check if password is provided
        if not password:
            message = "Password is required"
            app.logger.warning(f"Upload failed: {message}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
        
        # Log the upload attempt (without including the actual password)
        app.logger.info(f"Upload attempt: {uploaded_file.filename} ({uploaded_file.content_type})")
            
        # Check if the file type is allowed
        if not allowed_file(uploaded_file.filename):
            message = f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            app.logger.warning(f"Upload failed: {message} - Filename: {uploaded_file.filename}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
            
        # File Size Validation: Limit file size to 10MB
        uploaded_file.seek(0, os.SEEK_END)
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)
        
        if file_size > MAX_CONTENT_LENGTH:
            message = f"File size exceeds the {MAX_CONTENT_LENGTH // (1024 * 1024)}MB limit!"
            app.logger.warning(f"Upload failed: {message} - File size: {file_size/1024/1024:.2f}MB")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
            
        # MIME type validation
        if not validate_mime_type(uploaded_file):
            message = "Invalid file content or MIME type"
            app.logger.warning(f"Upload failed: {message} - Filename: {uploaded_file.filename}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)

        # Input Validation and Sanitization
        filename = secure_filename(uploaded_file.filename)
        if filename == '':
            message = "Invalid file name after sanitization"
            app.logger.warning(f"Upload failed: {message} - Original filename: {uploaded_file.filename}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
            
        # Additional sanitization: remove potentially dangerous characters
        filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

        file_uuid = str(uuid.uuid4())
        # Prepend the UUID to ensure filename uniqueness
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_{filename}")
        
        try:
            uploaded_file.save(file_path)
            app.logger.info(f"File saved: {file_path} - Size: {file_size/1024/1024:.2f}MB")
        except Exception as e:
            app.logger.error(f"File save error: {str(e)} - Path: {file_path}")
            message = "Error saving file"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)

        # Hash the password before storing
        try:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        except Exception as e:
            app.logger.error(f"Password hashing error: {str(e)}")
            message = "Password hashing failed!"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)
        
        # Check if password_hash is valid
        if not password_hash:
            message = "Password hashing failed!"
            app.logger.error("Empty password hash generated")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)

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
            # Log the error for server-side debugging
            app.logger.error(f"Database error: {str(e)}")
            
            # Delete the uploaded file if database operation failed
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    app.logger.info(f"Cleaned up file after database error: {file_path}")
                except Exception as cleanup_error:
                    app.logger.error(f"Error cleaning up file: {str(cleanup_error)} - Path: {file_path}")
                
            message = "An error occurred while saving the file."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message})
            flash(message)
            return redirect(request.url)

        # Return the download URL to the user
        file_url = url_for('get_file', file_uuid=file_uuid, _external=True)
        success_message = f"File uploaded successfully! Access it at: <a href='{file_url}'>{file_url}</a>"
        
        app.logger.info(f"Upload successful: {filename} - UUID: {file_uuid}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': success_message,
                'file_url': file_url
            })
        
        return render_template('index.html', success_message=success_message)
    
    return render_template('index.html')

@app.route('/get-file/<file_uuid>', methods=['GET', 'POST'])
def get_file(file_uuid):
    app.logger.info(f"File download page accessed: {file_uuid}")
    
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        app.logger.warning(f"File not found: {file_uuid}")
        return "File not found", 404

    if request.method == 'POST':
        entered_password = request.form.get('password')
        
        if not entered_password:
            app.logger.warning(f"Download attempt without password: {file_uuid}")
            flash("Password is required")
            return render_template('get_file.html', file_uuid=file_uuid)
        
        if bcrypt.check_password_hash(file_record.password_hash, entered_password):
            # Update download count
            file_record.download_count += 1
            try:
                db.session.commit()
                app.logger.info(f"Download count updated: {file_uuid} - New count: {file_record.download_count}")
            except Exception as e:
                app.logger.error(f"Error updating download count: {str(e)} - UUID: {file_uuid}")
            
            # Send the file as a download
            directory, stored_file = os.path.split(file_record.file_path)
            app.logger.info(f"File download successful: {file_uuid} - {file_record.file_name}")
            
            try:
                return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
            except Exception as e:
                app.logger.error(f"File send error: {str(e)} - Path: {file_record.file_path}")
                return "Error downloading file", 500
        else:
            app.logger.warning(f"Incorrect password attempt for file: {file_uuid}")
            flash("Incorrect password!")
    
    return render_template('get_file.html', file_uuid=file_uuid)

@app.route('/logs')
def view_logs():
    """Display logs of successful uploads and downloads."""
    try:
        # Query the database for file data
        files = UploadedFile.query.order_by(UploadedFile.upload_date.desc()).all()
        
        # Parse logs for successful uploads and downloads
        uploads = []
        downloads = []
        error_message = None
        
        logs_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        log_file = os.path.join(logs_dir, 'app.log')
        
        # Create empty log file if it doesn't exist
        if not os.path.exists(log_file):
            try:
                with open(log_file, 'w') as f:
                    f.write("Log file created\n")
                app.logger.info("Log file created")
                error_message = "Log file created. No activity logs to display yet."
            except Exception as e:
                app.logger.error(f"Error creating log file: {str(e)}")
                error_message = f"Could not create log file: {str(e)}"
        else:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            if "Upload successful:" in line:
                                uploads.append(line.strip())
                            elif "File download successful:" in line:
                                downloads.append(line.strip())
                        except Exception:
                            # Skip any problematic lines
                            continue
            except Exception as e:
                app.logger.error(f"Error reading log file: {str(e)}")
                error_message = f"Could not read log file: {str(e)}"
        
        # Sort logs in reverse chronological order (newest first)
        uploads.reverse()
        downloads.reverse()
        
        # Limit to the last 50 entries
        uploads = uploads[:50]
        downloads = downloads[:50]
        
        return render_template('logs.html', 
                            files=files, 
                            uploads=uploads,
                            downloads=downloads,
                            error=error_message)
    except Exception as e:
        app.logger.error(f"Error in logs view: {str(e)}")
        return render_template('logs.html', 
                            files=[], 
                            uploads=[],
                            downloads=[],
                            error=f"Could not load logs: {str(e)}")

@app.errorhandler(404)
def page_not_found(e):
    app.logger.info(f"404 error: {request.path}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
