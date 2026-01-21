#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书卡片构建演示

展示 CardBuilder 的各种用法和卡片模板。

Usage:
    python scripts/notifications/send_card_demo.py
    python scripts/notifications/send_card_demo.py --template success
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


# ========== 卡片模板 ==========

def template_success(title: str = "操作成功", content: str = "任务已完成"):
    """成功消息模板"""
    return (CardBuilder()
        .header(f"✅ {title}", status="success")
        .markdown(f"**详情**: {content}")
        .build())


def template_error(title: str = "操作失败", content: str = "发生了错误"):
    """错误消息模板"""
    return (CardBuilder()
        .header(f"❌ {title}", status="error")
        .metadata("错误类型", "Error")
        .markdown(f"**详情**: {content}")
        .note("请检查系统状态后重试")
        .build())


def template_warning(title: str = "需要注意", content: str = "需要注意的事项"):
    """警告消息模板"""
    return (CardBuilder()
        .header(f"⚠️  {title}", status="warning")
        .markdown(f"**提醒**: {content}")
        .build())


def template_info(title: str = "信息提示", content: str = "这是一条信息"):
    """信息消息模板"""
    return (CardBuilder()
        .header(f"🔔 {title}", status="info")
        .markdown(f"**内容**: {content}")
        .build())


def template_statistics(title: str, stats: dict):
    """统计消息模板"""
    card = (CardBuilder()
        .header(f"📊 {title}", status="success"))

    # 添加元数据
    for key, value in stats.items():
        card = card.metadata(key, str(value))

    return card.build()


def template_task_complete(task_name: str, duration: str = "未知"):
    """任务完成模板"""
    return (CardBuilder()
        .header("✅ 任务完成", status="success")
        .metadata("任务", task_name)
        .metadata("耗时", duration)
        .markdown(f"任务 **{task_name}** 已成功完成")
        .divider()
        .note(f"总耗时: {duration}")
        .build())


def template_batch_upload(total: int, success: int, failed: int, files: list):
    """批量上传模板"""
    file_list = "\n".join([f"- {f}" for f in files[:5]])
    if len(files) > 5:
        file_list += f"\n- ... 还有 {len(files) - 5} 个文件"

    return (CardBuilder()
        .header("📈 批量上传统计", status="success")
        .metadata("总数", f"{total} 个")
        .metadata("成功", f"{success} 个")
        .metadata("失败", f"{failed} 个")
        .markdown(f"**上传列表**:\n{file_list}")
        .divider()
        .note(f"成功: {success}, 失败: {failed}")
        .build())


def template_progress(title: str, current: int, total: int, status_msg: str):
    """进度消息模板"""
    percentage = int((current / total) * 100) if total > 0 else 0

    return (CardBuilder()
        .header(f"⏳ {title}", status="info")
        .metadata("进度", f"{current}/{total}")
        .metadata("百分比", f"{percentage}%")
        .markdown(f"**状态**: {status_msg}")
        .build())


def template_notification(title: str, message: str, metadata: dict = None):
    """通用通知模板"""
    card = (CardBuilder()
        .header(f"🔔 {title}", status="info")
        .markdown(message))

    if metadata:
        for key, value in metadata.items():
            card = card.metadata(key, str(value))

    return card.build()


# ========== 发送函数 ==========

def send_template(template_name: str, webhook_url: str, **kwargs):
    """发送指定模板"""
    templates = {
        "success": template_success,
        "error": template_error,
        "warning": template_warning,
        "info": template_info,
        "task_complete": template_task_complete,
        "statistics": template_statistics,
        "batch_upload": template_batch_upload,
        "progress": template_progress,
        "notification": template_notification,
    }

    if template_name not in templates:
        print(f"❌ 未知的模板: {template_name}")
        return False

    print(f"\n📝 发送模板: {template_name}")

    # 构建卡片
    if template_name == "statistics":
        card = templates[template_name](**kwargs)
    else:
        card = templates[template_name](**kwargs)

    # 发送
    settings = create_settings(webhook_url=webhook_url)

    try:
        with WebhookChannel(settings) as channel:
            success = channel.send(card.to_dict(), f"template_{template_name}")
            if success:
                print(f"   ✅ 模板 '{template_name}' 发送成功")
            else:
                print(f"   ❌ 模板 '{template_name}' 发送失败")
            return success
    except Exception as e:
        print(f"   💥 异常: {e}")
        return False


def demo_all_templates(webhook_url: str):
    """演示所有模板"""
    print("\n" + "=" * 70)
    print("🎨 演示所有卡片模板")
    print("=" * 70)

    demos = [
        ("success", {"title": "测试成功", "content": "所有测试通过"}),
        ("error", {"title": "测试失败", "content": "连接超时"}),
        ("warning", {"title": "警告", "content": "内存使用率过高"}),
        ("info", {"title": "系统信息", "content": "系统运行正常"}),
        ("task_complete", {"task_name": "数据同步", "duration": "2.5 秒"}),
        ("statistics", {"title": "性能统计", "stats": {"CPU": "45%", "内存": "2.3GB", "网络": "125Mbps"}}),
        ("batch_upload", {
            "total": 8,
            "success": 7,
            "failed": 1,
            "files": ["README.md", "API.md", "GUIDE.md", "CONFIG.md"]
        }),
        ("progress", {"title": "文件处理", "current": 3, "total": 10, "status_msg": "正在处理..."}),
        ("notification", {"title": "新消息", "message": "你有 3 条新通知", "metadata": {"来源": "系统", "时间": "10:30"}}),
    ]

    results = []
    for template_name, kwargs in demos:
        success = send_template(template_name, webhook_url, **kwargs)
        results.append((template_name, success))
        import time
        time.sleep(0.5)

    # 总结
    print("\n" + "=" * 70)
    print("📊 发送结果")
    print("=" * 70)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")

    passed = sum(1 for _, s in results if s)
    print(f"\n   总计: {passed}/{len(results)} 成功")

    return passed == len(results)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="飞书卡片构建演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用模板:
  success       - 成功消息
  error         - 错误消息
  warning       - 警告消息
  info          - 信息消息
  task_complete - 任务完成消息
  statistics    - 统计消息
  batch_upload  - 批量上传消息
  progress      - 进度消息
  notification  - 通用通知消息
  all           - 演示所有模板

示例:
  # 演示所有模板
  python scripts/notifications/send_card_demo.py

  # 发送成功消息
  python scripts/notifications/send_card_demo.py --template success

  # 发送任务完成消息
  python scripts/notifications/send_card_demo.py --template task_complete --task-name "数据同步"

  # 发送统计消息
  python scripts/notifications/send_card_demo.py --template statistics --title "性能统计"
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--template",
        choices=["success", "error", "warning", "info", "task_complete", "statistics",
                 "batch_upload", "progress", "notification", "all"],
        default="all",
        help="卡片模板 (默认: all)"
    )

    # 模板特定参数
    parser.add_argument("--title", help="标题")
    parser.add_argument("--content", help="内容")
    parser.add_argument("--task-name", help="任务名称")
    parser.add_argument("--duration", help="耗时")

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 飞书卡片构建演示")
    print("=" * 70)

    # 加载配置
    if args.url:
        webhook_url = args.url
    else:
        settings = create_settings()
        is_valid, missing = settings.validate_required_fields()
        if not is_valid:
            print(f"\n❌ 配置不完整！缺少: {', '.join(missing)}")
            return 1
        webhook_url = settings.webhook_url

    print(f"\n📡 Webhook URL: {webhook_url[:50]}...")

    # 演示所有模板
    if args.template == "all":
        success = demo_all_templates(webhook_url)
        return 0 if success else 1

    # 发送单个模板
    kwargs = {}
    if args.title:
        kwargs["title"] = args.title
    if args.content:
        kwargs["content"] = args.content
    if args.task_name:
        kwargs["task_name"] = args.task_name
    if args.duration:
        kwargs["duration"] = args.duration

    # 根据模板设置默认参数
    if args.template == "task_complete" and "task_name" not in kwargs:
        kwargs["task_name"] = "测试任务"
        kwargs["duration"] = "1.0 秒"
    elif args.template == "success" and "title" not in kwargs:
        kwargs["title"] = "测试成功"
        kwargs["content"] = "操作已完成"

    success = send_template(args.template, webhook_url, **kwargs)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
