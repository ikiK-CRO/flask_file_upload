import os
import sys
import re

# Path to your app.py
app_path = 'app.py'

# Read the current content
with open(app_path, 'r') as file:
    content = file.read()

# Check if imports are already added
if 'jsonify' not in content:
    import_line = 'from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session\n'
    new_import = 'from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify\n'
    content = content.replace(import_line, new_import)

# Add CORS support if not already present
if 'CORS' not in content:
    cors_import = 'from flask_cors import CORS\n'
    
    # Find where imports end and app initialization begins
    import_end = content.find('app = Flask')
    
    # Insert CORS import before app initialization
    content = content[:import_end] + cors_import + content[import_end:]
    
    # Add CORS initialization after app is created
    app_init = 'app = Flask(__name__)\n'
    cors_init = 'app = Flask(__name__)\nCORS(app)  # Enable CORS for all routes\n'
    content = content.replace(app_init, cors_init)

# Add route to serve React app if not already present
if 'def serve_react_app()' not in content:
    react_route = '''
@app.route('/react')
def serve_react_app():
    return render_template('react_index.html')

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
        'message': _("File uploaded successfully!"),
        'file_url': file_url
    })

@app.route('/api/files/<file_uuid>', methods=['POST'])
def api_get_file(file_uuid):
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        return jsonify({'success': False, 'message': "File not found"})

    entered_password = request.json.get('password')
    
    if not entered_password:
        return jsonify({'success': False, 'message': _("Password is required")})
    
    if bcrypt.check_password_hash(file_record.password_hash, entered_password):
        # Update download count
        file_record.download_count += 1
        try:
            db.session.commit()
            app.logger.info(f"Download count updated: {file_uuid} - New count: {file_record.download_count}")
        except Exception as e:
            app.logger.error(f"Error updating download count: {str(e)} - UUID: {file_uuid}")
        
        # Return the direct download URL
        download_url = url_for('download_file_direct', file_uuid=file_uuid, _external=True)
        return jsonify({
            'success': True,
            'download_url': download_url,
            'filename': file_record.file_name
        })
    else:
        app.logger.warning(f"Incorrect password attempt for file: {file_uuid}")
        return jsonify({'success': False, 'message': _("Incorrect password!")})

@app.route('/api/download/<file_uuid>', methods=['GET'])
def download_file_direct(file_uuid):
    # This route would handle the actual file download after auth is completed
    file_record = UploadedFile.query.filter_by(id=file_uuid).first()
    if not file_record:
        return "File not found", 404
        
    directory, stored_file = os.path.split(file_record.file_path)
    return send_from_directory(directory, stored_file, as_attachment=True, download_name=file_record.file_name)

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
'''
    
    # Find where the last route ends
    last_route_end = content.rfind('@app.route')
    last_route_end = content.find('\n\n', last_route_end)
    
    # Insert React route after the last existing route
    if last_route_end != -1:
        content = content[:last_route_end] + react_route + content[last_route_end:]
    else:
        # Append at the end if we can't find the right spot
        content += react_route

# Write the updated content
with open(app_path, 'w') as file:
    file.write(content)

print("Flask app updated to support React integration.")
