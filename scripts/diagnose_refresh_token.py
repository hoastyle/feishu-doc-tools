#!/usr/bin/env python3
"""
诊断 Refresh Token 问题

测试 refresh token API 调用并提供详细的诊断信息
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests
import json

def main():
    print("\n" + "=" * 80)
    print("  Refresh Token 诊断")
    print("=" * 80)

    # 加载环境变量
    env_path = project_root / ".env"
    load_dotenv(env_path)

    print("\n【1. 环境变量检查】")
    print("-" * 80)

    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    refresh_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")

    print(f"✓ FEISHU_APP_ID: {app_id if app_id else '❌ 未设置'}")
    print(f"✓ FEISHU_APP_SECRET: {'*' * (len(app_secret) - 4) + app_secret[-4:] if app_secret else '❌ 未设置'}")
    print(f"✓ FEISHU_USER_REFRESH_TOKEN: {'存在 (' + str(len(refresh_token)) + ' 字符)' if refresh_token else '❌ 未设置'}")

    if not all([app_id, app_secret, refresh_token]):
        print("\n❌ 错误: 缺少必要的环境变量")
        return

    print("\n【2. Refresh Token 格式检查】")
    print("-" * 80)

    # 检查 refresh token 格式（应该是 JWT）
    token_parts = refresh_token.split('.')
    print(f"Token 部分数量: {len(token_parts)} {'✓ (JWT格式)' if len(token_parts) == 3 else '❌ (非JWT格式)'}")

    if len(token_parts) == 3:
        import base64
        try:
            # 解码 header
            header_b64 = token_parts[0]
            # 添加 padding
            header_b64 += '=' * (4 - len(header_b64) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_b64))
            print(f"Token Header: {json.dumps(header, indent=2)}")

            # 解码 payload
            payload_b64 = token_parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            print(f"\nToken Payload:")
            print(f"  - client_id: {payload.get('client_id', 'N/A')}")
            print(f"  - scope: {payload.get('scope', 'N/A')}")
            print(f"  - exp (过期时间): {payload.get('exp', 'N/A')}")

            # 检查是否过期
            import time
            exp = payload.get('exp')
            if exp:
                now = int(time.time())
                if now > exp:
                    print(f"  ⚠️ Token 已过期! (过期于 {exp}, 现在 {now})")
                else:
                    remaining = exp - now
                    print(f"  ✓ Token 有效 (还剩 {remaining} 秒, 约 {remaining // 86400} 天)")

            # 检查 client_id 是否匹配
            token_client_id = payload.get('client_id')
            if token_client_id != app_id:
                print(f"  ⚠️ Token 的 client_id ({token_client_id}) 与环境变量不匹配 ({app_id})")
            else:
                print(f"  ✓ client_id 匹配")

        except Exception as e:
            print(f"❌ 解码 Token 失败: {e}")

    print("\n【3. 测试 Refresh Token API】")
    print("-" * 80)

    url = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "refresh_token": refresh_token,
    }

    print(f"API 端点: {url}")
    print(f"请求 Payload:")
    print(f"  - grant_type: {payload['grant_type']}")
    print(f"  - client_id: {payload['client_id']}")
    print(f"  - client_secret: {'*' * (len(payload['client_secret']) - 4) + payload['client_secret'][-4:]}")
    print(f"  - refresh_token: {refresh_token[:20]}...{refresh_token[-20:]}")

    print("\n发送请求...")

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)

        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'x-request-id', 'x-tt-logid']:
                print(f"  - {key}: {value}")

        print(f"\n响应体:")
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))

            # 分析错误
            if response.status_code != 200:
                print("\n【错误分析】")
                print("-" * 80)
                print(f"❌ HTTP {response.status_code} 错误")

                code = response_data.get('code')
                msg = response_data.get('msg')
                print(f"错误码: {code}")
                print(f"错误信息: {msg}")

                # 常见错误码分析
                if code == 20071:
                    print("\n可能原因:")
                    print("  - redirect_uri 不匹配")
                    print("  - 应用配置错误")
                elif code == 400:
                    print("\n可能原因:")
                    print("  - Refresh token 已过期")
                    print("  - Refresh token 格式错误")
                    print("  - client_id/client_secret 不匹配")

            elif response_data.get('code') == 0:
                print("\n【成功】")
                print("-" * 80)
                print("✓ Token 刷新成功!")
                print(f"新 access_token: {response_data.get('access_token', 'N/A')[:30]}...")
                print(f"新 refresh_token: {response_data.get('refresh_token', 'N/A')[:30]}...")
                print(f"expires_in: {response_data.get('expires_in', 'N/A')} 秒")

        except ValueError:
            print(response.text)

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
