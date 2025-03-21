"""Tests for file upload and download operations."""
import io
import json
import pytest

def test_upload_file(client, app):
    """Test that a valid file can be uploaded."""
    test_file = io.BytesIO(b'Test file content')
    password = 'testpassword123'
    
    response = client.post(
        '/api/upload',
        data={'file': (test_file, 'test.txt'), 'password': password},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'file_url' in data
    assert 'success' in data
    
def test_upload_no_file(client):
    """Test that uploading with no file returns an error."""
    response = client.post(
        '/api/upload',
        data={'password': 'testpassword123'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert data['success'] is False
    
def test_upload_no_password(client):
    """Test that uploading with no password returns an error."""
    test_file = io.BytesIO(b'Test file content')
    
    response = client.post(
        '/api/upload',
        data={'file': (test_file, 'test.txt')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert data['success'] is False 