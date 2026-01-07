"""LLM integration service"""
import time
from typing import Tuple, Optional, List, Dict, Any
from openai import AsyncOpenAI
import tiktoken

from app.core.config import settings
from app.core.logging import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.DEFAULT_MODEL
        
        # 初始化客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        # Token计数器
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Tuple[str, int, int]:
        """
        Send a chat completion request
        Returns: (response_text, input_tokens, output_tokens)
        """
        start_time = time.time()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        # 估算输入token
        input_text = system_prompt + user_message
        input_tokens = self.count_tokens(input_text)
        
        logger.info(
            "llm_request_start",
            model=self.model,
            input_tokens=input_tokens,
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.MAX_TOKENS,
            )
            
            response_text = response.choices[0].message.content
            output_tokens = self.count_tokens(response_text)
            
            # 使用API返回的token计数（如果有）
            if response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "llm_request_completed",
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )
            
            perf_logger.info(
                "llm_chat",
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )
            
            return response_text, input_tokens, output_tokens
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "llm_request_failed",
                model=self.model,
                error=str(e),
                duration_ms=duration_ms,
            )
            raise
    
    async def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Send a streaming chat completion request
        Yields response chunks
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        logger.info("llm_stream_request_start", model=self.model)
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.MAX_TOKENS,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("llm_stream_request_failed", model=self.model, error=str(e))
            raise
    
    async def evaluate_responses(
        self,
        original_prompt: str,
        responses: List[str],
        criteria: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Evaluate multiple responses against criteria
        Returns scores for each response
        """
        start_time = time.time()
        
        evaluation_prompt = f"""请评估以下多个回答的质量。

原始问题/提示：
{original_prompt}

评估标准及权重：
{chr(10).join([f"- {k}: {v*100}%" for k, v in criteria.items()])}

回答列表：
{chr(10).join([f"### 回答{i+1}:{chr(10)}{resp}{chr(10)}" for i, resp in enumerate(responses)])}

请为每个回答的每个标准打分（1-10分），并给出综合评价。
返回JSON格式：
{{
  "scores": [
    {{"relevance": 8, "accuracy": 7, "completeness": 9, "readability": 8, "total": 8.0}},
    ...
  ],
  "winner": 1,
  "reasoning": "详细分析..."
}}"""
        
        system_prompt = "你是一个专业的内容评估专家。请客观、公正地评估给定的回答质量。"
        
        try:
            response, _, _ = await self.chat(
                system_prompt=system_prompt,
                user_message=evaluation_prompt,
                temperature=0.3,  # 更低的温度以获得更一致的评估
            )
            
            # 尝试解析JSON
            import json
            import re
            
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"raw_response": response, "parse_error": True}
            
            perf_logger.info(
                "evaluate_responses",
                response_count=len(responses),
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
            return result
            
        except Exception as e:
            logger.error("evaluate_responses_failed", error=str(e))
            return {"error": str(e)}

