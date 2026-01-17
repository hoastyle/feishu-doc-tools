# Markdown to Feishu Uploader

将本地Markdown文件原样上传至飞书文档的工具，支持任意大小的文件，不占用AI模型上下文。

## 核心特性

- ✅ **零上下文占用** - 支持任意大小Markdown文件，不占用模型token
- ✅ **格式完整保留** - 支持标题、段落、代码块、列表、表格、图片等
- ✅ **批量处理** - 自动分批上传大文件（50 blocks/批次）
- ✅ **图片支持** - 本地图片、网络图片、多种处理模式
- ✅ **错误友好** - 清晰的错误提示和日志输出

## 架构设计

```
Markdown文件 → Python脚本解析 → JSON中介格式 → AI调用MCP工具 → 飞书文档
```

**关键优势**：
- 文件内容完全不进入模型上下文
- 使用结构化JSON传递信息
- 可独立测试和扩展

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本用法

```bash
# 1. 转换Markdown为JSON格式
python scripts/md_to_feishu.py <md_file_path> <feishu_doc_id> --output /tmp/blocks.json

# 2. 使用AI工具类上传（通过MCP）
python -c "from lib.feishu_md_uploader import FeishuMdUploader; \
           uploader = FeishuMdUploader(); \
           uploader.upload('<md_file>', '<doc_id>')"
```

### 命令行选项

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
│   └── md_to_feishu.py      # 核心转换脚本
├── lib/
│   └── feishu_md_uploader.py # 工具类封装
├── tests/
│   └── test_md_to_feishu.py  # 单元测试
├── examples/
│   └── sample.md             # 示例文件
├── docs/
│   └── design.md             # 设计文档
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
pytest tests/

# 运行特定测试
pytest tests/test_md_to_feishu.py -v

# 测试覆盖率
pytest --cov=scripts --cov=lib tests/
```

## 依赖要求

- Python 3.8+
- markdown-it-py >= 3.0.0
- 飞书MCP服务器（feishu-docker）

## 开发状态

- [x] 核心转换脚本
- [x] 工具类封装
- [x] 单元测试
- [x] 文档完善
- [ ] 性能优化
- [ ] 更多格式支持（docx, html等）

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关项目

- [Feishu-MCP](https://github.com/yourusername/Feishu-MCP) - 飞书MCP服务器
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) - Python Markdown解析器
