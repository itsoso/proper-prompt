"""Prompt template and execution API routes"""
import time
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.logging import get_logger, get_performance_logger
from app.models.group import GroupType
from app.models.prompt import PromptTemplate, PromptExecution, TimeGranularity, PromptStyle
from app.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptExecutionCreate,
    PromptExecutionResponse,
    GeneratePromptsRequest,
    GeneratePromptsResponse,
)
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService
from app.api.deps import get_llm_service

logger = get_logger(__name__)
perf_logger = get_performance_logger()
router = APIRouter()


@router.get("/templates", response_model=List[PromptTemplateResponse])
async def list_templates(
    group_type: Optional[GroupType] = None,
    time_granularity: Optional[TimeGranularity] = None,
    style: Optional[PromptStyle] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all prompt templates with optional filtering"""
    query = select(PromptTemplate).where(PromptTemplate.is_active == True)
    
    if group_type:
        query = query.where(PromptTemplate.group_type == group_type)
    if time_granularity:
        query = query.where(PromptTemplate.time_granularity == time_granularity)
    if style:
        query = query.where(PromptTemplate.style == style)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [PromptTemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=PromptTemplateResponse, status_code=201)
async def create_template(
    template_data: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new prompt template"""
    template = PromptTemplate(**template_data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    logger.info("template_created", template_id=template.id, name=template.name)
    return PromptTemplateResponse.model_validate(template)


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID"""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return PromptTemplateResponse.model_validate(template)


@router.patch("/templates/{template_id}", response_model=PromptTemplateResponse)
async def update_template(
    template_id: int,
    template_data: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a template"""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    # Increment version
    template.version += 1
    
    await db.commit()
    await db.refresh(template)
    
    logger.info("template_updated", template_id=template_id, version=template.version)
    return PromptTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a template"""
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    await db.commit()
    
    logger.info("template_deleted", template_id=template_id)


@router.post("/execute", response_model=PromptExecutionResponse)
async def execute_prompt(
    execution_data: PromptExecutionCreate,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Execute a prompt and get LLM response"""
    start_time = time.time()
    
    prompt_service = PromptService(db, llm_service)
    
    # Get template
    template = await prompt_service.get_template(execution_data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Render prompt
    chat_content = execution_data.variables.get("chat_content", "") or execution_data.chat_data or ""
    
    rendered = prompt_service.render_prompt(
        template=template.user_prompt_template,
        chat_content=chat_content,
        start_date=execution_data.start_date,
        end_date=execution_data.end_date,
        member_filter=execution_data.member_filter,
        extra_variables=execution_data.variables,
    )
    
    # Execute
    execution = await prompt_service.execute_prompt(
        template_id=execution_data.template_id,
        group_id=execution_data.group_id,
        rendered_prompt=rendered,
        variables_used=execution_data.variables,
        start_date=execution_data.start_date,
        end_date=execution_data.end_date,
        member_filter=execution_data.member_filter,
        system_prompt=template.system_prompt,
    )
    
    perf_logger.info(
        "api_execute_prompt",
        execution_id=execution.id,
        duration_ms=int((time.time() - start_time) * 1000)
    )
    
    return PromptExecutionResponse.model_validate(execution)


@router.get("/executions", response_model=List[PromptExecutionResponse])
async def list_executions(
    template_id: Optional[int] = None,
    group_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List prompt executions with filtering"""
    query = select(PromptExecution).order_by(PromptExecution.created_at.desc())
    
    if template_id:
        query = query.where(PromptExecution.template_id == template_id)
    if group_id:
        query = query.where(PromptExecution.group_id == group_id)
    if status:
        query = query.where(PromptExecution.status == status)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [PromptExecutionResponse.model_validate(e) for e in executions]


@router.get("/executions/{execution_id}", response_model=PromptExecutionResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an execution by ID"""
    result = await db.execute(
        select(PromptExecution).where(PromptExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return PromptExecutionResponse.model_validate(execution)


@router.post("/generate", response_model=GeneratePromptsResponse)
async def generate_prompts(
    request: GeneratePromptsRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate multiple prompt variants for a given scenario"""
    start_time = time.time()
    
    prompt_service = PromptService(db, llm_service)
    
    variants = await prompt_service.generate_prompt_variants(
        group_type=request.group_type,
        time_granularity=request.time_granularity,
        styles=request.styles,
        custom_requirements=request.custom_requirements,
    )
    
    # 创建临时模板响应
    prompts = []
    for i, variant in enumerate(variants):
        # 创建一个临时的模板对象用于响应
        temp_template = PromptTemplate(
            id=-(i + 1),  # 负数表示临时ID
            name=f"Generated {variant['style']} template",
            description=f"Auto-generated {variant['style']} style template for {variant['group_type']}",
            group_type=GroupType(variant['group_type']),
            time_granularity=TimeGranularity(variant['time_granularity']),
            style=PromptStyle(variant['style']) if variant['style'] != 'custom' else PromptStyle.ANALYTICAL,
            system_prompt="你是一个专业的群聊分析助手。",
            user_prompt_template=variant['template'],
            is_active=True,
            is_default=False,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        prompts.append(PromptTemplateResponse.model_validate(temp_template))
    
    generation_time = int((time.time() - start_time) * 1000)
    
    logger.info(
        "prompts_generated",
        group_type=request.group_type.value,
        count=len(prompts),
        generation_time_ms=generation_time
    )
    
    return GeneratePromptsResponse(
        prompts=prompts,
        generation_time_ms=generation_time
    )


@router.get("/builtin", response_model=List[dict])
async def list_builtin_templates():
    """List all built-in prompt templates"""
    from app.services.prompt_service import PROMPT_TEMPLATES
    
    result = []
    for group_type, granularities in PROMPT_TEMPLATES.items():
        for granularity, styles in granularities.items():
            for style, template in styles.items():
                result.append({
                    "group_type": group_type.value,
                    "time_granularity": granularity.value,
                    "style": style.value,
                    "template": template,
                })
    
    return result

