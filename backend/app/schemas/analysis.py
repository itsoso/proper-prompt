"""Analysis-related Pydantic schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.analysis import AnalysisStatus
from app.models.prompt import TimeGranularity


class AnalysisRequest(BaseModel):
    """Schema for requesting an analysis"""
    group_id: int = Field(..., description="群组ID")
    template_id: Optional[int] = Field(None, description="指定使用的模板ID")
    
    # Time range
    start_date: datetime = Field(..., description="分析开始日期")
    end_date: datetime = Field(..., description="分析结束日期")
    time_granularity: Optional[TimeGranularity] = Field(None, description="时间粒度")
    
    # Filters
    member_filter: Optional[List[str]] = Field(None, description="成员过滤列表")
    keyword_filter: Optional[List[str]] = Field(None, description="关键词过滤")
    
    # Options
    generate_multiple_prompts: bool = Field(default=False, description="是否生成多个Prompt进行比较")
    auto_evaluate: bool = Field(default=False, description="是否自动评测")


class AnalysisTaskResponse(BaseModel):
    """Schema for analysis task response"""
    id: int
    group_id: int
    template_id: Optional[int]
    start_date: datetime
    end_date: datetime
    member_filter: Optional[List[str]]
    keyword_filter: Optional[List[str]]
    status: AnalysisStatus
    progress: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    """Schema for analysis result response"""
    id: int
    task_id: int
    execution_id: Optional[int]
    summary: str
    detailed_analysis: Optional[str]
    key_insights: Optional[List[str]]
    statistics: Optional[Dict[str, Any]]
    trends: Optional[Dict[str, Any]]
    member_contributions: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    tags: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuickAnalysisRequest(BaseModel):
    """Schema for quick inline analysis (without task queue)"""
    group_type: str = Field(..., description="群组类型")
    chat_content: str = Field(..., min_length=1, description="聊天内容")
    time_period: Optional[str] = Field(None, description="时间段描述，如 '今天', '本周', '本月'")
    focus_members: Optional[List[str]] = Field(None, description="关注的成员列表")
    analysis_focus: Optional[str] = Field(None, description="分析重点，如 '话题热度', '成员活跃度'")
    custom_prompt: Optional[str] = Field(None, description="自定义Prompt模板，使用{chat_content}、{time_period}等变量")


class QuickAnalysisResponse(BaseModel):
    """Schema for quick analysis response"""
    prompt_used: str
    analysis: str
    key_points: List[str]
    execution_time_ms: int
    tokens_used: int

