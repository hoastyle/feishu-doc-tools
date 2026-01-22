#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通知限流器演示

展示 NotificationThrottle 的功能：
- 5层限流系统
- 重复检测
- 优先级处理
- 延迟队列

Usage:
    # 演示所有功能
    python scripts/notifications/test_notification_throttle.py

    # 演示特定功能
    python scripts/notifications/test_notification_throttle.py --type duplicate
    python scripts/notifications/test_notification_throttle.py --type rate-limit
    python scripts/notifications/test_notification_throttle.py --type priority
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.utils.notification_throttle import (
    NotificationThrottle,
    NotificationRequest,
    NotificationPriority,
    ThrottleAction,
)


def demo_duplicate_detection():
    """演示重复检测"""
    print("\n📝 演示：重复检测 (Layer 1)")
    print("   说明: 相同内容的通知在时间窗口内会被阻止")
    print("   配置: 重复窗口=5秒")

    throttle = NotificationThrottle(
        max_per_minute=60,
        max_per_hour=600,
        duplicate_window=5,  # 5秒窗口
    )

    # 创建重复的通知请求
    request = NotificationRequest(
        notification_id="test_001",
        event_type="document_created",
        channel="webhook",
        priority=NotificationPriority.NORMAL,
        content={"doc_name": "README.md", "size": "12KB"}
    )

    print("\n   📨 发送相同的通知3次:")

    for i in range(3):
        action = throttle.should_allow_notification(request)
        action_name = [action[0].value]

        if action == ThrottleAction.ALLOW:
            print(f"      ✅ 第 {i+1} 次: {action_name} (允许发送)")
        elif action == ThrottleAction.BLOCK:
            print(f"      ❌ 第 {i+1} 次: {action_name} (重复检测)")
        else:
            print(f"      ⏳ 第 {i+1} 次: {action_name}")

        if i < 2:
            time.sleep(1)

    # 等待窗口过期后再发送
    print("\n   ⏳ 等待重复窗口过期 (6秒)...")
    time.sleep(6)

    action = throttle.should_allow_notification(request)
    print(f"\n   📨 窗口过期后再次发送:")
    print(f"      ✅ 结果: {[action[0].value]} (允许发送)")

    # 获取统计
    stats = throttle.get_throttle_stats()
    print(f"\n   📊 统计信息:")
    print(f"      - 总请求: {stats["stats"]["allowed"] + stats["stats"]["blocked"]}")
    print(f"      - 允许: {stats["stats"]["allowed"]}")
    print(f"      - 阻止: {stats["stats"]["blocked"]}")
    print(f"      - 重复: {stats.get("stats", {}).get("duplicates_filtered", 0)}")

    return stats


def demo_global_rate_limits():
    """演示全局限流 (Layer 2)"""
    print("\n📝 演示：全局限流 (Layer 2)")
    print("   说明: 限制全局每分钟/每小时的通知数量")
    print("   配置: 5条/分钟, 10条/小时")

    throttle = NotificationThrottle(
        max_per_minute=5,  # 5条/分钟
        max_per_hour=10,   # 10条/小时
        duplicate_window=60,
    )

    print("\n   📨 快速发送10条通知:")

    allowed_count = 0
    blocked_count = 0

    for i in range(10):
        request = NotificationRequest(
            notification_id=f"test_{i:03d}",
            event_type="test_event",
            channel="webhook",
            priority=NotificationPriority.NORMAL,
            content={"index": i}
        )

        action = throttle.should_allow_notification(request)

        if action == ThrottleAction.ALLOW:
            print(f"      ✅ 通知 {i+1}: ALLOW")
            allowed_count += 1
        elif action == ThrottleAction.BLOCK:
            print(f"      ❌ 通知 {i+1}: BLOCK (达到限流)")
            blocked_count += 1
        else:
            print(f"      ⏳ 通知 {i+1}: {[action[0].value]}")

    # 获取统计
    stats = throttle.get_throttle_stats()
    print(f"\n   📊 结果:")
    print(f"      - 允许: {allowed_count}")
    print(f"      - 阻止: {blocked_count}")
    print(f"      - 负载状态: {stats.get('load_status', 'Unknown')}")

    return stats


def demo_channel_limits():
    """演示通道限流 (Layer 3)"""
    print("\n📝 演示：通道限流 (Layer 3)")
    print("   说明: 不同通道可以有独立的限流配置")

    # 配置不同通道的限流
    channel_limits = {
        "webhook": {"per_minute": 2, "per_hour": 10},
        "email": {"per_minute": 1, "per_hour": 5},
        "sms": {"per_minute": 0.5, "per_hour": 3}  # 更严格的限制
    }

    throttle = NotificationThrottle(
        max_per_minute=10,
        max_per_hour=100,
        duplicate_window=60,
        channel_limits=channel_limits,
    )

    print("\n   📨 向不同通道发送通知:")

    channels = ["webhook", "webhook", "email", "sms"]
    results = {}

    for channel in channels:
        request = NotificationRequest(
            notification_id=f"test_{channel}",
            event_type="test",
            channel=channel,
            priority=NotificationPriority.NORMAL,
            content={"test": "data"}
        )

        action = throttle.should_allow_notification(request)
        results[channel] = action[0]

        status = "✅" if action == ThrottleAction.ALLOW else "❌"
        print(f"      {status} {channel:10s}: {[action[0].value]}")

    # 获取通道统计
    stats = throttle.get_throttle_stats()
    channel_stats = stats.get('channel_stats', {})

    print(f"\n   📊 通道统计:")
    for channel, stat in channel_stats.items():
        print(f"      - {channel}: {stat.get('total', 0)} 条请求")

    return stats


def demo_event_limits():
    """演示事件限流 (Layer 4)"""
    print("\n📝 演示：事件限流 (Layer 4)")
    print("   说明: 不同事件类型可以有独立的限流和冷却时间")

    # 配置事件级别的限流
    event_limits = {
        "document_modified": {"cooldown": 60},  # 60秒冷却
        "sync_failed": {"cooldown": 10},        # 10秒冷却
        "system_alert": {"cooldown": 5},         # 5秒冷却
    }

    throttle = NotificationThrottle(
        max_per_minute=30,
        max_per_hour=300,
        duplicate_window=60,
        event_limits=event_limits,
    )

    print("\n   📨 测试事件冷却:")

    # 测试 document_modified 事件的冷却
    for i in range(3):
        request = NotificationRequest(
            notification_id=f"doc_mod_{i}",
            event_type="document_modified",
            channel="webhook",
            priority=NotificationPriority.NORMAL,
            content={"doc": "README.md"}
        )

        action = throttle.should_allow_notification(request)

        if action == ThrottleAction.ALLOW:
            print(f"      ✅ 第 {i+1} 次 document_modified: ALLOW")
        elif action == ThrottleAction.BLOCK:
            print(f"      ❌ 第 {i+1} 次 document_modified: BLOCK (冷却中)")
        else:
            print(f"      ⏳ 第 {i+1} 次: {[action[0].value]}")

        if i < 2:
            time.sleep(2)

    print(f"\n   💡 提示: document_modified 有60秒冷却时间，所以第2、3次被阻止")

    # 获取事件统计
    stats = throttle.get_throttle_stats()
    event_stats = stats.get('event_stats', {})

    print(f"\n   📊 事件统计:")
    for event, stat in event_stats.items():
        print(f"      - {event}: {stat.get('total', 0)} 条请求")

    return stats


def demo_priority_throttling():
    """演示优先级限流 (Layer 5)"""
    print("\n📝 演示：优先级限流 (Layer 5)")
    print("   说明: 高优先级通知更少受限流影响")

    throttle = NotificationThrottle(
        max_per_minute=5,  # 低限制以演示优先级效果
        max_per_hour=50,
        duplicate_window=60,
    )

    print("\n   📨 发送不同优先级的通知:")

    priorities = [
        NotificationPriority.LOW,
        NotificationPriority.NORMAL,
        NotificationPriority.HIGH,
        NotificationPriority.CRITICAL,
    ]

    results = {}

    for priority in priorities:
        request = NotificationRequest(
            notification_id=f"test_{priority.name}",
            event_type="test",
            channel="webhook",
            priority=priority,
            content={"test": "data"}
        )

        action = throttle.should_allow_notification(request)
        results[priority.name] = action

        # 显示权重
        weight = throttle.priority_weights.get(priority.name, 0.85)
        status = "✅" if action == ThrottleAction.ALLOW else "❌"
        print(f"      {status} {priority.name:10s} (权重={weight:.2f}): {[action[0].value]}")

    print(f"\n   💡 说明:")
    print(f"      - CRITICAL (权重=1.00): 几乎不受限制")
    print(f"      - HIGH (权重=0.95): 轻度限制")
    print(f"      - NORMAL (权重=0.85): 正常限制")
    print(f"      - LOW (权重=0.50): 重度限制")

    return results


def demo_delay_queue():
    """演示延迟队列"""
    print("\n📝 演示：延迟队列")
    print("   说明: 接近限制时通知会被延迟发送")

    throttle = NotificationThrottle(
        max_per_minute=3,  # 低限制
        max_per_hour=50,
        duplicate_window=60,
    )

    print("\n   📨 发送通知直到触发延迟:")

    for i in range(5):
        request = NotificationRequest(
            notification_id=f"test_{i:03d}",
            event_type="test",
            channel="webhook",
            priority=NotificationPriority.NORMAL,
            content={"index": i}
        )

        action = throttle.should_allow_notification(request)

        if action == ThrottleAction.ALLOW:
            print(f"      ✅ 通知 {i+1}: ALLOW (立即发送)")
        elif action == ThrottleAction.DELAY:
            print(f"      ⏳ 通知 {i+1}: DELAY (加入延迟队列)")
            # 添加到延迟队列
            throttle.add_delayed_notification(request)
        else:
            print(f"      ❌ 通知 {i+1}: BLOCK")

    # 获取延迟队列中的通知
    delayed = throttle.get_ready_notifications()
    print(f"\n   📦 延迟队列中有 {len(delayed)} 条通知:")

    for req in delayed:
        print(f"      - {req.notification_id}: {req.event_type}")

    # 获取统计
    stats = throttle.get_throttle_stats()
    print(f"\n   📊 统计:")
    print(f"      - 延迟: {stats.get("stats", {}).get("delayed", 0)}")

    return delayed


def demo_five_layer_system():
    """演示完整的5层限流系统"""
    print("\n📝 演示：完整的5层限流系统")
    print("   说明: 展示所有5层限流的协同工作")

    throttle = NotificationThrottle(
        max_per_minute=10,
        max_per_hour=100,
        duplicate_window=5,
        channel_limits={
            "webhook": {"per_minute": 5, "per_hour": 50}
        },
        event_limits={
            "document_created": {"cooldown": 30},
            "error": {"cooldown": 10}
        },
    )

    print("\n   📨 发送不同类型的通知:")

    test_cases = [
        ("重复通知", "document_created", NotificationPriority.NORMAL, {"doc": "README.md"}),
        ("高优先级", "document_created", NotificationPriority.HIGH, {"doc": "API.md"}),
        ("低优先级", "document_created", NotificationPriority.LOW, {"doc": "GUIDE.md"}),
        ("错误事件", "error", NotificationPriority.HIGH, {"error": "Timeout"}),
        ("普通事件", "info", NotificationPriority.NORMAL, {"info": "System ready"}),
        ("关键事件", "alert", NotificationPriority.CRITICAL, {"alert": "System overload"}),
    ]

    results = []

    for name, event_type, priority, content in test_cases:
        request = NotificationRequest(
            notification_id=f"test_{name}",
            event_type=event_type,
            channel="webhook",
            priority=priority,
            content=content
        )

        action = throttle.should_allow_notification(request)
        results.append((name, action))

        status_icon = {
            ThrottleAction.ALLOW: "✅",
            ThrottleAction.BLOCK: "❌",
            ThrottleAction.DELAY: "⏳",
            ThrottleAction.MERGE: "🔀"
        }.get(action, "❓")

        print(f"      {status_icon} {name:12s} ({event_type:15s}, {priority.name:8s}): {[action[0].value]}")

    # 获取完整统计
    stats = throttle.get_throttle_stats()

    print(f"\n   📊 完整统计:")
    print(f"      - 总请求: {stats["stats"]["allowed"] + stats["stats"]["blocked"]}")
    print(f"      - 允许: {stats["stats"]["allowed"]}")
    print(f"      - 阻止: {stats["stats"]["blocked"]}")
    print(f"      - 延迟: {stats.get("stats", {}).get("delayed", 0)}")
    print(f"      - 重复: {stats.get("stats", {}).get("duplicates_filtered", 0)}")
    print(f"      - 负载状态: {stats.get('load_status', 'Unknown')}")

    return stats


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="通知限流器演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能类型:
  duplicate     - 重复检测演示
  rate-limit    - 全局限流演示
  channel       - 通道限流演示
  event         - 事件限流演示
  priority      - 优先级限流演示
  delay         - 延迟队列演示
  five-layer    - 完整5层系统演示
  all           - 演示所有功能

示例:
  # 演示所有功能
  python scripts/notifications/test_notification_throttle.py

  # 演示特定功能
  python scripts/notifications/test_notification_throttle.py --type duplicate
        """
    )

    parser.add_argument(
        "--type",
        choices=["duplicate", "rate-limit", "channel", "event", "priority", "delay", "five-layer", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🚦 通知限流器演示")
    print("=" * 70)

    # 演示函数映射
    demos = {
        "duplicate": demo_duplicate_detection,
        "rate-limit": demo_global_rate_limits,
        "channel": demo_channel_limits,
        "event": demo_event_limits,
        "priority": demo_priority_throttling,
        "delay": demo_delay_queue,
        "five-layer": demo_five_layer_system,
    }

    # 运行演示
    results = []

    if args.type == "all":
        for demo_name, demo_func in demos.items():
            try:
                result = demo_func()
                results.append((demo_name, True))
                time.sleep(1)
            except Exception as e:
                print(f"   💥 {demo_name} 演示失败: {e}")
                import traceback
                traceback.print_exc()
                results.append((demo_name, False))
    else:
        demo_func = demos[args.type]
        try:
            result = demo_func()
            results.append((args.type, True))
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
