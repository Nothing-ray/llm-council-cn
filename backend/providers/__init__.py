"""
Provider注册表和工厂
使用函数式策略模式，每个provider导出标准签名的函数
"""
from typing import Callable, Dict, Any, List, Optional
import importlib

# Provider函数注册表
_provider_registry: Dict[str, Dict[str, Callable]] = {}


def register_provider(
    name: str,
    query_fn: Callable,
    query_parallel_fn: Callable,
    supports_reasoning: bool = False
) -> None:
    """注册provider及其函数"""
    _provider_registry[name] = {
        "query_model": query_fn,
        "query_models_parallel": query_parallel_fn,
        "supports_reasoning": supports_reasoning
    }


def get_provider(name: str) -> Dict[str, Callable]:
    """获取provider的函数集合"""
    if name not in _provider_registry:
        raise ValueError(f"Provider '{name}' not registered")
    return _provider_registry[name]


def list_providers() -> List[str]:
    """列出所有已注册的provider"""
    return list(_provider_registry.keys())


# 自动加载所有providers
def _autoload_providers() -> None:
    """自动发现并加载backend/providers/下的所有provider模块"""
    import pathlib

    providers_dir = pathlib.Path(__file__).parent
    excluded = {"__init__.py", "base.py"}  # 排除的文件

    for module_file in providers_dir.glob("*.py"):
        if module_file.name in excluded:
            continue

        module_name = module_file.stem
        try:
            module = importlib.import_module(f".providers.{module_name}", package="backend")

            # 检查模块是否有必要的函数
            if not all(hasattr(module, attr) for attr in ["query_model", "query_models_parallel"]):
                print(f"Warning: {module_name} missing required functions, skipping")
                continue

            # 检查是否有register函数
            if hasattr(module, "register"):
                module.register()

            print(f"Loaded provider: {module_name}")
        except Exception as e:
            print(f"Error loading provider {module_name}: {e}")


_autoload_providers()
