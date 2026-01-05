"""
SiliconFlow Provider实现
支持推理模型的特殊参数
"""
import httpx
from typing import List, Dict, Any, Optional


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    api_url: str,
    api_key: str,
    timeout: float = 120.0,
    enable_thinking: Optional[bool] = None,
    thinking_budget: Optional[int] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """查询单个模型，支持SiliconFlow特有参数"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    # SiliconFlow特有参数
    if enable_thinking is not None:
        payload["enable_thinking"] = enable_thinking
    if thinking_budget is not None:
        payload["thinking_budget"] = thinking_budget

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            # SiliconFlow使用reasoning_content字段
            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_content')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    api_url: str,
    api_key: str,
    enable_thinking: Optional[bool] = None,
    thinking_budget: Optional[int] = None,
    **kwargs
) -> Dict[str, Optional[Dict[str, Any]]]:
    """并行查询多个模型"""
    import asyncio

    tasks = [
        query_model(
            model, messages, api_url, api_key,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget,
            **kwargs
        )
        for model in models
    ]

    responses = await asyncio.gather(*tasks)

    return {model: response for model, response in zip(models, responses)}


def register() -> None:
    """注册SiliconFlow provider"""
    from . import register_provider
    register_provider(
        name="siliconflow",
        query_fn=query_model,
        query_parallel_fn=query_models_parallel,
        supports_reasoning=True
    )
