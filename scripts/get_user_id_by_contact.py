#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取当前飞书用户的 User ID

此脚本自动从 .env 文件读取配置，使用用户访问令牌获取当前用户信息。
使用 API: /authen/v1/user_info
权限要求: 基础 OAuth 授权即可（不需要额外的通讯录权限）

Usage:
    # 获取当前用户信息
    python scripts/get_user_id_by_contact.py

    # 获取并自动保存到 .env 文件
    python scripts/get_user_id_by_contact.py --save

说明:
    如果遇到认证错误，请运行: python scripts/setup_user_auth.py
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.feishu_api_client import FeishuApiClient
from dotenv import load_dotenv


def get_current_user_info(client: FeishuApiClient) -> Dict[str, Any]:
    """
    获取当前登录用户信息

    API: GET /authen/v1/user_info
    权限: 基础 OAuth 授权即可（不需要额外的通讯录权限）

    Returns:
        当前用户的详细信息
    """
    # 使用用户访问令牌
    token = client.get_user_token()
    url = f"{client.BASE_URL}/authen/v1/user_info"

    headers = {"Authorization": f"Bearer {token}"}

    response = client.session.get(url, headers=headers, timeout=10)
    result = response.json()

    if result.get("code") != 0:
        raise Exception(f"API Error [{result.get('code')}]: {result.get('msg')}")

    return result.get("data", {})


def format_user_info(user: Dict[str, Any]) -> None:
    """格式化并打印用户信息"""
    print("\n" + "=" * 70)
    print("👤 当前用户信息")
    print("=" * 70)
    print(f"   姓名: {user.get('name', 'N/A')}")
    print(f"   英文名: {user.get('en_name', 'N/A')}")
    print(f"   邮箱: {user.get('email', 'N/A')}")
    print(f"   手机: {user.get('mobile', 'N/A')}")
    print()
    print(f"   🔑 Open ID: {user.get('open_id', 'N/A')}")
    print(f"   🔑 Union ID: {user.get('union_id', 'N/A')}")
    print(f"   🔑 User ID: {user.get('user_id', 'N/A')}")
    print()
    print(f"   租户标识: {user.get('tenant_key', 'N/A')}")

    # 头像信息
    if user.get('avatar_url'):
        print(f"   头像: {user.get('avatar_url')}")

    print("=" * 70)


def save_to_env(user: Dict[str, Any], env_file: Path) -> bool:
    """
    保存用户信息到 .env 文件

    Args:
        user: 用户信息
        env_file: .env 文件路径

    Returns:
        是否成功保存
    """
    try:
        # 读取现有内容
        content = env_file.read_text(encoding='utf-8')

        user_id = user.get('open_id', '')
        name = user.get('name', '')

        if not user_id:
            print("❌ 错误: 无法获取 user_id")
            return False

        # 更新或添加 MY_USER_ID
        if re.search(r'^MY_USER_ID=', content, re.MULTILINE):
            # 更新现有行（包括注释的）
            content = re.sub(
                r'^#?\s*MY_USER_ID=.*$',
                f'MY_USER_ID={user_id}',
                content,
                flags=re.MULTILINE
            )
        else:
            # 添加新行（在 MY_NAME 后面）
            if 'MY_NAME=' in content:
                content = re.sub(
                    r'(MY_NAME=.*?)$',
                    r'\1\nMY_USER_ID=' + user_id,
                    content,
                    flags=re.MULTILINE
                )
            else:
                # 追加到文件末尾
                if not content.endswith('\n'):
                    content += '\n'
                content += f'\nMY_USER_ID={user_id}\n'

        # 更新 MY_NAME（如果不存在或为空）
        if name:
            if re.search(r'^MY_NAME=\s*$', content, re.MULTILINE):
                # 更新空的 MY_NAME
                content = re.sub(
                    r'^MY_NAME=\s*$',
                    f'MY_NAME={name}',
                    content,
                    flags=re.MULTILINE
                )
            elif not re.search(r'^MY_NAME=', content, re.MULTILINE):
                # 添加 MY_NAME（在用户信息区域）
                if 'MY_USER_ID=' in content:
                    content = re.sub(
                        r'(MY_USER_ID=.*?)$',
                        f'MY_NAME={name}\n\\1',
                        content,
                        flags=re.MULTILINE
                    )
                else:
                    if not content.endswith('\n'):
                        content += '\n'
                    content += f'\nMY_NAME={name}\n'

        # 写回文件
        env_file.write_text(content, encoding='utf-8')

        print("\n✅ 成功保存到 .env 文件:")
        print(f"   MY_NAME={name}")
        print(f"   MY_USER_ID={user_id}")

        return True

    except Exception as e:
        print(f"\n❌ 保存失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="获取当前飞书用户的 User ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 获取当前用户信息
    python scripts/get_user_id_by_contact.py

    # 获取并保存到 .env 文件
    python scripts/get_user_id_by_contact.py --save
        """
    )

    parser.add_argument("--save", action="store_true",
                       help="自动保存到 .env 文件")

    args = parser.parse_args()

    # 加载环境变量
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 错误: 未找到 .env 文件")
        print("   请先创建 .env 文件并配置以下内容:")
        print("   FEISHU_APP_ID=cli_xxxxx")
        print("   FEISHU_APP_SECRET=xxxxx")
        print("   FEISHU_USER_REFRESH_TOKEN=xxxxx")
        return 1

    load_dotenv(env_file)

    # 检查必需配置
    if not os.environ.get("FEISHU_APP_ID"):
        print("❌ 错误: .env 文件中缺少 FEISHU_APP_ID")
        return 1

    if not os.environ.get("FEISHU_APP_SECRET"):
        print("❌ 错误: .env 文件中缺少 FEISHU_APP_SECRET")
        return 1

    if not os.environ.get("FEISHU_USER_REFRESH_TOKEN"):
        print("❌ 错误: .env 文件中缺少 FEISHU_USER_REFRESH_TOKEN")
        print("   请先运行用户认证: python scripts/setup_user_auth.py")
        return 1

    print("🔍 正在获取当前用户信息...")

    # 创建客户端
    try:
        from lib.feishu_api_client import AuthMode

        app_id = os.environ.get("FEISHU_APP_ID")
        app_secret = os.environ.get("FEISHU_APP_SECRET")
        refresh_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")

        client = FeishuApiClient(
            app_id=app_id,
            app_secret=app_secret,
            auth_mode=AuthMode.USER,
            user_refresh_token=refresh_token
        )

        # 获取用户信息
        user_info = get_current_user_info(client)

        # 显示信息
        format_user_info(user_info)

        # 保存到 .env（如果指定）
        if args.save:
            print("\n💾 正在保存到 .env 文件...")
            save_to_env(user_info, env_file)
        else:
            print("\n💡 提示: 使用 --save 参数可以自动保存到 .env 文件")
            print("   python scripts/get_user_id_by_contact.py --save")

        print("\n" + "=" * 70)
        print("✅ 完成！你可以使用以下命令测试 @提及 功能:")
        print("   python scripts/notifications/demo_advanced_features.py --type person")
        print("=" * 70)

        return 0

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 错误: {e}")

        # 检查是否是权限或令牌错误
        if "99991679" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
            print("\n" + "=" * 70)
            print("🔧 认证问题解决方案")
            print("=" * 70)
            print("\n📋 问题原因:")
            print("   用户访问令牌（refresh token）可能已过期或无效。")

            print("\n✅ 解决步骤:")
            print("   1. 重新进行用户授权以获取新的 token:")
            print("      uv run python scripts/setup_user_auth.py")
            print()
            print("   2. 按照提示在浏览器中完成授权")
            print("   3. 授权后会自动获得新的 FEISHU_USER_REFRESH_TOKEN")
            print("   4. 重新运行本脚本:")
            print("      uv run python scripts/get_user_id_by_contact.py --save")
            print()
            print("💡 提示:")
            print("   现在使用 /authen/v1/user_info API，")
            print("   只需要基础的 OAuth 授权，不需要额外的通讯录权限。")
            print("=" * 70)
        else:
            import traceback
            traceback.print_exc()

            print("\n💡 故障排除:")
            print("   1. 确认已配置用户访问令牌: FEISHU_USER_REFRESH_TOKEN")
            print("   2. 确认应用已开启权限: contact:contact.base:readonly")
            print("   3. 运行: python scripts/setup_user_auth.py")

        return 1


if __name__ == '__main__':
    exit(main())
