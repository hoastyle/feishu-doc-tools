#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
消息分组器演示

展示 MessageGrouper 的功能：
- 时间窗口分组
- 内容相似度检测
- 批量发送逻辑
- 统计信息获取

Usage:
    # 演示所有功能
    python scripts/notifications/test_message_grouper.py

    # 演示特定功能
    python scripts/notifications/test_message_grouper.py --type time-window
    python scripts/notifications/test_message_grouper.py --type similarity
    python scripts/notifications/test_message_grouper.py --type batch
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from notifications.utils.message_grouper import (
    MessageGrouper,
    GroupingStrategy,
    MessageGroup,
)


def demo_time_window_grouping():
    """演示时间窗口分组"""
    print("\n📝 演示：时间窗口分组")
    print("   说明: 在指定时间窗口内的消息会被分组")
    print("   配置: 时间窗口=5秒，最大分组大小=5条")

    grouper = MessageGrouper(
        group_window=5,  # 5秒时间窗口
        max_group_size=5,
        send_threshold=3,  # 3条消息触发发送
    )

    # 模拟发送消息
    messages = []
    for i in range(8):
        msg = {
            "event_type": "file_uploaded",
            "file_name": f"document_{i}.md",
            "size": f"{(i+1)*100}KB"
        }
        should_group, group_id, merge_action = grouper.should_group_message(msg)

        if should_group:
            grouper.add_message_to_group(group_id, msg)
            messages.append(msg)
            print(f"   ✅ 消息 {i+1}: 已添加到分组 {group_id[:8]}...")
        else:
            print(f"   ⚠️  消息 {i+1}: 已创建新分组")

        time.sleep(0.5)  # 模拟消息间隔

    # 检查准备发送的分组
    print("\n   📊 检查准备发送的分组:")
    ready_groups = grouper.get_ready_groups()
    for group in ready_groups:
        print(f"   📦 分组 {group.group_id[:8]}...: {len(group.messages)} 条消息")

    # 获取统计信息
    stats = grouper.get_grouper_stats()
    print(f"\n   📈 统计信息:")
    print(f"      - 活跃分组数: {stats['active_groups']}")
    print(f"      - 总消息数: {stats['stats']['messages_grouped']}")

    return ready_groups


def demo_similarity_detection():
    """演示内容相似度检测"""
    print("\n📝 演示：内容相似度检测")
    print("   说明: 相似内容的消息会被分组到一起")
    print("   配置: 相似度阈值=0.8")

    grouper = MessageGrouper(
        similarity_threshold=0.8,
        max_group_size=5,
        send_threshold=2,
    )

    # 模拟发送相似消息
    messages = [
        {"event_type": "error", "message": "Connection timeout"},
        {"event_type": "error", "message": "Connection timeout"},  # 重复
        {"event_type": "error", "message": "Connection failed"},  # 相似
        {"event_type": "info", "message": "File uploaded"},
        {"event_type": "error", "message": "Connection refused"},  # 相似主题
    ]

    for i, msg in enumerate(messages):
        should_group, group_id, merge_action = grouper.should_group_message(msg)

        if should_group:
            grouper.add_message_to_group(group_id, msg)
            print(f"   ✅ 消息 {i+1} ({msg['message'][:25]}): 已添加到分组 {group_id[:8]}...")
        else:
            print(f"   ⚠️  消息 {i+1} ({msg['message'][:25]}): 已创建新分组")

    # 获取分组详情
    ready_groups = grouper.get_ready_groups()
    print(f"\n   📦 生成了 {len(ready_groups)} 个分组:")

    for group in ready_groups:
        print(f"\n   分组 {group.group_id[:8]}...:")
        for msg in group.messages:
            print(f"      - {msg['message']}")

    return ready_groups


def demo_batch_send():
    """演示批量发送逻辑"""
    print("\n📝 演示：批量发送逻辑")
    print("   说明: 消息累积到阈值后自动触发发送")

    grouper = MessageGrouper(
        max_group_size=10,
        send_threshold=5,  # 5条消息触发发送
        send_timeout=60,  # 60秒超时
    )

    # 模拟批量消息
    messages = []
    for i in range(12):
        msg = {
            "event_type": "task_completed",
            "task_id": f"task_{i}",
            "duration": f"{i*0.5}s"
        }
        should_group, group_id, merge_action = grouper.should_group_message(msg)

        if should_group:
            grouper.add_message_to_group(group_id, msg)
            messages.append(msg)

        # 检查是否达到发送阈值
        ready_groups = grouper.get_ready_groups()
        if ready_groups:
            print(f"   🚀 达到阈值! 准备发送分组 ({len(ready_groups[0].messages)} 条消息)")
            # 这里可以调用实际的发送逻辑
            # send_group(ready_groups[0])

    # 最终检查
    final_groups = grouper.get_ready_groups()
    print(f"\n   📊 最终统计:")
    print(f"      - 总消息数: {len(messages)}")
    print(f"      - 准备发送的分组: {len(final_groups)}")

    for group in final_groups:
        print(f"      - 分组 {group.group_id[:8]}...: {len(group.messages)} 条消息")

    return final_groups


def demo_priority_escalation():
    """演示优先级升级"""
    print("\n📝 演示：优先级升级")
    print("   说明: 高优先级消息会快速触发发送")

    grouper = MessageGrouper(
        max_group_size=10,
        send_threshold=5,
    )

    # 发送普通优先级消息
    print("\n   📨 发送普通消息:")
    for i in range(3):
        msg = {
            "event_type": "log_entry",
            "level": "info",
            "message": f"Log message {i}",
            "priority": "normal"
        }
        should_group, group_id, merge_action = grouper.should_group_message(msg)
        if should_group:
            grouper.add_message_to_group(group_id, msg)
            print(f"      ✅ 普通消息 {i+1} 已添加")

    # 发送高优先级消息
    print("\n   🚨 发送高优先级消息:")
    critical_msg = {
        "event_type": "log_entry",
        "level": "critical",
        "message": "System overload detected!",
        "priority": "critical"
    }

    should_group, group_id, merge_action = grouper.should_group_message(critical_msg)
    if should_group:
        grouper.add_message_to_group(group_id, critical_msg)
        print(f"      ✅ 关键消息已添加，优先级提升!")

    # 检查分组优先级
    ready_groups = grouper.get_ready_groups()
    if ready_groups:
        group = ready_groups[0]
        print(f"\n   📊 分组优先级: {group.priority}/4")
        print(f"      - 消息数量: {len(group.messages)}")
        print(f"      - 包含关键消息: {'是' if group.priority >= 3 else '否'}")

    return ready_groups


def demo_statistics():
    """演示统计信息"""
    print("\n📝 演示：统计信息")

    grouper = MessageGrouper(
        group_window=10,
        max_group_size=10,
        send_threshold=5,
    )

    # 添加不同项目的消息
    projects = ["frontend", "backend", "frontend", "backend", "database"]
    for i, project in enumerate(projects):
        msg = {
            "event_type": "build_completed",
            "project": project,
            "duration": f"{(i+1)*10}s"
        }
        should_group, group_id, merge_action = grouper.should_group_message(msg)
        if should_group:
            grouper.add_message_to_group(group_id, msg)

    # 获取详细统计
    stats = grouper.get_grouper_stats()

    print("\n   📊 完整统计信息:")
    print(f"      - 活跃分组数: {stats['active_groups']}")
    print(f"      - 总消息数: {stats['total_messages']}")

    return stats


def demo_cleanup():
    """演示自动清理过期分组"""
    print("\n📝 演示：自动清理过期分组")
    print("   说明: 超过时间窗口的分组会自动清理")

    grouper = MessageGrouper(
        group_window=3,  # 3秒时间窗口
        max_group_size=5,
    )

    # 添加消息
    msg1 = {"event_type": "test", "message": "First message"}
    should_group, group_id, merge_action = grouper.should_group_message(msg1)
    if should_group:
        grouper.add_message_to_group(group_id, msg1)
        print(f"   ✅ 消息1已添加 (时间: 0.0s)")

    # 等待超过时间窗口
    print(f"   ⏳ 等待 4 秒...")
    time.sleep(4)

    # 尝试添加新消息
    msg2 = {"event_type": "test", "message": "Second message"}
    should_group, group_id, merge_action = grouper.should_group_message(msg2)
    if should_group:
        grouper.add_message_to_group(group_id, msg2)
        print(f"   ✅ 消息2已添加 (时间: 4.0s) - 创建新分组")

    # 触发定期清理
    print(f"\n   🧹 触发定期清理...")

    # 获取统计
    stats = grouper.get_grouper_stats()
    print(f"   📊 清理后活跃分组数: {stats['active_groups']}")

    return stats


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="消息分组器演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
功能类型:
  time-window   - 时间窗口分组演示
  similarity     - 内容相似度检测演示
  batch          - 批量发送逻辑演示
  priority       - 优先级升级演示
  statistics     - 统计信息演示
  cleanup        - 自动清理演示
  all            - 演示所有功能

示例:
  # 演示所有功能
  python scripts/notifications/test_message_grouper.py

  # 演示特定功能
  python scripts/notifications/test_message_grouper.py --type time-window
        """
    )

    parser.add_argument(
        "--type",
        choices=["time-window", "similarity", "batch", "priority", "statistics", "cleanup", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🗂️  消息分组器演示")
    print("=" * 70)

    # 演示函数映射
    demos = {
        "time-window": demo_time_window_grouping,
        "similarity": demo_similarity_detection,
        "batch": demo_batch_send,
        "priority": demo_priority_escalation,
        "statistics": demo_statistics,
        "cleanup": demo_cleanup,
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
