# 飞书通知功能设计方案

**设计日期**: 2026-01-20
**设计目标**: 在 md-to-feishu 项目中增加独立、灵活的飞书通知功能
**设计原则**: 高维护性、高灵活性、高稳定性

---

## 📋 目录

- [一、飞书通知API能力调研](#一飞书通知api能力调研)
- [二、系统架构设计](#二系统架构设计)
- [三、核心代码设计](#三核心代码设计)
- [四、配置系统设计](#四配置系统设计)
- [五、使用方式](#五使用方式)
- [六、实现计划](#六实现计划)
- [七、设计优势](#七设计优势)
- [八、技术栈](#八技术栈)

---

## 一、飞书通知API能力调研

### 1.1 四种通知方式对比

| 方式 | 接收者 | 认证 | 难度 | 适用场景 |
|------|--------|------|------|---------|
| **群自定义机器人** | 仅群聊 | Webhook URL | ⭐ 简单 | CI/CD通知、告警、定期提醒 |
| **API发送消息** | 用户/群聊 | App凭证+Token | ⭐⭐⭐ 中等 | 个人通知、精准推送 |
| **卡片消息** | 用户/群聊 | 依赖上层 | ⭐⭐⭐ 中等 | 交互式通知、审批流 |
| **事件订阅** | 应用接收 | 加密回调 | ⭐⭐⭐⭐ 较难 | 聊天机器人、自动化 |

### 1.2 API调用示例

#### 群自定义机器人 Webhook

```python
import requests

webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxx"
data = {
    "msg_type": "text",
    "content": {"text": "群通知：部署成功！"}
}
response = requests.post(webhook_url, json=data)
```

**签名验证示例**：

```python
import hmac
import hashlib
import time
import uuid

webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxx"
verify_key = "your_verify_key"

timestamp = str(int(time.time()))
nonce = uuid.uuid4().hex
sign_str = timestamp + key + nonce
signature = hashlib.sha256(sign_str.encode()).hexdigest()

headers = {
    "X-Lark-Request-Timestamp": timestamp,
    "X-Lark-Request-Nonce": nonce,
    "X-Lark-Signature": signature
}

response = requests.post(webhook_url, json=data, headers=headers)
```

#### API发送消息

```python
import requests
import json

# 1. 获取 tenant_access_token
token_resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret}
)
token = token_resp.json()["tenant_access_token"]

# 2. 发送消息
msg_resp = requests.post(
    f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "receive_id": "ou_xxxxxxxxx",
        "msg_type": "text",
        "content": json.dumps({"text": "API 发送的消息"})
    }
)
```

#### 发送卡片消息

```python
card_content = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "部署成功通知"},
        "template": "green"
    },
    "elements": [
        {
            "tag": "div",
            "fields": [
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": "**项目**:\nfeishu-doc-tools"
                    }
                },
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": "**状态**:\n✅ 成功"
                    }
                }
            ]
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看日志"},
                    "type": "default",
                    "url": "https://example.com/logs"
                }
            ]
        }
    ]
}

data = {
    "msg_type": "interactive",
    "card": card_content
}

response = requests.post(webhook_url, json=data)
```

---

## 二、系统架构设计

### 2.1 核心设计原则

**保持与现有架构的一致性**：

```
现有架构: Markdown → Python Script → JSON → AI + MCP → Feishu
新增架构: Trigger → Python Script → JSON → AI + MCP → Feishu
```

**设计模式应用**：

- **Strategy Pattern** - 支持4种飞书通知方式
- **Builder Pattern** - 构建复杂的消息（卡片、模板）
- **Facade Pattern** - 简化使用接口
- **Observer Pattern** - 支持多种触发方式

### 2.2 项目结构

```
feishu-doc-tools/
├── scripts/
│   ├── md_to_feishu.py          # 现有
│   └── notification_sender.py   # 新增：CLI入口
├── lib/
│   ├── feishu_md_uploader.py     # 现有
│   └── feishu_notification.py    # 新增：核心库
├── notification/                  # 新增：通知模块
│   ├── __init__.py
│   ├── core/                     # 核心接口
│   │   ├── message.py           # NotificationMessage, NotificationTarget
│   │   ├── strategy.py          # NotificationStrategy（抽象基类）
│   │   └── sender.py            # NotificationSender（门面）
│   ├── strategies/               # 策略实现
│   │   ├── webhook.py           # WebhookNotificationStrategy
│   │   ├── api.py               # ApiNotificationStrategy
│   │   ├── card.py              # CardNotificationStrategy
│   │   └── event_subscription.py # EventSubscriptionStrategy
│   ├── builders/                 # 构建器
│   │   ├── base.py              # NotificationBuilder
│   │   ├── text_builder.py      # 文本消息构建器
│   │   └── card_builder.py      # 卡片消息构建器
│   ├── triggers/                 # 触发器
│   │   ├── cli.py               # CLI命令触发
│   │   ├── file_watch.py        # 文件变化触发
│   │   └── http.py              # HTTP请求触发
│   ├── templates/                # 消息模板
│   │   ├── deploy_success.yaml
│   │   └── error_alert.yaml
│   └── config.py                 # 配置管理
└── docs/
    └── NOTIFICATION_DESIGN.md    # 本文档
```

### 2.3 架构层次图

```
┌─────────────────────────────────────────────────────────────┐
│                    Notification System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Triggers   │─────▶│    Builder   │                    │
│  │ (CLI/HTTP/   │      │  (Template)  │                    │
│  │  FileWatch)  │      └──────┬───────┘                    │
│  └──────────────┘             │                             │
│                              ▼                             │
│  ┌────────────────────────────────────────┐                │
│  │         NotificationSender             │                │
│  │         (Facade + Retry + Log)         │                │
│  └───────────────┬────────────────────────┘                │
│                  │                                          │
│          ┌───────┴────────┐                                │
│          ▼                ▼                                │
│  ┌───────────────┐  ┌───────────────┐                      │
│  │   Strategies  │  │    Config    │                      │
│  │  (4种飞书方式) │  │  (YAML/ENV)  │                      │
│  └───────┬───────┘  └───────────────┘                      │
│          │                                                  │
│          ▼                                                  │
│  ┌────────────────────────────────────────┐                │
│  │              Feishu API                │                │
│  └────────────────────────────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心代码设计

### 3.1 核心接口（notification/core/message.py）

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class NotificationMessage:
    """通知消息的统一表示"""
    msg_type: str  # text, interactive, image, etc.
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class NotificationTarget:
    """通知目标的统一表示"""
    target_type: str  # webhook, user, group, chat
    target_id: str  # webhook_url, open_id, chat_id
    target_name: str  # for logging
```

### 3.2 策略接口（notification/core/strategy.py）

```python
from abc import ABC, abstractmethod
from typing import List

class NotificationStrategy(ABC):
    """通知策略的抽象基类"""

    @abstractmethod
    def send(self,
             message: NotificationMessage,
             target: NotificationTarget) -> bool:
        """发送通知，返回是否成功"""
        pass

    @abstractmethod
    def validate_target(self, target: NotificationTarget) -> bool:
        """验证目标是否有效"""
        pass

    @abstractmethod
    def get_supported_msg_types(self) -> List[str]:
        """获取支持的消息类型"""
        pass
```

### 3.3 发送器（notification/core/sender.py）

```python
import time
import logging
from typing import List, Dict

class NotificationSender:
    """通知发送器（门面模式）"""

    def __init__(self, strategy: NotificationStrategy):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

    def send(self,
             message: NotificationMessage,
             target: NotificationTarget,
             retry: int = 3) -> bool:
        """发送通知（带重试）"""
        if not self.strategy.validate_target(target):
            self.logger.error(f"Invalid target: {target.target_name}")
            return False

        for attempt in range(retry):
            try:
                success = self.strategy.send(message, target)
                if success:
                    self.logger.info(
                        f"✅ Sent to {target.target_name}: "
                        f"{message.msg_type}"
                    )
                    return True
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}"
                )
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # 指数退避

        self.logger.error(f"❌ Failed after {retry} attempts")
        return False

    def send_batch(self,
                   messages: List[NotificationMessage],
                   targets: List[NotificationTarget]) -> Dict[str, bool]:
        """批量发送"""
        results = {}
        for target in targets:
            results[target.target_name] = all(
                self.send(msg, target, retry=1)
                for msg in messages
            )
        return results
```

### 3.4 构建器（notification/builders/base.py）

```python
from typing import Dict, Any

class NotificationBuilder:
    """通知构建器（Builder Pattern）"""

    def __init__(self):
        self._msg_type = "text"
        self._content = {}
        self._metadata = {}

    def with_type(self, msg_type: str) -> 'NotificationBuilder':
        """设置消息类型"""
        self._msg_type = msg_type
        return self

    def with_text(self, text: str) -> 'NotificationBuilder':
        """设置文本内容"""
        self._content = {"text": text}
        return self

    def with_card(self, card: Dict) -> 'NotificationBuilder':
        """设置卡片内容"""
        self._content = {"card": card}
        return self

    def with_template(self,
                     template: str,
                     **kwargs) -> 'NotificationBuilder':
        """使用模板构建内容"""
        # 从模板文件加载并替换变量
        pass

    def with_metadata(self, **kwargs) -> 'NotificationBuilder':
        """添加元数据"""
        self._metadata.update(kwargs)
        return self

    def build(self) -> NotificationMessage:
        """构建消息"""
        return NotificationMessage(
            msg_type=self._msg_type,
            content=self._content,
            metadata=self._metadata or None
        )
```

### 3.5 策略实现示例（notification/strategies/webhook.py）

```python
import requests
from notification.core.strategy import NotificationStrategy
from notification.core.message import NotificationMessage, NotificationTarget

class WebhookNotificationStrategy(NotificationStrategy):
    """群自定义机器人策略"""

    def send(self,
             message: NotificationMessage,
             target: NotificationTarget) -> bool:
        """发送Webhook通知"""
        webhook_url = target.target_id

        # 构建请求数据
        data = {
            "msg_type": message.msg_type,
            "content": message.content
        }

        # 发送请求
        response = requests.post(
            webhook_url,
            json=data,
            timeout=30
        )

        return response.status_code == 200

    def validate_target(self, target: NotificationTarget) -> bool:
        """验证Webhook URL"""
        return target.target_id.startswith(
            "https://open.feishu.cn/open-apis/bot/v2/hook/"
        )

    def get_supported_msg_types(self) -> List[str]:
        """支持的消息类型"""
        return ["text", "post", "interactive", "image"]
```

---

## 四、配置系统设计

### 4.1 YAML配置文件

```yaml
# notification_config.yaml
strategy: webhook

# 目标配置（支持多个）
targets:
  - type: webhook
    id: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    name: "DevOps通知群"

  - type: webhook
    id: "https://open.feishu.cn/open-apis/bot/v2/hook/yyy"
    name: "产品群"

# 消息配置
message:
  type: text
  template: "✅ {project} 部署成功\n版本: {version}\n时间: {timestamp}"

# 发送配置
sending:
  retry: 3
  timeout: 30
  batch_size: 10

# 日志配置
logging:
  level: INFO
  file: notification.log
```

### 4.2 配置加载代码

```python
import yaml
import os
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class NotificationConfig:
    """通知配置"""
    strategy_type: str
    targets: List[Dict[str, str]]
    msg_type: str
    template: Optional[str] = None
    retry: int = 3
    timeout: int = 30

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'NotificationConfig':
        """从YAML文件加载配置"""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        """从环境变量加载配置"""
        return cls(
            strategy_type=os.getenv("NOTIFICATION_STRATEGY", "webhook"),
            targets=[{
                "type": "webhook",
                "id": os.getenv("FEISHU_WEBHOOK_URL"),
                "name": os.getenv("FEISHU_TARGET_NAME", "Default")
            }],
            msg_type="text",
            retry=int(os.getenv("NOTIFICATION_RETRY", "3"))
        )

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.targets:
            raise ValueError("No targets configured")
        return True
```

---

## 五、使用方式

### 5.1 CLI命令行

```bash
# 发送简单文本
python scripts/notification_sender.py \
  --config notification_config.yaml \
  --message "部署成功！"

# 使用模板
python scripts/notification_sender.py \
  --config notification_config.yaml \
  --template deploy_success \
  --var version=v1.2.3

# 从stdin读取（支持管道）
echo "构建失败" | python scripts/notification_sender.py \
  --config notification_config.yaml

# 监听文件变化
python scripts/notification_sender.py \
  --watch README.md \
  --config notification_config.yaml
```

### 5.2 Python库

```python
from lib.feishu_notification import NotificationSender, NotificationBuilder
from notification.strategies import WebhookNotificationStrategy
from notification.core import NotificationTarget

# 创建发送器
strategy = WebhookNotificationStrategy()
sender = NotificationSender(strategy)

# 构建消息
message = (NotificationBuilder()
    .with_type("text")
    .with_text("✅ 部署成功")
    .build())

# 发送通知
target = NotificationTarget(
    target_type="webhook",
    target_id="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    target_name="DevOps群"
)

sender.send(message, target)
```

### 5.3 发送卡片消息

```python
# 构建卡片内容
card_content = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "部署成功通知"},
        "template": "green"
    },
    "elements": [
        {
            "tag": "div",
            "fields": [
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": "**项目**:\nfeishu-doc-tools"
                    }
                },
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": "**状态**:\n✅ 成功"
                    }
                }
            ]
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看日志"},
                    "type": "default",
                    "url": "https://example.com/logs"
                }
            ]
        }
    ]
}

# 构建并发送
message = (NotificationBuilder()
    .with_type("interactive")
    .with_card(card_content)
    .build())

sender.send(message, target)
```

### 5.4 批量发送

```python
# 多个消息
messages = [
    (NotificationBuilder().with_text("消息1").build()),
    (NotificationBuilder().with_text("消息2").build()),
]

# 多个目标
targets = [
    NotificationTarget("webhook", webhook_url_1, "群1"),
    NotificationTarget("webhook", webhook_url_2, "群2"),
]

# 批量发送
results = sender.send_batch(messages, targets)
print(results)  # {"群1": True, "群2": True}
```

---

## 六、实现计划

### Phase 1: MVP - Webhook通知（3天）

**目标**: 可以通过Webhook发送文本通知

**任务清单**:
- [ ] 创建核心接口和数据类
  - [ ] `NotificationMessage` 和 `NotificationTarget`
  - [ ] `NotificationStrategy` 抽象基类
- [ ] 实现 `WebhookNotificationStrategy`
  - [ ] 支持文本消息
  - [ ] 支持签名验证
- [ ] 实现 `NotificationSender` 门面类
  - [ ] 重试机制
  - [ ] 错误处理
- [ ] 创建简单的CLI脚本
  - [ ] 环境变量配置
  - [ ] 命令行参数解析
- [ ] 编写基础测试
  - [ ] Mock飞书API
  - [ ] 单元测试覆盖

**交付物**:
- 可以通过Webhook发送文本通知
- 支持环境变量配置
- 基础测试覆盖

### Phase 2: 增强功能（4天）

**目标**: 支持4种消息类型和模板系统

**任务清单**:
- [ ] 实现 `ApiNotificationStrategy`
  - [ ] Token获取和管理
  - [ ] 支持个人通知
  - [ ] 限流处理
- [ ] 实现Builder系统
  - [ ] `NotificationBuilder` 基类
  - [ ] `TextBuilder` 文本构建器
  - [ ] `CardBuilder` 卡片构建器
- [ ] 实现模板系统
  - [ ] 模板加载
  - [ ] 变量替换
  - [ ] 内置模板
- [ ] 实现YAML配置支持
  - [ ] 配置文件解析
  - [ ] 配置验证
  - [ ] 多目标支持
- [ ] 完整测试覆盖
  - [ ] 各策略的单元测试
  - [ ] 集成测试
  - [ ] 测试覆盖率 > 80%

**交付物**:
- 支持4种消息类型
- 支持模板变量
- 支持配置文件
- 完整测试覆盖

### Phase 3: 高级特性（3-6天）

**目标**: 支持卡片消息和多种触发方式

**任务清单**:
- [ ] 实现 `CardNotificationStrategy`
  - [ ] 交互式卡片支持
  - [ ] 按钮、表单等元素
- [ ] 实现多种触发器
  - [ ] `CLITrigger` 命令行触发
  - [ ] `FileWatchTrigger` 文件监听
  - [ ] `HTTPTrigger` HTTP请求触发
- [ ] 批量发送优化
  - [ ] 并发发送
  - [ ] 速率控制
- [ ] 完善文档
  - [ ] API文档
  - [ ] 使用示例
  - [ ] 最佳实践

**交付物**:
- 支持卡片消息
- 支持多种触发方式
- 完整使用文档

**总工作量**: 10-13天

---

## 七、设计优势

### 7.1 高灵活性

- ✅ **支持4种飞书通知方式**: 从简单的Webhook到复杂的API和卡片
- ✅ **策略模式易于扩展**: 添加新的通知方式只需实现新策略
- ✅ **支持多种触发方式**: CLI、文件监听、HTTP请求等
- ✅ **支持模板和变量**: 灵活的消息内容定制

### 7.2 高维护性

- ✅ **SOLID原则**: 清晰的职责分离，每个类只做一件事
- ✅ **配置与代码分离**: YAML配置文件，易于修改
- ✅ **完善的类型注解**: 使用dataclass和类型提示
- ✅ **全面的单元测试**: 测试覆盖率 > 80%
- ✅ **详细的日志记录**: 便于调试和监控

### 7.3 高稳定性

- ✅ **错误处理和重试**: 指数退避重试机制
- ✅ **详细的日志记录**: INFO、WARNING、ERROR分级
- ✅ **配置验证**: 启动时验证配置有效性
- ✅ **幂等性保证**: 相同消息重复发送结果一致
- ✅ **优雅降级**: 部分目标失败不影响其他目标

### 7.4 与现有架构一致

- ✅ **保持Intermediary Script Pattern**: 不消耗AI上下文
- ✅ **使用相同的技术栈**: Python 3.8+, uv, pytest, mypy
- ✅ **独立的模块**: 不影响现有功能
- ✅ **遵循现有代码风格**: 与项目保持一致

---

## 八、技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **语言** | Python 3.8+ | 与现有项目一致 |
| **包管理** | uv | 现代Python依赖管理器 |
| **HTTP客户端** | requests | 飞书官方推荐 |
| **配置解析** | PyYAML | 配置文件支持 |
| **日志** | logging | Python标准库 |
| **测试** | pytest | 与现有项目一致 |
| **类型检查** | mypy | 静态类型检查 |
| **代码格式** | black | 代码格式化 |
| **代码检查** | flake8 | 代码风格检查 |

---

## 九、风险和缓解措施

### 9.1 飞书API限流

**风险**: 触发QPS或QPM限制，返回HTTP 429

**缓解措施**:
- 实现指数退避重试机制
- 批量发送时的速率控制
- 监控限流响应并动态调整

### 9.2 认证复杂性

**风险**: API认证需要多步流程，容易出错

**缓解措施**:
- 提供详细文档和示例
- 支持多种认证方式（Token、Webhook）
- 自动管理Token生命周期

### 9.3 测试困难

**风险**: 测试需要Mock飞书API，可能不够真实

**缓解措施**:
- 使用高质量的Mock对象
- 提供测试工具和脚本
- 集成测试使用真实环境

### 9.4 过度设计

**风险**: 设计过于复杂，难以维护

**缓解措施**:
- 从最简单的Webhook开始
- 渐进式实现其他策略
- 定期review和简化

---

## 十、参考资料

### 官方文档

- [飞书开放平台 - 自定义机器人使用指南](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
- [飞书开放平台 - 发送消息API](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/im-v1/message/create)
- [飞书开放平台 - 飞书卡片概述](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/feishu-card-overview)
- [飞书开放平台 - 发送飞书卡片](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/send-feishu-card)
- [飞书开放平台 - 事件订阅概述](https://open.feishu.cn/document/server-docs/event-subscription-guide/overview)
- [飞书开放平台 - API频率控制](https://open.feishu.cn/document/server-docs/api-call-guide/frequency-control)

### 社区资源

- [手把手教你通过飞书Webhook打造消息推送Bot](https://open.feishu.cn/community/articles/7271149634339422210)
- [SpringBoot对接飞书事件回调](https://blog.csdn.net/rgrgrwfe/article/details/144275211)

---

## 十一、快速开始决策树

```
需要发送飞书通知
    │
    ├─ 仅群聊？
    │   └─ 是 → 群自定义机器人 Webhook（最简单）
    │
    ├─ 需要发给个人？
    │   └─ 是 → API发送消息
    │
    ├─ 需要交互（按钮、表单）？
    │   └─ 是 → 卡片消息
    │
    └─ 需要接收用户消息？
        └─ 是 → 事件订阅 + API发送
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-20
**设计者**: Claude Code (with human collaboration)
**状态**: 待实现
**相关Memory**: notification-system-design-2026-01-20
