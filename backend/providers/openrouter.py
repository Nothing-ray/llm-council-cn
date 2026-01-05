"""
OpenRouter Provider实现
从原有openrouter.py重构，保持功能兼容
"""
import httpx
from typing import List, Dict, Any, Optional


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    api_url: str,
    api_key: str,
    timeout: float = 120.0,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """查询单个模型"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://llm-council.cn",
        "X-Title": "LLM Council"
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    api_url: str,
    api_key: str,
    **kwargs
) -> Dict[str, Optional[Dict[str, Any]]]:
    """并行查询多个模型"""
    import asyncio

    tasks = [
        query_model(model, messages, api_url, api_key, **kwargs)
        for model in models
    ]

    responses = await asyncio.gather(*tasks)

    return {model: response for model, response in zip(models, responses)}


def register() -> None:
    """注册OpenRouter provider"""
    from . import register_provider
    register_provider(
        name="openrouter",
        query_fn=query_model,
        query_parallel_fn=query_models_parallel,
        supports_reasoning=True
    )
