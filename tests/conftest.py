import os
import tempfile
import pytest
from app import app as flask_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Set up a temporary database
    db_fd, db_path = tempfile.mkstemp()
    test_db_url = f"sqlite:///{db_path}"
    
    # Configure the app for testing
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': test_db_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'WTF_CSRF_ENABLED': False
    })
    
    # Create the database and context
    with flask_app.app_context():
        # Initialize database for testing
        from app import db
        db.create_all()
    
    yield flask_app
    
    # Teardown: close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner() 