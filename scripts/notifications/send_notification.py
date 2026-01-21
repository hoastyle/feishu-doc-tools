#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书消息发送演示

展示如何使用通知系统给飞书发送卡片消息。

Usage:
    # 使用环境变量配置
    export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL
    python scripts/notifications/send_notification.py

    # 直接在命令行中指定 URL
    python scripts/notifications/send_notification.py --url YOUR_WEBHOOK_URL
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.templates.builder import CardBuilder
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings


def send_simple_message(webhook_url: str):
    """发送简单消息"""
    print("\n📝 发送简单消息...")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        card = (CardBuilder()
            .header("✅ 操作成功", status="success")
            .markdown("**文件**: README.md\n**行数**: 156 行")
            .build())

        success = channel.send(card.to_dict(), "simple_message")
        return success


def send_metadata_message(webhook_url: str):
    """发送带元数据的消息"""
    print("\n📝 发送带元数据的消息...")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        card = (CardBuilder()
            .header("📊 任务完成", status="success")
            .metadata("任务", "upload_docs")
            .metadata("耗时", "2.3 秒")
            .markdown("**详情**: 5 个文档已成功上传")
            .build())

        success = channel.send(card.to_dict(), "metadata_message")
        return success


def send_error_message(webhook_url: str):
    """发送错误消息"""
    print("\n📝 发送错误消息...")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        card = (CardBuilder()
            .header("❌ 上传失败", status="error")
            .metadata("文件", "CONFIG.md")
            .metadata("错误", "ConnectionError")
            .markdown("**原因**: 数据库连接超时")
            .note("请检查网络连接后重试")
            .build())

        success = channel.send(card.to_dict(), "error_message")
        return success


def send_statistics_message(webhook_url: str):
    """发送统计消息"""
    print("\n📝 发送统计消息...")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        card = (CardBuilder()
            .header("📈 批量上传统计", status="success")
            .metadata("总数", "8 个文档")
            .metadata("成功", "7 个")
            .metadata("失败", "1 个")
            .markdown("**上传列表**:\n- README.md (156 行)\n- API.md (234 行)\n- GUIDE.md (412 行)")
            .divider()
            .note("总耗时: 3.2 秒")
            .build())

        success = channel.send(card.to_dict(), "statistics_message")
        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="发送飞书卡片消息演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用环境变量
  export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL
  python scripts/notifications/send_notification.py

  # 指定 URL
  python scripts/notifications/send_notification.py --url YOUR_WEBHOOK_URL

  # 只发送简单消息
  python scripts/notifications/send_notification.py --type simple
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--type",
        choices=["simple", "metadata", "error", "statistics", "all"],
        default="all",
        help="消息类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📤 飞书消息发送演示")
    print("=" * 70)

    # 加载配置
    if args.url:
        webhook_url = args.url
    else:
        settings = create_settings()
        is_valid, missing = settings.validate_required_fields()
        if not is_valid:
            print(f"\n❌ 配置不完整！缺少: {', '.join(missing)}")
            print("\n请设置环境变量:")
            print("   export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL")
            return 1
        webhook_url = settings.webhook_url

    print(f"\n📡 Webhook URL: {webhook_url[:50]}...")

    # 根据类型发送消息
    results = []

    if args.type in ["simple", "all"]:
        results.append(("简单消息", send_simple_message(webhook_url)))

    if args.type in ["metadata", "all"]:
        results.append(("元数据消息", send_metadata_message(webhook_url)))

    if args.type in ["error", "all"]:
        results.append(("错误消息", send_error_message(webhook_url)))

    if args.type in ["statistics", "all"]:
        results.append(("统计消息", send_statistics_message(webhook_url)))

    # 总结
    print("\n" + "=" * 70)
    print("📊 发送结果")
    print("=" * 70)

    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {name}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n   总计: {passed}/{total} 成功")

    if passed == total:
        print("\n🎉 所有消息发送成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 条消息发送失败")
        return 1


if __name__ == '__main__':
    exit(main())
