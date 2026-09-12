import asyncio
import json
import logging
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.request_logging import RequestLoggingMiddleware, logger


@pytest.fixture
def request_logs(caplog):
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def records(caplog):
    return [json.loads(record.message) for record in caplog.records if record.name == logger.name]


def test_health_has_matching_generated_request_id(request_logs):
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "client-private-value"})
    request_id = response.headers["x-request-id"]
    assert UUID(request_id).version == 4
    assert response.json() == {"status": "ok"}
    entries = records(request_logs)
    assert len(entries) == 1
    assert entries[0] == {"request_id": request_id, "method": "GET", "route": "/health",
                          "status": 200, "duration_ms": entries[0]["duration_ms"]}
    assert entries[0]["duration_ms"] >= 0


@pytest.mark.parametrize("path,status,route", [
    ("/private-person@example.com?token=query-secret", 404, "<unmatched>"),
    ("/restaurants/private-person@example.com?token=query-secret", 422, "/restaurants/{restaurant_id}"),
    ("/users/me?token=query-secret", 401, "/users/me"),
])
def test_logs_omit_raw_url_and_headers(request_logs, path, status, route):
    # Invalid restaurant ID normally still resolves DB dependencies; override it
    # because this test checks HTTP logging only and must not require PostgreSQL.
    from app.db import get_session
    app.dependency_overrides[get_session] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.get(path, headers={"Cookie": "session=cookie-secret", "X-Request-ID": "id-secret"})
    finally:
        app.dependency_overrides.pop(get_session)
    assert response.status_code == status
    entry = records(request_logs)[0]
    assert entry["route"] == route and entry["status"] == status
    for secret in ["private-person@example.com", "query-secret", "cookie-secret", "id-secret"]:
        assert secret not in json.dumps(records(request_logs))


def test_validation_logs_omit_password_and_body(request_logs):
    from app.db import get_session
    app.dependency_overrides[get_session] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.post("/auth/register", json={"email": "private@example.com", "password": "pwXYZ",
                "name": "Private Name", "default_address": "Private Street"}, headers={"Authorization": "Bearer secret-token"})
    finally:
        app.dependency_overrides.pop(get_session)
    assert response.status_code == 422
    assert records(request_logs)[0]["status"] == 422
    for secret in ["private@example.com", "pwXYZ", "Private Name", "Private Street", "secret-token"]:
        assert secret not in json.dumps(records(request_logs))


def test_unexpected_failure_is_safe_and_correlated(request_logs):
    failing = FastAPI()
    failing.add_middleware(RequestLoggingMiddleware)

    @failing.get("/fail")
    def fail():
        raise RuntimeError("password=secret-value address=Private Street SQL parameters")

    with TestClient(failing) as client:
        response = client.get("/fail")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    entry = records(request_logs)[0]
    assert entry["request_id"] == response.headers["x-request-id"]
    assert entry["error_type"] == "RuntimeError" and entry["status"] == 500
    assert "secret-value" not in request_logs.text
    assert "Private Street" not in request_logs.text
    assert any(record.levelno == logging.ERROR for record in request_logs.records)


def test_http_error_detail_not_logged(request_logs):
    failing = FastAPI()
    failing.add_middleware(RequestLoggingMiddleware)

    @failing.get("/denied")
    def denied():
        raise HTTPException(403, "private-error-detail")

    with TestClient(failing) as client:
        response = client.get("/denied")
    assert response.status_code == 403
    assert records(request_logs)[0]["status"] == 403
    assert "private-error-detail" not in request_logs.text


def test_concurrent_requests_have_distinct_matching_ids(request_logs):
    async def requests():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await asyncio.gather(*(client.get("/health") for _ in range(10)))

    responses = asyncio.run(requests())
    ids = {response.headers["x-request-id"] for response in responses}
    assert len(ids) == 10
    assert {entry["request_id"] for entry in records(request_logs)} == ids
