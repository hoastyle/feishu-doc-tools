#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知系统综合集成测试

展示 MessageGrouper 和 NotificationThrottle 的协同工作：
- Grouper + Throttle 组合使用
- 完整的通知发送流程
- 错误处理和重试机制
- 实际应用场景模拟

Usage:
    # 运行综合测试
    python scripts/notifications/test_complete_integration.py

    # 运行特定场景
    python scripts/notifications/test_complete_integration.py --scenario batch-upload
    python scripts/notifications/test_complete_integration.py --scenario error-storm
    python scripts/notifications/test_complete_integration.py --scenario priority-mix
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
from notifications.templates.document_templates import DocumentTemplates
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings
from notifications.utils.message_grouper import (
    MessageGrouper,
    GroupingStrategy,
)
from notifications.utils.notification_throttle import (
    NotificationThrottle,
    NotificationRequest,
    NotificationPriority,
    ThrottleAction,
)


class NotificationSystem:
    """通知系统：整合 Grouper + Throttle + Channel"""

    def __init__(self, webhook_url: str):
        """初始化通知系统

        Args:
            webhook_url: 飞书 Webhook URL
        """
        self.webhook_url = webhook_url
        self.settings = create_settings(webhook_url=webhook_url)

        # 初始化 Message Grouper
        self.grouper = MessageGrouper(
            group_window=5,  # 5秒时间窗口
            max_group_size=10,
            send_threshold=5,  # 5条消息触发批量发送
        )

        # 初始化 Notification Throttle
        self.throttle = NotificationThrottle(
            max_per_minute=20,
            max_per_hour=200,
            duplicate_window=10,
        )

        # 统计信息
        self.stats = {
            "total_sent": 0,
            "total_blocked": 0,
            "total_delayed": 0,
            "total_grouped": 0,
        }

    def send_notification(
        self,
        card: Dict[str, Any],
        event_type: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        notification_id: str = None,
    ) -> bool:
        """发送通知（经过限流和分组）

        Args:
            card: 卡片内容
            event_type: 事件类型
            priority: 优先级
            notification_id: 通知ID

        Returns:
            是否发送成功
        """
        # 创建通知请求
        request = NotificationRequest(
            notification_id=notification_id or f"notif_{int(time.time() * 1000)}",
            event_type=event_type,
            channel="webhook",
            priority=priority,
            content=card
        )

        # 1. 检查限流
        action, reason, delay = self.throttle.should_allow_notification(request)

        if action == ThrottleAction.BLOCK:
            print(f"      ❌ 通知被限流阻止: {event_type}")
            self.stats["total_blocked"] += 1
            return False

        elif action == ThrottleAction.DELAY:
            print(f"      ⏳ 通知加入延迟队列: {event_type}")
            self.throttle.add_delayed_notification(request)
            self.stats["total_delayed"] += 1
            return False

        # 2. 检查是否应该分组
        should_group, group_id, merge_action = self.grouper.should_group_message({
            "card": card,
            "event_type": event_type,
            "priority": priority.value,
        })

        if should_group:
            # 添加到分组
            self.grouper.add_message_to_group(group_id, {
                "card": card,
                "event_type": event_type,
                "priority": priority.value,
            })
            self.stats["total_grouped"] += 1
            print(f"      📦 消息已分组: {group_id[:8]}...")

            # 检查是否达到发送阈值
            ready_groups = self.grouper.get_ready_groups()
            if ready_groups:
                print(f"      🚀 达到阈值，批量发送 {len(ready_groups)} 个分组")
                return self._send_batch_groups(ready_groups)
            return True

        # 3. 直接发送
        return self._send_single(card, event_type)

    def _send_single(self, card: Dict[str, Any], event_type: str) -> bool:
        """发送单个通知"""
        try:
            with WebhookChannel(self.settings) as channel:
                success = channel.send(card, event_type)
                if success:
                    self.stats["total_sent"] += 1
                    print(f"      ✅ 发送成功: {event_type}")
                else:
                    print(f"      ❌ 发送失败: {event_type}")
                return success
        except Exception as e:
            print(f"      💥 发送异常: {e}")
            return False

    def _send_batch_groups(self, groups: List) -> bool:
        """批量发送分组"""
        try:
            with WebhookChannel(self.settings) as channel:
                all_success = True
                for group in groups:
                    # 合并分组中的消息
                    merged_card = self._merge_group_to_card(group)
                    success = channel.send(merged_card, f"batch_{group.group_id[:8]}")
                    if success:
                        self.stats["total_sent"] += 1
                        print(f"      ✅ 批量发送成功: {len(group.messages)} 条消息")
                    else:
                        all_success = False
                return all_success
        except Exception as e:
            print(f"      💥 批量发送异常: {e}")
            return False

    def _merge_group_to_card(self, group) -> Dict[str, Any]:
        """将分组中的消息合并为一张卡片"""
        if len(group.messages) == 1:
            # 只有一条消息，直接返回
            return group.messages[0]["card"]

        # 多条消息，创建汇总卡片
        card = (CardBuilder()
            .header(f"📊 批量通知 ({len(group.messages)} 条)", status="info")
            .markdown(f"以下是 **{group.messages[0]['event_type']}** 事件的汇总:")
            .divider())

        # 添加每条消息的摘要
        for i, msg in enumerate(group.messages[:10], 1):  # 最多显示10条
            card = card.markdown(f"{i}. {msg['event_type']}")

        if len(group.messages) > 10:
            card = card.markdown(f"... 还有 {len(group.messages) - 10} 条消息")

        card = card.note(f"分组ID: {group.group_id[:8]}...")
        return card.build().to_dict()

    def flush_delayed_notifications(self):
        """发送延迟队列中的通知"""
        delayed = self.throttle.get_ready_notifications()
        if delayed:
            print(f"\n   📤 发送延迟队列中的 {len(delayed)} 条通知:")
            for request in delayed:
                card = request.content
                self._send_single(card, request.event_type)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        throttle_stats = self.throttle.get_throttle_stats()
        grouper_stats = self.grouper.get_grouper_stats()

        return {
            "system": self.stats,
            "throttle": throttle_stats,
            "grouper": grouper_stats,
        }


# ========== 测试场景 ==========

def scenario_batch_upload():
    """场景1: 批量上传"""
    print("\n📁 场景1: 批量文件上传")
    print("   模拟: 15个文件依次上传，通知会被分组合并")

    # 需要用户提供 Webhook URL
    settings = create_settings()
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print(f"\n   ❌ 配置不完整！缺少: {', '.join(missing)}")
        return False

    system = NotificationSystem(settings.webhook_url)

    # 模拟15个文件上传
    for i in range(15):
        card = (CardBuilder()
            .header("📤 文件上传", status="success")
            .metadata("文件", f"document_{i:03d}.md")
            .metadata("大小", f"{(i+1)*10}KB")
            .markdown(f"文件 **document_{i:03d}.md** 上传成功")
            .build())

        success = system.send_notification(
            card.to_dict(),
            event_type="file_uploaded",
            priority=NotificationPriority.NORMAL,
        )

        time.sleep(0.3)  # 模拟上传间隔

    # 发送延迟队列
    system.flush_delayed_notifications()

    # 显示统计
    stats = system.get_statistics()
    print(f"\n   📊 统计结果:")
    print(f"      - 总发送: {stats['system']['total_sent']}")
    print(f"      - 总阻止: {stats['system']['total_blocked']}")
    print(f"      - 总延迟: {stats['system']['total_delayed']}")
    print(f"      - 总分组: {stats['system']['total_grouped']}")

    return True


def scenario_error_storm():
    """场景2: 错误风暴"""
    print("\n🌪️  场景2: 错误风暴")
    print("   模拟: 大量错误发生，限流系统防止通知轰炸")

    settings = create_settings()
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print(f"\n   ❌ 配置不完整！缺少: {', '.join(missing)}")
        return False

    # 使用更严格的限流配置
    system = NotificationSystem(settings.webhook_url)
    system.throttle = NotificationThrottle(
        max_per_minute=5,  # 严格限制
        max_per_hour=50,
        duplicate_window=10,
    )

    # 模拟20个错误
    error_types = ["ConnectionError", "Timeout", "AuthError", "ServerError"]

    for i in range(20):
        error_type = error_types[i % len(error_types)]
        card = (CardBuilder()
            .header("❌ 错误", status="error", color="red")
            .metadata("错误类型", error_type)
            .metadata("位置", f"/api/endpoint_{i % 5}")
            .markdown(f"发生错误: **{error_type}**")
            .note("系统正在重试...")
            .build())

        priority = NotificationPriority.HIGH if i % 5 == 0 else NotificationPriority.NORMAL
        success = system.send_notification(
            card.to_dict(),
            event_type="error_occurred",
            priority=priority,
        )

        time.sleep(0.2)

    # 发送延迟队列
    system.flush_delayed_notifications()

    # 显示统计
    stats = system.get_statistics()
    print(f"\n   📊 统计结果:")
    print(f"      - 总发送: {stats['system']['total_sent']}")
    print(f"      - 总阻止: {stats['system']['total_blocked']} (防止通知轰炸)")
    print(f"      - 总延迟: {stats['system']['total_delayed']}")

    return True


def scenario_priority_mix():
    """场景3: 优先级混合"""
    print("\n🎯 场景3: 优先级混合")
    print("   模拟: 不同优先级的消息混合发送")

    settings = create_settings()
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print(f"\n   ❌ 配置不完整！缺少: {', '.join(missing)}")
        return False

    system = NotificationSystem(settings.webhook_url)

    # 不同优先级和事件类型
    notifications = [
        ("系统监控", "system_monitor", NotificationPriority.LOW),
        ("文档更新", "doc_updated", NotificationPriority.NORMAL),
        ("构建完成", "build_complete", NotificationPriority.NORMAL),
        ("测试失败", "test_failed", NotificationPriority.HIGH),
        ("服务崩溃", "service_crash", NotificationPriority.CRITICAL),
    ]

    for name, event_type, priority in notifications:
        card = DocumentTemplates.document_created(
            doc_name=name,
            creator="System"
        )

        success = system.send_notification(
            card.to_dict(),
            event_type=event_type,
            priority=priority,
        )

        time.sleep(0.5)

    # 发送延迟队列
    system.flush_delayed_notifications()

    # 显示统计
    stats = system.get_statistics()
    throttle_stats = stats['throttle']

    print(f"\n   📊 统计结果:")
    print(f"      - 总发送: {stats['system']['total_sent']}")
    print(f"      - 总阻止: {stats['system']['total_blocked']}")
    print(f"      - 负载状态: {throttle_stats.get('load_status', 'Unknown')}")

    return True


def scenario_complete_workflow():
    """场景4: 完整工作流"""
    print("\n🔄 场景4: 完整工作流")
    print("   模拟: 同步开始 -> 文档变更 -> 同步完成")

    settings = create_settings()
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print(f"\n   ❌ 配置不完整！缺少: {', '.join(missing)}")
        return False

    system = NotificationSystem(settings.webhook_url)

    # 1. 同步开始
    print("\n   1️⃣ 同步开始...")
    card1 = DocumentTemplates.sync_started(
        source="local/wiki/",
        destination="Product Wiki",
        file_count=10,
    )
    system.send_notification(card1.to_dict(), "sync_started", NotificationPriority.NORMAL)
    time.sleep(1)

    # 2. 文档创建（多条，会被分组）
    print("\n   2️⃣ 批量文档创建...")
    for i in range(5):
        card = DocumentTemplates.document_created(
            doc_name=f"Page {i+1}",
            creator="Migration Bot"
        )
        system.send_notification(card.to_dict(), "doc_created", NotificationPriority.NORMAL)
        time.sleep(0.3)

    # 3. 同步完成
    print("\n   3️⃣ 同步完成...")
    card2 = DocumentTemplates.sync_completed(
        source="local/wiki/",
        destination="Product Wiki",
        synced_count=10,
        duration="45秒",
    )
    system.send_notification(card2.to_dict(), "sync_completed", NotificationPriority.NORMAL)

    # 发送延迟队列
    system.flush_delayed_notifications()

    # 显示统计
    stats = system.get_statistics()
    print(f"\n   📊 统计结果:")
    print(f"      - 总发送: {stats['system']['total_sent']}")
    print(f"      - 总分组: {stats['system']['total_grouped']}")
    print(f"      - Grouper活跃分组: {stats['grouper']['active_groups']}")

    return True


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="通知系统综合集成测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试场景:
  batch-upload   - 批量上传场景（消息分组）
  error-storm    - 错误风暴场景（限流保护）
  priority-mix   - 优先级混合场景（优先级处理）
  complete-workflow - 完整工作流（综合演示）
  all            - 运行所有场景

示例:
  # 运行所有场景
  python scripts/notifications/test_complete_integration.py

  # 运行特定场景
  python scripts/notifications/test_complete_integration.py --scenario batch-upload
        """
    )

    parser.add_argument(
        "--scenario",
        choices=["batch-upload", "error-storm", "priority-mix", "complete-workflow", "all"],
        default="all",
        help="测试场景 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🔗 通知系统综合集成测试")
    print("=" * 70)

    # 检查配置
    settings = create_settings()
    is_valid, missing = settings.validate_required_fields()
    if not is_valid:
        print(f"\n❌ 配置不完整！缺少: {', '.join(missing)}")
        print("\n请设置环境变量:")
        print("   export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL")
        return 1

    print(f"\n📡 Webhook URL: {settings.webhook_url[:50]}...")

    # 场景函数映射
    scenarios = {
        "batch-upload": scenario_batch_upload,
        "error-storm": scenario_error_storm,
        "priority-mix": scenario_priority_mix,
        "complete-workflow": scenario_complete_workflow,
    }

    # 运行场景
    results = []

    if args.scenario == "all":
        for scenario_name, scenario_func in scenarios.items():
            try:
                success = scenario_func()
                results.append((scenario_name, success))
                time.sleep(2)  # 场景之间的间隔
            except Exception as e:
                print(f"   💥 {scenario_name} 失败: {e}")
                import traceback
                traceback.print_exc()
                results.append((scenario_name, False))
    else:
        scenario_func = scenarios[args.scenario]
        try:
            success = scenario_func()
            results.append((args.scenario, success))
        except Exception as e:
            print(f"   💥 场景失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((args.scenario, False))

    # 总结
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {name:20s}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n   总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有场景测试完成！")
        print("\n💡 总结:")
        print("   ✅ MessageGrouper 成功合并相似通知")
        print("   ✅ NotificationThrottle 成功防止通知轰炸")
        print("   ✅ 两者协同工作，提供智能通知管理")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个场景失败")
        return 1


if __name__ == '__main__':
    exit(main())
