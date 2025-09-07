import json


def test_ml_predict_smoke(client):
    resp = client.post("/api/ml/predict", json={"symbol": "BTC/USDT", "user_id": "u1"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "y_hat" in data and "prob_up" in data and "variant" in data

