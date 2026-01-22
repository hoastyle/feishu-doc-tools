# 飞书通知系统 - 交互功能实施路线图

**创建日期**: 2026-01-23
**版本**: v1.0
**状态**: 📋 规划中

---

## 📊 执行摘要

### 最近 3 个 Commit 分析

#### Commit 1: d600842 (2026-01-22 23:18)
**feat: add complex cards demo and advanced features documentation**

**实现内容**:
- ✅ `demo_complex_cards.py` - 5种复杂卡片演示（Dashboard、Report、Progress、Rich Format、Combined）
- ✅ `ADVANCED_FEATURES.md` - 1,866行完整高级功能文档
- ✅ 多层嵌套结构、4列指标展示、动态状态卡片

**代码量**: 2,545 行新增

#### Commit 2: cf6dc40 (2026-01-22 23:33)
**feat: implement extensible advanced features for notification cards**

**实现内容**:
- ✅ **图片元素 (img)** - 3种显示模式（crop_center、fit_center、full_strip）
- ✅ **进度条 (progress)** - 5种颜色选项，百分比显示
- ✅ **人员标签 (person)** - @mention 功能，用户ID和显示名
- ✅ **日期时间元素 (datetime_element)** - 3种模式（date、time、datetime）
- ✅ `demo_advanced_features.py` - 综合演示脚本（659行）
- ✅ CardBuilder 扩展方法：`.img()`, `.progress()`, `.datetime()`, `.person()`

**代码量**: 872 行新增

#### Commit 3: 4e910d8 (2026-01-23 00:53)
**chore: update user credentials for notification system**

**实现内容**:
- ✅ 刷新用户访问令牌（OAuth 授权）
- ✅ 添加当前用户信息（MY_NAME、MY_USER_ID）支持 @mention 功能
- ✅ `get_user_id_by_contact.py` - 通过联系方式获取用户ID工具（291行）

**代码量**: 291 行新增

### 总结
**总计新增**: 3,708 行代码 + 1,866 行文档
**核心成果**: 完整的卡片展示能力 + 基础的人员交互（@mention）

---

## ✅ 已实现功能总览

### 1. 展示类组件（完整）

#### 基础组件
- ✅ `markdown()` - Markdown 文本块
- ✅ `plain_text()` - 纯文本元素
- ✅ `text_tag()` - 彩色标签
- ✅ `header()` - 卡片头部（自动配色）
- ✅ `divider()` - 分隔线
- ✅ `note()` - 备注块

#### 布局组件
- ✅ `column()` - 单列布局
- ✅ `column_set()` - 多列容器
- ✅ `collapsible_panel()` - 可折叠面板

#### 媒体组件
- ✅ `img()` - 图片元素（3种显示模式）
- ✅ `progress()` - 进度条（5种颜色）

#### 用户组件
- ✅ `person()` - 人员标签（@mention）
- ✅ `datetime_element()` - 日期时间显示

#### 操作组件
- ✅ `action_button()` - 操作按钮（仅跳转链接）

### 2. 构建工具（完整）

- ✅ **CardBuilder** - 流式 API 构建器（478行）
  - 链式调用 API
  - 自动状态配色
  - 响应式文本配置

- ✅ **Building Blocks** - 13个可组合函数（317行）

### 3. 支持系统（完整）

- ✅ **Configuration** - 环境变量集成（275行）
- ✅ **BaseChannel** - 通道抽象层（322行）
- ✅ **Workflow Templates** - 文档模板（380行）
- ✅ **Message Grouper** - 消息分组（547行）
- ✅ **Notification Throttle** - 智能限流（649行）

---

## 🚧 待实现功能清单

### Phase 1: 交互组件基础（优先级：⭐⭐⭐）

#### 1.1 表单输入组件

| 组件 | 功能描述 | 飞书文档参考 | 优先级 |
|------|---------|-------------|--------|
| **input_text** | 文本输入框 | [文档链接](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/input-text) | ⭐⭐⭐ |
| **textarea** | 多行文本输入 | 同上 | ⭐⭐⭐ |
| **select_menu** | 下拉选择器 | [文档链接](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/select-menu) | ⭐⭐⭐ |
| **multi_select** | 多选下拉框 | 同上 | ⭐⭐ |
| **checkbox** | 复选框 | [文档链接](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/checkbox) | ⭐⭐⭐ |
| **radio** | 单选按钮 | 同上 | ⭐⭐ |
| **date_picker** | 日期选择器 | [文档链接](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/date-picker) | ⭐⭐ |
| **time_picker** | 时间选择器 | 同上 | ⭐⭐ |
| **datetime_picker** | 日期时间选择器 | [文档链接](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/datetime-picker) | ⭐⭐ |

#### 1.2 表单容器

| 组件 | 功能描述 | 优先级 |
|------|---------|--------|
| **form_container** | 表单容器，包裹多个输入组件 | ⭐⭐⭐ |
| **form_submit_button** | 表单提交按钮 | ⭐⭐⭐ |
| **form_reset_button** | 表单重置按钮 | ⭐⭐ |

**实施要点**:
```python
def form_container(
    form_id: str,
    *,
    elements: List[Block],
    submit_button: Optional[Block] = None,
    reset_button: Optional[Block] = None,
) -> Block:
    """创建表单容器

    Args:
        form_id: 表单唯一标识
        elements: 表单内的组件列表
        submit_button: 提交按钮（可选）
        reset_button: 重置按钮（可选）

    Returns:
        表单容器元素
    """
    return {
        "tag": "form",
        "form_id": form_id,
        "elements": elements,
        "submit_button": submit_button,
        "reset_button": reset_button,
    }
```

### Phase 2: 回调处理机制（优先级：⭐⭐⭐）

#### 2.1 回调处理器

**需要实现的模块**: `notifications/handlers/callback_handler.py`

**核心功能**:
```python
from typing import Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class CallbackEvent:
    """回调事件数据结构"""
    action: str  # 交互类型：callback, button_click, form_submit
    value: Dict[str, Any]  # 回传数据
    user_id: str  # 操作用户ID
    message_id: str  # 消息ID
    timestamp: int  # 时间戳

class CallbackHandler:
    """卡片交互回调处理器"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, action: str, handler: Callable):
        """注册回调处理函数

        Args:
            action: 回调动作类型
            handler: 处理函数
        """
        self._handlers[action] = handler

    def handle(self, event: CallbackEvent) -> Dict[str, Any]:
        """处理回调事件

        Args:
            event: 回调事件

        Returns:
            处理结果（用于更新卡片）
        """
        handler = self._handlers.get(event.action)
        if handler:
            return handler(event)
        return {"error": "Unknown action"}
```

#### 2.2 Webhook 服务器

**需要实现的模块**: `notifications/servers/webhook_server.py`

**功能需求**:
- ✅ 接收飞书回调请求
- ✅ 验证请求签名
- ✅ 解析回调数据
- ✅ 路由到对应的处理器
- ✅ 返回更新后的卡片

**技术栈**: FastAPI + uvicorn（已有 httpx 依赖，需添加 fastapi）

```python
from fastapi import FastAPI, Request, HTTPException
from notifications.handlers.callback_handler import CallbackHandler, CallbackEvent

app = FastAPI()
callback_handler = CallbackHandler()

@app.post("/webhook/card-callback")
async def handle_card_callback(request: Request):
    """处理飞书卡片回调"""

    # 1. 验证签名
    if not verify_signature(request):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. 解析回调数据
    data = await request.json()
    event = CallbackEvent(
        action=data["action"]["value"],
        value=data["action"]["form_values"],
        user_id=data["user_id"],
        message_id=data["message_id"],
        timestamp=data["timestamp"],
    )

    # 3. 处理回调
    result = callback_handler.handle(event)

    # 4. 返回更新后的卡片
    return {
        "card": result.get("updated_card"),
        "toast": result.get("toast_message"),
    }
```

### Phase 3: 交互式按钮增强（优先级：⭐⭐⭐）

#### 3.1 按钮交互能力扩展

**当前状态**: `action_button()` 仅支持跳转链接

**需要增强**:
```python
def action_button(
    text: str,
    *,
    type: str = "default",  # default, primary, danger
    action_type: str = "link",  # 新增: link, callback, open_url
    url: Optional[str] = None,  # 链接地址
    callback: Optional[Dict[str, Any]] = None,  # 新增: 回调配置
    confirm: Optional[Dict[str, str]] = None,  # 新增: 确认对话框
    disabled: bool = False,  # 新增: 禁用状态
) -> Block:
    """创建交互按钮

    Args:
        text: 按钮文本
        type: 按钮样式
        action_type: 交互类型（link/callback/open_url）
        url: 跳转链接（action_type=link时必需）
        callback: 回调配置 {"value": {...}, "action_id": "xxx"}
        confirm: 确认对话框配置 {"title": "确认", "text": "确定执行？"}
        disabled: 是否禁用
    """
    button = {
        "tag": "button",
        "text": {"tag": "plain_text", "content": text},
        "type": type,
    }

    if action_type == "link" and url:
        button["url"] = url
    elif action_type == "callback" and callback:
        button["behaviors"] = [{
            "type": "callback",
            "value": callback["value"],
        }]
        if "action_id" in callback:
            button["action_id"] = callback["action_id"]

    if confirm:
        button["confirm"] = {
            "title": {"tag": "plain_text", "content": confirm["title"]},
            "text": {"tag": "plain_text", "content": confirm["text"]},
        }

    if disabled:
        button["disabled"] = True

    return button
```

### Phase 4: 卡片更新机制（优先级：⭐⭐⭐）

#### 4.1 卡片更新 API

**需要实现的模块**: `lib/feishu_api_client.py` 扩展

```python
def update_message_card(
    self,
    message_id: str,
    card: Dict[str, Any],
    *,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """更新消息卡片

    Args:
        message_id: 消息ID
        card: 新的卡片内容
        token: 卡片更新token（从回调中获取）

    Returns:
        更新结果
    """
    url = f"{self.base_url}/im/v1/messages/{message_id}"

    data = {
        "content": json.dumps({"card": card}),
        "msg_type": "interactive",
    }

    if token:
        data["token"] = token

    response = self._patch(url, json=data)
    return response
```

### Phase 5: 高级交互场景（优先级：⭐⭐）

#### 5.1 审批流程场景

**功能描述**: 在卡片中完成审批操作

**实现示例**:
```python
from notifications.templates.builder import CardBuilder
from notifications.blocks.blocks import *

approval_card = (CardBuilder()
    .header("审批请求", status="warning")
    .metadata("申请人", "张三")
    .metadata("类型", "文档发布")
    .metadata("提交时间", "2026-01-23 10:00")
    .divider()
    .markdown("**文档标题**: 新功能API文档")
    .markdown("**说明**: 包含3个新增接口")
    .divider()
    # 表单容器
    .add_block(form_container(
        form_id="approval_form",
        elements=[
            # 审批结果选择
            select_menu(
                placeholder="请选择审批结果",
                options=[
                    {"value": "approve", "text": "✅ 批准"},
                    {"value": "reject", "text": "❌ 拒绝"},
                    {"value": "review", "text": "🔄 需要修改"},
                ],
                name="approval_result",
            ),
            # 审批意见
            textarea(
                placeholder="请输入审批意见（可选）",
                label="审批意见",
                name="approval_comment",
                max_length=500,
            ),
        ],
        submit_button=action_button(
            text="提交审批",
            type="primary",
            action_type="callback",
            callback={
                "value": {"action": "submit_approval"},
                "action_id": "approval_submit",
            },
            confirm={
                "title": "确认提交",
                "text": "确定提交审批结果吗？",
            },
        ),
    ))
    .build())
```

#### 5.2 数据收集场景

**功能描述**: 通过卡片收集用户反馈或信息

**实现示例**:
```python
feedback_card = (CardBuilder()
    .header("用户反馈收集", status="info")
    .markdown("请帮助我们改进产品！")
    .divider()
    .add_block(form_container(
        form_id="feedback_form",
        elements=[
            # 满意度评分
            select_menu(
                placeholder="请选择满意度",
                options=[
                    {"value": "5", "text": "⭐⭐⭐⭐⭐ 非常满意"},
                    {"value": "4", "text": "⭐⭐⭐⭐ 满意"},
                    {"value": "3", "text": "⭐⭐⭐ 一般"},
                    {"value": "2", "text": "⭐⭐ 不满意"},
                    {"value": "1", "text": "⭐ 非常不满意"},
                ],
                name="satisfaction_score",
            ),
            # 反馈类型
            checkbox(
                label="问题类型（可多选）",
                options=[
                    {"value": "bug", "text": "🐛 Bug"},
                    {"value": "feature", "text": "✨ 功能建议"},
                    {"value": "performance", "text": "⚡ 性能问题"},
                    {"value": "ux", "text": "🎨 体验问题"},
                ],
                name="feedback_type",
            ),
            # 详细描述
            textarea(
                placeholder="请详细描述您的反馈...",
                label="详细描述",
                name="feedback_detail",
                max_length=1000,
            ),
        ],
        submit_button=action_button(
            text="提交反馈",
            type="primary",
            action_type="callback",
            callback={
                "value": {"action": "submit_feedback"},
                "action_id": "feedback_submit",
            },
        ),
    ))
    .build())
```

#### 5.3 任务管理场景

**功能描述**: 任务状态更新和分配

**实现示例**:
```python
task_card = (CardBuilder()
    .header("任务更新", status="processing")
    .metadata("任务ID", "#1234")
    .metadata("创建者", "李四")
    .divider()
    .markdown("**任务**: 实现用户登录功能")
    .progress(60, color="blue")
    .divider()
    .add_block(form_container(
        form_id="task_update_form",
        elements=[
            # 状态更新
            select_menu(
                placeholder="更新状态",
                options=[
                    {"value": "todo", "text": "📋 待办"},
                    {"value": "in_progress", "text": "⚙️ 进行中"},
                    {"value": "testing", "text": "🧪 测试中"},
                    {"value": "done", "text": "✅ 已完成"},
                ],
                name="task_status",
            ),
            # 进度更新
            select_menu(
                placeholder="更新进度",
                options=[
                    {"value": "0", "text": "0%"},
                    {"value": "25", "text": "25%"},
                    {"value": "50", "text": "50%"},
                    {"value": "75", "text": "75%"},
                    {"value": "100", "text": "100%"},
                ],
                name="task_progress",
            ),
            # 备注
            input_text(
                placeholder="添加备注（可选）",
                label="备注",
                name="task_note",
            ),
        ],
        submit_button=action_button(
            text="更新任务",
            type="primary",
            action_type="callback",
            callback={
                "value": {"action": "update_task"},
                "action_id": "task_update",
            },
        ),
    ))
    .build())
```

---

## 🗺️ 实施路线图

### 阶段 1: 基础交互能力（Week 1-2）

**目标**: 实现基本的表单输入和提交功能

**任务清单**:
- [ ] 实现 `input_text` 组件
- [ ] 实现 `textarea` 组件
- [ ] 实现 `select_menu` 组件
- [ ] 实现 `checkbox` 组件
- [ ] 实现 `form_container` 组件
- [ ] 创建 `CallbackHandler` 基础框架
- [ ] 添加 CardBuilder 表单相关方法

**验收标准**:
- ✅ 能创建包含表单的卡片
- ✅ 能在演示中展示表单组件
- ✅ 文档完整覆盖所有新组件

**代码量估算**: ~800-1000 行

### 阶段 2: 回调处理系统（Week 3-4）

**目标**: 实现完整的交互回调链路

**任务清单**:
- [ ] 实现 `CallbackHandler` 完整功能
- [ ] 实现 Webhook 服务器（FastAPI）
- [ ] 添加请求签名验证
- [ ] 实现卡片更新 API
- [ ] 创建回调处理演示脚本

**验收标准**:
- ✅ 能接收并处理飞书回调
- ✅ 能根据用户交互更新卡片
- ✅ 有完整的错误处理机制
- ✅ 有端到端的集成测试

**代码量估算**: ~600-800 行

### 阶段 3: 增强型按钮（Week 5）

**目标**: 扩展按钮的交互能力

**任务清单**:
- [ ] 重构 `action_button` 支持回调
- [ ] 添加确认对话框功能
- [ ] 添加按钮禁用状态
- [ ] 更新 CardBuilder 按钮方法

**验收标准**:
- ✅ 按钮支持多种交互类型
- ✅ 有确认对话框演示
- ✅ 更新相关文档和示例

**代码量估算**: ~300-400 行

### 阶段 4: 高级交互场景（Week 6-7）

**目标**: 实现实际业务场景

**任务清单**:
- [ ] 实现审批流程场景示例
- [ ] 实现数据收集场景示例
- [ ] 实现任务管理场景示例
- [ ] 创建场景模板库
- [ ] 完善高级功能文档

**验收标准**:
- ✅ 有3个完整的实际场景示例
- ✅ 有场景使用教程
- ✅ 有最佳实践文档

**代码量估算**: ~1000-1200 行

### 阶段 5: 剩余组件补全（Week 8-9）

**目标**: 补全所有飞书支持的交互组件

**任务清单**:
- [ ] 实现 `multi_select` 组件
- [ ] 实现 `radio` 组件
- [ ] 实现 `date_picker` 组件
- [ ] 实现 `time_picker` 组件
- [ ] 实现 `datetime_picker` 组件
- [ ] 更新所有组件文档

**验收标准**:
- ✅ 覆盖飞书所有交互组件
- ✅ 每个组件有独立示例
- ✅ API 参考文档完整

**代码量估算**: ~800-1000 行

---

## 📈 技术架构更新

### 新增模块结构

```
feishu-doc-tools/
└── notifications/
    ├── blocks/
    │   ├── blocks.py (已有，需扩展)
    │   └── interactive.py (新增：交互组件)
    │
    ├── handlers/ (新增)
    │   ├── __init__.py
    │   ├── callback_handler.py (回调处理器)
    │   └── event_router.py (事件路由)
    │
    ├── servers/ (新增)
    │   ├── __init__.py
    │   ├── webhook_server.py (Webhook服务)
    │   └── middleware.py (签名验证等)
    │
    ├── scenarios/ (新增)
    │   ├── __init__.py
    │   ├── approval.py (审批场景)
    │   ├── feedback.py (反馈收集)
    │   └── task_management.py (任务管理)
    │
    └── templates/
        └── builder.py (已有，需扩展表单方法)
```

### 依赖更新需求

**新增依赖** (添加到 `pyproject.toml`):
```toml
dependencies = [
    # ... 已有依赖 ...
    "fastapi>=0.104.0",      # Webhook服务器
    "uvicorn>=0.24.0",       # ASGI服务器
    "python-multipart>=0.0.6", # 表单数据处理
]
```

---

## 💡 实施建议

### 优先级排序

**P0 (必须实现)**:
1. 基础表单组件（input_text, select_menu, form_container）
2. 回调处理系统（CallbackHandler, Webhook服务器）
3. 卡片更新API
4. 增强型按钮（支持回调）

**P1 (重要)**:
1. 审批流程场景
2. checkbox 组件
3. textarea 组件
4. 确认对话框

**P2 (可选)**:
1. 日期时间选择器
2. 多选下拉框
3. 单选按钮
4. 其他高级场景

### 技术风险

| 风险项 | 影响 | 缓解措施 |
|--------|------|---------|
| 飞书API变更 | 高 | 定期查看官方文档，版本锁定 |
| 回调签名验证复杂 | 中 | 参考官方SDK实现 |
| 表单数据验证 | 中 | 使用 pydantic 进行数据校验 |
| Webhook服务器性能 | 低 | 使用异步处理，添加限流 |

### 测试策略

1. **单元测试**: 每个新组件都需要单元测试
2. **集成测试**: Webhook 回调处理的端到端测试
3. **手动测试**: 在飞书客户端中测试实际交互
4. **性能测试**: 回调处理的响应时间 < 1s

---

## 🎯 成功指标

### 技术指标

- ✅ 代码覆盖率 > 80%
- ✅ 回调处理延迟 < 500ms
- ✅ 支持 100+ 并发回调请求
- ✅ 文档完整度 100%

### 功能指标

- ✅ 支持所有飞书交互组件（14+）
- ✅ 提供 3+ 实际场景模板
- ✅ 有完整的回调处理示例
- ✅ 兼容现有展示功能

### 用户体验指标

- ✅ 审批操作只需点击1次
- ✅ 表单提交即时反馈 < 1s
- ✅ 错误提示清晰友好
- ✅ 支持移动端交互

---

## 📚 参考资源

### 飞书官方文档

1. **卡片交互概述**: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/feishu-card-overview
2. **开发卡片交互机器人**: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/tutorial/develop-card-interaction-bot
3. **交互组件**: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components
4. **回调配置**: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-callback-communication

### 参考项目

1. **lark-webhook-notify**: 飞书webhook通知库
2. **Claude-Code-Notifier**: Claude通知系统参考

---

## 🔄 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-01-23 | 初始版本，基于最近3个commit的分析 |

---

**文档维护者**: Claude Code
**最后更新**: 2026-01-23
**状态**: 📋 规划中 → 待评审
