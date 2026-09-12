"""Structural checks for the API Gateway OpenAPI definition."""

from pathlib import Path

import yaml


API_SPEC = (
    Path(__file__).parents[1]
    / "terraform"
    / "api-specification-templates"
    / "hydrocron_aws_api.yml"
)


def _load_spec():
    """Parse the OpenAPI YAML into a structured object.

    Navigating the parsed structure is resilient to formatting/indentation changes; only the
    VTL mapping-template values (opaque strings inside the YAML) are substring-checked.
    """
    return yaml.safe_load(API_SPEC.read_text(encoding="utf-8"))


def _timeseries_integration_default(spec):
    """Return the default integration response for GET /timeseries."""
    return (
        spec["paths"]["/timeseries"]["get"]["x-amazon-apigateway-integration"]
        ["responses"]["default"]
    )


def test_csv_file_response_mapping_uses_explicit_download_sentinel():
    """The JSON response template must not infer downloads from CSV content."""
    response_template = _timeseries_integration_default(_load_spec())["responseTemplates"]["application/json"]

    assert "#set($isDownload = $input.path('$.__hydrocron_download__'))" in response_template
    assert "#if($isDownload == true)" in response_template
    assert "contains('__hydrocron_download__')" not in response_template
    assert "$input.path('$.csv_data')" in response_template
    assert 'Content-Disposition = "attachment; filename=$fn"' in response_template


def test_csv_file_response_headers_are_declared():
    """Headers set by the response template must exist on the 200 method response."""
    headers = _load_spec()["paths"]["/timeseries"]["get"]["responses"]["200"]["headers"]

    assert "Content-Disposition" in headers
    assert "Access-Control-Expose-Headers" in headers


def test_cors_options_exposes_content_disposition():
    """OPTIONS response must include the configured exposed-header value."""
    response_parameters = (
        _load_spec()["paths"]["/timeseries"]["options"]["x-amazon-apigateway-integration"]
        ["responses"]["default"]["responseParameters"]
    )

    assert response_parameters.get("method.response.header.Access-Control-Expose-Headers") == "'Content-Disposition'"
