import os
import uuid
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this in production

# Database configuration: use environment variable for flexibility.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/fileupload_db')
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
    password = db.Column(db.String(255), nullable=False)  # For production, consider storing a hash

# Create database tables (if they don't exist)
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        password = request.form.get('password')
        if uploaded_file and password:
            file_uuid = str(uuid.uuid4())
            filename = uploaded_file.filename
            # Prepend the UUID to ensure filename uniqueness
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_uuid}_{filename}")
            uploaded_file.save(file_path)
            # Save file metadata in the database
            new_file = UploadedFile(id=file_uuid, file_name=filename, file_path=file_path, password=password)
            db.session.add(new_file)
            db.session.commit()
            # Return the download URL to the user
            file_url = url_for('get_file', file_uuid=file_uuid, _external=True)
            return f"File uploaded successfully! Access it at: <a href='{file_url}'>{file_url}</a>"
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
        if entered_password == file_record.password:
            # Send the file as a download
            directory, stored_file = os.path.split(file_record.file_path)
            return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)
        else:
            flash("Incorrect password!")
    return render_template('get_file.html', file_uuid=file_uuid)

if __name__ == '__main__':
    # Use host '0.0.0.0' to make the container accessible externally
    app.run(host='0.0.0.0', port=5000, debug=True)
