"""API dependencies"""
import time
import hashlib
from typing import Optional
from datetime import datetime

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import get_logger, get_performance_logger
from app.models.api_key import APIKey
from app.services.llm_service import LLMService

logger = get_logger(__name__)
perf_logger = get_performance_logger()

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Optional[APIKey]:
    """Validate and return API key if provided"""
    if not api_key:
        return None
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up the key
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        logger.warning("invalid_api_key_attempt", key_prefix=api_key[:8] if len(api_key) >= 8 else api_key)
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        logger.warning("expired_api_key", key_id=api_key_obj.id)
        raise HTTPException(status_code=401, detail="API key expired")
    
    # Update usage stats
    api_key_obj.last_used_at = datetime.utcnow()
    api_key_obj.total_requests += 1
    await db.commit()
    
    logger.info("api_key_authenticated", key_id=api_key_obj.id, name=api_key_obj.name)
    return api_key_obj


def require_api_key(
    api_key: Optional[APIKey] = Depends(get_api_key),
) -> APIKey:
    """Require a valid API key"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def require_scope(required_scope: str):
    """Factory for scope requirement dependency"""
    def _require_scope(api_key: APIKey = Depends(require_api_key)) -> APIKey:
        if required_scope not in api_key.scopes:
            logger.warning(
                "insufficient_scope",
                key_id=api_key.id,
                required=required_scope,
                available=api_key.scopes,
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient scope. Required: {required_scope}",
            )
        return api_key
    return _require_scope


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return LLMService()


class PerformanceMiddleware:
    """Middleware for tracking request performance"""
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        # Add request ID to context
        response = await call_next(request)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        perf_logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        
        return response

