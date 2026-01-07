"""API Key model for external integrations"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class APIKey(Base):
    """API Key for external access"""
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Key info
    name: Mapped[str] = mapped_column(String(255), comment="API密钥名称")
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment="密钥哈希")
    prefix: Mapped[str] = mapped_column(String(10), comment="密钥前缀(用于显示)")
    
    # Permissions
    scopes: Mapped[list] = mapped_column(JSON, default=["read"], comment="权限范围")
    
    # Usage limits
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000, comment="每小时请求限制")
    monthly_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="每月请求限制")
    
    # Tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    
    # Integration info
    integration_type: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True, 
        comment="集成类型: browser-llm-orchestrator, chatlog, health-llm-driven"
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Webhook回调URL")
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.prefix}...)>"

