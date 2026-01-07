"""Analysis task and result models"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, Boolean, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisStatus(str, Enum):
    """Analysis task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisTask(Base):
    """Background analysis task"""
    __tablename__ = "analysis_tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Task configuration
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), comment="群组ID")
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("prompt_templates.id"), nullable=True, comment="模板ID")
    
    # Time range
    start_date: Mapped[datetime] = mapped_column(DateTime, comment="分析开始日期")
    end_date: Mapped[datetime] = mapped_column(DateTime, comment="分析结束日期")
    
    # Filters
    member_filter: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="成员过滤")
    keyword_filter: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="关键词过滤")
    
    # Status
    status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus), 
        default=AnalysisStatus.PENDING,
        comment="任务状态"
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, comment="进度百分比")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Request info
    requested_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="请求者")
    api_key_id: Mapped[Optional[int]] = mapped_column(ForeignKey("api_keys.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AnalysisTask(id={self.id}, group_id={self.group_id}, status={self.status})>"


class AnalysisResult(Base):
    """Analysis result storage"""
    __tablename__ = "analysis_results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # References
    task_id: Mapped[int] = mapped_column(ForeignKey("analysis_tasks.id"), comment="任务ID")
    execution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("prompt_executions.id"), nullable=True)
    
    # Result content
    summary: Mapped[str] = mapped_column(Text, comment="分析摘要")
    detailed_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="详细分析")
    
    # Structured data
    key_insights: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="关键洞察")
    statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="统计数据")
    trends: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="趋势分析")
    member_contributions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="成员贡献度")
    
    # Metadata
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="置信度评分")
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="标签")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, task_id={self.task_id})>"

