"""External integration API routes for Browser-LLM-Orchestrator, chatlog, health-llm-driven"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger, get_performance_logger
from app.models.api_key import APIKey
from app.services.analysis_service import AnalysisService
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService
from app.api.deps import require_api_key, get_llm_service

logger = get_logger(__name__)
perf_logger = get_performance_logger()
router = APIRouter()


# ============== Browser-LLM-Orchestrator Integration ==============

class BrowserLLMRequest(BaseModel):
    """Request from Browser-LLM-Orchestrator"""
    task_type: str = Field(..., description="任务类型")
    content: str = Field(..., description="待分析内容")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    options: Optional[Dict[str, Any]] = Field(None, description="选项配置")


class BrowserLLMResponse(BaseModel):
    """Response for Browser-LLM-Orchestrator"""
    success: bool
    result: Optional[str] = None
    prompt_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/browser-llm/analyze", response_model=BrowserLLMResponse)
async def browser_llm_analyze(
    request: BrowserLLMRequest,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Analyze content from Browser-LLM-Orchestrator
    
    Supports task types:
    - page_summary: 网页摘要
    - content_analysis: 内容分析
    - chat_extraction: 聊天提取
    - sentiment_analysis: 情感分析
    """
    import time
    start_time = time.time()
    
    try:
        # 根据任务类型选择Prompt
        prompts = {
            "page_summary": """请对以下网页内容进行摘要：

{content}

请提供：
1. 核心内容概述（100字以内）
2. 关键信息点（3-5个）
3. 相关标签""",
            
            "content_analysis": """请分析以下内容：

{content}

请从以下维度分析：
1. 主题和类型
2. 核心观点
3. 情感倾向
4. 关键实体（人物、组织、地点等）""",
            
            "chat_extraction": """请从以下内容中提取聊天记录：

{content}

请识别：
1. 对话参与者
2. 对话主题
3. 关键信息
4. 时间线（如果有）""",
            
            "sentiment_analysis": """请分析以下内容的情感：

{content}

请评估：
1. 整体情感（正面/负面/中性）
2. 情感强度（1-10）
3. 主要情感类型（如喜悦、愤怒、悲伤等）
4. 情感变化趋势（如果有多段内容）""",
        }
        
        prompt_template = prompts.get(request.task_type)
        if not prompt_template:
            return BrowserLLMResponse(
                success=False,
                error=f"Unknown task type: {request.task_type}"
            )
        
        rendered_prompt = prompt_template.format(content=request.content)
        
        response, tokens_in, tokens_out = await llm_service.chat(
            system_prompt="你是一个专业的内容分析助手。请提供准确、结构化的分析结果。",
            user_message=rendered_prompt,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "browser_llm_analysis",
            api_key_id=api_key.id,
            task_type=request.task_type,
            duration_ms=duration_ms
        )
        
        return BrowserLLMResponse(
            success=True,
            result=response,
            prompt_used=rendered_prompt,
            metadata={
                "tokens_input": tokens_in,
                "tokens_output": tokens_out,
                "duration_ms": duration_ms,
                "task_type": request.task_type,
            }
        )
        
    except Exception as e:
        logger.error("browser_llm_error", error=str(e))
        return BrowserLLMResponse(success=False, error=str(e))


# ============== Chatlog Integration ==============

class ChatlogRequest(BaseModel):
    """Request from chatlog project"""
    platform: str = Field(..., description="聊天平台，如 wechat, telegram, whatsapp")
    group_name: str = Field(..., description="群组名称")
    group_type: Optional[str] = Field("custom", description="群组类型")
    messages: List[Dict[str, Any]] = Field(..., description="消息列表")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    analysis_type: str = Field("summary", description="分析类型: summary, detailed, trending, member")


class ChatlogResponse(BaseModel):
    """Response for chatlog project"""
    success: bool
    analysis: Optional[str] = None
    summary: Optional[str] = None
    key_insights: Optional[List[str]] = None
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/chatlog/analyze", response_model=ChatlogResponse)
async def chatlog_analyze(
    request: ChatlogRequest,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Analyze chat logs from chatlog project
    
    Supports multiple platforms and analysis types.
    """
    import time
    start_time = time.time()
    
    try:
        # 格式化消息为文本
        formatted_messages = []
        for msg in request.messages:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted_messages.append(f"[{timestamp}] {sender}: {content}")
        
        chat_content = "\n".join(formatted_messages)
        
        # 使用分析服务
        analysis_service = AnalysisService(db, llm_service)
        
        result = await analysis_service.quick_analysis(
            group_type=request.group_type or "custom",
            chat_content=chat_content,
            time_period=None,
            focus_members=None,
            analysis_focus=request.analysis_type,
        )
        
        # 统计信息
        stats = {
            "message_count": len(request.messages),
            "platform": request.platform,
            "group_name": request.group_name,
            "unique_senders": len(set(m.get("sender", "") for m in request.messages)),
            "analysis_duration_ms": int((time.time() - start_time) * 1000),
        }
        
        logger.info(
            "chatlog_analysis",
            api_key_id=api_key.id,
            platform=request.platform,
            message_count=len(request.messages)
        )
        
        return ChatlogResponse(
            success=True,
            analysis=result["analysis"],
            summary=result["analysis"][:500] if len(result["analysis"]) > 500 else result["analysis"],
            key_insights=result["key_points"],
            statistics=stats,
        )
        
    except Exception as e:
        logger.error("chatlog_error", error=str(e))
        return ChatlogResponse(success=False, error=str(e))


# ============== Health-LLM-Driven Integration ==============

class HealthLLMRequest(BaseModel):
    """Request from health-llm-driven project"""
    data_type: str = Field(..., description="数据类型: health_record, symptom, lifestyle, medication")
    content: str = Field(..., description="健康相关内容")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="用户档案")
    context: Optional[str] = Field(None, description="上下文说明")


class HealthLLMResponse(BaseModel):
    """Response for health-llm-driven project"""
    success: bool
    analysis: Optional[str] = None
    recommendations: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    disclaimer: str = "本分析仅供参考，不构成医疗建议。如有健康问题，请咨询专业医生。"
    error: Optional[str] = None


@router.post("/health-llm/analyze", response_model=HealthLLMResponse)
async def health_llm_analyze(
    request: HealthLLMRequest,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Analyze health-related content from health-llm-driven project
    
    Supports various health data types with appropriate prompts.
    """
    import time
    start_time = time.time()
    
    try:
        # 根据数据类型选择Prompt
        prompts = {
            "health_record": """请分析以下健康记录：

{content}

{user_context}

请提供：
1. 健康状况概述
2. 需要关注的指标
3. 可能的健康趋势
4. 一般性建议

注意：这是一般性分析，不构成医疗建议。""",
            
            "symptom": """请分析以下症状描述：

{content}

{user_context}

请提供：
1. 症状归类
2. 可能的相关因素
3. 建议的应对措施
4. 需要就医的情况

重要提示：如症状严重或持续，请立即就医。""",
            
            "lifestyle": """请分析以下生活方式信息：

{content}

{user_context}

请评估：
1. 生活方式健康度
2. 积极因素
3. 需要改善的方面
4. 具体改善建议""",
            
            "medication": """请分析以下用药信息：

{content}

{user_context}

请提供：
1. 用药情况概述
2. 注意事项提醒
3. 可能的相互作用（一般性信息）
4. 建议

警告：药物使用请遵医嘱，不要自行调整用药。"""
        }
        
        prompt_template = prompts.get(request.data_type)
        if not prompt_template:
            return HealthLLMResponse(
                success=False,
                error=f"Unknown data type: {request.data_type}"
            )
        
        # 构建用户上下文
        user_context = ""
        if request.user_profile:
            age = request.user_profile.get("age", "未知")
            gender = request.user_profile.get("gender", "未知")
            conditions = request.user_profile.get("conditions", [])
            user_context = f"用户信息：年龄{age}，性别{gender}"
            if conditions:
                user_context += f"，既往病史：{', '.join(conditions)}"
        
        if request.context:
            user_context += f"\n额外说明：{request.context}"
        
        rendered_prompt = prompt_template.format(
            content=request.content,
            user_context=user_context if user_context else "无额外用户信息"
        )
        
        response, tokens_in, tokens_out = await llm_service.chat(
            system_prompt="""你是一个健康信息分析助手。请提供准确、负责任的健康信息分析。
            
重要原则：
1. 始终强调这不是医疗建议
2. 建议用户咨询专业医生
3. 不做具体诊断
4. 保持信息的一般性和教育性""",
            user_message=rendered_prompt,
        )
        
        # 提取建议和风险因素
        recommendations = []
        risk_factors = []
        
        for line in response.split("\n"):
            line = line.strip()
            if "建议" in line or "应该" in line or "可以" in line:
                if len(line) > 10:
                    recommendations.append(line[:200])
            if "注意" in line or "风险" in line or "警告" in line or "危险" in line:
                if len(line) > 10:
                    risk_factors.append(line[:200])
        
        logger.info(
            "health_llm_analysis",
            api_key_id=api_key.id,
            data_type=request.data_type,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return HealthLLMResponse(
            success=True,
            analysis=response,
            recommendations=recommendations[:5] if recommendations else None,
            risk_factors=risk_factors[:5] if risk_factors else None,
        )
        
    except Exception as e:
        logger.error("health_llm_error", error=str(e))
        return HealthLLMResponse(success=False, error=str(e))


# ============== Generic Webhook Integration ==============

class WebhookRequest(BaseModel):
    """Generic webhook request"""
    event_type: str
    payload: Dict[str, Any]
    timestamp: Optional[datetime] = None


@router.post("/webhook/{integration_type}")
async def handle_webhook(
    integration_type: str,
    request: WebhookRequest,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Handle webhooks from integrated systems"""
    logger.info(
        "webhook_received",
        integration_type=integration_type,
        event_type=request.event_type,
        api_key_id=api_key.id
    )
    
    # 验证集成类型
    if api_key.integration_type and api_key.integration_type != integration_type:
        raise HTTPException(
            status_code=403,
            detail=f"API key not authorized for {integration_type}"
        )
    
    # TODO: 处理不同类型的webhook事件
    
    return {
        "received": True,
        "event_type": request.event_type,
        "integration_type": integration_type,
    }

