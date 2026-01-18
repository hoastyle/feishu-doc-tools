#!/usr/bin/env python3
"""
测试 Refresh Token 自动更新功能
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from lib.feishu_api_client import FeishuApiClient, AuthMode
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("\n" + "=" * 80)
    print("  测试 Refresh Token 自动更新")
    print("=" * 80)

    env_path = project_root / ".env"
    load_dotenv(env_path)

    print("\n【1. 读取当前 refresh_token】")
    print("-" * 80)
    current_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")
    print(f"当前 token (前20字符): {current_token[:20] if current_token else 'None'}...")

    print("\n【2. 创建客户端】")
    print("-" * 80)
    client = FeishuApiClient.from_env(env_path)
    print(f"客户端创建成功，认证模式: {client.auth_mode}")

    print("\n【3. 调用需要认证的 API (会触发 token 刷新)】")
    print("-" * 80)
    try:
        print("正在获取用户信息...")
        user_info = client.get_user_info()
        print(f"✓ 成功获取用户信息: {user_info.get('name')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n【4. 验证 .env 文件是否已更新】")
    print("-" * 80)

    # 重新加载环境变量
    load_dotenv(env_path, override=True)
    new_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")

    print(f"新 token (前20字符): {new_token[:20] if new_token else 'None'}...")

    if current_token != new_token:
        print("✓ .env 文件已成功更新！")
        print(f"  旧 token: {current_token[:30]}...")
        print(f"  新 token: {new_token[:30]}...")
    else:
        print("⚠️  .env 文件未更新（token 相同）")
        print("  可能原因：token 还未过期，没有触发刷新")

    print("\n【5. 再次调用 API 验证持久化】")
    print("-" * 80)

    # 创建新客户端（模拟重启）
    client2 = FeishuApiClient.from_env(env_path)
    try:
        user_info2 = client2.get_user_info()
        print(f"✓ 第二次调用成功: {user_info2.get('name')}")
    except Exception as e:
        print(f"❌ 第二次调用失败: {e}")

    print("\n" + "=" * 80)
    print("✓ 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
