# 飞书通知系统 - 集成测试和演示

本目录包含飞书通知系统的集成测试脚本和演示程序。

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `test_webhook.py` | 测试 Webhook 配置是否正确 |
| `send_notification.py` | 发送各种类型的通知消息 |
| `send_card_demo.py` | 演示所有卡片模板和构建方法 |

---

## 🚀 快速开始

### 1. 配置 Webhook URL

在项目根目录的 `.env` 文件中设置：

```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL
```

或设置环境变量：

```bash
export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL
```

### 2. 运行测试

#### 测试 Webhook 连接

```bash
# 测试所有功能（4 种测试）
python scripts/notifications/test_webhook.py
```

输出：
```
📝 测试 1: 简单文本消息
   ✅ 简单文本消息发送成功！

📝 测试 2: 交互式卡片
   ✅ 交互式卡片发送成功！

📝 测试 3: WebhookChannel
   ✅ WebhookChannel 发送成功！

📝 测试 4: 不同类型的卡片
   ✅ 多种类型卡片发送成功！

🎉 所有测试通过！Webhook 配置正确！
```

#### 发送通知消息

```bash
# 发送所有类型的消息
python scripts/notifications/send_notification.py

# 只发送简单消息
python scripts/notifications/send_notification.py --type simple

# 发送错误消息
python scripts/notifications/send_notification.py --type error
```

#### 演示卡片模板

```bash
# 演示所有模板（9 种）
python scripts/notifications/send_card_demo.py

# 发送成功消息模板
python scripts/notifications/send_card_demo.py --template success

# 发送任务完成模板
python scripts/notifications/send_card_demo.py --template task_complete --task-name "数据同步"
```

---

## 📖 脚本详解

### test_webhook.py

Webhook 连接测试工具，验证飞书 Webhook 配置是否正确。

**测试内容**:
1. 简单文本消息
2. 交互式卡片
3. WebhookChannel
4. 多种类型卡片

### send_notification.py

发送各种类型的通知消息演示。

**消息类型**:
- `simple` - 简单消息
- `metadata` - 带元数据的消息
- `error` - 错误消息
- `statistics` - 统计消息
- `all` - 所有类型（默认）

### send_card_demo.py

展示所有卡片模板和构建方法。

**可用模板**:
| 模板 | 用途 |
|------|------|
| `success` | 成功消息 |
| `error` | 错误消息 |
| `warning` | 警告消息 |
| `info` | 信息消息 |
| `task_complete` | 任务完成消息 |
| `statistics` | 统计消息 |
| `batch_upload` | 批量上传消息 |
| `progress` | 进度消息 |
| `notification` | 通用通知消息 |

---

## 💡 代码示例

### 发送简单消息

```python
from notifications.templates.builder import CardBuilder
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings

settings = create_settings()

with WebhookChannel(settings) as channel:
    card = (CardBuilder()
        .header("✅ 消息标题", status="success")
        .markdown("**内容**: 你的消息内容")
        .build())

    channel.send(card.to_dict(), "message_type")
```

### 使用模板

```python
from scripts.notifications.send_card_demo import template_success, template_error

# 成功消息
card = template_success("操作完成", "所有任务已成功完成")

# 错误消息
card = template_error("连接失败", "数据库连接超时")
```

---

## 🔗 获取 Webhook URL

1. 打开飞书群聊
2. 群设置 → 群机器人 → 添加机器人
3. 选择「自定义机器人」
4. 复制 Webhook URL

---

## ⚠️ 注意事项

1. **Webhook URL 安全**: 不要将 URL 提交到公开仓库
2. **环境变量**: 推荐使用 `.env` 文件配置
3. **消息限制**: 飞书 Webhook 有频率限制，建议使用消息分组和限流
4. **测试环境**: 测试时建议使用专门的测试群聊

---

## 📚 相关文档

- [通知系统使用指南](../../../tmp/NOTIFICATION_USAGE_GUIDE.md)
- [快速参考](../../../tmp/QUICK_SEND_FEISHU.md)
- [通知系统设计](../../docs/IMPLEMENTATION_PROGRESS.md)

---

## 🛠️ 故障排查

### 错误: code 19001 - param invalid: incoming webhook access token invalid

**原因**: Webhook URL 无效或已过期

**解决**:
1. 检查 `.env` 文件中的 URL 是否正确
2. 去掉 URL 两端的引号
3. 重新创建 Webhook 机器人获取新 URL

### 错误: ModuleNotFoundError: No module named 'notifications'

**原因**: Python 路径问题

**解决**: 从项目根目录运行脚本
```bash
cd /path/to/feishu-doc-tools
python scripts/notifications/test_webhook.py
```

### 错误: 配置不完整

**原因**: 环境变量未设置

**解决**:
```bash
export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_URL
```
