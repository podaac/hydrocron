"""Structural checks for the API Gateway OpenAPI definition."""

from pathlib import Path


API_SPEC = (
    Path(__file__).parents[1]
    / "terraform"
    / "api-specification-templates"
    / "hydrocron_aws_api.yml"
)


def test_csv_file_response_mapping_uses_explicit_download_sentinel():
    """The JSON response template must not infer downloads from CSV content."""
    specification = API_SPEC.read_text(encoding="utf-8")
    response_template = specification.split(
        "            responseTemplates:\n", maxsplit=1
    )[1].split("              application/geo+json:", maxsplit=1)[0]

    assert "#set($isDownload = $input.path('$.__hydrocron_download__'))" in response_template
    assert "#if($isDownload == true)" in response_template
    assert "contains('__hydrocron_download__')" not in response_template
    assert "$input.path('$.csv_data')" in response_template
    assert 'Content-Disposition = "attachment; filename=$fn"' in response_template


def test_csv_file_response_headers_are_declared():
    """Headers set by the response template must exist on the 200 method response."""
    specification = API_SPEC.read_text(encoding="utf-8")
    success_response = specification.split('        "200":\n', maxsplit=1)[1].split(
        '        "400":', maxsplit=1
    )[0]

    assert "Content-Disposition:" in success_response
    assert "Access-Control-Expose-Headers:" in success_response


def test_cors_options_exposes_content_disposition():
    """OPTIONS response must include the configured exposed-header value."""
    specification = API_SPEC.read_text(encoding="utf-8")
    options_section = specification.split("options:", maxsplit=1)[1]

    assert (
        "method.response.header.Access-Control-Expose-Headers: "
        '"\'Content-Disposition\'"'
    ) in options_section
