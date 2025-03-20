import os
import uuid
import re
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this in production

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

# Modify your database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for Heroku PostgreSQL URL format (if needed)
    database_url = re.sub(r'^postgres:', 'postgresql:', database_url)
else:
    # Fallback for local development
    database_url = 'postgresql://postgres:postgres@db:5432/fileupload_db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define upload folder – using an absolute path within the container.
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Define the database model
class UploadedFile(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID4 as string
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Store hashed password
    password = db.Column(db.String(255), nullable=False)  # This might be the missing column

# Create database tables (if they don't exist)
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")



@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        password = request.form.get('password')
        
        # Debugging: Log the received password
        print(f"Received password: '{password}'")  # Debug statement
        
        if uploaded_file and password:
            # File Size Validation: Limit file size to 10MB
            if len(uploaded_file.read()) > 10 * 1024 * 1024:
                flash("File size exceeds the 10MB limit!")
                return redirect(request.url)
            uploaded_file.seek(0)  # Reset file pointer after size check

            # Input Validation and Sanitization
            filename = secure_filename(uploaded_file.filename)
            if filename == '':
                flash("Invalid file name!")
                return redirect(request.url)

            file_uuid = str(uuid.uuid4())
            # Prepend the UUID to ensure filename uniqueness
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_{filename}")
            uploaded_file.save(file_path)

            # Hash the password before storing
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Debugging: Log the hashed password
            print(f"Hashed password: '{password_hash}'")  # Debug statement

            # Check if password_hash is valid
            if not password_hash:
                flash("Password hashing failed!")
                return redirect(request.url)

            # Create the new_file instance
            new_file = UploadedFile(
                id=file_uuid,
                file_name=filename,
                file_path=file_path,
                password_hash=password_hash,
                password=password
            )
            
            # Debugging: Log the new_file object
            print(f"New file object: {new_file}")  # Debug statement
            
            # Save file metadata in the database
            db.session.add(new_file)
            try:
                db.session.commit()
            except Exception as e:
                print(f"Error committing to database: {e}")  # Debug statement
                flash("An error occurred while saving the file.")
                return redirect(request.url)

            # Return the download URL to the user
            file_url = url_for('get_file', file_uuid=file_uuid, _external=True)
            success_message = f"File uploaded successfully! Access it at: <a href='{file_url}'>{file_url}</a>"
            return render_template('index.html', success_message=success_message)
        else:
            flash("File and password are required!")
    return render_template('index.html')

@app.route('/get-file/<file_uuid>', methods=['GET', 'POST'])
def get_file(file_uuid):
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        return "File not found", 404

    if request.method == 'POST':
        entered_password = request.form.get('password')
        if bcrypt.check_password_hash(file_record.password_hash, entered_password):
            # Send the file as a download
            directory, stored_file = os.path.split(file_record.file_path)
            return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
        else:
            flash("Incorrect password!")
    return render_template('get_file.html', file_uuid=file_uuid)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=False for production
