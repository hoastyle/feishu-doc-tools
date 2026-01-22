#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书高级功能演示脚本

展示 CardBuilder 的新增高级功能：
- Image Element - 图片显示 (需要预先上传的图片 key)
- Progress Bar - 进度条展示 (支持多种颜色)
- Person Tag - 用户 @提及
- DateTime - 日期时间显示 (多种模式)
- Combined - 所有功能组合使用

Usage:
    # 演示所有功能
    python scripts/notifications/demo_advanced_features.py

    # 演示特定功能
    python scripts/notifications/demo_advanced_features.py --type image
    python scripts/notifications/demo_advanced_features.py --type progress
    python scripts/notifications/demo_advanced_features.py --type person
    python scripts/notifications/demo_advanced_features.py --type datetime
    python scripts/notifications/demo_advanced_features.py --type combined

    # 使用自定义图片 key
    python scripts/notifications/demo_advanced_features.py --type image --img-key img_v7_xxxxx
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.templates.builder import CardBuilder
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings
from notifications.blocks.blocks import person, markdown as md


# ========== Demo Functions ==========

def demo_image(webhook_url: str, img_key: str = None):
    """演示图片元素功能

    Args:
        webhook_url: 飞书 Webhook URL
        img_key: 预上传的图片 key (可选，使用示例 key 作为后备)
    """
    print("\n📸 演示：图片元素 (Image Element)")
    print(f"   使用图片 key: {img_key or '示例 key'}")

    settings = create_settings(webhook_url=webhook_url)

    # 使用提供的 key 或示例 key
    # 注意：实际使用时需要先通过飞书 API 上传图片获取 img_key
    actual_img_key = img_key or "img_v7_04b2e9fc-8cd9-4d0e-b7a7-5e7d12345678"

    with WebhookChannel(settings) as channel:
        # 1. 基础图片展示 - fit_center 模式
        card1 = (CardBuilder()
            .header("📸 图片展示 - 适应模式", status="info")
            .markdown("**模式**: fit_center (水平适应)")
            .markdown("**用途**: 截图预览、文档预览")
            .img(actual_img_key, alt="文档预览图", mode="fit_center")
            .divider()
            .markdown("**文件**: API架构图.png")
            .markdown("**大小**: 125 KB")
            .build())

        # 2. 图片展示 - crop_center 模式
        card2 = (CardBuilder()
            .header("🖼️ 图片展示 - 裁剪模式", status="info")
            .markdown("**模式**: crop_center (居中裁剪)")
            .markdown("**用途**: 头像、封面图")
            .img(actual_img_key, alt="用户头像", mode="crop_center")
            .divider()
            .note("图片以居中裁剪方式显示")
            .build())

        # 3. 图片 + 说明文字组合
        card3 = (CardBuilder()
            .header("🎨 图片 + 说明", status="success")
            .markdown("**图表**: 服务器性能趋势")
            .markdown("**时间**: 2026-01-22 14:00")
            .img(actual_img_key, alt="性能趋势图", mode="fit_center")
            .divider()
            .columns()
                .column("CPU", "45%", width="auto")
                .column("内存", "62%", width="auto")
                .column("网络", "28%", width="auto")
            .end_columns()
            .divider()
            .note("系统运行正常，未发现异常")
            .build())

        # 发送所有卡片
        cards = [
            ("适应模式", card1),
            ("裁剪模式", card2),
            ("图片+说明", card3),
        ]

        results = []
        for name, card in cards:
            try:
                success = channel.send(card.to_dict(), f"image_{name}")
                results.append((name, success))
                status = "✅" if success else "❌"
                print(f"   {status} {name}")
            except Exception as e:
                print(f"   💥 {name} 发送失败: {e}")
                results.append((name, False))

        return all(s for _, s in results)


def demo_progress(webhook_url: str):
    """演示进度条功能"""
    print("\n📊 演示：进度条 (Progress Bar)")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 1. 不同颜色的进度条
        card1 = (CardBuilder()
            .header("🔵 进度条颜色展示", status="info")
            .markdown("**蓝色** - 运行中 (默认)")
            .progress("60", "100", color="blue")
            .divider()
            .markdown("**绿色** - 正常进度")
            .progress("80", "100", color="green")
            .divider()
            .markdown("**黄色** - 需要关注")
            .progress("45", "100", color="yellow")
            .build())

        # 2. 不同状态的任务进度
        card2 = (CardBuilder()
            .header("📈 文件同步进度", status="running", color="wathet")
            .metadata("任务", "同步文档到云端")
            .metadata("已处理", "156/200")
            .progress("156", "200", color="blue")
            .divider()
            .columns()
                .column("速度", "12.5 MB/s", width="weighted", weight=1)
                .column("已用", "2分30秒", width="weighted", weight=1)
                .column("剩余", "约45秒", width="weighted", weight=1)
            .end_columns()
            .divider()
            .note("💡 提示: 请勿关闭窗口")
            .build())

        # 3. 批量任务进度展示
        card3 = (CardBuilder()
            .header("🚀 批量任务执行中", status="running", color="wathet")
            .markdown("**任务组**: 数据导出")
            .divider()

            # 任务 1
            .markdown("**任务 1**: 用户数据导出")
            .progress("100", "100", color="green")
            .markdown("✅ 已完成")

            .divider()

            # 任务 2
            .markdown("**任务 2**: 订单数据导出")
            .progress("65", "100", color="blue")
            .markdown("⏳ 进行中...")

            .divider()

            # 任务 3
            .markdown("**任务 3**: 日志数据导出")
            .progress("0", "100", color="grey")
            .markdown("⏸️ 等待中")

            .divider()
            .note("总计 3 个任务，1 个已完成")
            .build())

        # 发送所有卡片
        cards = [
            ("颜色展示", card1),
            ("文件同步", card2),
            ("批量任务", card3),
        ]

        results = []
        for name, card in cards:
            try:
                success = channel.send(card.to_dict(), f"progress_{name}")
                results.append((name, success))
                status = "✅" if success else "❌"
                print(f"   {status} {name}")
            except Exception as e:
                print(f"   💥 {name} 发送失败: {e}")
                results.append((name, False))

        return all(s for _, s in results)


def demo_person(webhook_url: str):
    """演示用户 @提及 功能"""
    print("\n👤 演示：用户 @提及 (Person Tag)")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 注意：实际使用时需要替换为真实的 user_id
        # 这里使用示例 ID 进行演示
        user_ids = {
            "张三": "ou_7d8a9f6e5c4b3a2d1e0f9e8d7c6b5a4",
            "李四": "ou_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6",
            "王五": "ou_9z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4",
        }

        # 1. 单用户提及
        card1 = (CardBuilder()
            .header("📋 代码审查请求", status="info")
            .markdown("**PR**: #123 - 添加用户认证功能")
            .markdown("**分支**: feature/user-auth")
            .divider()
            .markdown("**请 @张三 帮忙审查以下模块**:")
            .markdown("- `auth.py` - 认证逻辑")
            .markdown("- `models.py` - 用户模型")
            .markdown("- `tests/` - 测试用例")
            .divider()
            .note("💡 使用 @提及 会向用户发送通知")
            .build())

        # 2. 多用户提及
        card2 = (CardBuilder()
            .header("👥 团队会议提醒", status="warning")
            .markdown("**会议**: 周度技术评审")
            .markdown("**时间**: 今天 15:00")
            .markdown("**地点**: 会议室 A")
            .divider()
            .markdown("**参会人员**:")
            .markdown(f"- @张三 - 后端开发")
            .markdown(f"- @李四 - 前端开发")
            .markdown(f"- @王五 - 测试工程师")
            .divider()
            .markdown("**议程**:")
            .markdown("1. API 接口设计评审")
            .markdown("2. 前端组件选型")
            .markdown("3. 测试计划讨论")
            .build())

        # 3. 用户提及 + 任务分配
        card3 = (CardBuilder()
            .header("📝 新任务分配", status="success")
            .markdown("**任务**: 实现数据导入功能")
            .markdown("**优先级**: 高")
            .markdown("**截止日期**: 2026-01-25")
            .divider()
            .columns()
                .column("负责人", "@张三", width="weighted", weight=1)
                .column("审核人", "@李四", width="weighted", weight=1)
                .column("测试", "@王五", width="weighted", weight=1)
            .end_columns()
            .divider()
            .markdown("**任务详情**:")
            .markdown("- 支持 CSV/Excel 格式")
            .markdown("- 数据验证和错误处理")
            .markdown("- 进度展示和日志记录")
            .divider()
            .note("⚠️ 请各位及时完成任务")
            .build())

        # 发送所有卡片
        cards = [
            ("单用户提及", card1),
            ("多用户提及", card2),
            ("任务分配", card3),
        ]

        results = []
        for name, card in cards:
            try:
                success = channel.send(card.to_dict(), f"person_{name}")
                results.append((name, success))
                status = "✅" if success else "❌"
                print(f"   {status} {name}")
            except Exception as e:
                print(f"   💥 {name} 发送失败: {e}")
                results.append((name, False))

        return all(s for _, s in results)


def demo_datetime(webhook_url: str):
    """演示日期时间显示功能"""
    print("\n📅 演示：日期时间 (DateTime)")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 1. 仅日期模式
        card1 = (CardBuilder()
            .header("📅 日期模式展示", status="info")
            .markdown("**计划日期**: ")
            .datetime("2026-01-25", mode="date")
            .divider()
            .markdown("**项目里程碑**: Beta 版本发布")
            .markdown("**说明**: 使用 date 模式仅显示日期")
            .build())

        # 2. 仅时间模式
        card2 = (CardBuilder()
            .header("⏰ 时间模式展示", status="info")
            .markdown("**每日例会**: ")
            .datetime("15:00", mode="time")
            .divider()
            .markdown("**会议时长**: 30 分钟")
            .markdown("**说明**: 使用 time 模式仅显示时间")
            .build())

        # 3. 日期时间模式
        card3 = (CardBuilder()
            .header("📆 日期时间模式展示", status="success")
            .markdown("**开始时间**: ")
            .datetime("2026-01-25 14:00", mode="datetime")
            .divider()
            .markdown("**会议**: 产品需求评审")
            .markdown("**地点**: 会议室 B")
            .markdown("**说明**: 使用 datetime 模式显示完整时间")
            .divider()
            .columns()
                .column("主持人", "张三", width="auto")
                .column("时长", "1小时", width="auto")
                .column("状态", "待开始", width="auto")
            .end_columns()
            .build())

        # 4. 多个时间点展示
        card4 = (CardBuilder()
            .header("🗓️ 项目时间线", status="warning")
            .markdown("**项目**: 新功能开发")
            .divider()

            # 里程碑 1
            .markdown("**需求评审**:")
            .datetime("2026-01-20 10:00", mode="datetime")
            .markdown("✅ 已完成")

            .divider()

            # 里程碑 2
            .markdown("**开发完成**:")
            .datetime("2026-01-25 18:00", mode="datetime")
            .markdown("⏳ 进行中")

            .divider()

            # 里程碑 3
            .markdown("**测试完成**:")
            .datetime("2026-01-28 18:00", mode="datetime")
            .markdown("⏸️ 待开始")

            .divider()

            # 里程碑 4
            .markdown("**上线发布**:")
            .datetime("2026-01-30 10:00", mode="datetime")
            .markdown("⏸️ 待开始")

            .divider()
            .note("💡 请按时完成各阶段任务")
            .build())

        # 发送所有卡片
        cards = [
            ("日期模式", card1),
            ("时间模式", card2),
            ("日期时间模式", card3),
            ("项目时间线", card4),
        ]

        results = []
        for name, card in cards:
            try:
                success = channel.send(card.to_dict(), f"datetime_{name}")
                results.append((name, success))
                status = "✅" if success else "❌"
                print(f"   {status} {name}")
            except Exception as e:
                print(f"   💥 {name} 发送失败: {e}")
                results.append((name, False))

        return all(s for _, s in results)


def demo_combined(webhook_url: str, img_key: str = None):
    """演示所有功能的组合使用"""
    print("\n🎨 演示：组合功能 (Combined)")

    settings = create_settings(webhook_url=webhook_url)

    # 使用提供的 key 或示例 key
    actual_img_key = img_key or "img_v7_04b2e9fc-8cd9-4d0e-b7a7-5e7d12345678"

    with WebhookChannel(settings) as channel:
        # 组合卡片：图片 + 进度条 + 日期时间 + 用户提及
        card1 = (CardBuilder()
            .header("🚀 项目进度报告", status="success", color="green")
            .markdown("**项目**: AI 助手开发")
            .markdown("**报告时间**: ")
            .datetime("2026-01-22 18:00", mode="datetime")
            .divider()

            # 进度展示
            .markdown("**整体进度**: ")
            .progress("75", "100", color="green")
            .divider()

            # 项目截图
            .markdown("**界面预览**:")
            .img(actual_img_key, alt="界面截图", mode="fit_center")
            .divider()

            # 任务状态
            .markdown("**模块状态**:")
            .columns()
                .column("对话", "✅", width="auto")
                .column("知识库", "✅", width="auto")
                .column("工具调用", "⏳", width="auto")
                .column("测试", "⏳", width="auto")
            .end_columns()
            .divider()

            # 团队成员
            .markdown("**团队成员**:")
            .markdown("- @张三 - 后端开发")
            .markdown("- @李四 - 前端开发")
            .markdown("- @王五 - 测试工程师")
            .divider()

            .note("📅 下次评审: 2026-01-25 14:00")
            .build())

        # 组合卡片：任务详情 + 所有元素
        card2 = (CardBuilder()
            .header("📋 详细任务卡片", status="running", color="wathet")
            .metadata("任务ID", "TASK-2026-0122")
            .metadata("优先级", "高")
            .divider()

            # 日期时间
            .markdown("**创建时间**: ")
            .datetime("2026-01-20 09:00", mode="datetime")
            .markdown("**截止时间**: ")
            .datetime("2026-01-25 18:00", mode="datetime")
            .divider()

            # 进度
            .markdown("**当前进度**: ")
            .progress("45", "100", color="blue")
            .divider()

            # 图片说明
            .markdown("**设计图**:")
            .img(actual_img_key, alt="设计草图", mode="fit_center")
            .divider()

            # 负责人
            .markdown("**负责人**: @张三")
            .markdown("**审核人**: @李四")
            .divider()

            # 可折叠详情
            .collapsible("任务描述",
                       "实现用户认证功能，包括：\n"
                       "- 用户注册和登录\n"
                       "- JWT Token 管理\n"
                       "- 权限验证中间件")
            .divider()

            .collapsible("技术栈",
                       "- 后端: Python + FastAPI\n"
                       "- 数据库: PostgreSQL\n"
                       "- 缓存: Redis\n"
                       "- 前端: Vue 3")
            .divider()

            .note("⚠️ 请按时完成任务，如有问题请及时沟通")
            .build())

        # 发送所有卡片
        cards = [
            ("项目报告", card1),
            ("任务详情", card2),
        ]

        results = []
        for name, card in cards:
            try:
                success = channel.send(card.to_dict(), f"combined_{name}")
                results.append((name, success))
                status = "✅" if success else "❌"
                print(f"   {status} {name}")
            except Exception as e:
                print(f"   💥 {name} 发送失败: {e}")
                results.append((name, False))

        return all(s for _, s in results)


# ========== Main Program ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="飞书高级功能演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
演示类型:
  image      - 图片元素演示 (需要 --img-key 或使用示例 key)
  progress   - 进度条演示 (多种颜色和状态)
  person     - 用户 @提及演示
  datetime   - 日期时间演示 (多种显示模式)
  combined   - 所有功能组合演示
  all        - 运行所有演示 (默认)

示例:
  # 演示所有功能
  python scripts/notifications/demo_advanced_features.py

  # 演示特定功能
  python scripts/notifications/demo_advanced_features.py --type progress

  # 使用自定义图片 key
  python scripts/notifications/demo_advanced_features.py --type image --img-key img_v7_xxxxx

注意事项:
  1. 图片演示需要预先上传图片到飞书并获取 img_key
  2. 用户 @提及需要真实的 user_id 才能正常显示
  3. Webhook URL 从环境变量 FEISHU_WEBHOOK_URL 读取，或使用 --url 参数
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--type",
        choices=["image", "progress", "person", "datetime", "combined", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    parser.add_argument(
        "--img-key",
        help="图片 key (用于 image 和 combined 演示，默认使用示例 key)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 飞书高级功能演示")
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
        "image": lambda: demo_image(webhook_url, args.img_key),
        "progress": lambda: demo_progress(webhook_url),
        "person": lambda: demo_person(webhook_url),
        "datetime": lambda: demo_datetime(webhook_url),
        "combined": lambda: demo_combined(webhook_url, args.img_key),
    }

    # 运行演示
    results = []

    if args.type == "all":
        # 运行所有演示
        for demo_name, demo_func in demos.items():
            try:
                print(f"\n{'=' * 70}")
                print(f"📍 开始演示: {demo_name.upper()}")
                print('=' * 70)
                success = demo_func()
                results.append((demo_name, success))
                time.sleep(1)  # 避免发送过快
            except Exception as e:
                print(f"   💥 {demo_name} 演示失败: {e}")
                import traceback
                traceback.print_exc()
                results.append((demo_name, False))
    else:
        # 运行单个演示
        demo_func = demos[args.type]
        try:
            print(f"\n{'=' * 70}")
            print(f"📍 开始演示: {args.type.upper()}")
            print('=' * 70)
            success = demo_func()
            results.append((args.type, success))
        except Exception as e:
            print(f"   💥 演示失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((args.type, False))

    # 总结
    print("\n" + "=" * 70)
    print("📊 演示结果总结")
    print("=" * 70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name:15s}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n   总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有演示完成！")
        print("\n💡 提示:")
        print("   - 图片功能需要有效的 img_key")
        print("   - 用户 @提及需要真实的 user_id")
        print("   - 所有卡片都可在飞书客户端中查看")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个演示失败")
        print("\n💡 可能的原因:")
        print("   - 网络连接问题")
        print("   - Webhook URL 无效")
        print("   - 图片 key 不存在")
        print("   - API 限流")
        return 1


if __name__ == '__main__':
    exit(main())
