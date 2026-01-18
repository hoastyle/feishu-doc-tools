#!/usr/bin/env python3
"""
Feishu 用户认证完整诊断脚本

此脚本生成授权 URL，并提供详细的调试信息用于排查 State 参数问题
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.feishu_api_client import FeishuApiClient, AuthMode
from dotenv import load_dotenv

def main():
    print("\n" + "=" * 80)
    print("  Feishu 用户认证诊断 - State 参数修复验证")
    print("=" * 80)

    # 加载环境变量
    env_path = project_root / ".env"
    load_dotenv(env_path)

    print("\n【1. 环境配置检查】")
    print("-" * 80)

    # 检查必要的环境变量
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    auth_mode = os.environ.get("FEISHU_AUTH_TYPE") or os.environ.get("FEISHU_AUTH_MODE")

    print(f"✓ FEISHU_APP_ID: {app_id if app_id else '❌ 未设置'}")
    print(f"✓ FEISHU_APP_SECRET: {'*' * (len(app_secret) - 4) + app_secret[-4:] if app_secret else '❌ 未设置'}")
    print(f"✓ 认证模式: {auth_mode or '默认使用 tenant'}")

    if not app_id or not app_secret:
        print("\n❌ 错误: 缺少必要的环境变量")
        return

    # 创建客户端
    try:
        client = FeishuApiClient(
            app_id=app_id,
            app_secret=app_secret,
            auth_mode=AuthMode.USER
        )
        print("\n✓ 客户端创建成功")
    except Exception as e:
        print(f"\n❌ 客户端创建失败: {e}")
        return

    print("\n【2. 生成授权 URL】")
    print("-" * 80)

    redirect_uri = "http://localhost:3333/callback"

    try:
        auth_url = client.generate_oauth_url(redirect_uri=redirect_uri)
        print(f"✓ 授权 URL 生成成功\n")
        print(f"完整 URL:\n{auth_url}\n")

        # 解析 URL 参数
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)

        print("URL 参数详解:")
        print("-" * 80)
        for key, value in params.items():
            val = value[0]
            if key == "state":
                import base64
                try:
                    decoded = base64.b64decode(val).decode()
                    print(f"{key:20} = {val}")
                    print(f"{'↓ 解码后':20} = {decoded}")
                except:
                    print(f"{key:20} = {val}")
            else:
                print(f"{key:20} = {val}")

    except Exception as e:
        print(f"❌ 授权 URL 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n【3. State 参数对比】")
    print("-" * 80)

    import base64
    import json

    state = params.get("state")[0]
    state_decoded = base64.b64decode(state).decode()
    state_json = json.loads(state_decoded)

    print(f"State Base64 (长度: {len(state)}):")
    print(f"  {state}\n")

    print(f"State JSON (格式检查):")
    print(f"  是否使用紧凑格式: {'✓ 是 (无空格)' if ': ' not in state_decoded else '❌ 否 (有空格)'}")
    print(f"  原始内容: {state_decoded}\n")

    print(f"State 字段:")
    for key, value in state_json.items():
        print(f"  - {key}: {value}")

    print("\n【4. 关键检查项】")
    print("-" * 80)

    checks = [
        ("State 格式", "紧凑JSON (无空格)", ": " not in state_decoded),
        ("State 编码", "Base64", state == base64.b64encode(state_decoded.encode()).decode()),
        ("State URL编码", "未被编码 (=保持原样)", "=" in state),
        ("app_id 一致性", f"匹配 {app_id}", state_json.get("app_id") == app_id),
        ("redirect_uri 一致性", redirect_uri, state_json.get("redirect_uri") == redirect_uri),
        ("timestamp 存在", "是否有时间戳", "timestamp" in state_json),
    ]

    all_passed = True
    for check_name, expected, result in checks:
        status = "✓" if result else "❌"
        print(f"{status} {check_name:25} = {expected}")
        if not result:
            all_passed = False

    print("\n【5. 后续步骤】")
    print("-" * 80)

    if all_passed:
        print("✓ 所有检查通过！现在可以进行实际授权测试:")
        print("  1. 复制上面的授权 URL")
        print("  2. 在浏览器中打开该 URL")
        print("  3. 完成飞书登录授权")
        print("  4. 浏览器会重定向到 http://localhost:3333/callback?code=xxx&state=yyy")
        print("  5. 复制 code 参数值")
        print("  6. 粘贴到 setup_user_auth.py 脚本中")
    else:
        print("❌ 某些检查未通过，请查看上面的详细信息")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
