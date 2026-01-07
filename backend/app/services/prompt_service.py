"""Prompt template and generation service"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.group import GroupType
from app.models.prompt import PromptTemplate, PromptExecution, TimeGranularity, PromptStyle
from app.core.logging import get_logger, get_performance_logger
from app.services.llm_service import LLMService

logger = get_logger(__name__)
perf_logger = get_performance_logger()


# 预定义的Prompt模板库
PROMPT_TEMPLATES = {
    GroupType.INVESTMENT: {
        TimeGranularity.DAILY: {
            PromptStyle.ANALYTICAL: """你是一位专业的投资分析师。请分析以下投资群的聊天记录。

聊天记录时间范围：{start_date} 至 {end_date}
{member_filter_text}

请从以下几个维度进行分析：
1. 今日讨论的主要股票/基金/数字货币
2. 群内情绪倾向（看多/看空/中性）
3. 被提及最多的投资标的及其讨论热度
4. 值得关注的投资观点和分析
5. 风险提示和注意事项

聊天记录：
{chat_content}

请给出结构化的分析报告。""",
            PromptStyle.SUMMARY: """请简要总结以下投资群今日({start_date})的讨论要点：

{member_filter_text}

聊天记录：
{chat_content}

请用简洁的方式列出：
- 热门话题（3-5个）
- 市场情绪
- 重要观点
- 值得关注的标的""",
            PromptStyle.INSIGHT: """作为资深投资顾问，请从以下投资群聊天记录中挖掘有价值的投资洞察。

时间：{start_date}
{member_filter_text}

聊天记录：
{chat_content}

请提供：
1. 独特的投资视角和逆向思维观点
2. 可能被忽略的投资机会
3. 潜在的风险信号
4. 群体心理分析"""
        },
        TimeGranularity.MONTHLY: {
            PromptStyle.ANALYTICAL: """请对投资群{start_date}至{end_date}期间的讨论进行月度复盘分析。

{member_filter_text}

聊天记录：
{chat_content}

分析要点：
1. 本月讨论最多的投资标的排名
2. 群内观点的准确率回顾（如果有后续验证的话）
3. 月度投资情绪变化曲线
4. 重要的市场事件及群内反应
5. 活跃成员贡献度分析
6. 下月投资建议和关注方向"""
        }
    },
    GroupType.SCIENCE: {
        TimeGranularity.DAILY: {
            PromptStyle.ANALYTICAL: """你是一位科学传播专家。请分析以下科普群的聊天记录。

时间：{start_date} 至 {end_date}
{member_filter_text}

聊天记录：
{chat_content}

请分析：
1. 今日讨论的科学话题和领域
2. 分享的科普文章/视频质量评估
3. 常见的科学误解和纠正
4. 有价值的科学讨论和观点交锋
5. 建议进一步学习的科学主题""",
            PromptStyle.SUMMARY: """请总结科普群今日({start_date})的讨论内容：

{member_filter_text}

聊天记录：
{chat_content}

请列出：
- 讨论的科学领域
- 有趣的科学事实
- 推荐的科普资源
- 悬而未决的科学问题"""
        }
    },
    GroupType.LEARNING: {
        TimeGranularity.DAILY: {
            PromptStyle.ANALYTICAL: """你是一位学习顾问。请分析以下学习群的聊天记录。

时间：{start_date} 至 {end_date}
{member_filter_text}

聊天记录：
{chat_content}

请分析：
1. 今日讨论的学习主题和知识点
2. 成员提出的问题及解答质量
3. 分享的学习资源价值评估
4. 学习方法和技巧讨论
5. 学习进度和目标完成情况
6. 建议的学习资源和下一步计划""",
            PromptStyle.INSIGHT: """作为学习教练，请从以下学习群聊天中提取学习洞察。

时间：{start_date}
{member_filter_text}

聊天记录：
{chat_content}

请提供：
1. 高效学习者的学习策略
2. 常见的学习误区和改进建议
3. 值得借鉴的学习方法
4. 学习社群互助的最佳实践"""
        }
    },
    GroupType.TECHNOLOGY: {
        TimeGranularity.DAILY: {
            PromptStyle.ANALYTICAL: """你是一位技术专家。请分析以下技术群的聊天记录。

时间：{start_date} 至 {end_date}
{member_filter_text}

聊天记录：
{chat_content}

请分析：
1. 讨论的技术话题和技术栈
2. 技术问题及解决方案汇总
3. 新技术/工具/框架的讨论
4. 代码相关讨论和最佳实践
5. 技术趋势洞察
6. 推荐的技术资源"""
        }
    },
    GroupType.HEALTH: {
        TimeGranularity.DAILY: {
            PromptStyle.ANALYTICAL: """你是一位健康顾问。请分析以下健康群的聊天记录。

时间：{start_date} 至 {end_date}
{member_filter_text}

聊天记录：
{chat_content}

请分析：
1. 讨论的健康话题
2. 分享的健康知识准确性评估
3. 健康建议和提醒
4. 运动/饮食/睡眠相关讨论
5. 需要专业医疗建议的情况标注

注意：本分析仅供参考，不构成医疗建议。"""
        }
    }
}


class PromptService:
    """Service for managing prompt templates and executions"""
    
    def __init__(self, db: AsyncSession, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm_service = llm_service or LLMService()
    
    async def get_template(self, template_id: int) -> Optional[PromptTemplate]:
        """Get a prompt template by ID"""
        start_time = time.time()
        result = await self.db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        perf_logger.info(
            "get_template",
            template_id=template_id,
            found=template is not None,
            duration_ms=int((time.time() - start_time) * 1000)
        )
        return template
    
    async def get_templates_by_type(
        self, 
        group_type: GroupType,
        time_granularity: Optional[TimeGranularity] = None,
        style: Optional[PromptStyle] = None,
    ) -> List[PromptTemplate]:
        """Get templates filtered by type, granularity, and style"""
        start_time = time.time()
        
        conditions = [PromptTemplate.group_type == group_type, PromptTemplate.is_active == True]
        if time_granularity:
            conditions.append(PromptTemplate.time_granularity == time_granularity)
        if style:
            conditions.append(PromptTemplate.style == style)
        
        result = await self.db.execute(
            select(PromptTemplate).where(and_(*conditions))
        )
        templates = result.scalars().all()
        
        perf_logger.info(
            "get_templates_by_type",
            group_type=group_type.value,
            count=len(templates),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        return list(templates)
    
    def get_builtin_template(
        self,
        group_type: GroupType,
        time_granularity: TimeGranularity,
        style: PromptStyle = PromptStyle.ANALYTICAL,
    ) -> Optional[str]:
        """Get a built-in prompt template"""
        type_templates = PROMPT_TEMPLATES.get(group_type, {})
        granularity_templates = type_templates.get(time_granularity, {})
        template = granularity_templates.get(style)
        
        if not template:
            # 回退到ANALYTICAL风格
            template = granularity_templates.get(PromptStyle.ANALYTICAL)
        
        logger.info(
            "get_builtin_template",
            group_type=group_type.value,
            time_granularity=time_granularity.value,
            style=style.value,
            found=template is not None
        )
        return template
    
    def render_prompt(
        self,
        template: str,
        chat_content: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        member_filter: Optional[List[str]] = None,
        extra_variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a prompt template with variables"""
        start_time = time.time()
        
        # 准备变量
        variables = {
            "chat_content": chat_content,
            "start_date": start_date.strftime("%Y-%m-%d") if start_date else "未指定",
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else "未指定",
            "member_filter_text": f"关注成员：{', '.join(member_filter)}" if member_filter else "",
        }
        
        if extra_variables:
            variables.update(extra_variables)
        
        # 渲染模板
        rendered = template.format(**variables)
        
        perf_logger.info(
            "render_prompt",
            template_length=len(template),
            rendered_length=len(rendered),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        return rendered
    
    async def execute_prompt(
        self,
        template_id: Optional[int],
        group_id: Optional[int],
        rendered_prompt: str,
        variables_used: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        member_filter: Optional[List[str]] = None,
        system_prompt: str = "你是一个专业的群聊分析助手。",
    ) -> PromptExecution:
        """Execute a rendered prompt and save the result"""
        start_time = time.time()
        
        # 创建执行记录
        execution = PromptExecution(
            template_id=template_id or 0,
            group_id=group_id,
            rendered_prompt=rendered_prompt,
            variables_used=variables_used,
            start_date=start_date,
            end_date=end_date,
            member_filter=member_filter,
            status="running",
            model_used=self.llm_service.model,
        )
        self.db.add(execution)
        await self.db.flush()
        
        try:
            # 调用LLM
            response, tokens_in, tokens_out = await self.llm_service.chat(
                system_prompt=system_prompt,
                user_message=rendered_prompt,
            )
            
            execution.response = response
            execution.tokens_input = tokens_in
            execution.tokens_output = tokens_out
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "prompt_execution_completed",
                execution_id=execution.id,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                latency_ms=execution.latency_ms
            )
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.latency_ms = int((time.time() - start_time) * 1000)
            logger.error("prompt_execution_failed", execution_id=execution.id, error=str(e))
        
        await self.db.commit()
        
        perf_logger.info(
            "execute_prompt",
            execution_id=execution.id,
            status=execution.status,
            duration_ms=execution.latency_ms
        )
        return execution
    
    async def generate_prompt_variants(
        self,
        group_type: GroupType,
        time_granularity: TimeGranularity,
        styles: List[PromptStyle],
        custom_requirements: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple prompt variants for comparison"""
        start_time = time.time()
        variants = []
        
        for style in styles:
            template = self.get_builtin_template(group_type, time_granularity, style)
            if template:
                variants.append({
                    "group_type": group_type.value,
                    "time_granularity": time_granularity.value,
                    "style": style.value,
                    "template": template,
                    "is_builtin": True,
                })
        
        # 如果有自定义需求，也可以用LLM生成自定义模板
        if custom_requirements:
            custom_template = await self._generate_custom_template(
                group_type, time_granularity, custom_requirements
            )
            if custom_template:
                variants.append({
                    "group_type": group_type.value,
                    "time_granularity": time_granularity.value,
                    "style": "custom",
                    "template": custom_template,
                    "is_builtin": False,
                })
        
        perf_logger.info(
            "generate_prompt_variants",
            group_type=group_type.value,
            variant_count=len(variants),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        return variants
    
    async def _generate_custom_template(
        self,
        group_type: GroupType,
        time_granularity: TimeGranularity,
        requirements: str,
    ) -> Optional[str]:
        """Generate a custom prompt template based on requirements"""
        system_prompt = """你是一个专业的Prompt工程师。请根据用户的需求生成一个群聊分析的Prompt模板。

模板中应包含以下占位符：
- {chat_content}: 聊天内容
- {start_date}: 开始日期
- {end_date}: 结束日期
- {member_filter_text}: 成员过滤文本（可选）

请只返回Prompt模板本身，不要有其他说明文字。"""
        
        user_message = f"""请为以下场景生成Prompt模板：

群组类型：{group_type.value}
时间粒度：{time_granularity.value}
特定需求：{requirements}

请生成一个专业、结构化的分析Prompt模板。"""
        
        try:
            response, _, _ = await self.llm_service.chat(
                system_prompt=system_prompt,
                user_message=user_message,
            )
            return response
        except Exception as e:
            logger.error("generate_custom_template_failed", error=str(e))
            return None

