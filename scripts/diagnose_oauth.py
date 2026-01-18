#!/usr/bin/env python3
"""
飞书 OAuth 重定向 URI 诊断工具

帮助诊断和解决 OAuth 授权中的 redirect_uri 错误
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.feishu_api_client import FeishuApiClient


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def diagnose_redirect_uri():
    """诊断重定向 URI 配置"""
    print_section("飞书 OAuth 重定向 URI 诊断")

    print("\n请确认以下配置完全一致:\n")

    print("1️⃣  飞书开发者后台配置:")
    print("   应用 ID: cli_a9e09cc76d345bb4")
    print("   路径: 开发配置 > 安全设置 > 重定向 URL")
    print("   配置值: http://localhost:3333/callback")

    print("\n2️⃣  当前授权 URL 使用的重定向 URI:")
    client = FeishuApiClient.from_env()

    # 生成多个可能的重定向 URI 供用户选择
    redirect_uris = [
        "http://localhost:3333/callback",
        "http://localhost:3333/callback/",
        "https://localhost:3333/callback",
    ]

    print("\n   使用的 URI: http://localhost:3333/callback")
    print("\n3️⃣  常见的不匹配情况:")
    print("   ❌ http://localhost:3333/callback  vs  http://localhost:8080/callback (端口不同)")
    print("   ❌ http://localhost:3333/callback  vs  https://localhost:3333/callback (协议不同)")
    print("   ❌ http://localhost:3333/callback  vs  http://localhost:3333/callback/ (尾部斜杠)")

    print("\n" + "=" * 70)
    print("  🔍 诊断和解决方案")
    print("=" * 70)

    print("\n方案 A: 检查并修复开发者后台配置")
    print("   1. 访问: https://open.feishu.cn/open-apis/app_modal")
    print("   2. 选择应用: cli_a9e09cc76d345bb4")
    print("   3. 进入: 开发配置 > 安全设置 > 重定向 URL")
    print("   4. 检查配置，确认是: http://localhost:3333/callback")
    print("   5. 如果有多个配置，删除不需要的")
    print("   6. 等待 1-2 分钟后重试")

    print("\n方案 B: 使用飞书提供的默认重定向 URI")
    print("   某些应用可能需要使用特定的域名格式")
    print("   请尝试配置为: https://open.feishu.cn/app/cli_a9e09cc76d345bb4/callback")

    print("\n方案 C: 使用手动授权码获取")
    print("   如果上述方案都不可行，可以使用飞书提供的其他授权方式")

    print("\n" + "=" * 70)
    print("  🧪 测试步骤")
    print("=" * 70)

    # 提供一个测试用的授权 URL
    test_url = client.generate_oauth_url(redirect_uri="http://localhost:3333/callback")

    print("\n请按以下步骤测试:")
    print(f"\n1. 访问此 URL:")
    print(f"   {test_url}")

    print(f"\n2. 如果仍然出现错误 20029，请检查:")
    print(f"   - 开发者后台的重定向 URL 配置")
    print(f"   - URL 中是否有多余的空格")
    print(f"   - URL 是否被截断或修改")

    print(f"\n3. 如果成功，您将被重定向到:")
    print(f"   http://localhost:3333/callback?code=xxxxx&state=xxxxx")
    print(f"   (可能会显示'无法连接到此页面'，这是正常的)")

    print(f"\n4. 复制地址栏中 code= 后面的内容")

    print("\n" + "=" * 70)
    print("  💡 快速修复建议")
    print("=" * 70)

    print("\n建议 1: 删除所有重定向 URL，重新添加")
    print("  - 开发者后台 > 安全设置 > 重定向 URL")
    print("  - 删除现有配置")
    print("  - 重新添加: http://localhost:3333/callback")

    print("\n建议 2: 确保应用状态正确")
    print("  - 确认应用状态为'已启用'")
    print("  - 确认权限已开通")

    print("\n建议 3: 尝试使用生产域名")
    print("  - 如果有域名，配置: https://yourdomain.com/callback")
    print("  - 然后运行时输入该域名")

    print("\n建议 4: 使用环境变量指定重定向 URI")
    print("  - 在 .env 文件中添加:")
    print("  - FEISHU_REDIRECT_URI=http://localhost:3333/callback")

    # 生成多个不同重定向 URI 的授权 URL
    print("\n" + "=" * 70)
    print("  🔧 不同重定向 URI 的授权 URL")
    print("=" * 70)

    for uri in redirect_uris:
        url = client.generate_oauth_url(redirect_uri=uri)
        print(f"\n重定向 URI: {uri}")
        print(f"授权 URL: {url}")


if __name__ == "__main__":
    try:
        diagnose_redirect_uri()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 诊断过程中出错: {e}")
        print("\n请确保:")
        print("  1. .env 文件配置正确")
        print("  2. 应用凭证有效")
        print("  3. 网络连接正常")
