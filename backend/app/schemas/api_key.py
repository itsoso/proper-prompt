"""API Key Pydantic schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str = Field(..., min_length=1, max_length=255, description="API密钥名称")
    scopes: List[str] = Field(default=["read"], description="权限范围")
    rate_limit: int = Field(default=1000, ge=1, description="每小时请求限制")
    monthly_limit: Optional[int] = Field(None, ge=1, description="每月请求限制")
    integration_type: Optional[str] = Field(
        None, 
        description="集成类型: browser-llm-orchestrator, chatlog, health-llm-driven"
    )
    webhook_url: Optional[str] = Field(None, description="Webhook回调URL")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class APIKeyResponse(BaseModel):
    """Schema for API key response"""
    id: int
    name: str
    prefix: str
    scopes: List[str]
    rate_limit: int
    monthly_limit: Optional[int]
    integration_type: Optional[str]
    webhook_url: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    total_requests: int
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """Schema for newly created API key (includes full key once)"""
    key: str = Field(..., description="完整的API密钥（仅在创建时返回一次）")


class APIKeyValidateRequest(BaseModel):
    """Schema for validating an API key"""
    key: str = Field(..., description="要验证的API密钥")


class APIKeyValidateResponse(BaseModel):
    """Schema for API key validation response"""
    valid: bool
    api_key_id: Optional[int] = None
    scopes: Optional[List[str]] = None
    rate_limit_remaining: Optional[int] = None

