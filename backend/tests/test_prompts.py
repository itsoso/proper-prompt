"""Tests for prompt template and execution API"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, sample_prompt_template_data):
    """Test creating a new prompt template"""
    response = await client.post(
        "/api/v1/prompts/templates", 
        json=sample_prompt_template_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_prompt_template_data["name"]
    assert data["group_type"] == sample_prompt_template_data["group_type"]
    assert data["version"] == 1
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, sample_prompt_template_data):
    """Test listing prompt templates"""
    await client.post("/api/v1/prompts/templates", json=sample_prompt_template_data)
    
    response = await client.get("/api/v1/prompts/templates")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_templates_with_filter(client: AsyncClient, sample_prompt_template_data):
    """Test listing templates with filters"""
    await client.post("/api/v1/prompts/templates", json=sample_prompt_template_data)
    
    response = await client.get(
        "/api/v1/prompts/templates",
        params={"group_type": "investment", "time_granularity": "daily"}
    )
    
    assert response.status_code == 200
    data = response.json()
    for template in data:
        assert template["group_type"] == "investment"
        assert template["time_granularity"] == "daily"


@pytest.mark.asyncio
async def test_get_template(client: AsyncClient, sample_prompt_template_data):
    """Test getting a single template"""
    create_response = await client.post(
        "/api/v1/prompts/templates", 
        json=sample_prompt_template_data
    )
    template_id = create_response.json()["id"]
    
    response = await client.get(f"/api/v1/prompts/templates/{template_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient, sample_prompt_template_data):
    """Test updating a template"""
    create_response = await client.post(
        "/api/v1/prompts/templates", 
        json=sample_prompt_template_data
    )
    template_id = create_response.json()["id"]
    
    update_data = {"name": "Updated Template", "description": "Updated description"}
    response = await client.patch(
        f"/api/v1/prompts/templates/{template_id}", 
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Template"
    assert data["version"] == 2  # Version should increment


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient, sample_prompt_template_data):
    """Test deleting a template"""
    create_response = await client.post(
        "/api/v1/prompts/templates", 
        json=sample_prompt_template_data
    )
    template_id = create_response.json()["id"]
    
    response = await client.delete(f"/api/v1/prompts/templates/{template_id}")
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_list_builtin_templates(client: AsyncClient):
    """Test listing built-in templates"""
    response = await client.get("/api/v1/prompts/builtin")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check structure
    for template in data:
        assert "group_type" in template
        assert "time_granularity" in template
        assert "style" in template
        assert "template" in template


@pytest.mark.asyncio
async def test_generate_prompts(client: AsyncClient):
    """Test generating prompt variants"""
    request_data = {
        "group_type": "investment",
        "time_granularity": "daily",
        "styles": ["analytical", "summary"],
    }
    
    response = await client.post("/api/v1/prompts/generate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "prompts" in data
    assert "generation_time_ms" in data
    assert len(data["prompts"]) >= 1


@pytest.mark.asyncio
async def test_list_executions(client: AsyncClient):
    """Test listing prompt executions"""
    response = await client.get("/api/v1/prompts/executions")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

