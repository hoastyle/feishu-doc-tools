#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档模板演示

展示 DocumentTemplates 的6种预定义模板：
- document_created: 文档创建通知
- document_modified: 文档修改通知
- document_deleted: 文档删除通知
- sync_started: 同步开始通知
- sync_completed: 同步完成通知
- sync_failed: 同步失败通知

Usage:
    # 演示所有模板
    python scripts/notifications/test_document_templates.py

    # 演示特定模板
    python scripts/notifications/test_document_templates.py --type created
    python scripts/notifications/test_document_templates.py --type modified
    python scripts/notifications/test_document_templates.py --type sync
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.templates.document_templates import DocumentTemplates
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings


def demo_document_created(webhook_url: str):
    """演示文档创建模板"""
    print("\n📝 演示：文档创建通知")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 基础版本
        card1 = DocumentTemplates.document_created(
            doc_name="API Reference",
            creator="Alice"
        )

        # 完整版本
        card2 = DocumentTemplates.document_created(
            doc_name="User Guide",
            creator="Bob",
            doc_type="Wiki",
            folder="产品文档/用户指南",
            doc_url="https://feishu.cn/docs/xxx",
            metadata={
                "size": "125KB",
                "language": "zh-CN",
                "tags": ["guide", "tutorial"]
            }
        )

        # 发送
        r1 = channel.send(card1.to_dict(), "doc_created_basic")
        r2 = channel.send(card2.to_dict(), "doc_created_full")

        results = [("基础版本", r1), ("完整版本", r2)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_document_modified(webhook_url: str):
    """演示文档修改模板"""
    print("\n📝 演示：文档修改通知")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 基础版本
        card1 = DocumentTemplates.document_modified(
            doc_name="README.md",
            modifier="Charlie",
            changes="更新了安装说明"
        )

        # 完整版本
        card2 = DocumentTemplates.document_modified(
            doc_name="API.md",
            modifier="David",
            changes="添加了3个新的API端点",
            change_count=3,
            doc_url="https://feishu.cn/docs/yyy",
            metadata={
                "previous_size": "45KB",
                "new_size": "52KB",
                "changed_sections": ["Authentication", "Endpoints", "Examples"]
            }
        )

        # 发送
        r1 = channel.send(card1.to_dict(), "doc_modified_basic")
        r2 = channel.send(card2.to_dict(), "doc_modified_full")

        results = [("基础版本", r1), ("完整版本", r2)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_document_deleted(webhook_url: str):
    """演示文档删除模板"""
    print("\n📝 演示：文档删除通知")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 基础版本
        card1 = DocumentTemplates.document_deleted(
            doc_name="Old Draft",
            deleter="Eve"
        )

        # 完整版本
        card2 = DocumentTemplates.document_deleted(
            doc_name="Deprecated API",
            deleter="Admin",
            doc_type="Wiki",
            folder="废弃文档",
            reason="功能已移除，被新API替代"
        )

        # 发送
        r1 = channel.send(card1.to_dict(), "doc_deleted_basic")
        r2 = channel.send(card2.to_dict(), "doc_deleted_full")

        results = [("基础版本", r1), ("完整版本", r2)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_sync_templates(webhook_url: str):
    """演示同步相关模板"""
    print("\n📝 演示：同步相关通知")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # sync_started
        card1 = DocumentTemplates.sync_started(
            source="local/docs/",
            destination="Feishu Wiki",
            file_count=15,
            sync_type="incremental",
            metadata={"last_sync": "2026-01-19 10:00"}
        )

        # sync_completed
        card2 = DocumentTemplates.sync_completed(
            source="local/docs/",
            destination="Feishu Wiki",
            synced_count=14,
            duration="2分35秒",
            failed_count=1,
            metadata={"total_size": "2.3GB", "avg_speed": "12.5MB/s"}
        )

        # sync_failed
        card3 = DocumentTemplates.sync_failed(
            source="local/docs/",
            destination="Feishu Wiki",
            error_message="Network connection lost after 5 files",
            synced_count=5,
            total_count=15
        )

        # 发送
        r1 = channel.send(card1.to_dict(), "sync_started")
        r2 = channel.send(card2.to_dict(), "sync_completed")
        r3 = channel.send(card3.to_dict(), "sync_failed")

        results = [
            ("同步开始", r1),
            ("同步完成", r2),
            ("同步失败", r3)
        ]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_color_schemes(webhook_url: str):
    """演示不同颜色方案"""
    print("\n📝 演示：颜色方案")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # Wathet (运行中)
        card1 = DocumentTemplates.sync_started(
            source="local/data",
            destination="Cloud Storage"
        )

        # Green (成功)
        card2 = DocumentTemplates.document_created(
            doc_name="New Feature",
            creator="System"
        )

        # Red (失败)
        card3 = DocumentTemplates.sync_failed(
            source="backup",
            destination="remote",
            error_message="Authentication failed"
        )

        # Orange (删除)
        card4 = DocumentTemplates.document_deleted(
            doc_name="Temp File",
            deleter="CleanUp Bot"
        )

        # Blue (修改)
        card5 = DocumentTemplates.document_modified(
            doc_name="Config",
            modifier="Admin"
        )

        # 发送所有卡片
        cards = [
            ("Wathet (运行中)", card1),
            ("Green (成功)", card2),
            ("Red (失败)", card3),
            ("Orange (删除)", card4),
            ("Blue (修改)", card5),
        ]

        results = []
        for name, card in cards:
            success = channel.send(card.to_dict(), f"color_{name.split()[0].lower()}")
            results.append((name, success))

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_real_world_scenarios(webhook_url: str):
    """演示真实场景"""
    print("\n📝 演示：真实场景")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 场景1: 批量上传Wiki
        print("\n   📂 场景1: 批量上传Wiki")
        card1 = DocumentTemplates.sync_started(
            source="local/wiki/",
            destination="Product Wiki",
            file_count=25,
            sync_type="full"
        )
        r1 = channel.send(card1.to_dict(), "scenario1_start")

        # 场景2: 文档审核流程
        print("\n   📋 场景2: 文档审核流程")
        card2 = DocumentTemplates.document_modified(
            doc_name="API Specification",
            modifier="Reviewer",
            changes="通过审核，准备发布",
            change_count=1,
            doc_url="https://feishu.cn/docs/api-spec"
        )
        r2 = channel.send(card2.to_dict(), "scenario2_review")

        # 场景3: 备份失败处理
        print("\n   💾 场景3: 备份失败处理")
        card3 = DocumentTemplates.sync_failed(
            source="production_db",
            destination="backup_storage",
            error_message="Storage quota exceeded (100GB used)",
            synced_count=0,
            total_count=150
        )
        r3 = channel.send(card3.to_dict(), "scenario3_backup")

        results = [
            ("批量上传", r1),
            ("文档审核", r2),
            ("备份失败", r3)
        ]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_metadata_handling(webhook_url: str):
    """演示元数据处理"""
    print("\n📝 演示：元数据处理")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 丰富的元数据示例
        card = DocumentTemplates.document_created(
            doc_name="System Architecture",
            creator="Tech Lead",
            doc_type="Wiki",
            folder="技术文档/架构",
            doc_url="https://feishu.cn/docs/arch",
            metadata={
                # 基本信息
                "size": "256KB",
                "language": "zh-CN",
                "version": "1.0",

                # 分类信息
                "category": "Architecture",
                "tags": ["system", "design", "high-level"],

                # 审核信息
                "reviewer": "Senior Architect",
                "review_status": "Approved",

                # 关联信息
                "related_docs": ["API Design", "Database Schema"],
                "dependencies": ["diagrams/arch_v1.png"],

                # 统计信息
                "word_count": 3500,
                "reading_time": "15分钟",
            }
        )

        success = channel.send(card.to_dict(), "metadata_demo")

        status = "✅" if success else "❌"
        print(f"   {status} 丰富元数据演示")

        return success


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="文档模板演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模板类型:
  created     - 文档创建通知
  modified    - 文档修改通知
  deleted     - 文档删除通知
  sync        - 同步相关通知 (started/completed/failed)
  colors      - 颜色方案演示
  scenarios   - 真实场景演示
  metadata    - 元数据处理演示
  all         - 演示所有模板

示例:
  # 演示所有模板
  python scripts/notifications/test_document_templates.py

  # 演示特定模板
  python scripts/notifications/test_document_templates.py --type created
  python scripts/notifications/test_document_templates.py --type sync
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--type",
        choices=["created", "modified", "deleted", "sync", "colors", "scenarios", "metadata", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📄 文档模板演示")
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
        "created": demo_document_created,
        "modified": demo_document_modified,
        "deleted": demo_document_deleted,
        "sync": demo_sync_templates,
        "colors": demo_color_schemes,
        "scenarios": demo_real_world_scenarios,
        "metadata": demo_metadata_handling,
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
                import traceback
                traceback.print_exc()
                results.append((demo_name, False))
    else:
        demo_func = demos[args.type]
        try:
            success = demo_func(webhook_url)
            results.append((args.type, success))
        except Exception as e:
            print(f"   💥 演示失败: {e}")
            import traceback
            traceback.print_exc()
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
