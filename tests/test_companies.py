from fastapi.testclient import TestClient
from app.main import create_app

def test_company_lifecycle(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as client:
        assert client.get("/companies").json() == []
        data = {"name": "Example Company", "website_url": "https://example.com"}
        response = client.post("/companies", json=data)
        assert response.status_code == 201
        company_id = response.json()["id"]
        assert client.post("/companies", json={"name": " example  company "}).status_code == 409
        assert client.put(f"/companies/{company_id}", json={**data, "enabled": False}).json()["enabled"] is False
        assert client.get(f"/companies/{company_id}").status_code == 200
        assert client.delete(f"/companies/{company_id}").status_code == 204
        assert client.get("/companies").json() == []
    with TestClient(app) as client:
        assert client.get("/companies").json() == []
        assert client.post("/companies", json=data).status_code == 409

def test_validation(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as client:
        assert client.post("/companies", json={"name": "  "}).status_code == 422
        assert client.post("/companies", json={"name": "Test", "career_url": "invalid"}).status_code == 422


def test_dashboard(tmp_path):
    with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Add company" in response.text
        assert "/companies" in response.text
