"""Evaluation service for comparing prompts"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.prompt import PromptExecution, PromptEvaluation
from app.services.llm_service import LLMService
from app.core.logging import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class EvaluationService:
    """Service for evaluating and comparing prompt executions"""
    
    def __init__(self, db: AsyncSession, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm_service = llm_service or LLMService()
    
    async def create_evaluation(
        self,
        name: str,
        execution_ids: List[int],
        criteria: Optional[Dict[str, float]] = None,
        description: Optional[str] = None,
        auto_evaluate: bool = True,
    ) -> PromptEvaluation:
        """Create a new evaluation comparing multiple executions"""
        start_time = time.time()
        
        # 默认评测标准
        if not criteria:
            criteria = {
                "relevance": 0.25,
                "accuracy": 0.25,
                "completeness": 0.25,
                "readability": 0.25,
            }
        
        # 获取执行记录
        executions = []
        for exec_id in execution_ids:
            result = await self.db.execute(
                select(PromptExecution).where(PromptExecution.id == exec_id)
            )
            execution = result.scalar_one_or_none()
            if execution:
                executions.append(execution)
        
        if len(executions) < 2:
            raise ValueError("At least 2 valid executions required for evaluation")
        
        # 创建评测记录
        evaluation = PromptEvaluation(
            name=name,
            description=description,
            execution_ids=execution_ids,
            criteria=criteria,
            scores={},
            auto_evaluated=auto_evaluate,
        )
        
        self.db.add(evaluation)
        await self.db.flush()
        
        # 自动评测
        if auto_evaluate:
            await self._run_auto_evaluation(evaluation, executions)
        
        await self.db.commit()
        await self.db.refresh(evaluation)
        
        logger.info(
            "evaluation_created",
            evaluation_id=evaluation.id,
            execution_count=len(executions),
            auto_evaluated=auto_evaluate,
        )
        
        perf_logger.info(
            "create_evaluation",
            evaluation_id=evaluation.id,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return evaluation
    
    async def _run_auto_evaluation(
        self,
        evaluation: PromptEvaluation,
        executions: List[PromptExecution],
    ):
        """Run automatic evaluation using LLM"""
        start_time = time.time()
        
        # 收集所有响应
        responses = [exec.response or "" for exec in executions]
        
        # 使用第一个执行的prompt作为原始问题
        original_prompt = executions[0].rendered_prompt
        
        try:
            # 调用LLM评估
            eval_result = await self.llm_service.evaluate_responses(
                original_prompt=original_prompt,
                responses=responses,
                criteria=evaluation.criteria,
            )
            
            if "error" in eval_result:
                logger.error("auto_evaluation_failed", error=eval_result["error"])
                return
            
            # 解析评估结果
            scores = eval_result.get("scores", [])
            
            # 构建评分字典
            evaluation.scores = {
                str(exec.id): score 
                for exec, score in zip(executions, scores)
            }
            
            # 提取各维度评分
            if scores:
                evaluation.relevance_scores = {
                    str(exec.id): score.get("relevance", 0)
                    for exec, score in zip(executions, scores)
                }
                evaluation.accuracy_scores = {
                    str(exec.id): score.get("accuracy", 0)
                    for exec, score in zip(executions, scores)
                }
                evaluation.completeness_scores = {
                    str(exec.id): score.get("completeness", 0)
                    for exec, score in zip(executions, scores)
                }
                evaluation.readability_scores = {
                    str(exec.id): score.get("readability", 0)
                    for exec, score in zip(executions, scores)
                }
            
            # 设置获胜者
            winner_idx = eval_result.get("winner", 1) - 1  # 转换为0-based索引
            if 0 <= winner_idx < len(executions):
                evaluation.winner_execution_id = executions[winner_idx].id
            
            # 保存评估备注
            evaluation.evaluator_notes = eval_result.get("reasoning", "")
            
            logger.info(
                "auto_evaluation_completed",
                evaluation_id=evaluation.id,
                winner_id=evaluation.winner_execution_id,
            )
            
        except Exception as e:
            logger.error("auto_evaluation_error", evaluation_id=evaluation.id, error=str(e))
        
        perf_logger.info(
            "auto_evaluation",
            evaluation_id=evaluation.id,
            duration_ms=int((time.time() - start_time) * 1000)
        )
    
    async def manual_score(
        self,
        evaluation_id: int,
        execution_id: int,
        scores: Dict[str, float],
    ) -> PromptEvaluation:
        """Add or update manual scores for an execution"""
        result = await self.db.execute(
            select(PromptEvaluation).where(PromptEvaluation.id == evaluation_id)
        )
        evaluation = result.scalar_one_or_none()
        
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")
        
        if execution_id not in evaluation.execution_ids:
            raise ValueError(f"Execution {execution_id} not part of this evaluation")
        
        # 更新评分
        exec_key = str(execution_id)
        if not evaluation.scores:
            evaluation.scores = {}
        evaluation.scores[exec_key] = scores
        
        # 更新各维度评分
        if "relevance" in scores:
            if not evaluation.relevance_scores:
                evaluation.relevance_scores = {}
            evaluation.relevance_scores[exec_key] = scores["relevance"]
        
        if "accuracy" in scores:
            if not evaluation.accuracy_scores:
                evaluation.accuracy_scores = {}
            evaluation.accuracy_scores[exec_key] = scores["accuracy"]
        
        if "completeness" in scores:
            if not evaluation.completeness_scores:
                evaluation.completeness_scores = {}
            evaluation.completeness_scores[exec_key] = scores["completeness"]
        
        if "readability" in scores:
            if not evaluation.readability_scores:
                evaluation.readability_scores = {}
            evaluation.readability_scores[exec_key] = scores["readability"]
        
        # 重新计算获胜者
        await self._recalculate_winner(evaluation)
        
        await self.db.commit()
        await self.db.refresh(evaluation)
        
        logger.info(
            "manual_score_added",
            evaluation_id=evaluation_id,
            execution_id=execution_id,
        )
        
        return evaluation
    
    async def _recalculate_winner(self, evaluation: PromptEvaluation):
        """Recalculate the winner based on weighted scores"""
        if not evaluation.scores:
            return
        
        best_score = -1
        winner_id = None
        
        for exec_id, scores in evaluation.scores.items():
            if isinstance(scores, dict):
                # 计算加权总分
                total = sum(
                    scores.get(criterion, 0) * weight
                    for criterion, weight in evaluation.criteria.items()
                )
            else:
                total = float(scores) if scores else 0
            
            if total > best_score:
                best_score = total
                winner_id = int(exec_id)
        
        evaluation.winner_execution_id = winner_id
    
    async def get_evaluation(self, evaluation_id: int) -> Optional[PromptEvaluation]:
        """Get an evaluation by ID"""
        result = await self.db.execute(
            select(PromptEvaluation).where(PromptEvaluation.id == evaluation_id)
        )
        return result.scalar_one_or_none()
    
    async def list_evaluations(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[PromptEvaluation]:
        """List evaluations with pagination"""
        result = await self.db.execute(
            select(PromptEvaluation)
            .order_by(PromptEvaluation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def compare_prompts(
        self,
        template_ids: List[int],
        chat_content: str,
        group_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compare multiple prompts by executing them and evaluating results"""
        from app.services.prompt_service import PromptService
        
        start_time = time.time()
        prompt_service = PromptService(self.db, self.llm_service)
        
        executions = []
        
        for template_id in template_ids:
            template = await prompt_service.get_template(template_id)
            if not template:
                continue
            
            # 渲染并执行每个模板
            rendered = prompt_service.render_prompt(
                template=template.user_prompt_template,
                chat_content=chat_content,
                start_date=start_date,
                end_date=end_date,
            )
            
            execution = await prompt_service.execute_prompt(
                template_id=template_id,
                group_id=group_id,
                rendered_prompt=rendered,
                variables_used={"chat_content_length": len(chat_content)},
                start_date=start_date,
                end_date=end_date,
                system_prompt=template.system_prompt,
            )
            executions.append(execution)
        
        if len(executions) < 2:
            raise ValueError("Need at least 2 valid templates for comparison")
        
        # 创建评测
        evaluation = await self.create_evaluation(
            name=f"Prompt Comparison {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            execution_ids=[e.id for e in executions],
            auto_evaluate=True,
        )
        
        perf_logger.info(
            "compare_prompts",
            template_count=len(template_ids),
            execution_count=len(executions),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return {
            "executions": [
                {
                    "id": e.id,
                    "template_id": e.template_id,
                    "response": e.response,
                    "tokens": e.tokens_input + e.tokens_output,
                    "latency_ms": e.latency_ms,
                }
                for e in executions
            ],
            "evaluation": {
                "id": evaluation.id,
                "scores": evaluation.scores,
                "winner_id": evaluation.winner_execution_id,
                "notes": evaluation.evaluator_notes,
            }
        }

