"""
Kokat bazë të sigurisë të API-së (ADR 0018): `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, dhe
`Cache-Control: no-store` për `/auth/*`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.accounts import World

BASE = {
    "referrer-policy": "no-referrer",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def _has_base(response) -> None:
    for key, value in BASE.items():
        assert response.headers.get(key) == value, (key, dict(response.headers))


def test_every_kind_of_response_carries_the_base_headers(world):
    world.confirmed()
    access = world.tokens()["access_token"]
    for response in (
        world.client.get("/health"),  # 200
        world.client.get("/nuk-ekziston"),  # 404 i Starlette
        world.client.get("/documents"),  # 401 i problemit
        world.client.post("/auth/login", json={"email": "x"}),  # 422
        world.me(access),  # 200 i /auth
        world.client.get("/openapi.json"),
    ):
        _has_base(response)


def test_auth_responses_are_not_cacheable_and_others_are_left_alone(world):
    world.confirmed()
    access = world.tokens()["access_token"]
    for response in (
        world.login(),
        world.login(password="fjalekalim-i-gabuar-xyz"),
        world.me(access),
        world.client.get("/auth/me"),
        world.forgot(),
        world.client.post("/auth/refresh", json={"refresh_token": "x"}),
    ):
        assert response.headers["cache-control"] == "no-store", response.request.url
    assert "cache-control" not in world.client.get("/health").headers
    assert "cache-control" not in world.client.get("/documents").headers


def test_a_path_that_merely_starts_with_auth_is_not_an_auth_path(world):
    assert "cache-control" not in world.client.get("/authors").headers


def test_the_headers_are_on_cors_preflight_responses(world):
    response = world.client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    _has_base(response)
    assert response.headers["cache-control"] == "no-store"


def test_an_unexpected_error_carries_the_headers_and_no_detail(world):
    def boom() -> None:
        raise RuntimeError("tekst i brendshëm që nuk duhet të dalë")

    world.app.add_api_route("/auth/boom", boom)
    client = TestClient(world.app, raise_server_exceptions=False)
    response = client.get("/auth/boom")
    assert response.status_code == 500
    _has_base(response)
    assert response.headers["cache-control"] == "no-store"
    assert "brendshëm që" not in response.text


def test_a_response_the_endpoint_sets_headers_on_is_not_overwritten_except_for_these(world):
    world.confirmed()
    blocked = None
    for _ in range(6):
        blocked = world.login(password="fjalekalim-i-gabuar-xyz")
    assert blocked.status_code == 429
    assert "retry-after" in blocked.headers  # kokat e endpoint-it mbijetojnë
    _has_base(blocked)
