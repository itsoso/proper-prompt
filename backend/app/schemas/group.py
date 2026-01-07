"""Group-related Pydantic schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.group import GroupType


class GroupBase(BaseModel):
    """Base group schema"""
    name: str = Field(..., min_length=1, max_length=255, description="群组名称")
    type: GroupType = Field(default=GroupType.CUSTOM, description="群组类型")
    description: Optional[str] = Field(None, description="群组描述")
    member_count: int = Field(default=0, ge=0, description="成员数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class GroupCreate(GroupBase):
    """Schema for creating a group"""
    external_id: str = Field(..., min_length=1, max_length=255, description="外部系统群组ID")
    custom_prompt_template: Optional[str] = Field(None, description="自定义Prompt模板")


class GroupUpdate(BaseModel):
    """Schema for updating a group"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[GroupType] = None
    description: Optional[str] = None
    member_count: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    custom_prompt_template: Optional[str] = None
    is_active: Optional[bool] = None


class GroupResponse(GroupBase):
    """Schema for group response"""
    id: int
    external_id: str
    custom_prompt_template: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """Schema for paginated group list"""
    items: List[GroupResponse]
    total: int
    page: int
    size: int
    pages: int

