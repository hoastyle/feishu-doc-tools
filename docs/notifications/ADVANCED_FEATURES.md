# 飞书通知系统 - 高级功能参考

**版本**: v1.0
**创建日期**: $(date +%Y-%m-%d)
**所属项目**: feishu-doc-tools
**适用范围**: 飞书卡片通知、消息交互、高级组件

---

## 📋 目录

- [一、当前支持的复杂功能组合](#一当前支持的复杂功能组合)
- [二、可扩展的高级功能](#二可扩展的高级功能)
- [三、Feishu API 参考](#三feishu-api-参考)
- [四、实现指南](#四实现指南)
- [五、最佳实践](#五最佳实践)

---

## 一、当前支持的复杂功能组合

### 1.1 多列布局 + 可折叠面板组合

**使用场景**: 批量上传结果展示，包含成功/失败统计和详细日志

**JSON 结构**:
```json
{
  "header": {
    "title": {
      "tag": "plain_text",
      "content": "批量上传完成"
    },
    "template": "green",
    "text_tag_list": [
      {
        "tag": "text_tag",
        "text": {
          "tag": "plain_text",
          "content": "success"
        },
        "color": "green"
      }
    ]
  },
  "elements": [
    {
      "tag": "column_set",
      "columns": [
        {
          "tag": "column",
          "width": "auto",
          "elements": [
            {
              "tag": "markdown",
              "content": "**总数**: 156 个"
            }
          ]
        },
        {
          "tag": "column",
          "width": "auto",
          "elements": [
            {
              "tag": "markdown",
              "content": "**成功**: 155 个"
            }
          ]
        },
        {
          "tag": "column",
          "width": "auto",
          "elements": [
            {
              "tag": "markdown",
              "content": "**失败**: 1 个"
            }
          ]
        }
      ]
    },
    {
      "tag": "hr",
      "margin": "0px 0px 0px 0px"
    },
    {
      "tag": "collapsible_panel",
      "header": {
        "title": {
          "tag": "markdown",
          "content": "**失败文件**",
          "margin": "0px"
        }
      },
      "elements": [
        {
          "tag": "markdown",
          "content": "```\n1. large_file.dat (超过 100MB 限制)\n   错误: File size exceeds limit\n```"
        }
      ],
      "expanded": false
    },
    {
      "tag": "collapsible_panel",
      "header": {
        "title": {
          "tag": "markdown",
          "content": "**上传日志**",
          "margin": "0px"
        }
      },
      "elements": [
        {
          "tag": "markdown",
          "content": "```json\n{\n  \"start_time\": \"10:00:00\",\n  \"end_time\": \"10:03:15\",\n  \"duration\": \"195s\"\n}\n```"
        }
      ],
      "expanded": false
    }
  ],
  "config": {
    "update_multi": true,
    "style": {
      "text_size": {
        "normal_v2": {
          "default": "normal",
          "pc": "normal",
          "mobile": "heading"
        }
      }
    }
  }
}
```

**CardBuilder 实现**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("批量上传完成", status="success", color="green")
    .columns()
        .column("总数", "156 个", width="auto")
        .column("成功", "155 个", width="auto")
        .column("失败", "1 个", width="auto")
    .end_columns()
    .divider()
    .collapsible("失败文件",
               "```\n1. large_file.dat (超过 100MB 限制)\n"
               "   错误: File size exceeds limit\n"
               "```")
    .divider()
    .collapsible("上传日志",
               "```json\n"
               "{\n"
               "  \"start_time\": \"10:00:00\",\n"
               "  \"end_time\": \"10:03:15\",\n"
               "  \"duration\": \"195s\"\n"
               "}\n"
               "```")
    .build())
```

### 1.2 嵌套列 + 权重宽度

**使用场景**: 复杂数据展示，如任务进度报告

**JSON 结构**:
```json
{
  "header": {
    "title": {"tag": "plain_text", "content": "任务进度报告"},
    "template": "blue"
  },
  "elements": [
    {
      "tag": "column_set",
      "columns": [
        {
          "tag": "column",
          "width": "weighted",
          "weight": 2,
          "elements": [
            {"tag": "markdown", "content": "**任务名称**: 数据同步"}
          ]
        },
        {
          "tag": "column",
          "width": "weighted",
          "weight": 1,
          "elements": [
            {"tag": "markdown", "content": "**进度**: 75%"}
          ]
        },
        {
          "tag": "column",
          "width": "weighted",
          "weight": 1,
          "elements": [
            {"tag": "markdown", "content": "**状态**: 进行中"}
          ]
        }
      ]
    },
    {
      "tag": "hr"
    },
    {
      "tag": "column_set",
      "columns": [
        {
          "tag": "column",
          "width": "weighted",
          "weight": 1,
          "elements": [
            {"tag": "markdown", "content": "**开始时间**: 10:00"}
          ]
        },
        {
          "tag": "column",
          "width": "weighted",
          "weight": 1,
          "elements": [
            {"tag": "markdown", "content": "**耗时**: 2分30秒"}
          ]
        },
        {
          "tag": "column",
          "width": "weighted",
          "weight": 1,
          "elements": [
            {"tag": "markdown", "content": "**预计完成**: 10:05"}
          ]
        }
      ]
    }
  ]
}
```

**CardBuilder 实现**:
```python
card = (CardBuilder()
    .header("任务进度报告", status="info")
    .columns()
        .column("任务名称", "数据同步", width="weighted", weight=2)
        .column("进度", "75%", width="weighted", weight=1)
        .column("状态", "进行中", width="weighted", weight=1)
    .end_columns()
    .divider()
    .columns()
        .column("开始时间", "10:00", width="weighted", weight=1)
        .column("耗时", "2分30秒", width="weighted", weight=1)
        .column("预计完成", "10:05", width="weighted", weight=1)
    .end_columns()
    .build())
```

### 1.3 Note 提示框 + 分隔线组合

**使用场景**: 错误报告和系统诊断

**JSON 结构**:
```json
{
  "header": {
    "title": {"tag": "plain_text", "content": "系统诊断"},
    "template": "wathet",
    "text_tag_list": [
      {
        "tag": "text_tag",
        "text": {"tag": "plain_text", "content": "info"},
        "color": "blue"
      }
    ]
  },
  "elements": [
    {
      "tag": "markdown",
      "content": "系统运行正常，以下是详细信息"
    },
    {
      "tag": "hr"
    },
    {
      "tag": "collapsible_panel",
      "header": {
        "title": {
          "tag": "markdown",
          "content": "**环境信息**"
        }
      },
      "elements": [
        {
          "tag": "markdown",
          "content": "- **系统**: Linux 5.15\n- **Python**: 3.8.1\n- **内存**: 2.3GB / 8GB"
        }
      ],
      "expanded": false
    },
    {
      "tag": "hr"
    },
    {
      "tag": "note",
      "elements": [
        {
          "tag": "markdown",
          "content": "所有系统指标正常，无需采取行动"
        }
      ]
    }
  ]
}
```

**CardBuilder 实现**:
```python
card = (CardBuilder()
    .header("系统诊断", status="info", color="wathet")
    .markdown("系统运行正常，以下是详细信息")
    .divider()
    .collapsible("环境信息",
               "- **系统**: Linux 5.15\n"
               "- **Python**: 3.8.1\n"
               "- **内存**: 2.3GB / 8GB")
    .divider()
    .note("所有系统指标正常，无需采取行动")
    .build())
```

### 1.4 混合布局 (auto + weighted)

**使用场景**: 复杂的任务报告，标签使用固定宽度，内容使用权重

**JSON 结构**:
```json
{
  "header": {
    "title": {"tag": "plain_text", "content": "混合布局示例"},
    "template": "orange"
  },
  "elements": [
    {
      "tag": "column_set",
      "columns": [
        {
          "tag": "column",
          "width": "auto",
          "elements": [
            {"tag": "markdown", "content": "**标签**: 重要"}
          ]
        },
        {
          "tag": "column",
          "width": "weighted",
          "weight": 3,
          "elements": [
            {"tag": "markdown", "content": "**任务名称**: 完成API接口开发"}
          ]
        },
        {
          "tag": "column",
          "width": "auto",
          "elements": [
            {"tag": "markdown", "content": "**优先级**: 高"}
          ]
        }
      ]
    }
  ]
}
```

**CardBuilder 实现**:
```python
card = (CardBuilder()
    .header("混合布局示例", status="warning", color="orange")
    .columns()
        .column("标签", "重要", width="auto")
        .column("任务名称", "完成API接口开发", width="weighted", weight=3)
        .column("优先级", "高", width="auto")
    .end_columns()
    .build())
```

---

## 二、可扩展的高级功能

### 2.1 图片元素 (img tag)

**功能描述**: 在卡片中嵌入图片，支持本地图片和网络图片

**JSON 结构**:
```json
{
  "tag": "img",
  "img_key": "img_v2_04b2e9fc-8cd9-4d0e-b7a7-5e7d12345678",
  "alt": {
    "tag": "plain_text",
    "content": "图片描述"
  },
  "title": {
    "tag": "plain_text",
    "content": "图片标题（可选）"
  },
  "preview": true,
  "mode": "fit_horizontal"
}
```

**参数说明**:
- `img_key`: 图片的唯一标识（通过上传 API 获取）
- `alt`: 图片的替代文本（必填）
- `title`: 图片标题（可选）
- `preview`: 是否支持点击预览（默认 true）
- `mode`: 图片显示模式
  - `fit_horizontal`: 水平适应
  - `crop_center`: 居中裁剪
  - `full`: 完整显示

**使用示例**:
```python
from notifications.blocks.blocks import Block

def image_element(
    img_key: str,
    alt_text: str,
    *,
    title: Optional[str] = None,
    preview: bool = True,
    mode: str = "fit_horizontal",
) -> Block:
    """创建图片元素

    Args:
        img_key: 图片唯一标识（通过上传API获取）
        alt_text: 图片替代文本
        title: 图片标题（可选）
        preview: 是否允许预览
        mode: 显示模式

    Returns:
        图片元素字典
    """
    img: Block = {
        "tag": "img",
        "img_key": img_key,
        "alt": {"tag": "plain_text", "content": alt_text},
        "preview": preview,
        "mode": mode,
    }
    if title:
        img["title"] = {"tag": "plain_text", "content": title}
    return img
```

**集成到 CardBuilder**:
```python
from notifications.templates.builder import CardBuilder

# 方法扩展
class CardBuilder:
    def image(self, img_key: str, alt: str, **kwargs) -> CardBuilder:
        """添加图片元素"""
        self._elements.append(image_element(img_key, alt, **kwargs))
        return self

# 使用示例
card = (CardBuilder()
    .header("文档预览", status="info")
    .image(
        img_key="img_v2_04b2e9fc-8cd9-4d0e-b7a7-5e7d12345678",
        alt_text="文档预览图",
        title="API 架构图",
        mode="fit_horizontal"
    )
    .markdown("**文档**: API Reference Guide")
    .build())
```

**Feishu API 参考**:
- 图片上传: `POST https://open.feishu.cn/open-apis/im/v1/images`
- 文档: [图片元素](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)

### 2.2 进度条 (progress)

**功能描述**: 显示操作进度，适用于长时间运行的任务

**JSON 结构**:
```json
{
  "tag": "progress",
  "value": "75%",
  "status": "running",
  "color": "blue"
}
```

**参数说明**:
- `value`: 进度值（格式：数字 + %，如 "75%"）
- `status`: 进度状态
  - `running`: 运行中
  - `success`: 成功
  - `error`: 错误
  - `warning`: 警告
- `color`: 进度条颜色（当 status 为 running 时有效）

**使用示例**:
```python
def progress_bar(
    value: str,
    *,
    status: str = "running",
    color: str = "blue",
) -> Block:
    """创建进度条元素

    Args:
        value: 进度值 (格式: "75%")
        status: 进度状态 (running/success/error/warning)
        color: 进度条颜色

    Returns:
        进度条元素字典
    """
    return {
        "tag": "progress",
        "value": value,
        "status": status,
        "color": color,
    }

# 使用示例
progress = progress_bar("75%", status="running", color="blue")
```

**完整卡片示例**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("文件同步中", status="running", color="wathet")
    .markdown("**任务**: 同步文档到云端")
    .markdown("**文件数**: 150/200")
    .add_block(progress_bar("75%", status="running", color="blue"))
    .markdown("**预计剩余时间**: 2 分钟")
    .build())
```

**Feishu API 参考**:
- 文档: [进度条元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/content-components/progress)

### 2.3 人员标签 (@mention)

**功能描述**: 在消息中 @ 提及用户，支持通知和链接跳转

**JSON 结构**:
```json
{
  "tag": "mention",
  "user_id": "ou_1234567890abcdef",
  "name": "张三",
  "tenant_key": "cli_1234567890"
}
```

**参数说明**:
- `user_id`: 用户的 Open ID（必填）
- `name`: 显示的用户名（必填）
- `tenant_key`: 租户 key（多租户应用时需要）

**使用示例**:
```python
def mention_user(
    user_id: str,
    name: str,
    *,
    tenant_key: Optional[str] = None,
) -> Block:
    """创建 @提及 元素

    Args:
        user_id: 用户 Open ID
        name: 显示的用户名
        tenant_key: 租户 key（可选）

    Returns:
        提及元素字典
    """
    mention: Block = {
        "tag": "mention",
        "user_id": user_id,
        "name": name,
    }
    if tenant_key:
        mention["tenant_key"] = tenant_key
    return mention

# 使用示例
mention = mention_user(
    user_id="ou_1234567890abcdef",
    name="张三"
)
```

**在 Markdown 中使用**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("代码审查请求", status="info")
    .markdown("**PR**: #123 - 添加用户认证功能")
    .markdown("**审查者**: @张三 请帮忙审查")
    # 注意：实际使用需要在 markdown 内容中嵌入 mention 对象
    .build())
```

**高级用法 - 组合 Markdown 和 Mention**:
```python
def markdown_with_mentions(content: str, mentions: List[Block]) -> Block:
    """创建包含 @提及 的 Markdown 内容

    Args:
        content: Markdown 内容
        mentions: 提及的用户列表

    Returns:
        Markdown 元素字典（包含提及）
    """
    # Feishu 的 markdown 提及格式
    # 需要在内容中使用特殊语法，并在 elements 数组中包含 mention 对象
    return {
        "tag": "lark_md",
        "content": content,
        "elements": mentions,
    }
```

**Feishu API 参考**:
- 用户信息: `GET https://open.feishu.cn/open-apis/contact/v3/users/{user_id}`
- 文档: [Mention 元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/content-components/mention)

### 2.4 日期时间元素 (date_picker)

**功能描述**: 在卡片中显示日期时间选择器或日期时间展示

**JSON 结构 (展示模式)**:
```json
{
  "tag": "datepicker",
  "value": "2026-01-20",
  "mode": "date"
}
```

**参数说明**:
- `value`: 日期时间值
  - 日期模式: `YYYY-MM-DD`
  - 时间模式: `HH:mm`
  - 日期时间模式: `YYYY-MM-DD HH:mm`
- `mode`: 显示模式
  - `date`: 仅日期
  - `time`: 仅时间
  - `datetime`: 日期和时间

**使用示例**:
```python
def date_picker(
    value: str,
    *,
    mode: str = "date",
) -> Block:
    """创建日期时间元素

    Args:
        value: 日期时间值
        mode: 显示模式 (date/time/datetime)

    Returns:
        日期时间元素字典
    """
    return {
        "tag": "datepicker",
        "value": value,
        "mode": mode,
    }

# 使用示例
date = date_picker("2026-01-20", mode="date")
datetime = date_picker("2026-01-20 14:30", mode="datetime")
```

**完整卡片示例**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("会议提醒", status="info")
    .markdown("**会议**: 产品需求评审")
    .markdown("**参与者**: @张三 @李四")
    .add_block(date_picker("2026-01-20 14:30", mode="datetime"))
    .markdown("**地点**: 3 号会议室")
    .build())
```

**Feishu API 参考**:
- 文档: [DatePicker 元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/date-time-picker)

### 2.5 交互式元素 (select_menu)

**功能描述**: 下拉选择菜单，用于收集用户输入（需要配置交互回调）

**JSON 结构**:
```json
{
  "tag": "select_menu",
  "placeholder": {
    "tag": "plain_text",
    "content": "请选择优先级"
  },
  "options": [
    {
      "value": "high",
      "text": {
        "tag": "plain_text",
        "content": "高优先级"
      }
    },
    {
      "value": "medium",
      "text": {
        "tag": "plain_text",
        "content": "中优先级"
      }
    },
    {
      "value": "low",
      "text": {
        "tag": "plain_text",
        "content": "低优先级"
      }
    }
  ],
  "initial_option": {
    "value": "medium",
    "text": {
      "tag": "plain_text",
      "content": "中优先级"
    }
  }
}
```

**参数说明**:
- `placeholder`: 占位提示文本
- `options`: 选项列表
  - `value`: 选项值
  - `text`: 显示文本
- `initial_option`: 初始选中的选项（可选）

**使用示例**:
```python
def select_menu(
    placeholder: str,
    options: List[Dict[str, str]],
    *,
    initial_option: Optional[Dict[str, str]] = None,
) -> Block:
    """创建下拉选择菜单

    Args:
        placeholder: 占位提示
        options: 选项列表
        initial_option: 初始选项（可选）

    Returns:
        下拉菜单元素字典
    """
    menu: Block = {
        "tag": "select_menu",
        "placeholder": {"tag": "plain_text", "content": placeholder},
        "options": [
            {
                "value": opt["value"],
                "text": {"tag": "plain_text", "content": opt["text"]}
            }
            for opt in options
        ],
    }
    if initial_option:
        menu["initial_option"] = {
            "value": initial_option["value"],
            "text": {"tag": "plain_text", "content": initial_option["text"]}
        }
    return menu

# 使用示例
priority_menu = select_menu(
    placeholder="请选择优先级",
    options=[
        {"value": "high", "text": "高优先级"},
        {"value": "medium", "text": "中优先级"},
        {"value": "low", "text": "低优先级"},
    ],
    initial_option={"value": "medium", "text": "中优先级"}
)
```

**完整卡片示例 - 审批流程**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("审批请求", status="warning")
    .metadata("申请人", "张三")
    .metadata("类型", "文档发布")
    .markdown("**文档**: 新功能API文档")
    .markdown("**说明**: 包含3个新增接口")
    .divider()
    .markdown("**请选择审批结果**:")
    .add_block(select_menu(
        placeholder="请选择",
        options=[
            {"value": "approve", "text": "批准"},
            {"value": "reject", "text": "拒绝"},
            {"value": "review", "text": "需要修改"},
        ]
    ))
    .build())
```

**Feishu API 参考**:
- 文档: [SelectMenu 元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/select-menu)

### 2.6 输入表单 (input_text)

**功能描述**: 文本输入框，用于收集用户输入（需要配置交互回调）

**JSON 结构**:
```json
{
  "tag": "input_text",
  "placeholder": {
    "tag": "plain_text",
    "content": "请输入审批意见"
  },
  "label": {
    "tag": "plain_text",
    "content": "审批意见"
  },
  "max_length": 500
}
```

**参数说明**:
- `placeholder`: 占位提示文本
- `label`: 输入框标签
- `max_length`: 最大输入长度（可选，默认 2000）

**使用示例**:
```python
def input_text(
    placeholder: str,
    label: str,
    *,
    max_length: int = 500,
) -> Block:
    """创建文本输入框

    Args:
        placeholder: 占位提示
        label: 输入框标签
        max_length: 最大长度

    Returns:
        输入框元素字典
    """
    return {
        "tag": "input_text",
        "placeholder": {"tag": "plain_text", "content": placeholder},
        "label": {"tag": "plain_text", "content": label},
        "max_length": max_length,
    }

# 使用示例
comment_input = input_text(
    placeholder="请输入您的审批意见",
    label="审批意见",
    max_length=500
)
```

**完整卡片示例**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("文档审批", status="warning")
    .metadata("文档名", "API Reference Guide")
    .metadata("申请人", "张三")
    .divider()
    .markdown("**请输入审批意见**:")
    .add_block(input_text(
        placeholder="请输入您的审批意见...",
        label="审批意见",
        max_length=500
    ))
    .build())
```

**Feishu API 参考**:
- 文档: [InputText 元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components/input-text)

### 2.7 表格 (table) - 多维表格

**功能描述**: 在卡片中嵌入多维表格，展示结构化数据

**JSON 结构**:
```json
{
  "tag": "table",
  "table_column_type": [
    {
      "type": "text",
      "width": 200
    },
    {
      "type": "text",
      "width": 150
    },
    {
      "type": "text",
      "width": 150
    }
  ],
  "table_data": [
    {
      "cells": [
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "文档1"
          }
        },
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "已完成"
          }
        },
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "2026-01-20"
          }
        }
      ]
    },
    {
      "cells": [
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "文档2"
          }
        },
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "进行中"
          }
        },
        {
          "tag": "table_cell",
          "text": {
            "tag": "plain_text",
            "content": "2026-01-21"
          }
        }
      ]
    }
  ],
  "row_header": 1,
  "col_header": 1
}
```

**参数说明**:
- `table_column_type`: 列定义
  - `type`: 列类型（text/number/date/url等）
  - `width`: 列宽度（像素）
- `table_data`: 表格数据
  - `cells`: 单元格数组
- `row_header`: 行标题数量
- `col_header`: 列标题数量

**使用示例**:
```python
def table(
    columns: List[Dict[str, Any]],
    rows: List[List[Dict[str, str]]],
    *,
    row_header: int = 1,
    col_header: int = 1,
) -> Block:
    """创建表格元素

    Args:
        columns: 列定义 [{"type": "text", "width": 200}, ...]
        rows: 行数据 [[{"content": "..."}, ...], ...]
        row_header: 行标题数量
        col_header: 列标题数量

    Returns:
        表格元素字典
    """
    return {
        "tag": "table",
        "table_column_type": [
            {"type": col["type"], "width": col.get("width", 150)}
            for col in columns
        ],
        "table_data": [
            {
                "cells": [
                    {
                        "tag": "table_cell",
                        "text": {"tag": "plain_text", "content": cell["content"]}
                    }
                    for cell in row
                ]
            }
            for row in rows
        ],
        "row_header": row_header,
        "col_header": col_header,
    }

# 使用示例
doc_table = table(
    columns=[
        {"type": "text", "width": 200},
        {"type": "text", "width": 150},
        {"type": "text", "width": 150},
    ],
    rows=[
        [
            {"content": "文档名称"},
            {"content": "状态"},
            {"content": "更新时间"},
        ],
        [
            {"content": "API Reference"},
            {"content": "已完成"},
            {"content": "2026-01-20"},
        ],
        [
            {"content": "User Guide"},
            {"content": "进行中"},
            {"content": "2026-01-21"},
        ],
    ],
    row_header=1,
    col_header=1
)
```

**完整卡片示例**:
```python
from notifications.templates.builder import CardBuilder

card = (CardBuilder()
    .header("文档状态报告", status="info")
    .markdown("**项目**: feishu-doc-tools")
    .markdown("**更新**: 共 15 个文档")
    .divider()
    .add_block(table(
        columns=[
            {"type": "text", "width": 200},
            {"type": "text", "width": 150},
            {"type": "text", "width": 150},
        ],
        rows=[
            [
                {"content": "文档名称"},
                {"content": "状态"},
                {"content": "更新时间"},
            ],
            [
                {"content": "API Reference"},
                {"content": "已完成"},
                {"content": "2026-01-20"},
            ],
            [
                {"content": "User Guide"},
                {"content": "进行中"},
                {"content": "2026-01-21"},
            ],
            [
                {"content": "Quick Start"},
                {"content": "待审核"},
                {"content": "2026-01-22"},
            ],
        ],
        row_header=1,
        col_header=1
    ))
    .build())
```

**Feishu API 参考**:
- 文档: [Table 元素](https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/content-components/table)
- 多维表格 API: `POST https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records`

---

## 三、Feishu API 参考

### 3.1 卡片消息 API

**发送卡片消息**:
```http
POST https://open.feishu.cn/open-apis/im/v1/messages
Authorization: Bearer {tenant_access_token}
Content-Type: application/json

{
  "receive_id": "ou_xxxxxxxxxxxxxxxx",
  "msg_type": "interactive",
  "content": "{\"config\":{\"wide_screen_mode\":true},\"elements\":[...]}"
}
```

**Webhook 发送**:
```http
POST https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "msg_type": "interactive",
  "card": {
    "config": {"wide_screen_mode": true},
    "elements": [...]
  }
}
```

### 3.2 官方文档链接

| 功能 | 文档链接 |
|------|---------|
| **卡片总览** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-structure |
| **卡片元素** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/content-components |
| **交互组件** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/interactive-components |
| **自定义机器人** | https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot |
| **消息发送** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/im-v1/message/create |
| **图片上传** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/im-v1/image/create |
| **用户信息** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/contact-v3/user/get |
| **多维表格** | https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/reference/bitable-v1/app-table-record |

### 3.3 卡片结构规范

**完整的卡片结构**:
```json
{
  "config": {
    "wide_screen_mode": true,
    "enable_forward": true
  },
  "header": {
    "template": "blue",
    "title": {
      "tag": "plain_text",
      "content": "卡片标题"
    }
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**Markdown 内容**"
      }
    },
    {
      "tag": "hr"
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "text": {
            "tag": "plain_text",
            "content": "按钮文本"
          },
          "type": "primary",
          "url": "https://example.com"
        }
      ]
    }
  ]
}
```

**config 参数说明**:
- `wide_screen_mode`: 宽屏模式（默认 true）
- `enable_forward`: 是否允许转发（默认 true）

---

## 四、实现指南

### 4.1 扩展 CardBuilder

**添加新元素方法**:

```python
from notifications.templates.builder import CardBuilder
from notifications.blocks.blocks import Block

def image_element(img_key: str, alt: str, **kwargs) -> Block:
    """图片元素实现（见上文）"""
    pass

def progress_bar(value: str, **kwargs) -> Block:
    """进度条实现（见上文）"""
    pass

def mention_user(user_id: str, name: str, **kwargs) -> Block:
    """@提及实现（见上文）"""
    pass

# 扩展 CardBuilder 类
class AdvancedCardBuilder(CardBuilder):
    """扩展的 CardBuilder，支持高级功能"""

    def image(self, img_key: str, alt: str, **kwargs) -> 'AdvancedCardBuilder':
        """添加图片元素"""
        self._elements.append(image_element(img_key, alt, **kwargs))
        return self

    def progress(self, value: str, **kwargs) -> 'AdvancedCardBuilder':
        """添加进度条"""
        self._elements.append(progress_bar(value, **kwargs))
        return self

    def mention(self, user_id: str, name: str, **kwargs) -> 'AdvancedCardBuilder':
        """添加 @提及"""
        self._elements.append(mention_user(user_id, name, **kwargs))
        return self

    def date_picker(self, value: str, **kwargs) -> 'AdvancedCardBuilder':
        """添加日期时间选择器"""
        self._elements.append(date_picker(value, **kwargs))
        return self

    def select_menu(self, placeholder: str, options: List[Dict], **kwargs) -> 'AdvancedCardBuilder':
        """添加下拉选择菜单"""
        self._elements.append(select_menu(placeholder, options, **kwargs))
        return self

    def input_text(self, placeholder: str, label: str, **kwargs) -> 'AdvancedCardBuilder':
        """添加文本输入框"""
        self._elements.append(input_text(placeholder, label, **kwargs))
        return self

    def table(self, columns: List[Dict], rows: List[List[Dict]], **kwargs) -> 'AdvancedCardBuilder':
        """添加表格"""
        self._elements.append(table(columns, rows, **kwargs))
        return self
```

**使用示例**:
```python
from notifications.templates.builder import CardBuilder

# 使用扩展的 CardBuilder
card = (AdvancedCardBuilder()
    .header("任务进度", status="running", color="wathet")
    .markdown("**任务**: 批量文件处理")
    .markdown("**总数**: 200 个文件")
    .progress("65%", status="running", color="blue")
    .mention(
        user_id="ou_1234567890abcdef",
        name="张三"
    )
    .date_picker("2026-01-20 15:00", mode="datetime")
    .build())
```

### 4.2 创建高级模板工厂

```python
from typing import Optional, Dict, Any, List

class AdvancedTemplates:
    """高级功能模板工厂"""

    @staticmethod
    def task_with_progress(
        task_name: str,
        current: int,
        total: int,
        assignee: Optional[str] = None,
        assignee_id: Optional[str] = None,
        deadline: Optional[str] = None,
    ) -> CardTemplate:
        """创建带进度条的任务通知

        Args:
            task_name: 任务名称
            current: 当前进度
            total: 总量
            assignee: 负责人姓名（可选）
            assignee_id: 负责人 ID（可选）
            deadline: 截止时间（可选）

        Returns:
            CardTemplate 实例
        """
        percentage = int((current / total) * 100)
        builder = AdvancedCardBuilder().header(
            "任务进行中", status="running", color="wathet"
        )

        # 任务信息
        builder.metadata("任务", task_name)
        builder.metadata("进度", f"{current}/{total} ({percentage}%)")

        # 进度条
        builder.progress(f"{percentage}%", status="running", color="blue")

        # 负责人
        if assignee and assignee_id:
            builder.divider()
            builder.markdown("**负责人**:")
            builder.mention(assignee_id, assignee)

        # 截止时间
        if deadline:
            builder.divider()
            builder.markdown("**截止时间**:")
            builder.date_picker(deadline, mode="datetime")

        return builder.build()

    @staticmethod
    def approval_request(
        requester: str,
        requester_id: str,
        doc_name: str,
        doc_url: str,
        options: Optional[List[Dict[str, str]]] = None,
    ) -> CardTemplate:
        """创建审批请求卡片

        Args:
            requester: 申请人姓名
            requester_id: 申请人 ID
            doc_name: 文档名称
            doc_url: 文档链接
            options: 审批选项（可选）

        Returns:
            CardTemplate 实例
        """
        builder = AdvancedCardBuilder().header(
            "审批请求", status="warning", color="orange"
        )

        builder.metadata("申请人", requester)
        builder.mention(requester_id, requester)
        builder.metadata("文档", doc_name)

        builder.divider()
        builder.markdown(f"[查看文档]({doc_url})")

        # 审批选项
        if not options:
            options = [
                {"value": "approve", "text": "批准"},
                {"value": "reject", "text": "拒绝"},
            ]

        builder.divider()
        builder.markdown("**请选择审批结果**:")
        builder.select_menu(
            placeholder="请选择...",
            options=options,
        )

        # 审批意见
        builder.input_text(
            placeholder="请输入审批意见（可选）",
            label="审批意见",
        )

        return builder.build()

    @staticmethod
    def data_report(
        title: str,
        data: List[Dict[str, Any]],
        columns: List[Dict[str, Any]],
        summary: Optional[str] = None,
    ) -> CardTemplate:
        """创建数据报告卡片

        Args:
            title: 报告标题
            data: 数据列表
            columns: 列定义
            summary: 摘要说明（可选）

        Returns:
            CardTemplate 实例
        """
        builder = AdvancedCardBuilder().header(
            title, status="info", color="blue"
        )

        # 摘要
        if summary:
            builder.markdown(summary)
            builder.divider()

        # 表格
        rows = []
        # 表头
        rows.append([{"content": col["name"]} for col in columns])
        # 数据行
        for item in data:
            rows.append([{"content": str(item.get(col["key"], ""))} for col in columns])

        col_types = [{"type": "text", "width": col.get("width", 150)} for col in columns]

        builder.table(
            columns=col_types,
            rows=rows,
            row_header=1,
            col_header=1,
        )

        return builder.build()
```

### 4.3 图片上传工具

```python
import requests
from typing import Optional

class FeishuImageUploader:
    """飞书图片上传工具"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_token = None

    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        if self._tenant_token:
            return self._tenant_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, json=data)
        result = response.json()

        if result.get("code") != 0:
            raise ValueError(f"获取 token 失败: {result}")

        self._tenant_token = result["tenant_access_token"]
        return self._tenant_token

    def upload_image(self, image_path: str, image_type: str = "message") -> str:
        """上传图片并返回 img_key

        Args:
            image_path: 图片路径（本地路径或 URL）
            image_type: 图片类型

        Returns:
            img_key: 图片唯一标识
        """
        token = self._get_tenant_token()

        url = "https://open.feishu.cn/open-apis/im/v1/images"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        # 判断是本地文件还是 URL
        if image_path.startswith("http://") or image_path.startswith("https://"):
            # 从 URL 下载图片
            import io
            image_response = requests.get(image_path)
            files = {
                "image": ("image", io.BytesIO(image_response.content), "image/jpeg")
            }
            data = {"image_type": image_type}
        else:
            # 上传本地文件
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {"image_type": image_type}

        response = requests.post(url, headers=headers, files=files, data=data)
        result = response.json()

        if result.get("code") != 0:
            raise ValueError(f"上传图片失败: {result}")

        return result["data"]["image_key"]

    def add_image_to_card(
        self,
        image_path: str,
        alt_text: str,
        **kwargs
    ) -> Block:
        """上传图片并生成卡片元素

        Args:
            image_path: 图片路径
            alt_text: 图片替代文本
            **kwargs: 其他图片参数

        Returns:
            图片元素字典
        """
        img_key = self.upload_image(image_path)
        return image_element(img_key, alt_text, **kwargs)
```

**使用示例**:
```python
uploader = FeishuImageUploader(
    app_id="your_app_id",
    app_secret="your_app_secret"
)

# 上传并创建图片元素
img_element = uploader.add_image_to_card(
    image_path="/path/to/chart.png",
    alt_text="数据图表",
    title="2026年1月销售数据",
    mode="fit_horizontal"
)

# 添加到卡片
card = (CardBuilder()
    .header("数据报告", status="info")
    .add_block(img_element)
    .markdown("**总销售额**: ¥1,234,567")
    .build())
```

---

## 五、最佳实践

### 5.1 内容组织

**原则**: 从重要到次要，从概括到详细

**推荐结构**:
```
1. 标题 (header) - 状态 + 关键信息
2. 核心信息 (columns) - 关键指标并排展示
3. 分隔线 (divider) - 视觉分割
4. 详细说明 (markdown) - 具体内容
5. 可折叠详情 (collapsible) - 可选的详细信息
6. 提示/注意 (note) - 重要提醒
7. 操作按钮 (action) - 可执行操作
```

**示例**:
```python
card = (CardBuilder()
    # 1. 标题 - 状态一目了然
    .header("批量上传完成", status="success", color="green")

    # 2. 核心指标 - 并排展示
    .columns()
        .column("总数", "156", width="auto")
        .column("成功", "155", width="auto")
        .column("失败", "1", width="auto")
    .end_columns()

    # 3. 分隔线 - 视觉分割
    .divider()

    # 4. 详细说明 - 具体信息
    .markdown("**总大小**: 2.3 GB")
    .markdown("**平均速度**: 12.5 MB/s")
    .markdown("**耗时**: 3分15秒")

    # 5. 可折叠详情 - 失败信息
    .collapsible("失败文件", "large_file.dat (超过限制)")

    # 6. 提示信息 - 操作提醒
    .note("失败的文件可以稍后手动上传")

    .build())
```

### 5.2 颜色选择指南

| 场景 | 推荐颜色 | template 值 |
|------|---------|-------------|
| 成功完成 | 绿色 | `"green"` |
| 运行中 | 浅蓝色 | `"wathet"` |
| 普通更新 | 蓝色 | `"blue"` |
| 警告/注意 | 橙色 | `"orange"` |
| 错误/失败 | 红色 | `"red"` |
| 信息提示 | 紫色 | `"purple"` |
| 中性信息 | 灰色 | `"grey"` |

### 5.3 性能优化

**1. 减少元素数量**:
```python
# ❌ 不推荐：太多小元素
for item in items:
    builder.markdown(f"- {item['name']}: {item['status']}")

# ✅ 推荐：合并为单个 markdown
content = "\n".join(f"- {item['name']}: {item['status']}" for item in items)
builder.markdown(content)
```

**2. 使用可折叠面板**:
```python
# ❌ 不推荐：大量详细信息直接展示
builder.markdown("```json\n" + large_json + "\n```")

# ✅ 推荐：折叠详细信息
builder.collapsible("详细信息", "```json\n" + large_json + "\n```", expanded=False)
```

**3. 图片优化**:
```python
# ❌ 不推荐：使用大尺寸图片
uploader.add_image_to_card("large_image.png", "图表")

# ✅ 推荐：压缩后上传
from PIL import Image

img = Image.open("large_image.png")
img.thumbnail((800, 600))  # 缩放到合理尺寸
img.save("optimized_image.png", optimize=True, quality=85)
uploader.add_image_to_card("optimized_image.png", "图表")
```

### 5.4 可访问性

**1. 使用有意义的替代文本**:
```python
# ❌ 不推荐
.image(img_key, "图片")

# ✅ 推荐
.image(img_key, "2026年Q1销售数据趋势图，显示销售额增长15%")
```

**2. 颜色对比度**:
```python
# ❌ 不推荐：浅色文字配浅色背景
.color("grey")  # 在白色背景下可能看不清

# ✅ 推荐：使用合适的颜色组合
.color("green")  # 高对比度，清晰可读
```

**3. 结构清晰**:
```python
# ✅ 推荐：使用标题和分隔线组织内容
.header("报告标题")
.divider()
.markdown("## 第一部分")
.divider()
.markdown("## 第二部分")
```

### 5.5 错误处理

**完整的错误处理示例**:
```python
from notifications.channels.webhook import WebhookChannel
from notifications.config.settings import create_settings

def send_notification_safe(card: CardTemplate) -> bool:
    """安全发送通知，包含完整错误处理"""
    try:
        settings = create_settings()
        if not settings.validate_required_fields()[0]:
            raise ValueError("配置不完整")

        with WebhookChannel(settings) as channel:
            success = channel.send(card.to_dict(), "notification")

            if not success:
                # 记录失败
                logging.error(f"通知发送失败: {channel.get_last_error()}")
                return False

            return True

    except ValueError as e:
        logging.error(f"配置错误: {e}")
        return False
    except requests.RequestException as e:
        logging.error(f"网络错误: {e}")
        return False
    except Exception as e:
        logging.error(f"未知错误: {e}")
        return False
```

### 5.6 测试建议

**单元测试示例**:
```python
import pytest
from notifications.templates.builder import CardBuilder

def test_card_builder_with_columns():
    """测试多列布局"""
    builder = CardBuilder()
    result = (builder
        .header("测试", status="info")
        .columns()
            .column("A", "1")
            .column("B", "2")
        .end_columns()
        .build())

    card = result.to_dict()

    # 验证列结构
    assert "elements" in card
    assert card["elements"][0]["tag"] == "column_set"
    assert len(card["elements"][0]["columns"]) == 2

def test_card_builder_collapsible():
    """测试可折叠面板"""
    builder = CardBuilder()
    result = (builder
        .header("测试")
        .collapsible("标题", "内容", expanded=False)
        .build())

    card = result.to_dict()

    # 验证可折叠面板
    collapsible = card["elements"][0]
    assert collapsible["tag"] == "collapsible_panel"
    assert collapsible["expanded"] == False
```

**Mock 测试**:
```python
from unittest.mock import Mock, patch

def test_webhook_channel_send():
    """测试 Webhook 发送"""
    mock_settings = Mock()
    mock_settings.webhook_url = "https://test.webhook.url"

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200

        channel = WebhookChannel(mock_settings)
        card = {"elements": [{"tag": "markdown", "content": "test"}]}

        result = channel.send(card, "test")

        assert result == True
        mock_post.assert_called_once()
```

---

## 附录

### A. 完整的颜色列表

```python
FEISHU_CARD_COLORS = [
    "blue",      # 蓝色 - 普通信息
    "wathet",    # 浅蓝色 - 运行中
    "turquoise", # 青绿色
    "green",     # 绿色 - 成功
    "yellow",    # 黄色
    "orange",    # 橙色 - 警告
    "red",       # 红色 - 错误
    "carmine",   # 胭脂红
    "violet",    # 紫色
    "purple",    # 紫罗兰
    "grey",      # 灰色 - 中性
]
```

### B. 元素标签列表

```python
FEISHU_ELEMENT_TAGS = [
    # 内容元素
    "div",           # 容器
    "hr",            # 分隔线
    "markdown",      # Markdown 文本
    "plain_text",    # 纯文本
    "lark_md",       # 飞书 Markdown（支持 @）

    # 布局元素
    "column_set",    # 列集合
    "column",        # 列
    "collapsible_panel",  # 可折叠面板

    # 交互元素
    "button",        # 按钮
    "select_menu",   # 下拉选择
    "input_text",    # 文本输入
    "datepicker",    # 日期时间选择

    # 媒体元素
    "img",           # 图片
    "progress",      # 进度条

    # 其他元素
    "note",          # 提示框
    "table",         # 表格
    "mention",       # @提及
    "text_tag",      # 文本标签
]
```

### C. 相关文档

- **CardBuilder 文档**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/notifications/templates/builder.py`
- **Blocks 文档**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/notifications/blocks/blocks.py`
- **文档模板**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/notifications/templates/document_templates.py`
- **高级示例**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/scripts/notifications/test_advanced_cards.py`
- **快速参考**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/docs/notification-reference/QUICK_REFERENCE_CARD.md`
- **完整参考**: `/home/hao/Workspace/MM/utility/feishu/feishu-doc-tools/docs/notification-reference/notification_system_reference_guide.md`

---

**文档版本**: v1.0
**最后更新**: $(date +%Y-%m-%d)
**维护者**: Development Team
**反馈**: 请提交 Issue 到项目仓库
