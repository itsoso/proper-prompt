"""Analysis API routes"""
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import get_logger, get_performance_logger
from app.models.analysis import AnalysisTask, AnalysisResult, AnalysisStatus
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisTaskResponse,
    AnalysisResultResponse,
    QuickAnalysisRequest,
    QuickAnalysisResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMService
from app.api.deps import get_llm_service

logger = get_logger(__name__)
perf_logger = get_performance_logger()
router = APIRouter()


@router.post("/tasks", response_model=AnalysisTaskResponse, status_code=201)
async def create_analysis_task(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Create a new analysis task"""
    analysis_service = AnalysisService(db, llm_service)
    
    task = await analysis_service.create_analysis_task(
        group_id=request.group_id,
        template_id=request.template_id,
        start_date=request.start_date,
        end_date=request.end_date,
        member_filter=request.member_filter,
        keyword_filter=request.keyword_filter,
    )
    
    logger.info("analysis_task_created", task_id=task.id)
    
    return AnalysisTaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/run", response_model=AnalysisResultResponse)
async def run_analysis_task(
    task_id: int,
    chat_content: str,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Run an analysis task with provided chat content"""
    start_time = time.time()
    
    analysis_service = AnalysisService(db, llm_service)
    
    try:
        result = await analysis_service.run_analysis(
            task_id=task_id,
            chat_content=chat_content,
        )
        
        perf_logger.info(
            "api_run_analysis",
            task_id=task_id,
            result_id=result.id,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return AnalysisResultResponse.model_validate(result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("run_analysis_failed", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/tasks", response_model=List[AnalysisTaskResponse])
async def list_analysis_tasks(
    group_id: Optional[int] = None,
    status: Optional[AnalysisStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List analysis tasks with filtering"""
    query = select(AnalysisTask).order_by(AnalysisTask.created_at.desc())
    
    if group_id:
        query = query.where(AnalysisTask.group_id == group_id)
    if status:
        query = query.where(AnalysisTask.status == status)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [AnalysisTaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=AnalysisTaskResponse)
async def get_analysis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an analysis task by ID"""
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return AnalysisTaskResponse.model_validate(task)


@router.get("/tasks/{task_id}/result", response_model=AnalysisResultResponse)
async def get_task_result(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the result of an analysis task"""
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.task_id == task_id)
    )
    analysis_result = result.scalar_one_or_none()
    
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return AnalysisResultResponse.model_validate(analysis_result)


@router.post("/quick", response_model=QuickAnalysisResponse)
async def quick_analysis(
    request: QuickAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Perform quick inline analysis without creating a task"""
    start_time = time.time()
    
    analysis_service = AnalysisService(db, llm_service)
    
    result = await analysis_service.quick_analysis(
        group_type=request.group_type,
        chat_content=request.chat_content,
        time_period=request.time_period,
        focus_members=request.focus_members,
        analysis_focus=request.analysis_focus,
    )
    
    perf_logger.info(
        "api_quick_analysis",
        group_type=request.group_type,
        duration_ms=int((time.time() - start_time) * 1000)
    )
    
    return QuickAnalysisResponse(**result)


@router.get("/results", response_model=List[AnalysisResultResponse])
async def list_analysis_results(
    task_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List analysis results"""
    query = select(AnalysisResult).order_by(AnalysisResult.created_at.desc())
    
    if task_id:
        query = query.where(AnalysisResult.task_id == task_id)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    results = result.scalars().all()
    
    return [AnalysisResultResponse.model_validate(r) for r in results]


@router.get("/results/{result_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an analysis result by ID"""
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == result_id)
    )
    analysis_result = result.scalar_one_or_none()
    
    if not analysis_result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return AnalysisResultResponse.model_validate(analysis_result)

