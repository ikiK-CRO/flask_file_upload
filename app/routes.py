from flask_bcrypt import Bcrypt
from flask import request, abort
from werkzeug.utils import secure_filename

bcrypt = Bcrypt()

def register_user(username, password):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    # Store hashed_password in the database
    # ... existing code ...

def verify_user(username, password):
    # Retrieve hashed_password from the database
    if bcrypt.check_password_hash(hashed_password, password):
        # Password is correct
        return True
    return False 

def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not filename:
            abort(400, 'Invalid file name. Please provide a valid file.')
        if file.content_length > 10 * 1024 * 1024:  # 10MB limit
            abort(400, 'File size exceeds 10MB limit.')
        # Save the file with the secure filename
        # ... existing code ... 