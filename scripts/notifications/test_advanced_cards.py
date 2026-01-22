#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书高级卡片功能演示

展示 CardBuilder 的高级功能：
- 多列布局 (columns)
- 可折叠面板 (collapsible_panel)
- 操作按钮 (action_button)
- 分隔线 (divider)
- 不同颜色主题

Usage:
    # 演示所有高级功能
    python scripts/notifications/test_advanced_cards.py

    # 演示特定功能
    python scripts/notifications/test_advanced_cards.py --type columns
    python scripts/notifications/test_advanced_cards.py --type collapsible
    python scripts/notifications/test_advanced_cards.py --type buttons
    python scripts/notifications/test_advanced_cards.py --type colors
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


# ========== 高级卡片模板 ==========

def demo_columns(webhook_url: str):
    """演示多列布局"""
    print("\n📝 演示：多列布局")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 双列布局 - auto宽度
        card1 = (CardBuilder()
            .header("📊 双列布局", status="info")
            .markdown("使用 **auto** 宽度的双列布局")
            .columns()
                .column("文件名", "README.md", width="auto")
                .column("状态", "已上传", width="auto")
            .end_columns()
            .divider()
            .columns()
                .column("大小", "12.5 KB", width="auto")
                .column("修改时间", "2026-01-20", width="auto")
            .end_columns()
            .build())

        # 三列布局
        card2 = (CardBuilder()
            .header("📈 三列布局", status="success")
            .markdown("使用 **weighted** 宽度的三列布局")
            .columns()
                .column("任务", "数据同步", width="weighted", weight=2)
                .column("进度", "75%", width="weighted", weight=1)
                .column("状态", "进行中", width="weighted", weight=1)
            .end_columns()
            .divider()
            .columns()
                .column("开始时间", "10:00", width="weighted", weight=1)
                .column("耗时", "2分30秒", width="weighted", weight=1)
                .column("预计完成", "10:05", width="weighted", weight=1)
            .end_columns()
            .build())

        # 混合布局（auto + weighted）
        card3 = (CardBuilder()
            .header("🎯 混合布局", status="warning")
            .markdown("混合使用 **auto** 和 **weighted** 宽度")
            .columns()
                .column("标签", "重要", width="auto")
                .column("任务名称", "完成API接口开发", width="weighted", weight=3)
                .column("优先级", "高", width="auto")
            .end_columns()
            .build())

        # 发送
        r1 = channel.send(card1.to_dict(), "columns_2col")
        r2 = channel.send(card2.to_dict(), "columns_3col")
        r3 = channel.send(card3.to_dict(), "columns_mixed")

        results = [("双列布局", r1), ("三列布局", r2), ("混合布局", r3)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_collapsible(webhook_url: str):
    """演示可折叠面板"""
    print("\n📝 演示：可折叠面板")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 可折叠的错误详情
        card1 = (CardBuilder()
            .header("❌ 同步失败", status="error")
            .metadata("任务", "数据同步")
            .metadata("失败数", "3 个文件")
            .collapsible("错误详情",
                       "```\nConnectionError: Connection refused\n"
                       "  at /src/api/client.py:145\n"
                       "  at processTicksAndRejections (node:internal/process/task_queues:96)\n"
                       "```")
            .note("请检查网络连接后重试")
            .build())

        # 可折叠的详细信息（JSON格式）
        card2 = (CardBuilder()
            .header("📦 任务完成", status="success")
            .metadata("任务", "批量上传")
            .metadata("成功", "8/8")
            .collapsible("详细信息",
                       "```json\n"
                       "{\n"
                       "  \"total\": 8,\n"
                       "  \"success\": 8,\n"
                       "  \"failed\": 0,\n"
                       "  \"duration\": \"3.2s\",\n"
                       "  \"files\": [\n"
                       "    \"README.md\",\n"
                       "    \"API.md\",\n"
                       "    \"GUIDE.md\"\n"
                       "  ]\n"
                       "}\n"
                       "```")
            .build())

        # 多个可折叠面板
        card3 = (CardBuilder()
            .header("🔍 系统诊断", status="info")
            .markdown("系统运行正常，以下是详细信息")
            .divider()
            .collapsible("环境信息",
                       "- **系统**: Linux 5.15\n"
                       "- **Python**: 3.8.1\n"
                       "- **内存**: 2.3GB / 8GB")
            .divider()
            .collapsible("性能指标",
                       "- **CPU**: 45%\n"
                       "- **磁盘IO**: 125 MB/s\n"
                       "- **网络**: 1.2 Gbps")
            .build())

        # 发送
        r1 = channel.send(card1.to_dict(), "collapsible_error")
        r2 = channel.send(card2.to_dict(), "collapsible_json")
        r3 = channel.send(card3.to_dict(), "collapsible_multiple")

        results = [("错误详情", r1), ("JSON数据", r2), ("多个面板", r3)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_buttons(webhook_url: str):
    """演示操作按钮"""
    print("\n📝 演示：操作按钮")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 注意：飞书卡片消息中的按钮需要配合交互功能使用
        # 这里演示如何构建包含按钮的卡片结构

        card1 = (CardBuilder()
            .header("🔗 快捷操作", status="info")
            .markdown("**文档**: API Reference\n**状态**: 需要审核")
            .divider()
            .markdown("📌 **操作按钮**（需要配置交互功能）")
            .markdown("按钮需要配合飞书卡片的交互功能使用")
            .note("当前 Webhook 模式不支持交互按钮，需要使用机器人应用模式")
            .build())

        # 实际使用中的按钮示例（仅展示结构）
        card2 = (CardBuilder()
            .header("📋 审批请求", status="warning")
            .metadata("申请人", "张三")
            .metadata("类型", "文档发布")
            .markdown("**文档**: 新功能API文档\n**说明**: 包含3个新增接口")
            .divider()
            .markdown("⚠️ **注意**: 审批功能需要配置飞书机器人应用")
            .build())

        r1 = channel.send(card1.to_dict(), "buttons_demo")
        r2 = channel.send(card2.to_dict(), "approval_request")

        results = [("按钮演示", r1), ("审批请求", r2)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_colors(webhook_url: str):
    """演示不同颜色主题"""
    print("\n📝 演示：颜色主题")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # Wathet (浅蓝) - 运行中
        card1 = (CardBuilder()
            .header("⏳ 任务运行中", status="running", color="wathet")
            .metadata("任务", "数据同步")
            .markdown("正在同步数据，请稍候...")
            .build())

        # Green - 成功
        card2 = (CardBuilder()
            .header("✅ 操作成功", status="success", color="green")
            .metadata("任务", "文件上传")
            .markdown("所有文件已成功上传")
            .build())

        # Red - 失败
        card3 = (CardBuilder()
            .header("❌ 操作失败", status="failed", color="red")
            .metadata("错误", "ConnectionError")
            .markdown("连接数据库失败")
            .note("请检查数据库服务状态")
            .build())

        # Orange - 警告
        card4 = (CardBuilder()
            .header("⚠️ 性能警告", status="warning", color="orange")
            .metadata("指标", "CPU使用率")
            .markdown("当前CPU使用率：85%")
            .note("建议检查系统负载")
            .build())

        # Blue - 信息
        card5 = (CardBuilder()
            .header("🔔 系统通知", status="info", color="blue")
            .metadata("类型", "安全更新")
            .markdown("系统将于今晚进行安全更新")
            .build())

        # 发送所有卡片
        cards = [
            ("Wathet (运行中)", card1),
            ("Green (成功)", card2),
            ("Red (失败)", card3),
            ("Orange (警告)", card4),
            ("Blue (信息)", card5),
        ]

        results = []
        for name, card in cards:
            success = channel.send(card.to_dict(), f"color_{name.split()[0].lower()}")
            results.append((name, success))

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_divider(webhook_url: str):
    """演示分隔线使用"""
    print("\n📝 演示：分隔线使用")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 使用分隔线组织内容
        card = (CardBuilder()
            .header("📋 任务报告", status="success")
            .markdown("**任务名称**: 数据迁移")
            .divider()
            .metadata("开始时间", "10:00")
            .metadata("结束时间", "10:15")
            .metadata("耗时", "15分钟")
            .divider()
            .markdown("**统计信息**:")
            .markdown("- 迁移文件: 156 个\n- 总大小: 2.3 GB\n- 成功率: 100%")
            .divider()
            .note("所有任务已完成，未发现错误")
            .build())

        success = channel.send(card.to_dict(), "divider_demo")

        status = "✅" if success else "❌"
        print(f"   {status} 分隔线演示")

        return success


def demo_combined(webhook_url: str):
    """演示组合使用多种功能"""
    print("\n📝 演示：组合使用")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 组合使用 columns, collapsible, divider
        card = (CardBuilder()
            .header("🚀 批量上传完成", status="success", color="green")
            .columns()
                .column("总数", "156 个", width="auto")
                .column("成功", "155 个", width="auto")
                .column("失败", "1 个", width="auto")
            .end_columns()
            .divider()
            .markdown("**详细统计**:")
            .markdown("- 总大小: 2.3 GB\n- 平均速度: 12.5 MB/s\n- 总耗时: 3分15秒")
            .divider()
            .collapsible("失败文件",
                       "```\n1. large_file.dat (超过 100MB 限制)\n"
                       "   错误: File size exceeds limit\n"
                       "```")
            .divider()
            .collapsible("上传日志",
                       "```json\n"
                       "{\n"
                       "  \"start_time\": \"10:00:00\",\n"
                       "  \"end_time\": \"10:03:15\",\n"
                       "  \"duration\": \"195s\",\n"
                       "  \"average_speed\": \"12.5 MB/s\"\n"
                       "}\n"
                       "```")
            .divider()
            .note("💡 提示: 失败的文件可以稍后手动上传")
            .build())

        success = channel.send(card.to_dict(), "combined_demo")

        status = "✅" if success else "❌"
        print(f"   {status} 组合演示")

        return success


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="飞书高级卡片功能演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能类型:
  columns      - 多列布局演示
  collapsible  - 可折叠面板演示
  buttons      - 操作按钮演示
  colors       - 颜色主题演示
  divider      - 分隔线使用演示
  combined     - 组合使用演示
  all          - 演示所有功能

示例:
  # 演示所有功能
  python scripts/notifications/test_advanced_cards.py

  # 演示特定功能
  python scripts/notifications/test_advanced_cards.py --type columns
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--type",
        choices=["columns", "collapsible", "buttons", "colors", "divider", "combined", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 飞书高级卡片功能演示")
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

    # 演示函数映射
    demos = {
        "columns": demo_columns,
        "collapsible": demo_collapsible,
        "buttons": demo_buttons,
        "colors": demo_colors,
        "divider": demo_divider,
        "combined": demo_combined,
    }

    # 运行演示
    import time

    results = []

    if args.type == "all":
        for demo_name, demo_func in demos.items():
            try:
                success = demo_func(webhook_url)
                results.append((demo_name, success))
                time.sleep(1)  # 避免发送过快
            except Exception as e:
                print(f"   💥 {demo_name} 演示失败: {e}")
                results.append((demo_name, False))
    else:
        demo_func = demos[args.type]
        try:
            success = demo_func(webhook_url)
            results.append((args.type, success))
        except Exception as e:
            print(f"   💥 演示失败: {e}")
            results.append((args.type, False))

    # 总结
    print("\n" + "=" * 70)
    print("📊 演示结果")
    print("=" * 70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name:15s}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n   总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有演示完成！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个演示失败")
        return 1


if __name__ == '__main__':
    exit(main())
