"""Group models for chat group management"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GroupType(str, Enum):
    """Types of chat groups"""
    INVESTMENT = "investment"       # 投资群
    SCIENCE = "science"            # 科普群
    LEARNING = "learning"          # 学习群
    TECHNOLOGY = "technology"      # 技术群
    LIFESTYLE = "lifestyle"        # 生活群
    NEWS = "news"                  # 新闻群
    ENTERTAINMENT = "entertainment" # 娱乐群
    HEALTH = "health"              # 健康群
    BUSINESS = "business"          # 商务群
    CUSTOM = "custom"              # 自定义


class Group(Base):
    """Chat group model"""
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment="外部系统群组ID")
    name: Mapped[str] = mapped_column(String(255), comment="群组名称")
    type: Mapped[GroupType] = mapped_column(SQLEnum(GroupType), default=GroupType.CUSTOM, comment="群组类型")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="群组描述")
    
    # Group info
    member_count: Mapped[int] = mapped_column(Integer, default=0, comment="成员数量")
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="额外元数据")
    
    # Prompt configuration
    custom_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="自定义Prompt模板")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name={self.name}, type={self.type})>"

