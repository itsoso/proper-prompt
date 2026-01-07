"""Evaluation API routes"""
import time
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import get_logger, get_performance_logger
from app.models.prompt import PromptEvaluation
from app.schemas.prompt import (
    PromptEvaluationCreate,
    PromptEvaluationResponse,
    PromptComparisonRequest,
)
from app.services.evaluation_service import EvaluationService
from app.services.llm_service import LLMService
from app.api.deps import get_llm_service

logger = get_logger(__name__)
perf_logger = get_performance_logger()
router = APIRouter()


class ManualScoreRequest(BaseModel):
    """Request for adding manual scores"""
    execution_id: int
    scores: Dict[str, float]


@router.post("", response_model=PromptEvaluationResponse, status_code=201)
async def create_evaluation(
    request: PromptEvaluationCreate,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Create a new evaluation comparing multiple executions"""
    start_time = time.time()
    
    evaluation_service = EvaluationService(db, llm_service)
    
    try:
        evaluation = await evaluation_service.create_evaluation(
            name=request.name,
            description=request.description,
            execution_ids=request.execution_ids,
            criteria=request.criteria,
            auto_evaluate=True,
        )
        
        perf_logger.info(
            "api_create_evaluation",
            evaluation_id=evaluation.id,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return PromptEvaluationResponse.model_validate(evaluation)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[PromptEvaluationResponse])
async def list_evaluations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all evaluations"""
    result = await db.execute(
        select(PromptEvaluation)
        .order_by(PromptEvaluation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    evaluations = result.scalars().all()
    
    return [PromptEvaluationResponse.model_validate(e) for e in evaluations]


@router.get("/{evaluation_id}", response_model=PromptEvaluationResponse)
async def get_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an evaluation by ID"""
    result = await db.execute(
        select(PromptEvaluation).where(PromptEvaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    return PromptEvaluationResponse.model_validate(evaluation)


@router.post("/{evaluation_id}/score", response_model=PromptEvaluationResponse)
async def add_manual_score(
    evaluation_id: int,
    request: ManualScoreRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Add or update manual scores for an execution in an evaluation"""
    evaluation_service = EvaluationService(db, llm_service)
    
    try:
        evaluation = await evaluation_service.manual_score(
            evaluation_id=evaluation_id,
            execution_id=request.execution_id,
            scores=request.scores,
        )
        
        logger.info(
            "manual_score_added",
            evaluation_id=evaluation_id,
            execution_id=request.execution_id
        )
        
        return PromptEvaluationResponse.model_validate(evaluation)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare", response_model=dict)
async def compare_prompts(
    request: PromptComparisonRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Compare multiple prompts by executing them and evaluating results"""
    start_time = time.time()
    
    if not request.chat_data:
        raise HTTPException(status_code=400, detail="chat_data is required for comparison")
    
    evaluation_service = EvaluationService(db, llm_service)
    
    try:
        result = await evaluation_service.compare_prompts(
            template_ids=request.template_ids,
            chat_content=request.chat_data,
            group_id=request.group_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        perf_logger.info(
            "api_compare_prompts",
            template_count=len(request.template_ids),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{evaluation_id}", status_code=204)
async def delete_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an evaluation"""
    result = await db.execute(
        select(PromptEvaluation).where(PromptEvaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    await db.delete(evaluation)
    await db.commit()
    
    logger.info("evaluation_deleted", evaluation_id=evaluation_id)

