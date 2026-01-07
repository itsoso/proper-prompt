"""Prompt-related Pydantic schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.group import GroupType
from app.models.prompt import TimeGranularity, PromptStyle


class PromptTemplateBase(BaseModel):
    """Base prompt template schema"""
    name: str = Field(..., min_length=1, max_length=255, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    group_type: GroupType = Field(..., description="适用群组类型")
    time_granularity: TimeGranularity = Field(..., description="时间粒度")
    style: PromptStyle = Field(default=PromptStyle.ANALYTICAL, description="Prompt风格")
    system_prompt: str = Field(..., min_length=1, description="系统提示词")
    user_prompt_template: str = Field(..., min_length=1, description="用户提示词模板")
    required_variables: List[str] = Field(default_factory=list, description="必需变量列表")
    optional_variables: List[str] = Field(default_factory=list, description="可选变量列表")


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a prompt template"""
    is_default: bool = Field(default=False, description="是否为默认模板")


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    group_type: Optional[GroupType] = None
    time_granularity: Optional[TimeGranularity] = None
    style: Optional[PromptStyle] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PromptTemplateResponse(BaseModel):
    """Schema for prompt template response"""
    id: int
    name: str
    description: Optional[str] = None
    group_type: GroupType
    time_granularity: TimeGranularity
    style: PromptStyle
    system_prompt: str
    user_prompt_template: str
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    is_active: bool
    is_default: bool
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        # Convert None to empty list
        if data.get('required_variables') is None:
            data['required_variables'] = []
        if data.get('optional_variables') is None:
            data['optional_variables'] = []
        super().__init__(**data)


class PromptExecutionCreate(BaseModel):
    """Schema for creating a prompt execution"""
    template_id: int = Field(..., description="模板ID")
    group_id: Optional[int] = Field(None, description="群组ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量值")
    start_date: Optional[datetime] = Field(None, description="分析开始日期")
    end_date: Optional[datetime] = Field(None, description="分析结束日期")
    member_filter: Optional[List[str]] = Field(None, description="成员过滤列表")
    
    # Chat data (if provided directly)
    chat_data: Optional[str] = Field(None, description="聊天数据内容")


class PromptExecutionResponse(BaseModel):
    """Schema for prompt execution response"""
    id: int
    template_id: int
    group_id: Optional[int]
    rendered_prompt: str
    variables_used: Optional[Dict[str, Any]]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    member_filter: Optional[List[str]]
    response: Optional[str]
    model_used: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PromptComparisonRequest(BaseModel):
    """Schema for comparing multiple prompts"""
    template_ids: List[int] = Field(..., min_length=2, description="要比较的模板ID列表")
    group_id: Optional[int] = Field(None, description="群组ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="共享变量值")
    chat_data: Optional[str] = Field(None, description="聊天数据")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PromptEvaluationCreate(BaseModel):
    """Schema for creating a prompt evaluation"""
    name: str = Field(..., min_length=1, max_length=255, description="评测名称")
    description: Optional[str] = Field(None, description="评测描述")
    execution_ids: List[int] = Field(..., min_length=2, description="参与评测的执行ID列表")
    criteria: Dict[str, float] = Field(
        default_factory=lambda: {
            "relevance": 0.25,
            "accuracy": 0.25,
            "completeness": 0.25,
            "readability": 0.25,
        },
        description="评测标准权重"
    )


class PromptEvaluationResponse(BaseModel):
    """Schema for prompt evaluation response"""
    id: int
    name: str
    description: Optional[str]
    execution_ids: List[int]
    criteria: Dict[str, float]
    scores: Dict[str, Any]
    relevance_scores: Optional[Dict[str, float]]
    accuracy_scores: Optional[Dict[str, float]]
    completeness_scores: Optional[Dict[str, float]]
    readability_scores: Optional[Dict[str, float]]
    winner_execution_id: Optional[int]
    evaluator_notes: Optional[str]
    auto_evaluated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class GeneratePromptsRequest(BaseModel):
    """Schema for generating multiple prompt variants"""
    group_type: GroupType = Field(..., description="群组类型")
    time_granularity: TimeGranularity = Field(..., description="时间粒度")
    styles: List[PromptStyle] = Field(
        default_factory=lambda: [PromptStyle.ANALYTICAL, PromptStyle.SUMMARY, PromptStyle.INSIGHT],
        description="要生成的Prompt风格列表"
    )
    custom_requirements: Optional[str] = Field(None, description="自定义需求描述")


class GeneratePromptsResponse(BaseModel):
    """Schema for generated prompts response"""
    prompts: List[PromptTemplateResponse]
    generation_time_ms: int

