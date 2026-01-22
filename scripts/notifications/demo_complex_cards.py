#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
飞书复杂卡片内容组合演示

展示 CardBuilder 的复杂内容组合能力：
- Multi-level nested structures (dashboard with columns, collapsible panels)
- Complex statistical reports (weekly summary with metrics)
- Progressive notifications (release progress with stages)
- Rich formatting examples (markdown, dividers, notes)

Usage:
    # 演示所有复杂卡片
    python scripts/notifications/demo_complex_cards.py

    # 演示特定类型
    python scripts/notifications/demo_complex_cards.py --type dashboard
    python scripts/notifications/demo_complex_cards.py --type report
    python scripts/notifications/demo_complex_cards.py --type progress
    python scripts/notifications/demo_complex_cards.py --type rich
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


# ========== 复杂卡片模板 ==========

def demo_dashboard(webhook_url: str):
    """演示多级嵌套结构 - 项目仪表板"""
    print("\n📊 演示：项目仪表板（多级嵌套结构）")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 项目概览仪表板
        card = (CardBuilder()
            .header("📊 项目仪表板", status="running", color="wathet", subtitle="实时监控面板")

            # 顶部指标行 - 4列
            .columns()
                .column("📁 总任务", "156", width="weighted", weight=1)
                .column("✅ 进行中", "45", width="weighted", weight=1)
                .column("⏳ 待处理", "89", width="weighted", weight=1)
                .column("❌ 已延期", "22", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 项目状态列 - 双列布局
            .columns()
                .column("🔵 前端开发", "进度: 75%", width="weighted", weight=1)
                .column("🟢 后端API", "进度: 90%", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 可折叠面板 - 开发环境信息
            .collapsible("开发环境详情",
                       "- **系统**: Linux 5.15.0\n"
                       "- **Python**: 3.11.5\n"
                       "- **Node**: v20.10.0\n"
                       "- **Docker**: 24.0.7\n"
                       "- **内存**: 4.2GB / 16GB\n"
                       "- **CPU**: 45%")

            .divider()

            # 可折叠面板 - 任务分布
            .collapsible("任务分布详情",
                       "```json\n"
                       "{\n"
                       "  \"high_priority\": 12,\n"
                       "  \"medium_priority\": 45,\n"
                       "  \"low_priority\": 89,\n"
                       "  \"completed_this_week\": 34,\n"
                       "  \"overdue\": 22\n"
                       "}\n"
                       "```")

            .divider()

            # 底部操作提示
            .markdown("**快捷操作**:")
            .markdown("- 📝 查看详情\n"
                     "- 🔄 刷新数据\n"
                     "- ⚙️ 配置提醒")

            .divider()

            .note("💡 提示：数据每5分钟自动更新一次")

            .build())

        success = channel.send(card.to_dict(), "dashboard_project")

        status = "✅" if success else "❌"
        print(f"   {status} 项目仪表板")

        return success


def demo_report(webhook_url: str):
    """演示复杂统计报告 - 周报"""
    print("\n📈 演示：统计报告（周报）")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 周报卡片
        card = (CardBuilder()
            .header("📈 周度统计报告", status="success", color="green",
                   subtitle="2026年01月第3周")

            # 基本指标 - 三列布局
            .markdown("**本周概览**")
            .columns()
                .column("📄 文档更新", "23 篇", width="weighted", weight=1)
                .column("🐛 问题修复", "15 个", width="weighted", weight=1)
                .column("✨ 新功能", "8 项", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 代码统计 - 多列布局
            .markdown("**代码统计**")
            .columns()
                .column("新增代码", "+2,345 行", width="auto")
                .column("删除代码", "-892 行", width="auto")
                .column("净增", "+1,453 行", width="auto")
            .end_columns()

            .divider()

            # 质量指标
            .markdown("**质量指标**")
            .columns()
                .column("测试覆盖", "87.5%", width="weighted", weight=2)
                .column("代码审查", "100%", width="weighted", weight=1)
                .column("文档完整", "92%", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 详细数据 - 可折叠面板
            .collapsible("详细数据",
                       "- **提交次数**: 156 commits\n"
                       "- **参与人员**: 8 人\n"
                       "- **代码审查**: 42 PRs\n"
                       "- **平均响应时间**: 2.3 小时\n"
                       "- **问题解决率**: 94.2%")

            .collapsible("各部门贡献",
                       "```json\n"
                       "{\n"
                       "  \"frontend\": {\n"
                       "    \"commits\": 67,\n"
                       "    \"files_changed\": 34,\n"
                       "    \"lines_added\": 1234\n"
                       "  },\n"
                       "  \"backend\": {\n"
                       "    \"commits\": 89,\n"
                       "    \"files_changed\": 45,\n"
                       "    \"lines_added\": 1111\n"
                       "  }\n"
                       "}\n"
                       "```")

            .divider()

            # 同比数据
            .markdown("**同比上周**")
            .columns()
                .column("文档", "↑ 15%", width="auto")
                .column("修复", "↑ 8%", width="auto")
                .column("功能", "→ 0%", width="auto")
            .end_columns()

            .divider()

            # 总结与建议
            .note("📊 本周团队表现优秀，文档更新量和代码质量都有显著提升。建议继续保持代码审查频率。")

            .build())

        success = channel.send(card.to_dict(), "report_weekly")

        status = "✅" if success else "❌"
        print(f"   {status} 周度统计报告")

        return success


def demo_progress(webhook_url: str):
    """演示渐进式通知 - 发布进度"""
    print("\n🚀 演示：渐进式通知（发布进度）")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 发布阶段1 - 准备中
        card1 = (CardBuilder()
            .header("🔄 发布准备中", status="running", color="wathet",
                   subtitle="版本 v2.3.0")
            .markdown("**当前阶段**: 代码审查")
            .metadata("进度", "1/5")
            .metadata("预计耗时", "15 分钟")
            .divider()
            .markdown("**发布流程**:")
            .markdown("1. ✅ 代码合并\n"
                     "2. 🔄 代码审查 (当前)\n"
                     "3. ⏳ 单元测试\n"
                     "4. ⏳ 集成测试\n"
                     "5. ⏳ 生产部署")
            .divider()
            .note("⏰ 开始时间: 10:00")
            .build())

        # 发布阶段2 - 测试中
        card2 = (CardBuilder()
            .header("🧪 测试进行中", status="running", color="wathet",
                   subtitle="版本 v2.3.0")
            .markdown("**当前阶段**: 集成测试")
            .metadata("进度", "3/5")
            .metadata("预计耗时", "20 分钟")
            .divider()
            .markdown("**发布流程**:")
            .markdown("1. ✅ 代码合并\n"
                     "2. ✅ 代码审查\n"
                     "3. ✅ 单元测试 (156/156 通过)\n"
                     "4. 🔄 集成测试 (当前)\n"
                     "5. ⏳ 生产部署")
            .divider()
            .collapsible("测试结果",
                       "- **单元测试**: 156 通过, 0 失败\n"
                       "- **测试覆盖率**: 87.5%\n"
                       "- **性能测试**: 通过\n"
                       "- **安全扫描**: 无高危漏洞")
            .divider()
            .note("⏰ 预计完成: 10:35")
            .build())

        # 发布阶段3 - 发布成功
        card3 = (CardBuilder()
            .header("✅ 发布成功", status="success", color="green",
                   subtitle="版本 v2.3.0")
            .markdown("**所有阶段已完成**")
            .metadata("总耗时", "42 分钟")
            .metadata("发布时间", "10:42")
            .divider()
            .markdown("**发布流程**:")
            .markdown("1. ✅ 代码合并 (10:00)\n"
                     "2. ✅ 代码审查 (10:15)\n"
                     "3. ✅ 单元测试 (10:22)\n"
                     "4. ✅ 集成测试 (10:35)\n"
                     "5. ✅ 生产部署 (10:42)")
            .divider()
            .columns()
                .column("测试通过", "156/156", width="weighted", weight=1)
                .column("覆盖率", "87.5%", width="weighted", weight=1)
                .column("回滚", "无需", width="weighted", weight=1)
            .end_columns()
            .divider()
            .collapsible("发布详情",
                       "```json\n"
                       "{\n"
                       "  \"version\": \"v2.3.0\",\n"
                       "  \"commit\": \"a1b2c3d\",\n"
                       "  \"build_time\": \"2026-01-22 10:35:00\",\n"
                       "  \"deploy_time\": \"2026-01-22 10:42:00\",\n"
                       "  \"environment\": \"production\"\n"
                       "}\n"
                       "```")
            .divider()
            .note("🎉 感谢团队的辛勤工作！")
            .build())

        # 发送所有卡片（模拟渐进式通知）
        r1 = channel.send(card1.to_dict(), "progress_stage1")

        import time
        time.sleep(2)  # 模拟时间间隔

        r2 = channel.send(card2.to_dict(), "progress_stage2")

        time.sleep(2)

        r3 = channel.send(card3.to_dict(), "progress_stage3")

        results = [("阶段1: 准备中", r1), ("阶段2: 测试中", r2), ("阶段3: 发布成功", r3)]

        for name, success in results:
            status = "✅" if success else "❌"
            print(f"   {status} {name}")

        return all(s for _, s in results)


def demo_rich(webhook_url: str):
    """演示富文本格式 - 多种格式组合"""
    print("\n🎨 演示：富文本格式")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 富文本示例卡片
        card = (CardBuilder()
            .header("🎨 富文本格式示例", status="info", color="blue")

            # Markdown 格式示例
            .markdown("**Markdown 格式示例**")
            .markdown("这是 **粗体** 和 *斜体* 文本")
            .markdown("这是 `行内代码` 和代码块:")
            .markdown("```python\n"
                     "def hello():\n"
                     "    print('Hello, Feishu!')\n"
                     "```")

            .divider()

            # 列表示例
            .markdown("**列表示例**:")
            .markdown("- 无序列表项 1\n"
                     "- 无序列表项 2\n"
                     "  - 嵌套项 2.1\n"
                     "  - 嵌套项 2.2\n"
                     "- 无序列表项 3")

            .markdown("**有序列表示例**:")
            .markdown("1. 第一项\n"
                     "2. 第二项\n"
                     "3. 第三项")

            .divider()

            # 链接和引用
            .markdown("**链接和引用**:")
            .markdown("[飞书开放平台](https://open.feishu.cn)")
            .markdown("> 这是引用文本\n> 可以跨行")

            .divider()

            # 表格（使用列布局模拟）
            .markdown("**表格数据** (使用列布局)")
            .columns()
                .column("姓名", "张三", width="weighted", weight=1)
                .column("职位", "工程师", width="weighted", weight=1)
                .column("状态", "在线", width="weighted", weight=1)
            .end_columns()
            .columns()
                .column("姓名", "李四", width="weighted", weight=1)
                .column("职位", "设计师", width="weighted", weight=1)
                .column("状态", "忙碌", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 强调和提示
            .markdown("**强调和提示**:")
            .markdown("⚠️ **警告**: 这是警告信息")
            .markdown("❌ **错误**: 这是错误信息")
            .markdown("✅ **成功**: 这是成功信息")
            .markdown("💡 **提示**: 这是提示信息")

            .divider()

            # Note 示例
            .note("这是 Note 示例：灰色背景的信息提示框")

            .divider()

            # 可折叠的代码示例
            .collapsible("查看更多示例",
                       "**水平线**:\n"
                       "---\n"
                       "***\n"
                       "___\n\n"
                       "**代码高亮**:\n"
                       "```javascript\n"
                       "console.log('Hello');\n"
                       "const x = 100;\n"
                       "```\n\n"
                       "**任务列表**:\n"
                       "- [x] 已完成任务\n"
                       "- [ ] 待办任务")

            .divider()

            # 混合格式
            .markdown("**混合格式示例**:")
            .markdown("在一段文字中混合使用 **粗体**、*斜体*、`代码` 和 [链接](https://example.com)")

            .build())

        success = channel.send(card.to_dict(), "rich_formatting")

        status = "✅" if success else "❌"
        print(f"   {status} 富文本格式示例")

        return success


def demo_combined_complex(webhook_url: str):
    """演示组合使用多种复杂功能"""
    print("\n🎯 演示：组合复杂功能")

    settings = create_settings(webhook_url=webhook_url)

    with WebhookChannel(settings) as channel:
        # 组合多种复杂功能的超级卡片
        card = (CardBuilder()
            .header("🎯 综合示例：系统健康报告",
                   status="success",
                   color="green",
                   subtitle="2026-01-22 14:30")

            # 顶部关键指标 - 多列布局
            .markdown("**📊 关键指标**")
            .columns()
                .column("系统状态", "🟢 正常", width="weighted", weight=1)
                .column("CPU使用", "45%", width="weighted", weight=1)
                .column("内存", "62%", width="weighted", weight=1)
                .column("磁盘", "78%", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 服务状态 - 嵌套列布局
            .markdown("**🔧 服务状态**")
            .columns()
                .column("API服务", "✅ 运行中", width="weighted", weight=2)
                .column("响应时间", "45ms", width="weighted", weight=1)
            .end_columns()
            .columns()
                .column("数据库", "✅ 运行中", width="weighted", weight=2)
                .column("连接数", "23/100", width="weighted", weight=1)
            .end_columns()
            .columns()
                .column("缓存", "✅ 运行中", width="weighted", weight=2)
                .column("命中率", "94.5%", width="weighted", weight=1)
            .end_columns()
            .columns()
                .column("消息队列", "⚠️ 高负载", width="weighted", weight=2)
                .column("积压", "1,234", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 今日统计
            .markdown("**📈 今日统计**")
            .columns()
                .column("请求总数", "1,234,567", width="weighted", weight=1)
                .column("错误率", "0.02%", width="weighted", weight=1)
                .column("平均响应", "38ms", width="weighted", weight=1)
            .end_columns()

            .divider()

            # 多层可折叠面板 - 详细信息
            .collapsible("系统配置",
                       "- **操作系统**: Ubuntu 22.04 LTS\n"
                       "- **内核版本**: 5.15.0\n"
                       "- **Python**: 3.11.5\n"
                       "- **应用版本**: v2.3.0")

            .collapsible("性能详情",
                       "```json\n"
                       "{\n"
                       "  \"cpu\": {\n"
                       "    \"usage\": 45,\n"
                       "    \"cores\": 8,\n"
                       "    \"frequency\": \"3.2GHz\"\n"
                       "  },\n"
                       "  \"memory\": {\n"
                       "    \"total\": \"16GB\",\n"
                       "    \"used\": \"9.9GB\",\n"
                       "    \"cached\": \"4.2GB\"\n"
                       "  },\n"
                       "  \"disk\": {\n"
                       "    \"total\": \"500GB\",\n"
                       "    \"used\": \"390GB\",\n"
                       "    \"available\": \"110GB\"\n"
                       "  }\n"
                       "}\n"
                       "```")

            .collapsible("最近告警",
                       "- 14:20 - 消息队列积压超过 1000 (已恢复)\n"
                       "- 13:45 - CPU使用率短暂超过 80% (已恢复)\n"
                       "- 12:30 - 数据库慢查询 (已优化)")

            .collapsible("操作日志",
                       "```text\n"
                       "[14:30] 系统检查完成\n"
                       "[14:25] 清理临时文件\n"
                       "[14:20] 重启消息队列\n"
                       "[14:15] 数据库备份完成\n"
                       "[14:00] 定时任务执行\n"
                       "```")

            .divider()

            # 建议和操作
            .markdown("**📋 建议操作**:")
            .markdown("1. 🔄 检查消息队列消费者配置\n"
                     "2. 📊 监控CPU使用趋势\n"
                     "3. 💾 清理历史日志文件")

            .divider()

            # 多个 Note 提供不同级别的信息
            .note("ℹ️ 下次计划维护时间: 2026-01-25 02:00-04:00")

            .divider()

            # 页脚信息
            .markdown("**报告生成时间**: 2026-01-22 14:30:15")
            .markdown("**数据来源**: 生产环境监控系统")

            .build())

        success = channel.send(card.to_dict(), "complex_combined")

        status = "✅" if success else "❌"
        print(f"   {status} 组合复杂功能")

        return success


# ========== 主程序 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="飞书复杂卡片内容组合演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
演示类型:
  dashboard  - 多级嵌套结构演示（项目仪表板）
  report     - 复杂统计报告演示（周报）
  progress   - 渐进式通知演示（发布进度）
  rich       - 富文本格式演示
  all        - 演示所有复杂卡片类型

示例:
  # 演示所有复杂卡片
  python scripts/notifications/demo_complex_cards.py

  # 演示特定类型
  python scripts/notifications/demo_complex_cards.py --type dashboard
  python scripts/notifications/demo_complex_cards.py --type report
  python scripts/notifications/demo_complex_cards.py --type progress
  python scripts/notifications/demo_complex_cards.py --type rich
        """
    )

    parser.add_argument(
        "--url",
        help="飞书 Webhook URL (默认使用环境变量 FEISHU_WEBHOOK_URL)"
    )

    parser.add_argument(
        "--type",
        choices=["dashboard", "report", "progress", "rich", "combined", "all"],
        default="all",
        help="演示类型 (默认: all)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🎨 飞书复杂卡片内容组合演示")
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
        "dashboard": demo_dashboard,
        "report": demo_report,
        "progress": demo_progress,
        "rich": demo_rich,
        "combined": demo_combined_complex,
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
