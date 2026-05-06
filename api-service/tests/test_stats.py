import pytest
import asyncio
from unittest.mock import patch, PropertyMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app, SECRET_KEY, ALGORITHM, create_access_token
from app.db import redis_client
import fakeredis.aioredis

@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)

@pytest.mark.anyio
async def test_middleware_records_stats(fake_redis):
    with patch("app.db.RedisClient.redis", new_callable=PropertyMock) as mock_redis_prop:
        mock_redis_prop.return_value = fake_redis
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = AsyncMock(status_code=200, json=lambda: {})
            with TestClient(app) as client:
                # Hit an endpoint multiple times
                client.get("/health")
                client.get("/health")
                client.get("/api/leaderboard") 

                # Check stats via admin endpoint
                response = client.get("/api/admin/stats")
                assert response.status_code == 200
                stats = response.json()
                assert stats.get("/health") == 2
                assert stats.get("/api/leaderboard") == 1

@pytest.mark.anyio
async def test_admin_stats_accessible_without_token(fake_redis):
    with patch("app.db.RedisClient.redis", new_callable=PropertyMock) as mock_redis_prop:
        mock_redis_prop.return_value = fake_redis
        with TestClient(app) as client:
            response = client.get("/api/admin/stats")
            assert response.status_code == 200

@pytest.mark.anyio
async def test_route_pattern_masking(fake_redis):
    with patch("app.db.RedisClient.redis", new_callable=PropertyMock) as mock_redis_prop:
        mock_redis_prop.return_value = fake_redis
        with TestClient(app) as client:
            # Hit an endpoint with path parameters
            client.post("/api/lobbies/lobby123/add-bot")
            client.post("/api/lobbies/lobby456/add-bot")

            response = client.get("/api/admin/stats")
            assert response.status_code == 200
            stats = response.json()
            # It should group by the route pattern, not the actual path
            assert stats.get("/api/lobbies/{lobby_id}/add-bot") == 2
