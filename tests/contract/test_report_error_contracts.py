from app.api import create_app


def test_invalid_format_returns_422_with_error_code():
    app = create_app()

    with app.test_client() as client:
        payload = {
            "report_name": "test",
            "format": "pdf",
            "input_text": "sample",
            "llm_enabled": False
        }

        response = client.post(
            "/reports/download",
            json=payload,
            content_type="application/json"
        )

        assert response.status_code == 422
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error_code"] == "INVALID_FORMAT"
        assert "run_id" in data


def test_missing_field_returns_400_with_error_code():
    app = create_app()

    with app.test_client() as client:
        payload = {
            "format": "txt",
            "input_text": "sample",
            "llm_enabled": False
        }

        response = client.post(
            "/reports/download",
            json=payload,
            content_type="application/json"
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "run_id" in data
