#!/usr/bin/env python3
"""
飞书应用状态诊断脚本

权限已确认的情况下，检查应用状态和配置。

使用方法:
    python scripts/diagnose_app_status.py
"""

import json
from pathlib import Path

APP_ID = "cli_a9e09cc76d345bb4"
REDIRECT_URI = "http://localhost:3333/callback"

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    print(f"\n【{title}】")
    print("-" * 80)

def main():
    print_header("飞书应用状态诊断清单")
    print()
    print(f"App ID: {APP_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()
    print("请登录飞书开发者后台确认以下配置:")
    print("https://open.feishu.cn/app")

    # 1. 应用基本信息
    print_section("1. 应用基本信息")
    print("路径: 应用详情 > 凭证与基础信息")
    print()
    print("请确认以下信息:")
    print()
    questions = {
        "app_type": "应用类型是什么？",
        "app_status": "应用状态是什么？",
        "app_available": "应用可用范围是什么？",
    }

    options = {
        "app_type": ["自建应用（企业内部应用）", "商店应用"],
        "app_status": ["已启用", "停用", "未发布"],
        "app_available": ["仅本企业", "所有企业", "指定企业"],
    }

    for key, question in questions.items():
        print(f"{question}")
        for i, option in enumerate(options[key], 1):
            print(f"  {i}. {option}")
        print()

    # 2. 应用发布状态
    print_section("2. 应用发布/安装状态")
    print()
    print("关键检查:")
    print("  [ ] 应用是否已启用（不是'停用'状态）")
    print("  [ ] 应用是否已发布/上线")
    print("  [ ] 应用是否已安装到测试租户")
    print()
    print("错误码参考:")
    print("  20069 - 应用未启用")
    print("  20009 - 租户未安装应用")
    print("  20048 - 应用不存在")
    print()

    # 3. 重定向 URI 配置
    print_section("3. 重定向 URI 配置")
    print("路径: 应用详情 > 开发配置 > 安全设置 > 重定向 URL")
    print()
    print("请确认:")
    print(f"  [ ] 已配置: {REDIRECT_URI}")
    print(f"  [ ] 没有尾部斜杠: {REDIRECT_URI}/ ❌")
    print(f"  [ ] 协议正确: https://localhost:3333/callback ❌")
    print()
    print("错误码参考:")
    print("  20029 - redirect_uri 请求不合法（端口不匹配）")
    print("  20071 - redirect_uri 与授权时不一致")
    print()

    # 4. 测试用户权限
    print_section("4. 测试用户权限")
    print()
    print("请确认:")
    print("  [ ] 测试用户在应用可用企业内")
    print("  [ ] 测试用户有应用使用权限")
    print("  [ ] 测试用户状态正常（未被停用或删除）")
    print()
    print("错误码参考:")
    print("  20010 - 用户无应用使用权限")
    print("  20066 - 用户状态非法")
    print()

    # 5. 权限确认
    print_section("5. 用户权限确认")
    print("路径: 应用详情 > 开发配置 > 权限管理 > API 权限")
    print()
    print("✅ 已确认用户权限包括:")
    required_scopes = [
        "contact:user.base:readonly",
        "docx:document",
        "docx:document:readonly",
        "wiki:wiki:readonly",
        "offline_access",
    ]
    for scope in required_scopes:
        print(f"  ✅ {scope}")
    print()

    # 6. 诊断测试 URLs
    print_section("6. 诊断测试 URLs")
    print("请依次测试以下 URL:")
    print()

    test_urls = [
        {
            "name": "测试 A: 最简化（无 scope，无 state）",
            "url": f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&response_type=code",
            "purpose": "如果成功 → scope 参数有问题",
        },
        {
            "name": "测试 B: 最小权限",
            "url": f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=contact%3Auser.base%3Areadonly&response_type=code&state=123456",
            "purpose": "如果成功 → 其他 scope 有问题",
        },
        {
            "name": "测试 C: 单独测试 offline_access",
            "url": f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=offline_access&response_type=code&state=123456",
            "purpose": "如果成功 → 其他 scope 有问题",
        },
    ]

    for i, test in enumerate(test_urls, 1):
        print(f"{test['name']}")
        print(f"URL:")
        print(f"  {test['url']}")
        print(f"说明: {test['purpose']}")
        print()

    # 7. 结果分析
    print_section("7. 结果分析")
    print()
    print("根据测试结果判断:")
    print()
    print("场景 1: 测试 A 失败")
    print("  → 应用状态或用户权限问题")
    print("  → 检查: 应用是否启用/发布/安装")
    print("  → 检查: 测试用户是否有权限")
    print()
    print("场景 2: 测试 A 成功，测试 B/C 失败")
    print("  → Scope 权限问题（虽然已申请，但可能有其他问题）")
    print("  → 检查: 权限状态是否为'已开通'")
    print("  → 检查: 是否有权限审核限制")
    print()
    print("场景 3: 所有测试都失败")
    print("  → 应用配置问题")
    print("  → 联系飞书技术支持")
    print()

    # 8. 联系支持
    print_section("8. 联系飞书技术支持")
    print()
    print("如果所有测试都失败，联系飞书技术支持时请提供:")
    print()
    print("  应用信息:")
    print(f"    App ID: {APP_ID}")
    print("    应用名称: [填写]")
    print("    应用类型: [填写]")
    print("    应用状态: [填写]")
    print()
    print("  错误信息:")
    print("    错误码: 400")
    print("    错误描述: state 参数格式错误")
    print("    出现位置: [打开 URL 时 / 点击授权后]")
    print("    Log ID: [从错误页面获取]")
    print()
    print("  已尝试的方案:")
    print("    1. ✅ 测试了 6 种 state 格式 - 全部失败")
    print("    2. ✅ 测试了新旧 API 版本 - 全部失败")
    print("    3. ✅ 修复了 URL 编码问题 - 仍然失败")
    print("    4. ✅ 修复了 redirect_uri 端口 - 仍然失败")
    print("    5. ✅ 确认了所有权限已申请 - 仍然失败")
    print("    6. ✅ 检查了应用状态配置 - 仍然失败")
    print()

    # 9. 导出检查清单
    print_section("9. 导出检查清单")
    checklist = {
        "app_info": {
            "app_id": APP_ID,
            "app_type": "[填写: 自建应用/商店应用]",
            "app_status": "[填写: 已启用/停用/未发布]",
            "app_available": "[填写: 仅本企业/所有企业/指定企业]",
        },
        "redirect_uri": {
            "configured": REDIRECT_URI,
            "verified": "[ ] 已确认配置正确",
        },
        "user_info": {
            "test_user": "[填写: 测试用户飞书账号]",
            "has_permission": "[ ] 用户有应用使用权限",
            "user_status": "[填写: 正常/停用/已删除]",
        },
        "test_results": {
            "test_a_minimal": "[ ] 成功 / [ ] 失败",
            "test_b_minimal_scope": "[ ] 成功 / [ ] 失败",
            "test_c_offline_access": "[ ] 成功 / [ ] 失败",
        },
    }

    checklist_file = Path("app_status_checklist.json")
    with open(checklist_file, "w", encoding="utf-8") as f:
        json.dump(checklist, f, indent=2, ensure_ascii=False)

    print(f"✅ 检查清单已导出到: {checklist_file}")
    print("   请填写完成后发送给飞书技术支持")
    print()

    print("=" * 80)
    print("诊断完成！")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
