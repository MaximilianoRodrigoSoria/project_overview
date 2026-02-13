from app.api import create_app


def test_openapi_includes_format_enum_and_examples():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/apispec.json")
        assert response.status_code == 200

        spec = response.get_json()
        paths = spec.get("paths", {})
        report_path = paths.get("/reports/download", {})
        post_def = report_path.get("post", {})
        parameters = post_def.get("parameters", [])

        body_param = next(
            (param for param in parameters if param.get("in") == "body"),
            None
        )
        assert body_param is not None

        schema = body_param.get("schema", {})
        props = schema.get("properties", {})
        fmt_prop = props.get("format", {})
        assert "enum" in fmt_prop
        assert set(fmt_prop["enum"]) >= {"excel", "csv", "txt", "markdown", "doc"}

        examples = body_param.get("examples", {})
        assert "excel" in examples
        assert "csv" in examples
