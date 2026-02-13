from app.api import create_app


def test_invalid_format_returns_standard_error_body():
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

        data = response.get_json()
        assert response.status_code == 422
        assert set(data.keys()) == {"status", "error_code", "message", "run_id"}
