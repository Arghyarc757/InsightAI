from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_categories():
    """Test that the available categories are fetched from ChromaDB correctly."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Even if empty, it must be a list. Ideally, it shouldn't be empty if the DB is seeded.
    if len(data) > 0:
        assert isinstance(data[0], str)

def test_get_manufacturers():
    """Test that the available manufacturers are fetched from ChromaDB correctly."""
    response = client.get("/api/manufacturers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Verify string items
    if len(data) > 0:
        assert isinstance(data[0], str)

def test_analyze_input_validation():
    """Verify that bad inputs are instantly rejected by FastAPI."""
    # Sending missing 'query' payload
    response = client.post("/api/analyze", json={"filters": {}})
    assert response.status_code == 422 # Standard FastAPI Validation Error
