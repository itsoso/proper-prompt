"""Prompt template and execution models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, Boolean, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.group import GroupType


class TimeGranularity(str, Enum):
    """Time granularity for analysis"""
    DAILY = "daily"          # 天级别
    WEEKLY = "weekly"        # 周级别
    MONTHLY = "monthly"      # 月级别
    QUARTERLY = "quarterly"  # 季度级别
    YEARLY = "yearly"        # 年级别
    CUSTOM = "custom"        # 自定义日期范围


class PromptStyle(str, Enum):
    """Different styles of prompts"""
    ANALYTICAL = "analytical"      # 分析型
    SUMMARY = "summary"            # 总结型
    INSIGHT = "insight"            # 洞察型
    COMPARATIVE = "comparative"    # 对比型
    TRENDING = "trending"          # 趋势型
    MEMBER_FOCUSED = "member_focused"  # 成员聚焦型


class PromptTemplate(Base):
    """Prompt template model"""
    __tablename__ = "prompt_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), comment="模板名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="模板描述")
    
    # Template configuration
    group_type: Mapped[GroupType] = mapped_column(SQLEnum(GroupType), comment="适用群组类型")
    time_granularity: Mapped[TimeGranularity] = mapped_column(SQLEnum(TimeGranularity), comment="时间粒度")
    style: Mapped[PromptStyle] = mapped_column(SQLEnum(PromptStyle), default=PromptStyle.ANALYTICAL, comment="Prompt风格")
    
    # Template content
    system_prompt: Mapped[str] = mapped_column(Text, comment="系统提示词")
    user_prompt_template: Mapped[str] = mapped_column(Text, comment="用户提示词模板")
    
    # Variables
    required_variables: Mapped[Optional[list]] = mapped_column(JSON, default=list, comment="必需变量列表")
    optional_variables: Mapped[Optional[list]] = mapped_column(JSON, default=list, comment="可选变量列表")
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为默认模板")
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<PromptTemplate(id={self.id}, name={self.name}, group_type={self.group_type})>"


class PromptExecution(Base):
    """Record of prompt execution"""
    __tablename__ = "prompt_executions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # References
    template_id: Mapped[int] = mapped_column(ForeignKey("prompt_templates.id"), comment="模板ID")
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"), nullable=True, comment="群组ID")
    
    # Execution context
    rendered_prompt: Mapped[str] = mapped_column(Text, comment="渲染后的Prompt")
    variables_used: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="使用的变量")
    
    # Time range
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="分析开始日期")
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="分析结束日期")
    member_filter: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="成员过滤列表")
    
    # LLM response
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="LLM响应")
    model_used: Mapped[str] = mapped_column(String(100), comment="使用的模型")
    
    # Performance metrics
    tokens_input: Mapped[int] = mapped_column(Integer, default=0, comment="输入token数")
    tokens_output: Mapped[int] = mapped_column(Integer, default=0, comment="输出token数")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, comment="响应延迟(毫秒)")
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", comment="执行状态")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误信息")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<PromptExecution(id={self.id}, template_id={self.template_id}, status={self.status})>"


class PromptEvaluation(Base):
    """Evaluation results for prompt comparisons"""
    __tablename__ = "prompt_evaluations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Evaluation context
    name: Mapped[str] = mapped_column(String(255), comment="评测名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="评测描述")
    
    # Executions being compared
    execution_ids: Mapped[list] = mapped_column(JSON, comment="参与评测的执行ID列表")
    
    # Evaluation criteria and scores
    criteria: Mapped[dict] = mapped_column(JSON, comment="评测标准")
    scores: Mapped[dict] = mapped_column(JSON, comment="评分结果")
    
    # Metrics
    relevance_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="相关性评分")
    accuracy_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="准确性评分")
    completeness_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="完整性评分")
    readability_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="可读性评分")
    
    # Winner
    winner_execution_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="胜出的执行ID")
    
    # Metadata
    evaluator_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="评测备注")
    auto_evaluated: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否自动评测")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<PromptEvaluation(id={self.id}, name={self.name})>"

