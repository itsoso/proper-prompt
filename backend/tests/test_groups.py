"""Tests for group management API"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, sample_group_data):
    """Test creating a new group"""
    response = await client.post("/api/v1/groups", json=sample_group_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_group_data["name"]
    assert data["external_id"] == sample_group_data["external_id"]
    assert data["type"] == sample_group_data["type"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_group(client: AsyncClient, sample_group_data):
    """Test creating a group with duplicate external_id"""
    # Create first group
    await client.post("/api/v1/groups", json=sample_group_data)
    
    # Try to create duplicate
    response = await client.post("/api/v1/groups", json=sample_group_data)
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient, sample_group_data):
    """Test listing groups"""
    # Create a group first
    await client.post("/api/v1/groups", json=sample_group_data)
    
    response = await client.get("/api/v1/groups")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_groups_with_filter(client: AsyncClient, sample_group_data):
    """Test listing groups with type filter"""
    await client.post("/api/v1/groups", json=sample_group_data)
    
    response = await client.get("/api/v1/groups", params={"type": "investment"})
    
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["type"] == "investment"


@pytest.mark.asyncio
async def test_get_group(client: AsyncClient, sample_group_data):
    """Test getting a single group"""
    create_response = await client.post("/api/v1/groups", json=sample_group_data)
    group_id = create_response.json()["id"]
    
    response = await client.get(f"/api/v1/groups/{group_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == group_id
    assert data["name"] == sample_group_data["name"]


@pytest.mark.asyncio
async def test_get_nonexistent_group(client: AsyncClient):
    """Test getting a nonexistent group"""
    response = await client.get("/api/v1/groups/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient, sample_group_data):
    """Test updating a group"""
    create_response = await client.post("/api/v1/groups", json=sample_group_data)
    group_id = create_response.json()["id"]
    
    update_data = {"name": "Updated Group Name", "member_count": 100}
    response = await client.patch(f"/api/v1/groups/{group_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Group Name"
    assert data["member_count"] == 100


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient, sample_group_data):
    """Test deleting (soft delete) a group"""
    create_response = await client.post("/api/v1/groups", json=sample_group_data)
    group_id = create_response.json()["id"]
    
    response = await client.delete(f"/api/v1/groups/{group_id}")
    
    assert response.status_code == 204
    
    # Verify group is soft deleted
    get_response = await client.get(f"/api/v1/groups/{group_id}")
    assert get_response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_list_group_types(client: AsyncClient):
    """Test listing available group types"""
    response = await client.get("/api/v1/groups/types/list")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check structure
    for item in data:
        assert "value" in item
        assert "label" in item

