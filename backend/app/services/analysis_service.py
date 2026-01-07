"""Analysis service for group chat analysis"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.group import Group, GroupType
from app.models.prompt import TimeGranularity, PromptStyle
from app.models.analysis import AnalysisTask, AnalysisResult, AnalysisStatus
from app.services.prompt_service import PromptService
from app.services.llm_service import LLMService
from app.core.logging import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class AnalysisService:
    """Service for managing group chat analysis"""
    
    def __init__(self, db: AsyncSession, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm_service = llm_service or LLMService()
        self.prompt_service = PromptService(db, self.llm_service)
    
    async def create_analysis_task(
        self,
        group_id: int,
        start_date: datetime,
        end_date: datetime,
        template_id: Optional[int] = None,
        member_filter: Optional[List[str]] = None,
        keyword_filter: Optional[List[str]] = None,
        requested_by: Optional[str] = None,
        api_key_id: Optional[int] = None,
    ) -> AnalysisTask:
        """Create a new analysis task"""
        start_time = time.time()
        
        task = AnalysisTask(
            group_id=group_id,
            template_id=template_id,
            start_date=start_date,
            end_date=end_date,
            member_filter=member_filter,
            keyword_filter=keyword_filter,
            status=AnalysisStatus.PENDING,
            requested_by=requested_by,
            api_key_id=api_key_id,
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        logger.info(
            "analysis_task_created",
            task_id=task.id,
            group_id=group_id,
            date_range=f"{start_date} - {end_date}",
        )
        
        perf_logger.info(
            "create_analysis_task",
            task_id=task.id,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
        return task
    
    async def run_analysis(
        self,
        task_id: int,
        chat_content: str,
    ) -> AnalysisResult:
        """Run analysis for a task"""
        start_time = time.time()
        
        # 获取任务
        result = await self.db.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # 更新任务状态
        task.status = AnalysisStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.progress = 10
        await self.db.commit()
        
        try:
            # 获取群组信息
            group_result = await self.db.execute(
                select(Group).where(Group.id == task.group_id)
            )
            group = group_result.scalar_one_or_none()
            
            if not group:
                raise ValueError(f"Group {task.group_id} not found")
            
            task.progress = 20
            await self.db.commit()
            
            # 确定时间粒度
            time_granularity = self._determine_time_granularity(task.start_date, task.end_date)
            
            # 获取或生成Prompt模板
            if task.template_id:
                template = await self.prompt_service.get_template(task.template_id)
                if template:
                    prompt_template = template.user_prompt_template
                    system_prompt = template.system_prompt
                else:
                    prompt_template = self.prompt_service.get_builtin_template(
                        group.type, time_granularity, PromptStyle.ANALYTICAL
                    )
                    system_prompt = "你是一个专业的群聊分析助手。"
            else:
                prompt_template = self.prompt_service.get_builtin_template(
                    group.type, time_granularity, PromptStyle.ANALYTICAL
                )
                system_prompt = "你是一个专业的群聊分析助手。"
            
            # 如果没有匹配的模板，使用通用模板
            if not prompt_template:
                prompt_template = self._get_generic_template(time_granularity)
            
            task.progress = 40
            await self.db.commit()
            
            # 渲染Prompt
            rendered_prompt = self.prompt_service.render_prompt(
                template=prompt_template,
                chat_content=chat_content,
                start_date=task.start_date,
                end_date=task.end_date,
                member_filter=task.member_filter,
            )
            
            task.progress = 50
            await self.db.commit()
            
            # 执行Prompt
            execution = await self.prompt_service.execute_prompt(
                template_id=task.template_id,
                group_id=task.group_id,
                rendered_prompt=rendered_prompt,
                variables_used={
                    "start_date": task.start_date.isoformat(),
                    "end_date": task.end_date.isoformat(),
                    "member_filter": task.member_filter,
                },
                start_date=task.start_date,
                end_date=task.end_date,
                member_filter=task.member_filter,
                system_prompt=system_prompt,
            )
            
            task.progress = 80
            await self.db.commit()
            
            # 解析结果创建分析报告
            analysis_result = await self._parse_analysis_response(
                task_id=task.id,
                execution_id=execution.id,
                response=execution.response or "",
            )
            
            # 更新任务状态
            task.status = AnalysisStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info(
                "analysis_completed",
                task_id=task_id,
                result_id=analysis_result.id,
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
            return analysis_result
            
        except Exception as e:
            task.status = AnalysisStatus.FAILED
            task.error_message = str(e)
            await self.db.commit()
            
            logger.error("analysis_failed", task_id=task_id, error=str(e))
            raise
    
    async def quick_analysis(
        self,
        group_type: str,
        chat_content: str,
        time_period: Optional[str] = None,
        focus_members: Optional[List[str]] = None,
        analysis_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform quick inline analysis without creating a task"""
        start_time = time.time()
        
        # 转换群组类型
        try:
            gt = GroupType(group_type)
        except ValueError:
            gt = GroupType.CUSTOM
        
        # 确定时间粒度
        time_granularity = TimeGranularity.DAILY
        if time_period:
            if "月" in time_period:
                time_granularity = TimeGranularity.MONTHLY
            elif "周" in time_period:
                time_granularity = TimeGranularity.WEEKLY
            elif "季" in time_period:
                time_granularity = TimeGranularity.QUARTERLY
            elif "年" in time_period:
                time_granularity = TimeGranularity.YEARLY
        
        # 获取模板
        prompt_template = self.prompt_service.get_builtin_template(
            gt, time_granularity, PromptStyle.ANALYTICAL
        )
        
        if not prompt_template:
            prompt_template = self._get_generic_template(time_granularity)
        
        # 渲染Prompt
        now = datetime.utcnow()
        rendered_prompt = self.prompt_service.render_prompt(
            template=prompt_template,
            chat_content=chat_content,
            start_date=now,
            end_date=now,
            member_filter=focus_members,
            extra_variables={"analysis_focus": analysis_focus} if analysis_focus else None,
        )
        
        # 调用LLM
        response, tokens_in, tokens_out = await self.llm_service.chat(
            system_prompt="你是一个专业的群聊分析助手。请提供结构化的分析结果。",
            user_message=rendered_prompt,
        )
        
        # 提取关键点
        key_points = self._extract_key_points(response)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        perf_logger.info(
            "quick_analysis",
            group_type=group_type,
            duration_ms=duration_ms,
            tokens_used=tokens_in + tokens_out
        )
        
        return {
            "prompt_used": rendered_prompt,
            "analysis": response,
            "key_points": key_points,
            "execution_time_ms": duration_ms,
            "tokens_used": tokens_in + tokens_out,
        }
    
    def _determine_time_granularity(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> TimeGranularity:
        """Determine appropriate time granularity based on date range"""
        days = (end_date - start_date).days
        
        if days <= 1:
            return TimeGranularity.DAILY
        elif days <= 7:
            return TimeGranularity.WEEKLY
        elif days <= 31:
            return TimeGranularity.MONTHLY
        elif days <= 92:
            return TimeGranularity.QUARTERLY
        else:
            return TimeGranularity.YEARLY
    
    def _get_generic_template(self, time_granularity: TimeGranularity) -> str:
        """Get a generic analysis template"""
        period_desc = {
            TimeGranularity.DAILY: "今日",
            TimeGranularity.WEEKLY: "本周",
            TimeGranularity.MONTHLY: "本月",
            TimeGranularity.QUARTERLY: "本季度",
            TimeGranularity.YEARLY: "今年",
            TimeGranularity.CUSTOM: "指定时间段",
        }
        
        return f"""请分析以下群聊记录（{period_desc.get(time_granularity, '指定时间段')}）。

时间范围：{{start_date}} 至 {{end_date}}
{{member_filter_text}}

聊天记录：
{{chat_content}}

请从以下维度进行分析：
1. 主要讨论话题
2. 活跃成员和贡献度
3. 有价值的信息和观点
4. 群聊氛围和互动质量
5. 建议和总结"""
    
    async def _parse_analysis_response(
        self,
        task_id: int,
        execution_id: int,
        response: str,
    ) -> AnalysisResult:
        """Parse LLM response and create analysis result"""
        # 提取关键洞察
        key_insights = self._extract_key_points(response)
        
        # 创建分析结果
        result = AnalysisResult(
            task_id=task_id,
            execution_id=execution_id,
            summary=response[:500] + "..." if len(response) > 500 else response,
            detailed_analysis=response,
            key_insights=key_insights,
        )
        
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        
        return result
    
    def _extract_key_points(self, response: str) -> List[str]:
        """Extract key points from response text"""
        key_points = []
        lines = response.split("\n")
        
        for line in lines:
            line = line.strip()
            # 提取以数字或项目符号开头的要点
            if line and (
                line[0].isdigit() or 
                line.startswith("-") or 
                line.startswith("•") or
                line.startswith("*")
            ):
                # 清理格式
                point = line.lstrip("0123456789.-•* ")
                if len(point) > 10:  # 过滤太短的内容
                    key_points.append(point[:200])  # 限制长度
        
        return key_points[:10]  # 最多返回10个要点

