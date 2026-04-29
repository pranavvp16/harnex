from __future__ import annotations

import json

import pytest

from harnex_api.services.ingestion.fetcher import (
    SpecValidationError,
    parse_spec_bytes,
    parse_uploaded_spec,
)


def test_parse_openapi_3_json():
    doc = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "paths": {"/x": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    result = parse_spec_bytes(json.dumps(doc).encode("utf-8"))
    assert result.original_format == "openapi-3"
    assert result.document["paths"]["/x"]["get"]["responses"]["200"]["description"] == "ok"


def test_parse_yaml_openapi_3():
    yaml_text = """
openapi: 3.0.3
info:
  title: t
  version: '1'
paths:
  /y:
    get:
      responses:
        '200':
          description: ok
""".strip()
    result = parse_spec_bytes(yaml_text.encode("utf-8"))
    assert result.original_format == "openapi-3"


def test_swagger_2_upconvert():
    swagger = {
        "swagger": "2.0",
        "info": {"title": "t", "version": "1"},
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "paths": {
            "/things": {
                "post": {
                    "operationId": "createThing",
                    "summary": "Create",
                    "consumes": ["application/json"],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {"type": "object"},
                        }
                    ],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    result = parse_spec_bytes(json.dumps(swagger).encode("utf-8"))
    assert result.original_format == "swagger-2"
    out = result.document
    assert out["openapi"].startswith("3.")
    assert out["servers"][0]["url"] == "https://api.example.com/v1"
    op = out["paths"]["/things"]["post"]
    assert "requestBody" in op
    assert op["requestBody"]["content"]["application/json"]["schema"] == {"type": "object"}


def test_invalid_spec_raises():
    with pytest.raises(SpecValidationError):
        parse_uploaded_spec(b"{}")
