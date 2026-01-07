"""Tests for API key management"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient):
    """Test creating a new API key"""
    request_data = {
        "name": "Test API Key",
        "scopes": ["read", "write"],
        "rate_limit": 1000,
        "integration_type": "chatlog",
    }
    
    response = await client.post("/api/v1/api-keys", json=request_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == request_data["name"]
    assert data["scopes"] == request_data["scopes"]
    assert "key" in data  # Full key only shown on creation
    assert data["key"].startswith("pp_")
    assert data["prefix"].startswith("pp_")


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient):
    """Test listing API keys"""
    # Create a key first
    await client.post("/api/v1/api-keys", json={
        "name": "Test Key",
        "scopes": ["read"],
    })
    
    response = await client.get("/api/v1/api-keys")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Full key should not be in list response
    for key in data:
        assert "key" not in key or key.get("key") is None


@pytest.mark.asyncio
async def test_get_api_key(client: AsyncClient):
    """Test getting a single API key"""
    create_response = await client.post("/api/v1/api-keys", json={
        "name": "Test Key",
        "scopes": ["read"],
    })
    key_id = create_response.json()["id"]
    
    response = await client.get(f"/api/v1/api-keys/{key_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == key_id


@pytest.mark.asyncio
async def test_validate_api_key(client: AsyncClient):
    """Test validating an API key"""
    # Create a key
    create_response = await client.post("/api/v1/api-keys", json={
        "name": "Test Key",
        "scopes": ["read", "write"],
    })
    full_key = create_response.json()["key"]
    
    # Validate the key
    response = await client.post("/api/v1/api-keys/validate", json={"key": full_key})
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["scopes"] == ["read", "write"]


@pytest.mark.asyncio
async def test_validate_invalid_api_key(client: AsyncClient):
    """Test validating an invalid API key"""
    response = await client.post("/api/v1/api-keys/validate", json={"key": "invalid_key"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient):
    """Test revoking an API key"""
    create_response = await client.post("/api/v1/api-keys", json={
        "name": "Test Key",
        "scopes": ["read"],
    })
    key_id = create_response.json()["id"]
    full_key = create_response.json()["key"]
    
    # Revoke the key
    response = await client.delete(f"/api/v1/api-keys/{key_id}")
    assert response.status_code == 204
    
    # Validate should now fail
    validate_response = await client.post(
        "/api/v1/api-keys/validate", 
        json={"key": full_key}
    )
    assert validate_response.json()["valid"] is False


@pytest.mark.asyncio
async def test_update_api_key(client: AsyncClient):
    """Test updating an API key"""
    create_response = await client.post("/api/v1/api-keys", json={
        "name": "Original Name",
        "scopes": ["read"],
    })
    key_id = create_response.json()["id"]
    
    response = await client.patch(
        f"/api/v1/api-keys/{key_id}",
        params={"name": "Updated Name", "rate_limit": 500}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["rate_limit"] == 500

