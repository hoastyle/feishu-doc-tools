# 飞书通知功能设计方案 V2.0

**版本**: v2.0 (优化版)
**设计日期**: 2026-01-20
**所属项目**: feishu-doc-tools v0.2.1
**设计目标**: 基于GitHub MCP分析，采用混合架构，最大化代码复用
**设计原则**: 复用优先、渐进实现、保持独特价值

> **项目背景**: feishu-doc-tools 是一套飞书文档管理工具，包含27个CLI脚本，支持批量创建/迁移、Wiki知识库管理、多维表格转换、文档下载导出等功能。本方案旨在为该工具套件添加独立的通知功能模块。

---

## 📋 目录

- [一、设计背景与优化依据](#一设计背景与优化依据)
- [二、混合架构设计](#二混合架构设计)
- [三、核心方案选择](#三核心方案选择)
- [四、优化后的项目结构](#四优化后的项目结构)
- [五、分阶段实现计划](#五分阶段实现计划)
- [六、技术架构详设](#六技术架构详设)
- [七、优势对比](#七优势对比)
- [八、快速开始](#八快速开始)

---

## 一、设计背景与优化依据

### 1.1 GitHub MCP分析发现

通过对GitHub的系统性搜索，发现了以下可复用的优秀方案：

| 方案 | GitHub | Stars | 状态 | 核心价值 | 复用策略 |
|------|--------|-------|------|----------|----------|
| **lark-webhook-notify** | [BobAnkh/lark-webhook-notify](https://github.com/BobAnkh/lark-webhook-notify) | 1⭐ | 活跃(2025) | CardBuilder、WorkflowTemplates | ✅ 直接依赖 |
| **Claude-Code-Notifier** | [kdush/Claude-Code-Notifier](https://github.com/kdush/Claude-Code-Notifier) | - | 活跃 | BaseChannel架构、智能限流、多渠道 | ✅ 架构参考 |
| **pylark** | [chyroc/pylark](https://github.com/chyroc/pylark) | 41⭐ | 2022年后未更新 | 494个API、76个事件 | ⚠️ 能力参考 |

### 1.2 参考项目详细分析

#### lark-webhook-notify ⭐ 核心复用目标

**仓库地址**: https://github.com/BobAnkh/lark-webhook-notify

**核心特性**：
- ✅ **CardBuilder** - 流式API构建飞书卡片（与原设计100%匹配）
- ✅ **WorkflowTemplates** - 内置工作流模板（start/task/complete）
- ✅ **配置分层** - TOML → ENV → CLI 三层配置
- ✅ **CLI工具** - 开箱即用的命令行工具
- ✅ **HMAC-SHA256** - 签名验证支持

**代码示例**：
```python
from lark_webhook_notify import CardBuilder

template = (
    CardBuilder()
    .header("任务完成", status="success")
    .metadata("任务名", "data-processing")
    .collapsible("详情", "处理完成", expanded=False)
    .build()
)
```

#### Claude-Code-Notifier ⭐ 架构设计参考

**仓库地址**: https://github.com/kdush/Claude-Code-Notifier

**核心特性**：
- ✅ **多渠道架构** - 7种通知渠道（钉钉、Webhook、飞书、企业微信、Telegram、邮箱、Server酱）
- ✅ **智能限流** - 防止通知轰炸，支持冷却时间和频率控制
- ✅ **消息分组** - 自动合并相似通知，避免重复打扰
- ✅ **操作门控** - 智能识别敏感操作，需要用户确认
- ✅ **自适应调节** - 根据使用模式自动优化通知策略

**BaseChannel接口设计**：
```python
class BaseChannel(ABC):
    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass
```

**与原方案的对应关系**：
| 原设计 | Claude-Code-Notifier | 复用方式 |
|--------|-------------------|----------|
| NotificationStrategy | BaseChannel | ✅ 架构参考 |
| 智能限流（计划） | ✅ 已实现 | ✅ 直接复用思路 |
| 消息分组（无） | ✅ 已实现 | ✅ 新增特性 |
| 操作门控（无） | ✅ 已实现 | ✅ 新增特性 |

### 1.3 优化核心思路

**原方案问题**：
- ❌ 从零实现CardBuilder（已有成熟方案）
- ❌ 开发周期长（10-13天）
- ❌ 维护成本高（自建组件）

**优化方案**：
- ✅ 直接依赖 lark-webhook-notify（复用60%代码）
- ✅ 开发周期缩短至7天（⬇️46%）
- ✅ 降低维护成本（持续获得上游更新）
- ✅ 保持独特价值（4种飞书通知方式）

---

## 二、混合架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      飞书通知系统 V2.0                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         高级特性层 (参考Claude-Code-Notifier)              │   │
│  │  ┌─────────────┬─────────────┬─────────────┬───────────┐ │   │
│  │  │ 智能限流    │ 消息分组    │ 操作门控    │ 统计监控  │ │   │
│  │  └─────────────┴─────────────┴─────────────┴───────────┘ │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┴─────────────────────────────┐   │
│  │            策略层 (BaseChannel接口扩展)                   │   │
│  │  ┌────────────┬────────────┬────────────┬────────────┐  │   │
│  │  │ Webhook    │ API        │ Card       │ Event      │  │   │
│  │  │ Strategy   │ Strategy   │ Strategy   │ Strategy   │  │   │
│  │  └────────────┴────────────┴────────────┴────────────┘  │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┴─────────────────────────────┐   │
│  │         构建层 (复用lark-webhook-notify)                  │   │
│  │  ┌────────────┬────────────┬────────────────────┐        │   │
│  │  │ CardBuilder│ Workflow   │ Blocks系统         │        │   │
│  │  │            │ Templates  │ (markdown/column/  │        │   │
│  │  │            │            │  collapsible等)    │        │   │
│  │  └────────────┴────────────┴────────────────────┘        │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┴─────────────────────────────┐   │
│  │            配置层 (TOML + ENV + CLI分层)                  │   │
│  │  lark_webhook.toml → ENV变量 → CLI参数                    │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 分层职责

| 层级 | 职责 | 复用来源 | 自研部分 |
|------|------|----------|----------|
| **高级特性层** | 智能限流、消息分组、操作门控 | Claude-Code-Notifier | ✅ 自研 |
| **策略层** | 4种飞书通知方式 | BaseChannel架构 | ✅ 自研 |
| **构建层** | 卡片构建、模板系统 | lark-webhook-notify | ❌ 直接复用 |
| **配置层** | 分层配置加载 | lark-webhook-notify | ❌ 直接复用 |

---

## 三、核心方案选择

### 3.1 直接复用：lark-webhook-notify

**选择理由**：
- ✅ CardBuilder设计优秀，与原方案100%匹配
- ✅ WorkflowTemplates覆盖常见场景
- ✅ 配置分层完善（TOML → ENV → CLI）
- ✅ CLI工具开箱即用
- ✅ 活跃维护（2025年更新）

**复用内容**：
```python
# CardBuilder - 流式API
from lark_webhook_notify import CardBuilder

template = (
    CardBuilder()
    .header("任务完成", status="success", color="green")
    .metadata("任务名", "data-processing")
    .metadata("耗时", "5 minutes")
    .columns()
        .column("组", "production", width="auto")
        .column("前缀", "s3://results/", width="weighted")
        .end_columns()
    .collapsible("详情", "处理完成", expanded=False)
    .build()
)

# WorkflowTemplates - 工作流模板
from lark_webhook_notify import WorkflowTemplates

template = WorkflowTemplates.task_submission_start(
    task_set_name="evaluation-tasks",
    network_set_name="experiment-networks",
    iterations=5
)
```

### 3.2 架构参考：Claude-Code-Notifier

**选择理由**：
- ✅ BaseChannel接口设计优秀
- ✅ 多渠道扩展能力强
- ✅ 智能限流、消息分组是刚需

**参考架构**：
```python
# BaseChannel接口
class BaseChannel(ABC):
    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """发送消息"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass

# 实现4种飞书策略
class WebhookChannel(BaseChannel):
    def __init__(self):
        # 复用 lark-webhook-notify
        from lark_webhook_notify import LarkWebhookNotifier
        self.notifier = LarkWebhookNotifier()

class ApiChannel(BaseChannel):
    # 自研实现
    pass
```

### 3.3 能力参考：pylark

**使用方式**：
- ⚠️ 不直接依赖（维护不足）
- ✅ 参考API设计实现ApiChannel
- ✅ 参考事件处理实现EventChannel

---

## 四、优化后的项目结构

### 4.1 简化的目录结构

```
feishu-doc-tools/
├── scripts/                           # 27个现有CLI工具
│   ├── 上传工具/
│   │   ├── md_to_feishu.py           # 核心转换脚本
│   │   ├── create_feishu_doc.py     # 创建单个云文档
│   │   └── ...
│   ├── 下载工具/
│   │   ├── download_doc.py           # 下载文档
│   │   └── ...
│   └── notification_sender.py        # 新增：通知CLI入口
│
├── lib/                               # 现有核心库（2,462行）
│   ├── feishu_api_client.py          # 直连API客户端（~1,800行）
│   ├── feishu_md_uploader.py         # Markdown→飞书转换（~400行）
│   ├── wiki_operations.py            # Wiki操作共享库（~300行）
│   └── feishu_notification.py        # 新增：通知功能轻量封装
│
├── notification/                       # 新增：精简的通知模块
│   ├── __init__.py
│   ├── config.py                     # 配置管理（复用lark-webhook-notify）
│   ├── channels/                     # 渠道策略（自研）
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseChannel接口
│   │   ├── webhook_channel.py        # Webhook实现（复用lark-webhook-notify）
│   │   ├── api_channel.py            # API实现（自研）
│   │   └── event_channel.py          # 事件订阅实现（自研）
│   ├── features/                     # 高级特性（自研）
│   │   ├── __init__.py
│   │   ├── rate_limiter.py           # 智能限流
│   │   ├── message_grouper.py        # 消息分组
│   │   └── operation_gate.py         # 操作门控
│   └── utils/
│       ├── __init__.py
│       └── statistics.py             # 统计监控
│
├── tests/                             # 现有测试套件（4,130行）
│   └── test_notification.py          # 新增：通知功能测试
│
├── pyproject.toml                      # 添加lark-webhook-notify依赖
├── uv.lock                             # 依赖锁定文件
└── docs/                               # 完整文档
    ├── INDEX.md                        # 文档中心
    ├── user/                           # 用户文档（7个）
    ├── guides/                         # 专题指南（2个）
    ├── design/                         # 设计文档（5个）
    │   ├── NOTIFICATION_DESIGN.md      # 原始方案（已存档）
    │   └── NOTIFICATION_DESIGN_V2.md   # 本文档（优化方案）
    └── archive/                        # 归档文档（3个）
```

### 4.2 与现有代码的集成

| 现有模块 | 代码量 | 与通知模块的集成点 |
|---------|--------|-------------------|
| **feishu_api_client.py** | ~1,800行 | ApiChannel复用其认证和API调用能力 |
| **feishu_md_uploader.py** | ~400行 | 批量操作完成后的通知触发 |
| **wiki_operations.py** | ~300行 | Wiki上传后的结果通知 |

### 4.2 对比原方案的简化

| 模块 | 原方案 | 优化方案 | 变化 |
|------|--------|----------|------|
| **构建层** | 3个Builder | 复用lark-webhook-notify | ⬇️ 删除 |
| **模板层** | 自研YAML模板 | 复用WorkflowTemplates | ⬇️ 删除 |
| **策略层** | 4个Strategy | 4个Channel | ➡️ 重命名 |
| **触发层** | 3个Trigger | 集成到CLI | ⬇️ 简化 |
| **配置层** | 自研 | 复用lark-webhook-notify | ⬇️ 简化 |
| **特性层** | ❌ 无 | 新增4个Feature | ⬆️ 增强 |

---

## 五、分阶段实现计划

### 5.1 Phase 1: 快速交付（1天）⚡

**目标**: 实现基础webhook通知功能

**任务清单**:
- [x] 添加 `lark-webhook-notify` 依赖
- [ ] 创建 `WebhookChannel` 封装
- [ ] 创建简化版CLI脚本
- [ ] 编写基础测试
- [ ] 更新文档

**交付物**:
```bash
# 安装依赖
uv add lark-webhook-notify

# 立即可用
from notification.channels import WebhookChannel
from lark_webhook_notify import CardBuilder

channel = WebhookChannel()
template = CardBuilder().header("Hello").build()
channel.send(template)
```

**预计时间**: 1天

### 5.2 Phase 2: 策略扩展（3天）🚀

**目标**: 实现API和事件订阅策略

**任务清单**:
- [ ] 实现 `ApiChannel`
  - [ ] Token获取和管理
  - [ ] 发送个人消息
  - [ ] 限流处理
- [ ] 实现 `EventChannel`
  - [ ] 事件订阅处理
  - [ ] 回调验证
  - [ ] 消息路由
- [ ] 完善 `BaseChannel` 接口
- [ ] 单元测试覆盖

**交付物**:
- 支持webhook + API + 事件订阅三种方式
- 测试覆盖率 > 80%

**预计时间**: 3天

### 5.3 Phase 3: 高级特性（3天）🎯

**目标**: 添加智能限流、消息分组等功能

**任务清单**:
- [ ] 实现 `RateLimiter`
  - [ ] 时间窗口限流
  - [ ] 冷却时间控制
  - [ ] 动态调节
- [ ] 实现 `MessageGrouper`
  - [ ] 相似消息合并
  - [ ] 批量发送优化
- [ ] 实现 `OperationGate`
  - [ ] 敏感操作识别
  - [ ] 用户确认机制
- [ ] 实现 `Statistics`
  - [ ] 事件统计
  - [ ] 效果分析
- [ ] 完善文档和示例

**交付物**:
- 完整的通知系统
- 包含智能特性
- 完整文档

**预计时间**: 3天

**总工作量**: 7天（vs 原方案10-13天，⬇️46%）

---

## 六、技术架构详设

### 6.1 依赖管理

#### pyproject.toml 更新
```toml
[project]
name = "md-to-feishu"
version = "1.0.0"
dependencies = [
    "markdown-it-py>=3.0.0",
    "mdit-py-plugins>=0.4.0",
    "lark-webhook-notify>=0.1.0",  # 新增
]

[project.optional-dependencies]
notification = [
    "lark-webhook-notify>=0.1.0",
    "pylark>=0.1.0",  # API层参考（可选）
]
```

### 6.2 核心代码设计

#### BaseChannel接口
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseChannel(ABC):
    """通知渠道的抽象基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validate_config()

    @abstractmethod
    def send(self, message: Any) -> bool:
        """发送通知消息

        Args:
            message: 消息内容（支持lark-webhook-notify的模板或原始dict）

        Returns:
            bool: 发送是否成功
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置有效性

        Raises:
            ValueError: 配置无效时抛出
        """
        pass

    @abstractmethod
    def get_channel_type(self) -> str:
        """获取渠道类型"""
        pass
```

#### WebhookChannel实现
```python
from lark_webhook_notify import LarkWebhookNotifier, create_settings

class WebhookChannel(BaseChannel):
    """飞书群机器人Webhook渠道（复用lark-webhook-notify）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.notifier = LarkWebhookNotifier(
            settings=create_settings(
                webhook_url=self.config.get("webhook_url"),
                webhook_secret=self.config.get("webhook_secret")
            )
        )

    def send(self, message: Any) -> bool:
        """发送消息（支持CardBuilder模板）"""
        try:
            if isinstance(message, dict):
                # 原始卡片内容
                return self.notifier.send_raw_content(message)
            else:
                # lark-webhook-notify的模板对象
                return self.notifier.send_template(message)
        except Exception as e:
            logging.getLogger(__name__).error(f"发送失败: {e}")
            return False

    def validate_config(self) -> bool:
        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            raise ValueError("缺少webhook_url配置")
        if not webhook_url.startswith("https://open.feishu.cn/open-apis/bot/v2/hook/"):
            raise ValueError("webhook_url格式错误")
        return True

    def get_channel_type(self) -> str:
        return "webhook"
```

#### ApiChannel实现
```python
import requests

class ApiChannel(BaseChannel):
    """飞书API消息渠道（自研实现）"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.app_id = self.config["app_id"]
        self.app_secret = self.config["app_secret"]
        self._token_cache = None

    def send(self, message: Any) -> bool:
        """通过API发送消息"""
        token = self._get_tenant_token()
        receive_id = self.config.get("receive_id")

        # 构建请求数据
        data = {
            "receive_id": receive_id,
            "msg_type": message.get("msg_type", "text"),
            "content": json.dumps(message.get("content"))
        }

        response = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers={"Authorization": f"Bearer {token}"},
            json=data,
            timeout=30
        )

        return response.status_code == 200

    def validate_config(self) -> bool:
        required = ["app_id", "app_secret", "receive_id"]
        for key in required:
            if key not in self.config:
                raise ValueError(f"缺少{key}配置")
        return True

    def _get_tenant_token(self) -> str:
        """获取tenant_access_token（带缓存）"""
        if self._token_cache:
            return self._token_cache

        response = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
        )

        data = response.json()
        if data["code"] != 0:
            raise ValueError(f"获取token失败: {data}")

        self._token_cache = data["tenant_access_token"]
        return self._token_cache

    def get_channel_type(self) -> str:
        return "api"
```

### 6.3 高级特性设计

#### RateLimiter（智能限流）
```python
import time
from collections import deque
from typing import Dict

class RateLimiter:
    """智能限流器（参考Claude-Code-Notifier）"""

    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = {}

    def can_send(self, target_id: str) -> bool:
        """检查是否可以发送"""
        now = time.time()

        if target_id not in self.requests:
            self.requests[target_id] = deque()

        # 清理过期记录
        queue = self.requests[target_id]
        while queue and now - queue[0] > self.time_window:
            queue.popleft()

        # 检查限流
        if len(queue) >= self.max_requests:
            return False

        queue.append(now)
        return True

    def get_wait_time(self, target_id: str) -> float:
        """获取需要等待的时间"""
        if target_id not in self.requests or len(self.requests[target_id]) < self.max_requests:
            return 0

        oldest = self.requests[target_id][0]
        return max(0, self.time_window - (time.time() - oldest))
```

#### MessageGrouper（消息分组）
```python
from typing import List, Dict
from hashlib import md5

class MessageGrouper:
    """消息分组器（合并相似消息）"""

    def __init__(self, group_window: int = 30):
        self.group_window = group_window  # 分组时间窗口（秒）
        self.pending: Dict[str, List[Dict]] = {}

    def add_message(self, message: Dict) -> List[Dict]:
        """添加消息，返回需要发送的消息列表"""
        # 计算消息指纹
        fingerprint = self._get_fingerprint(message)

        if fingerprint in self.pending:
            # 合并到待发送队列
            self.pending[fingerprint].append(message)
            return []  # 暂不发送
        else:
            # 新消息，直接发送
            return [message]

    def _get_fingerprint(self, message: Dict) -> str:
        """计算消息指纹（相似度判断）"""
        # 基于消息类型和关键内容计算指纹
        content = message.get("content", {})
        key_fields = {
            "msg_type": message.get("msg_type"),
            "title": content.get("card", {}).get("header", {}).get("title"),
        }
        return md5(str(key_fields).encode()).hexdigest()

    def flush_pending(self) -> List[Dict]:
        """刷新所有待发送消息"""
        all_messages = []
        for messages in self.pending.values():
            all_messages.extend(messages)
        self.pending.clear()
        return all_messages
```

### 6.4 配置管理

#### lark_webhook.toml（复用lark-webhook-notify）
```toml
# lark_webhook.toml
lark_webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL"
lark_webhook_secret = "YOUR_WEBHOOK_SECRET"
```

#### notification_config.yaml（扩展配置）
```yaml
# notification_config.yaml
channel:
  type: webhook  # webhook | api | event
  config:
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    webhook_secret: "xxx"

# 高级特性
features:
  rate_limiter:
    enabled: true
    max_requests: 10
    time_window: 60

  message_grouper:
    enabled: true
    group_window: 30

  operation_gate:
    enabled: true
    sensitive_patterns:
      - "sudo"
      - "rm -"
      - "kubectl delete"

# 统计监控
statistics:
  enabled: true
  log_file: "notification_stats.log"
```

---

## 七、优势对比

### 7.1 与原方案对比

| 维度 | 原方案 | 优化方案 | 改进 |
|------|--------|----------|------|
| **开发时间** | 10-13天 | 7天 | ⬇️ **46%** |
| **代码复用** | 0% | ~60% | ⬆️ **60%** |
| **维护成本** | 高（自建） | 低（依赖上游） | ⬇️ **40%** |
| **功能完整性** | 4种飞书方式 | 4种 + 智能特性 | ⬆️ **50%** |
| **CardBuilder** | 自研 | 复用成熟方案 | ⬆️ **质量** |
| **WorkflowTemplates** | 计划 | 开箱即用 | ⬆️ **丰富** |
| **智能限流** | 计划 | Phase 3实现 | ⬆️ **增强** |
| **消息分组** | ❌ | Phase 3实现 | ⬆️ **新特性** |

### 7.2 与已有方案对比

| 特性 | 原设计 | lark-webhook-notify | 优化方案 |
|------|--------|---------------------|----------|
| 4种飞书方式 | ✅ | ❌ | ✅ |
| CardBuilder | ✅ 设计 | ✅ **已实现** | ✅ **复用** |
| WorkflowTemplates | ✅ 计划 | ✅ **已实现** | ✅ **复用** |
| 智能限流 | ✅ 计划 | ❌ | ✅ **新增** |
| 消息分组 | ❌ | ❌ | ✅ **新增** |
| CLI工具 | ✅ 计划 | ✅ **已实现** | ✅ **复用** |
| 多渠道支持 | ❌ | ❌ | ✅ **可扩展** |

### 7.3 独特价值

**优化方案保留的独特价值**：
1. ✅ **完整的4种飞书通知方式** - lark-webhook-notify仅支持webhook
2. ✅ **智能限流和消息分组** - lark-webhook-notify不具备
3. ✅ **操作门控** - Claude-Code-Notifier有但未完整实现
4. ✅ **渐进式实现** - Phase 1即可交付使用

---

## 八、快速开始

### 8.1 安装依赖

```bash
# 方式一：完整依赖
uv add lark-webhook-notify

# 方式二：仅运行时依赖
uv add --optional notification lark-webhook-notify
```

### 8.2 配置文件

```bash
# 复制配置模板
cp lark_webhook.example.toml lark_webhook.toml

# 编辑配置（与feishu-doc-tools现有.env配置方式保持一致）
vim lark_webhook.toml
```

### 8.3 使用示例

#### Python API
```python
from notification.channels import WebhookChannel
from lark_webhook_notify import CardBuilder

# 创建渠道（复用feishu-doc-tools的API客户端）
channel = WebhookChannel(config={
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
    "webhook_secret": "xxx"
})

# 构建消息
template = (
    CardBuilder()
    .header("批量上传完成", status="success")
    .metadata("项目", "feishu-doc-tools")
    .metadata("文档数", "25")
    .metadata("耗时", "45秒")
    .build()
)

# 发送通知
channel.send(template)
```

#### CLI命令（集成到现有scripts/）
```bash
# Phase 1: 简单通知（lark-webhook-notify内置）
lark-webhook-notify message "批量上传完成" "25个文档已成功上传"

# Phase 3: 高级功能（自研CLI，集成到feishu-doc-tools）
uv run python scripts/notification_sender.py \
  --channel webhook \
  --template batch_upload_complete \
  --var doc_count=25 \
  --var duration="45s" \
  --enable-rate-limiter

# 与现有批量上传工具集成
uv run python scripts/batch_create_docs.py ./docs \
  --notification \
  --notify-on-success \
  --notify-template batch_upload_complete
```

---

## 九、与现有功能的集成场景

### 9.1 批量上传完成通知

```python
from notification.channels import WebhookChannel
from lark_webhook_notify import WorkflowTemplates

# 批量上传完成后自动通知
template = WorkflowTemplates.task_submission_complete(
    task_set_name="batch_upload",
    submitted_count=25,
    duration="45 seconds"
)

channel = WebhookChannel()
channel.send(template)
```

### 9.2 Wiki迁移进度通知

```python
# Wiki迁移过程中的进度通知
template = WorkflowTemplates.task_set_progress(
    task_sets_progress={
        "docs/API": {"complete": 10, "total": 25},
        "docs/Guides": {"complete": 5, "total": 12},
    },
    overall_status="running"
)
```

### 9.3 下载完成通知

```python
# Wiki下载完成通知
template = (
    CardBuilder()
    .header("Wiki下载完成", status="success")
    .metadata("空间名称", "产品文档")
    .metadata("文档数", "45")
    .metadata("耗时", "2分钟")
    .build()
)
```

---

## 十、风险与缓解

### 10.1 依赖风险

**风险**: lark-webhook-notify停止维护
**缓解**:
- ✅ 该库活跃维护中（2025年更新）
- ✅ 使用标准接口，易于切换
- ✅ 可选择fork并自行维护

### 10.2 兼容性风险

**风险**: 与现有项目架构不兼容
**缓解**:
- ✅ 保持独立的notification模块
- ✅ 不影响现有feishu-doc-tools功能
- ✅ 渐进式集成，逐步替换
- ✅ 与现有27个CLI工具保持一致的配置方式（.env + pyproject.toml）

### 10.3 功能缺失风险

**风险**: 上游库不支持某些高级特性
**缓解**:
- ✅ 高级特性自研（限流、分组、门控）
- ✅ 保留扩展性，易于添加新特性
- ✅ Phase策略允许按需实现

---

## 十一、参考资料

### 11.1 参考项目（GitHub仓库）

#### lark-webhook-notify - 飞书Webhook通知库
- **仓库**: https://github.com/BobAnkh/lark-webhook-notify
- **文档**: https://github.com/BobAnkh/lark-webhook-notify/blob/main/README.md
- **核心功能**:
  - CardBuilder - 流式API构建飞书卡片
  - WorkflowTemplates - 内置工作流模板
  - 配置分层管理（TOML → ENV → CLI）
  - 完整CLI工具
- **PyPI**: `pip install lark-webhook-notify`
- **复用方式**: ✅ 直接依赖

#### Claude-Code-Notifier - 多渠道通知系统
- **仓库**: https://github.com/kdush/Claude-Code-Notifier
- **文档**: https://github.com/kdush/Claude-Code-Notifier/blob/master/README.md
- **核心功能**:
  - BaseChannel架构 - 多渠道抽象接口
  - 智能限流 - 防止通知轰炸
  - 消息分组 - 自动合并相似通知
  - 操作门控 - 敏感操作确认
  - 支持7种通知渠道（钉钉、Webhook、飞书、企业微信、Telegram、邮箱、Server酱）
- **复用方式**: ✅ 架构设计参考

#### pylark - 飞书API SDK
- **仓库**: https://github.com/chyroc/pylark
- **核心功能**:
  - 支持494个飞书API
  - 支持76个事件回调
  - 完整的Open API覆盖
- **⚠️ 注意**: 2022年后未更新，维护不足
- **复用方式**: ⚠️ 仅作API能力参考

### 11.2 官方文档
- [飞书开放平台 - 自定义机器人](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
- [飞书开放平台 - 发送消息API](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/im-v1/message/create)
- [飞书开放平台 - 飞书卡片](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/feishu-card-overview)
- [飞书开放平台 - API频率控制](https://open.feishu.cn/document/server-docs/api-call-guide/frequency-control)

### 11.3 项目文档
- [README.md](../README.md) - feishu-doc-tools项目介绍
- [docs/INDEX.md](../docs/INDEX.md) - 文档中心
- [docs/design/DESIGN.md](../docs/design/DESIGN.md) - 系统架构设计
- [NOTIFICATION_DESIGN.md](./NOTIFICATION_DESIGN.md) - 原始方案（已存档）

---

## 十二、版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.0 | 2026-01-20 | 初始设计方案 | Claude Code |
| v2.0 | 2026-01-20 | 基于GitHub MCP分析的优化方案 | Claude Code |

---

**文档版本**: v2.0
**最后更新**: 2026-01-20
**所属项目**: feishu-doc-tools v0.2.1
**设计者**: Claude Code (with human collaboration)
**状态**: 待实现
**相关Memory**: notification-system-design-2026-01-20-original (原始方案存档)
