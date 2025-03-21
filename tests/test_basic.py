"""Basic tests for the Flask application."""

def test_index_route(client):
    """Test that the index route returns a successful response."""
    response = client.get('/')
    assert response.status_code == 200
    
def test_api_logs_route(client):
    """Test that the logs API route returns a successful response."""
    response = client.get('/api/logs')
    assert response.status_code == 200
    assert b'success' in response.data
    
def test_nonexistent_route(client):
    """Test that a nonexistent route returns a 404 response."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404 