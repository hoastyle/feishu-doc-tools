#!/usr/bin/env python3
"""
OAuth URL 生成测试脚本

测试修复后的 OAuth URL 生成功能。
"""
import sys
from lib.feishu_api_client import FeishuApiClient


def main():
    print("=" * 80)
    print("OAuth URL 生成测试")
    print("=" * 80)
    print()

    try:
        # 创建客户端
        client = FeishuApiClient.from_env()

        # 生成授权 URL
        url = client.generate_oauth_url()

        print("✓ 成功生成 OAuth 授权 URL")
        print()
        print("完整 URL:")
        print("-" * 80)
        print(url)
        print("-" * 80)
        print()

        # 验证关键特征
        print("URL 验证结果:")
        print("-" * 80)

        checks = [
            ("使用正确域名 (accounts.feishu.cn)", "accounts.feishu.cn" in url),
            ("包含 client_id 参数", "client_id=" in url),
            ("包含 redirect_uri 参数（已编码）", "redirect_uri=" in url and "%3A%2F%2F" in url),
            ("包含 scope 参数（空格已编码为 %20）", "scope=" in url and "%20" in url),
            ("包含 response_type=code", "response_type=code" in url),
            ("包含 state 参数", "state=" in url),
            ("scope 包含 offline_access", "offline_access" in url),
        ]

        all_passed = True
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"{status} {check_name}: {'通过' if result else '失败'}")
            if not result:
                all_passed = False

        print("-" * 80)
        print()

        if all_passed:
            print("🎉 所有检查通过！")
            print()
            print("下一步:")
            print("1. 复制上面的完整 URL")
            print("2. 在浏览器中打开")
            print("3. 完成飞书授权")
            print("4. 从回调 URL 中获取 code 参数")
            print("5. 运行: uv run python scripts/setup_user_auth.py")
            return 0
        else:
            print("❌ 部分检查失败，请检查配置")
            return 1

    except FileNotFoundError as e:
        print(f"❌ 错误: 配置文件不存在 - {e}")
        print()
        print("请确保以下文件之一存在:")
        print("  - .env")
        print("  - ../Feishu-MCP/.env")
        return 1

    except KeyError as e:
        print(f"❌ 错误: 缺少必需的环境变量 - {e}")
        print()
        print("请在 .env 文件中设置:")
        print("  FEISHU_APP_ID=cli_xxxxx")
        print("  FEISHU_APP_SECRET=xxxxx")
        return 1

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
