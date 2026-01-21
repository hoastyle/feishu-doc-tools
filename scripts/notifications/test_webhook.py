#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feishu Webhook 测试工具

测试飞书 Webhook 配置是否正确，发送测试消息验证连接。

Usage:
    python scripts/notifications/test_webhook.py
    FEISHU_WEBHOOK_URL=https://... python scripts/notifications/test_webhook.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.templates.builder import CardBuilder
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings
import httpx
import json
import time


def test_simple_text(url: str) -> bool:
    """测试简单文本消息"""
    print("\n📝 测试 1: 简单文本消息")

    payload = {
        "msg_type": "text",
        "content": {
            "text": "🔔 Webhook 测试成功！这是一条简单的文本消息。"
        }
    }

    try:
        response = httpx.post(
            url,
            headers={"Content-Type": "application/json"},
            content=json.dumps(payload, ensure_ascii=False),
            timeout=10
        )
        resp = response.json()
        code = resp.get("code")

        if code == 0:
            print("   ✅ 简单文本消息发送成功！")
            return True
        else:
            print(f"   ❌ 错误: code {code} - {resp.get('msg')}")
            return False
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False


def test_interactive_card(url: str) -> bool:
    """测试交互式卡片"""
    print("\n📝 测试 2: 交互式卡片")

    card = (CardBuilder()
        .header("测试消息", status="info")
        .markdown("这是一条**测试消息**！如果你看到这条消息，说明配置正确！")
        .build())

    payload = {
        "msg_type": "interactive",
        "card": card.to_dict()
    }

    try:
        response = httpx.post(
            url,
            headers={"Content-Type": "application/json"},
            content=json.dumps(payload, ensure_ascii=False),
            timeout=10
        )
        resp = response.json()
        code = resp.get("code")

        if code == 0:
            print("   ✅ 交互式卡片发送成功！")
            return True
        else:
            print(f"   ❌ 错误: code {code} - {resp.get('msg')}")
            return False
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False


def test_webhook_channel(url: str) -> bool:
    """测试 WebhookChannel"""
    print("\n📝 测试 3: WebhookChannel")

    settings = create_settings(webhook_url=url)

    try:
        with WebhookChannel(settings) as channel:
            card = (CardBuilder()
                .header("✅ 测试成功", status="success")
                .markdown("使用 **WebhookChannel** 发送的消息")
                .build())

            success = channel.send(card.to_dict(), "test")
            if success:
                print("   ✅ WebhookChannel 发送成功！")
                return True
            else:
                print("   ❌ WebhookChannel 发送失败")
                return False
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False


def test_card_variations(url: str) -> bool:
    """测试不同类型的卡片"""
    print("\n📝 测试 4: 不同类型的卡片")

    settings = create_settings(webhook_url=url)

    try:
        with WebhookChannel(settings) as channel:
            # 成功卡片
            success_card = (CardBuilder()
                .header("✅ 操作成功", status="success")
                .markdown("**任务**: 测试任务\n**状态**: 已完成")
                .build())

            # 警告卡片
            warning_card = (CardBuilder()
                .header("⚠️  需要注意", status="warning")
                .markdown("**提醒**: 这是一条警告消息")
                .build())

            # 发送
            r1 = channel.send(success_card.to_dict(), "test_success")
            time.sleep(0.5)
            r2 = channel.send(warning_card.to_dict(), "test_warning")

            if r1 and r2:
                print("   ✅ 多种类型卡片发送成功！")
                return True
            else:
                print("   ❌ 部分卡片发送失败")
                return False
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 飞书 Webhook 测试工具")
    print("=" * 70)

    # 加载配置
    settings = create_settings()

    # 验证配置
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print("\n❌ 配置不完整！")
        print(f"   缺少字段: {', '.join(missing)}")
        print("\n请设置环境变量:")
        print("   export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL")
        print("\n或在 .env 文件中配置:")
        print("   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL")
        return 1

    url = settings.webhook_url
    print(f"\n📡 Webhook URL: {url[:50]}...")
    print(f"   完整 URL: {url}")

    # 运行测试
    results = []

    results.append(("简单文本消息", test_simple_text(url)))
    time.sleep(1)

    results.append(("交互式卡片", test_interactive_card(url)))
    time.sleep(1)

    results.append(("WebhookChannel", test_webhook_channel(url)))
    time.sleep(1)

    results.append(("多种类型卡片", test_card_variations(url)))

    # 总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name:20s}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n   总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！Webhook 配置正确！")
        return 0
    elif passed > 0:
        print("\n⚠️  部分测试通过，请检查失败的测试")
        return 1
    else:
        print("\n❌ 所有测试失败，请检查 Webhook URL 配置")
        return 1


if __name__ == '__main__':
    exit(main())
