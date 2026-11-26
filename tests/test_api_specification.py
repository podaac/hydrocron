"""Structural checks for the API Gateway OpenAPI definition."""

import re
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


def test_node_fields_parameter_is_declared():
    """node_fields is documented as an optional query string parameter."""
    parameters = {p["name"]: p for p in _load_spec()["paths"]["/timeseries"]["get"]["parameters"]}

    assert parameters["node_fields"]["in"] == "query"
    assert parameters["node_fields"]["required"] is False
    assert parameters["node_fields"]["schema"]["type"] == "string"


def _status_for(error_message, integration_responses):
    """Return the status API Gateway would pick: the first error regex that matches, else the default (200)."""
    for pattern, response in integration_responses.items():
        if pattern != "default" and re.fullmatch(pattern, error_message):
            return response["statusCode"]
    return integration_responses["default"]["statusCode"]


def test_error_codes_are_mapped():
    """Each error message maps to the right status, one regex per status, and every mapped status has a method response."""
    get = _load_spec()["paths"]["/timeseries"]["get"]
    integration_responses = get["x-amazon-apigateway-integration"]["responses"]

    status_codes = [response["statusCode"] for response in integration_responses.values()]
    assert len(status_codes) == len(set(status_codes)), "API Gateway keeps only one integration response per status code"
    for response in integration_responses.values():
        assert response["statusCode"] in get["responses"]

    for message, status in (("400: bad", "400"), ("404: none", "404"), ("413: big", "413"), ("415: type", "415"),
                            ("500: Internal error (request ID x)", "500"), ("503: Service busy.", "503"),
                            ("Unable to import module 'x'", "500"), ("'geometry'", "500"),
                            ("Runtime error\nline 2", "500"), ('Init error: "quoted"', "500")):
        assert _status_for(message, integration_responses) == status, repr(message)


def test_500_template_never_echoes_raw_runtime_errors():
    """The 500 template echoes only our pre-escaped "500: ..." messages; anything else gets a fixed body (no broken JSON, no leaks)."""
    integration_responses = _load_spec()["paths"]["/timeseries"]["get"]["x-amazon-apigateway-integration"]["responses"]
    template = next(r for r in integration_responses.values() if r["statusCode"] == "500")["responseTemplates"]["application/json"]

    assert "#if($msg.startsWith('500:'))" in template
    fallback = template.split("#else", 1)[1]
    assert "$input" not in fallback and "$msg" not in fallback
    assert '"500: Internal error (request ID $context.requestId).' in fallback


def test_cors_options_exposes_content_disposition():
    """OPTIONS response must include the configured exposed-header value."""
    response_parameters = (
        _load_spec()["paths"]["/timeseries"]["options"]["x-amazon-apigateway-integration"]
        ["responses"]["default"]["responseParameters"]
    )

    assert response_parameters.get("method.response.header.Access-Control-Expose-Headers") == "'Content-Disposition'"
