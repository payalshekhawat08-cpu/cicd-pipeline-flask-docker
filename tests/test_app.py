from app.app import create_app


def make_client():
    return create_app().test_client()


def test_index_returns_message():
    response = make_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["author"] == "Payal Shekhawat"


def test_health_is_ok():
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_returns_sum():
    response = make_client().get("/api/add?a=2&b=3")
    assert response.status_code == 200
    assert response.get_json() == {"result": 5}


def test_add_rejects_bad_input():
    response = make_client().get("/api/add?a=2")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_metrics_counts_requests():
    client = make_client()
    client.get("/")
    client.get("/health")
    data = client.get("/metrics").get_json()
    assert data["requests_total"] == 3
    assert data["uptime_seconds"] >= 0
