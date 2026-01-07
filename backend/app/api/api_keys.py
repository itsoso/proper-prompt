"""API Key management routes"""
import secrets
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.api_key import APIKey
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
    APIKeyValidateRequest,
    APIKeyValidateResponse,
)

logger = get_logger(__name__)
router = APIRouter()


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key, returning (full_key, prefix, hash)"""
    # Generate a random 32-byte key
    key_bytes = secrets.token_bytes(32)
    full_key = f"pp_{secrets.token_urlsafe(32)}"
    prefix = full_key[:10]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


@router.post("", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key"""
    full_key, prefix, key_hash = generate_api_key()
    
    api_key = APIKey(
        name=request.name,
        key_hash=key_hash,
        prefix=prefix,
        scopes=request.scopes,
        rate_limit=request.rate_limit,
        monthly_limit=request.monthly_limit,
        integration_type=request.integration_type,
        webhook_url=request.webhook_url,
        expires_at=request.expires_at,
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    logger.info("api_key_created", key_id=api_key.id, name=api_key.name, prefix=prefix)
    
    # Return with the full key (only shown once)
    response_data = APIKeyResponse.model_validate(api_key).model_dump()
    response_data["key"] = full_key
    
    return APIKeyCreatedResponse(**response_data)


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    integration_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
):
    """List all API keys (without showing full keys)"""
    query = select(APIKey)
    
    if is_active is not None:
        query = query.where(APIKey.is_active == is_active)
    if integration_type:
        query = query.where(APIKey.integration_type == integration_type)
    
    result = await db.execute(query)
    keys = result.scalars().all()
    
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an API key by ID"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyResponse.model_validate(api_key)


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    name: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    rate_limit: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update an API key"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if name is not None:
        api_key.name = name
    if scopes is not None:
        api_key.scopes = scopes
    if rate_limit is not None:
        api_key.rate_limit = rate_limit
    if is_active is not None:
        api_key.is_active = is_active
    
    await db.commit()
    await db.refresh(api_key)
    
    logger.info("api_key_updated", key_id=key_id)
    
    return APIKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Revoke (deactivate) an API key"""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    await db.commit()
    
    logger.info("api_key_revoked", key_id=key_id)


@router.post("/validate", response_model=APIKeyValidateResponse)
async def validate_api_key(
    request: APIKeyValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate an API key"""
    key_hash = hashlib.sha256(request.key.encode()).hexdigest()
    
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key or not api_key.is_active:
        return APIKeyValidateResponse(valid=False)
    
    from datetime import datetime
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return APIKeyValidateResponse(valid=False)
    
    return APIKeyValidateResponse(
        valid=True,
        api_key_id=api_key.id,
        scopes=api_key.scopes,
        rate_limit_remaining=api_key.rate_limit,  # TODO: 实际计算剩余配额
    )

