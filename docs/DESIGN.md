# 设计文档

## 背景与目标

### 问题
用户需要将本地生成的Markdown文件上传至飞书文档，但存在以下挑战：
1. 文件可能很大，直接读入AI上下文会消耗大量token
2. 需要保持Markdown格式的完整性
3. 需要支持图片等复杂元素

### 解决方案
采用**中介脚本模式**：Markdown文件 → Python脚本 → JSON → AI调用MCP → 飞书文档

**核心优势**：
- ✅ 文件内容不进入AI上下文，支持任意大小
- ✅ 结构化JSON传递信息，易于处理
- ✅ 脚本可独立测试和调试
- ✅ 可扩展支持更多格式

## 架构设计

### 系统架构图

```
┌─────────────────┐
│  Markdown文件   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  scripts/md_to_feishu.py    │
│  - 解析Markdown             │
│  - 映射为飞书blocks格式     │
│  - 输出JSON                 │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│  JSON中介文件   │
│  - batches      │
│  - images       │
│  - metadata     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  lib/feishu_md_uploader.py  │
│  - 读取JSON                 │
│  - 生成MCP调用指令          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  AI + MCP Tools             │
│  - batch_create_blocks      │
│  - upload_images            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│   飞书文档      │
└─────────────────┘
```

### 数据流

```
Markdown → AST → Blocks → Batches → JSON → MCP Params → Feishu API
```

#### 各阶段说明

1. **Markdown → AST**
   - 使用 `markdown-it-py` 解析
   - 生成Token树

2. **AST → Blocks**
   - 遍历Token树
   - 映射为飞书block格式
   - 处理样式和嵌套

3. **Blocks → Batches**
   - 按50个block分批
   - 计算索引和位置

4. **Batches → JSON**
   - 序列化为JSON
   - 包含元数据

5. **JSON → MCP Params**
   - 提取参数
   - 生成调用指令

6. **MCP → Feishu**
   - AI执行MCP调用
   - 上传到飞书

## 核心模块设计

### 1. 转换器（MarkdownToFeishuConverter）

#### 职责
- 读取Markdown文件
- 解析为Token树
- 转换为飞书blocks
- 分批和输出JSON

#### 主要方法

```python
class MarkdownToFeishuConverter:
    def convert(self) -> Dict[str, Any]:
        """执行完整转换流程"""

    def _process_tokens(self, tokens: List[Token]):
        """处理token列表，生成blocks"""

    def _process_heading(self, tokens, start_idx, level):
        """处理标题"""

    def _process_paragraph(self, tokens, start_idx):
        """处理段落"""

    def _process_code_block(self, token):
        """处理代码块"""

    def _process_list(self, tokens, start_idx, ordered):
        """处理列表"""

    def _extract_inline_styles(self, token):
        """提取行内样式（粗体、斜体等）"""

    def _create_batches(self):
        """创建批次"""
```

### 2. 上传器（FeishuMdUploader）

#### 职责
- 调用转换脚本
- 读取JSON结果
- 准备MCP调用参数
- 生成AI指令文档

#### 主要方法

```python
class FeishuMdUploader:
    def convert_md_to_json(self, md_file, doc_id, **options):
        """调用转换脚本"""

    def prepare_mcp_calls(self, conversion_result):
        """准备MCP调用数据"""

    def generate_upload_instructions(self, md_file, doc_id):
        """生成AI可执行的指令文档"""
```

### 3. 便捷函数

```python
def upload_md_to_feishu(md_file: str, doc_id: str) -> str:
    """供AI直接调用的简化接口"""
```

## Markdown → 飞书映射规则

### 支持的元素

| Markdown | 飞书Block类型 | 参数 |
|----------|--------------|------|
| `# H1` - `###### H6` | heading1-heading6 | level, content |
| 段落 | text | textStyles, align |
| ` ```code``` ` | code | code, language, wrap |
| `- 列表` | list | content, isOrdered=false |
| `1. 列表` | list | content, isOrdered=true |
| `![img](url)` | image | width, height |
| 表格 | table | rowSize, columnSize, cells |
| `> 引用` | text | 前缀 "> " |

### 行内样式映射

| Markdown | 飞书Style | 字段 |
|----------|----------|------|
| `**bold**` | bold | style.bold=true |
| `*italic*` | italic | style.italic=true |
| `` `code` `` | inline_code | style.inline_code=true |
| `~~strike~~` | strikethrough | style.strikethrough=true |

### 代码语言映射

参见 `scripts/md_to_feishu.py` 中的 `LANGUAGE_MAP` 字典。

示例：
- python → 49
- javascript → 30
- go → 22
- rust → 53

## JSON格式规范

### 成功响应

```json
{
  "success": true,
  "documentId": "doc123",
  "batches": [
    {
      "batchIndex": 0,
      "startIndex": 0,
      "blocks": [...]
    }
  ],
  "images": [
    {
      "blockIndex": 5,
      "batchIndex": 0,
      "localPath": "/path/to/img.png",
      "altText": "描述"
    }
  ],
  "metadata": {
    "totalBlocks": 150,
    "totalBatches": 3,
    "totalImages": 5
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误描述",
  "errorType": "FileNotFoundError"
}
```

## 关键设计决策

### 1. 为什么使用中介JSON？

**备选方案**：
- A. 直接在AI中处理Markdown
- B. 流式处理不保存中间文件
- C. 中介JSON文件（当前方案）

**选择C的原因**：
- ✅ 不占用AI上下文
- ✅ 可调试和检查中间结果
- ✅ 解耦转换和上传逻辑
- ✅ 支持暂停和恢复

### 2. 为什么分批处理？

**原因**：
- 飞书API限制单次请求大小
- 避免超时
- 支持进度显示
- 错误恢复更容易

**批次大小**：50个blocks（可配置）

### 3. 图片处理模式

#### local模式（默认）
- 仅处理本地图片
- 最安全，不涉及网络
- 适合大多数场景

#### download模式
- 下载网络图片
- 需要网络访问
- 可能有安全风险

#### skip模式
- 跳过所有图片
- 最快速
- 适合纯文本文档

### 4. 错误处理策略

**原则**：
- 脚本层：返回错误JSON
- 上传器层：抛出Python异常
- AI层：向用户报告

**可恢复错误**：
- 图片不存在 → 插入占位符
- 未知语言 → 使用PlainText

**不可恢复错误**：
- 文件不存在 → 终止
- 解析失败 → 终止

## 性能考虑

### 文件大小限制

| 文件大小 | 处理时间 | 内存占用 | 建议 |
|---------|----------|---------|------|
| < 100KB | < 1s | < 10MB | 直接处理 |
| 100KB-1MB | 1-5s | 10-50MB | 正常处理 |
| 1MB-10MB | 5-30s | 50-200MB | 分批上传 |
| > 10MB | > 30s | > 200MB | 分文件上传 |

### 优化策略

1. **批次大小调整**
   - 小文件：增大批次减少API调用
   - 大文件：减小批次避免超时

2. **图片处理优化**
   - 跳过图片加快速度
   - 图片并行上传（未实现）

3. **内存优化**
   - 流式处理（未实现）
   - 不保留完整AST

## 扩展性设计

### 支持新格式

添加新的Markdown元素支持：

1. 在 `_process_tokens` 添加token类型判断
2. 实现处理方法
3. 映射到飞书block格式
4. 添加测试

示例：支持数学公式

```python
def _process_math(self, token):
    """处理数学公式"""
    equation = token.content
    return {
        'blockType': 'text',
        'options': {
            'text': {
                'textStyles': [{
                    'equation': equation,
                    'style': {}
                }]
            }
        }
    }
```

### 支持新文件格式

通过类似架构支持docx、html等：

```
DocxToFeishuConverter
HtmlToFeishuConverter
...
```

## 测试策略

### 单元测试

- 覆盖所有Markdown元素
- 边界情况（空文件、超大文件）
- 错误处理

### 集成测试

- 端到端转换流程
- 与飞书API集成（需Mock）

### 测试覆盖率目标

- 代码覆盖率 > 80%
- 核心功能覆盖率 > 95%

## 未来改进

### 短期（1-2周）
- [ ] 实现download图片模式
- [ ] 支持表格转换
- [ ] 优化超长段落分割

### 中期（1-2月）
- [ ] 支持双向同步（飞书→Markdown）
- [ ] 支持增量更新
- [ ] 图片并行上传

### 长期（3-6月）
- [ ] 支持更多格式（docx, html）
- [ ] 可视化配置界面
- [ ] 插件系统

## 参考资料

- [Markdown-it-py文档](https://markdown-it-py.readthedocs.io/)
- [飞书开放平台文档](https://open.feishu.cn/document/)
- [MCP协议规范](https://modelcontextprotocol.io/)
