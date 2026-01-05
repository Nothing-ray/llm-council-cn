"""测试provider连接性和功能

运行此脚本以验证：
1. Provider注册表是否正常工作
2. 各provider的API连接是否正常
3. 模型调用是否成功

使用方法:
    python -m backend.test_providers              # 测试所有启用的provider
    python -m backend.test_providers openrouter   # 测试指定provider
    python -m backend.test_providers siliconflow  # 测试指定provider
"""
import asyncio
import sys
import os
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.providers import list_providers, get_provider
from backend.config import get_config, get_provider_config


async def test_provider_registry():
    """测试provider注册表"""
    print("=" * 60)
    print("测试 Provider 注册表")
    print("=" * 60)

    providers = list_providers()
    print(f"\n已注册的 Providers: {providers}")

    config = get_config()
    active = config.get("active_provider", "openrouter")
    print(f"当前激活的 Provider: {active}")

    return True


async def test_single_provider(provider_name: str) -> bool:
    """测试单个provider

    Args:
        provider_name: Provider名称 (e.g., 'openrouter', 'siliconflow')

    Returns:
        bool: 测试是否成功
    """
    print("\n" + "=" * 60)
    print(f"测试 Provider: {provider_name}")
    print("=" * 60)

    try:
        # 获取provider配置
        provider_config = get_provider_config(provider_name)
        print(f"\n配置信息:")
        print(f"  API URL: {provider_config['api_url']}")
        print(f"  API Key Env: {provider_config['api_key_env']}")

        # 检查API key
        api_key = os.getenv(provider_config["api_key_env"])
        if not api_key:
            print(f"\n❌ 失败: 未找到环境变量 {provider_config['api_key_env']}")
            print(f"   请在 .env 文件中设置: {provider_config['api_key_env']}=your_api_key")
            return False

        print(f"  API Key: {'*' * 20}{api_key[-4:]}")  # 只显示最后4位

        # 获取provider函数
        provider_fns = get_provider(provider_name)
        print(f"\nProvider函数:")
        print(f"  query_model: {'✓' if 'query_model' in provider_fns else '✗'}")
        print(f"  query_models_parallel: {'✓' if 'query_models_parallel' in provider_fns else '✗'}")

        # 获取测试模型
        models = provider_config.get("models", {})
        council_models = models.get("council", [])
        if not council_models:
            print("\n❌ 失败: 配置中没有council模型")
            return False

        test_model = council_models[0]
        print(f"\n测试模型: {test_model}")
        print("发送测试查询...")

        # 测试单个模型查询
        response = await provider_fns["query_model"](
            model=test_model,
            messages=[{"role": "user", "content": "你好，请回复'测试成功'"}],
            api_url=provider_config["api_url"],
            api_key=api_key
        )

        if response:
            print(f"\n✅ 成功!")
            content = response.get('content', '')
            print(f"响应内容: {content[:100]}{'...' if len(content) > 100 else ''}")

            reasoning = response.get('reasoning_details')
            if reasoning:
                print(f"推理内容: 是 ({len(reasoning)} 字符)")
        else:
            print(f"\n❌ 失败: 没有收到响应")
            return False

        # 如果有多个模型，测试并行查询
        if len(council_models) > 1:
            print(f"\n测试并行查询 ({len(council_models)} 个模型)...")
            responses = await provider_fns["query_models_parallel"](
                models=council_models[:2],  # 只测试前2个模型
                messages=[{"role": "user", "content": "请简短回复'并行测试'"}],
                api_url=provider_config["api_url"],
                api_key=api_key
            )

            success_count = sum(1 for r in responses.values() if r is not None)
            print(f"并行查询结果: {success_count}/{len(responses)} 个模型响应成功")

        return True

    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    # 解析命令行参数
    provider_to_test = sys.argv[1] if len(sys.argv) > 1 else None

    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "LLM Council Provider 测试" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")

    # 测试注册表
    await test_provider_registry()

    # 确定要测试的providers
    config = get_config()
    providers_config = config.get("providers", {})

    if provider_to_test:
        # 测试指定的provider
        if provider_to_test not in providers_config:
            print(f"\n❌ 错误: 未找到 provider '{provider_to_test}'")
            print(f"可用的 providers: {list(providers_config.keys())}")
            return
        providers_to_test = [provider_to_test]
    else:
        # 测试所有启用的provider
        providers_to_test = [
            name for name, cfg in providers_config.items()
            if cfg.get("enabled", False)
        ]

    if not providers_to_test:
        print("\n❌ 没有启用的 provider 可供测试")
        return

    # 测试每个provider
    results = {}
    for name in providers_to_test:
        results[name] = await test_single_provider(name)

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:20} {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败，请检查配置和API密钥")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
