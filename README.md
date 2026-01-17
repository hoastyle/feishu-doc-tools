# Markdown to Feishu Uploader

将本地Markdown文件原样上传至飞书文档的工具，支持任意大小的文件，不占用AI模型上下文。

## 核心特性

- ✅ **零上下文占用** - 支持任意大小Markdown文件，不占用模型token
- ✅ **直连API模式** - 直接调用飞书API，无需AI/MCP，更快更便宜
- ✅ **格式完整保留** - 支持标题、段落、代码块、列表、表格、图片等
- ✅ **批量处理** - 自动分批上传大文件（200 blocks/批次）
- ✅ **图片支持** - 本地图片、网络图片、多种处理模式
- ✅ **文档创建** - 从Markdown直接创建新飞书文档
- ✅ **批量迁移** - 一次性创建整个文件夹的文档
- ✅ **文件夹管理** - 创建和组织飞书云文件夹
- ✅ **错误友好** - 清晰的错误提示和日志输出

## 架构设计

### 模式1：直连API模式（推荐，默认）

```
Markdown文件 → Python脚本 → 飞书API → 飞书文档
```

**优势**：
- 无需AI/LLM，零成本
- 直接API调用，速度快
- 独立运行，简单可靠

### 模式2：MCP模式（用于AI辅助）

```
Markdown文件 → Python脚本 → JSON → AI调用MCP工具 → 飞书文档
```

**适用场景**：
- 需要AI智能修改内容
- 需要AI摘要提取
- 集成AI工作流

## 快速开始

### 安装依赖

本项目使用 [uv](https://docs.astral.sh/uv/) 进行依赖管理。

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync

# 安装开发依赖
uv sync --extra dev
```

### 基本用法

#### 方式1：上传到现有文档（推荐）

```bash
# 1. 设置飞书应用凭证
export FEISHU_APP_ID=cli_xxxxx
export FEISHU_APP_SECRET=xxxxx

# 2. 上传Markdown内容到现有文档
python scripts/md_to_feishu_upload.py README.md doxcnxxxxx
```

#### 方式2：创建新文档并上传

```bash
# 从单个Markdown文件创建新文档
python scripts/create_feishu_doc.py README.md --title "My Document"

# 指定目标文件夹
python scripts/create_feishu_doc.py README.md --folder fldcnxxxxx
```

#### 方式3：批量迁移

```bash
# 从整个文件夹批量创建文档
python scripts/batch_create_docs.py ./docs

# 在特定文件夹中创建
python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx

# 自定义文件匹配
python scripts/batch_create_docs.py ./docs --pattern "**/*.md"
```

#### 方式4：MCP/AI模式

```bash
# 1. 转换Markdown为JSON格式
python scripts/md_to_feishu.py <md_file_path> <feishu_doc_id> --output /tmp/blocks.json

# 2. 使用AI工具类上传（通过MCP）
python -c "from lib.feishu_md_uploader import FeishuMdUploader; \
           uploader = FeishuMdUploader(); \
           print(uploader.generate_upload_instructions('<md_file>', '<doc_id>'))"
```

### 命令行选项

```bash
# 直连API模式
python scripts/md_to_feishu_upload.py <md_file> <doc_id> [options]

Options:
  --mode direct|json     模式选择（默认：direct直连API）
  --batch-size <n>       每批blocks数量（默认：200）
  --image-mode <mode>    图片处理模式：local|download|skip（默认：local）
  --app-id <id>          飞书应用ID（或使用FEISHU_APP_ID环境变量）
  --app-secret <secret>  飞书应用密钥（或使用FEISHU_APP_SECRET环境变量）
  --verbose              详细日志输出
  --help-env             显示环境变量设置帮助

# MCP模式
python scripts/md_to_feishu.py <md_file> <doc_id> [options]

Options:

```bash
python scripts/md_to_feishu.py <md_file> <doc_id> [options]

Options:
  --output <path>          输出JSON文件路径（默认：/tmp/feishu_blocks.json）
  --batch-size <n>         每批blocks数量（默认：50）
  --image-mode <mode>      图片处理模式：local|download|skip（默认：local）
  --max-text-length <n>    单个text block最大长度（默认：2000）
```

## 支持的Markdown元素

| Markdown | 飞书Block | 说明 |
|----------|----------|------|
| `# Heading` | heading1-9 | 支持h1-h9 |
| 段落 | text | 支持粗体、斜体、代码等 |
| ` ```code``` ` | code | 自动识别语言 |
| `- 列表` | list | 有序/无序列表 |
| `![img](url)` | image | 本地/网络图片 |
| 表格 | table | 完整表格支持 |

## 项目结构

```
md-to-feishu/
├── scripts/
│   ├── md_to_feishu.py             # 核心转换脚本（MCP模式）
│   ├── md_to_feishu_upload.py      # 统一上传脚本（支持direct和json模式）
│   ├── create_feishu_doc.py        # 创建单个文档脚本（新增）
│   ├── batch_create_docs.py        # 批量创建文档脚本（新增）
│   ├── test_api_connectivity.py    # API连通性测试
│   └── create_wiki.py              # Wiki创建脚本（规划）
├── lib/
│   ├── feishu_api_client.py        # 直连API客户端（已扩展）
│   │   ├── create_document()       # 创建文档
│   │   ├── create_folder()         # 创建文件夹
│   │   ├── list_folder_contents()  # 列出文件夹内容
│   │   └── batch_create_*()        # 批量操作
│   └── feishu_md_uploader.py       # MCP工具类封装
├── tests/
│   ├── test_md_to_feishu.py        # Markdown转换测试
│   └── test_feishu_api_extended.py # API功能测试（新增）
├── examples/
│   └── sample.md                   # 示例文件
├── docs/
│   ├── DESIGN.md                   # 设计文档
│   ├── DIRECT_API_MODE.md          # 直连API模式文档
│   ├── API_OPERATIONS.md           # API操作参考（新增）
│   └── BATCH_OPERATIONS.md         # 批量操作指南（新增）
└── README.md
```

## 工作流程

### 阶段1：Markdown → JSON

```python
# scripts/md_to_feishu.py
1. 读取MD文件
2. 使用markdown-it-py解析为AST
3. 遍历AST节点，映射为飞书block格式
4. 分批处理（50 blocks/批）
5. 输出JSON结构
```

### 阶段2：JSON → 飞书文档

```python
# lib/feishu_md_uploader.py
1. 调用转换脚本生成JSON
2. 读取JSON（结构化数据）
3. 循环调用feishu-docker MCP工具
4. 上传blocks和图片
5. 返回结果
```

## JSON格式示例

```json
{
  "success": true,
  "documentId": "doc123",
  "batches": [
    {
      "batchIndex": 0,
      "startIndex": 0,
      "blocks": [
        {
          "blockType": "heading1",
          "options": {
            "heading": {
              "level": 1,
              "content": "标题"
            }
          }
        }
      ]
    }
  ],
  "images": [
    {
      "blockIndex": 3,
      "batchIndex": 0,
      "localPath": "/path/to/image.png"
    }
  ],
  "metadata": {
    "totalBlocks": 150,
    "totalBatches": 3,
    "totalImages": 5
  }
}
```

## 测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/test_md_to_feishu.py -v

# 测试覆盖率
uv run pytest --cov=scripts --cov=lib tests/
```

## 依赖要求

- Python 3.8.1+
- uv (用于依赖管理)
- markdown-it-py >= 3.0.0
- 飞书MCP服务器（feishu-docker）

## 开发状态

### Phase 1：上传模式 ✅ 完成
- [x] 核心转换脚本
- [x] 工具类封装
- [x] 单元测试（11个测试通过）
- [x] 使用文档
- [x] 设计文档
- [x] uv环境配置

### Phase 2：创建和迁移模式 ✅ 完成（MVP）
- [x] 文档创建API（create_document）
- [x] 文件夹管理API（create_folder, list_folder）
- [x] 单文档创建脚本（create_feishu_doc.py）
- [x] 批量创建脚本（batch_create_docs.py）
- [x] 批量创建函数（batch_create_documents_from_folder）
- [x] 综合单元测试（14个新测试）
- [x] API参考文档（API_OPERATIONS.md）
- [x] 批量操作指南（BATCH_OPERATIONS.md）

### Phase 3：高级功能 🔨 规划中
- [ ] Wiki操作API（create_wiki_space, create_wiki_node）
- [ ] Bitable操作API（create_bitable, create_table）
- [ ] Wiki创建脚本（create_wiki.py）
- [ ] 表格转Bitable脚本（md_table_to_bitable.py）
- [ ] 性能优化
- [ ] Download图片模式
- [ ] 更多格式支持（docx, html等）

## 项目状态

✅ **MVP可用于生产** - 核心上传和创建功能已完成并测试通过

**测试覆盖**：
```bash
$ uv run pytest tests/
======================== 25 passed in 1.23s =========================
```

**MVP功能**：
- ✅ 上传到现有文档
- ✅ 创建新文档
- ✅ 批量迁移文档
- ✅ 文件夹管理
- ✅ 图片上传
- ✅ 错误处理

**支持的Markdown元素**：
- ✅ 标题（h1-h6）
- ✅ 段落和文本样式（粗体、斜体、代码、删除线）
- ✅ 代码块（50+语言）
- ✅ 列表（有序和无序）
- ✅ 图片（本地模式）
- ✅ 引用块
- ⏸️ 表格（待实现）
- ⏸️ 数学公式（待实现）

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关项目

- [Feishu-MCP](https://github.com/yourusername/Feishu-MCP) - 飞书MCP服务器
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) - Python Markdown解析器
