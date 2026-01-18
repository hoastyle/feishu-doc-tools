#!/usr/bin/env python3
"""
Scope 权限测试脚本

测试不同的 scope 组合，验证是否是权限未申请导致的"state格式错误"。

使用方法:
    python test_scope_permissions.py
"""

from urllib.parse import quote
import json

APP_ID = "cli_a9e09cc76d345bb4"
REDIRECT_URI = "http://localhost:3333/callback"

# 生成授权 URL 的函数
def generate_auth_url(scope: str, state: str = "123456") -> str:
    """生成授权 URL"""
    base_url = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    params = {
        "client_id": APP_ID,
        "redirect_uri": quote(REDIRECT_URI, safe=''),
        "scope": quote(scope, safe=''),
        "response_type": "code",
        "state": state,
    }
    url = f"{base_url}?{ '&'.join([f'{k}={v}' for k, v in params.items()])}"
    return url

# 测试用例
test_cases = [
    {
        "name": "测试 1: 最小权限（contact:user.base:readonly）",
        "scope": "contact:user.base:readonly",
        "description": "最常见的用户权限，几乎所有应用都有",
        "expected": "✅ 如果成功，说明问题是 scope 权限",
    },
    {
        "name": "测试 2: 只有 offline_access",
        "scope": "offline_access",
        "description": "只请求离线访问权限",
        "expected": "✅ 如果成功，说明其他权限未申请",
    },
    {
        "name": "测试 3: 完全不传 scope",
        "scope": "",
        "description": "不传递任何权限参数",
        "expected": "✅ 如果成功，说明所有 scope 都有问题",
    },
    {
        "name": "测试 4: 单独测试 docx:document",
        "scope": "docx:document",
        "description": "只测试文档创建权限",
        "expected": "❌ 如果失败，说明该权限未申请",
    },
    {
        "name": "测试 5: 单独测试 wiki:wiki:readonly",
        "scope": "wiki:wiki:readonly",
        "description": "只测试知识库只读权限",
        "expected": "❌ 如果失败，说明该权限未申请",
    },
    {
        "name": "测试 6: 当前代码使用的完整 scope",
        "scope": "docx:document docx:document:readonly wiki:wiki:readonly offline_access",
        "description": "当前 generate_oauth_url() 使用的 scope",
        "expected": "❌ 预期失败（问题复现）",
    },
]

def main():
    print("=" * 80)
    print("飞书 OAuth Scope 权限测试")
    print("=" * 80)
    print()
    print(f"App ID: {APP_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()
    print("=" * 80)
    print()

    # 生成测试 URLs
    for i, test in enumerate(test_cases, 1):
        print(f"【{test['name']}】")
        print(f"说明: {test['description']}")
        print(f"Scope: {test['scope'] or '(空)'}")
        print(f"预期: {test['expected']}")
        print()
        url = generate_auth_url(test['scope'])
        print(f"URL:")
        # 分行显示 URL 以便复制
        if len(url) > 100:
            # 按 & 分割参数
            parts = url.split("&")
            for j, part in enumerate(parts):
                if j == 0:
                    print(f"  {part}")
                else:
                    print(f"  &{part}")
        else:
            print(f"  {url}")
        print()
        print("-" * 80)
        print()

    # 使用指南
    print("=" * 80)
    print("测试步骤")
    print("=" * 80)
    print()
    print("1. 依次复制上面的 URL 到浏览器中访问")
    print("2. 观察每个 URL 的结果:")
    print("   - ✅ 成功：正常显示飞书授权页面")
    print("   - ❌ 失败：显示错误页面（state格式错误）")
    print()
    print("3. 结果分析:")
    print("   - 如果测试 1-3 都成功 → 问题确实是 scope 权限未申请")
    print("   - 如果测试 1-3 都失败 → 问题可能是应用状态/用户权限")
    print("   - 如果测试 4-5 失败 → 对应权限未在飞书后台申请")
    print()
    print("4. 飞书后台权限申请:")
    print("   访问: https://open.feishu.cn/app")
    print("   路径: 开发配置 > 权限管理 > API 权限")
    print()
    print("=" * 80)
    print()

    # 导出为 JSON 文件
    output_file = "scope_test_urls.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([
            {
                "name": test["name"],
                "scope": test["scope"],
                "description": test["description"],
                "url": generate_auth_url(test["scope"]),
            }
            for test in test_cases
        ], f, indent=2, ensure_ascii=False)

    print(f"✅ 测试 URLs 已导出到: {output_file}")
    print()

if __name__ == "__main__":
    main()
