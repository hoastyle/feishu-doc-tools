# 使用指南

## 快速开始

### 1. 安装依赖

```bash
# 确保已安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone <repository-url>
cd md-to-feishu

# 安装依赖
uv sync
```

### 2. 基本使用

#### 方式一：直接使用转换脚本

```bash
# 转换Markdown为JSON
uv run python scripts/md_to_feishu.py \
  examples/sample.md \
  your_feishu_doc_id \
  --output /tmp/output.json

# 查看输出
cat /tmp/output.json | jq '.metadata'
```

#### 方式二：使用工具类（推荐用于AI）

```python
from lib.feishu_md_uploader import upload_md_to_feishu

# 生成上传指令
instructions = upload_md_to_feishu('path/to/file.md', 'doc_id')
print(instructions)

# AI按照指令调用MCP工具完成上传
```

### 3. 命令行参数

```bash
python scripts/md_to_feishu.py <md_file> <doc_id> [选项]

选项:
  --output PATH          输出JSON文件路径（默认：/tmp/feishu_blocks.json）
  --batch-size N         每批blocks数量（默认：50）
  --image-mode MODE      图片处理模式：local|download|skip（默认：local）
  --max-text-length N    单个text block最大长度（默认：2000）
  --verbose, -v          启用详细日志
```

## 图片处理模式

### local（默认）
- 仅处理本地图片
- 图片路径相对于Markdown文件所在目录
- 网络图片将被跳过并警告

```bash
uv run python scripts/md_to_feishu.py file.md doc_id --image-mode local
```

### download（待实现）
- 下载网络图片到临时目录
- 作为本地图片处理

### skip
- 跳过所有图片
- 图片位置插入占位文本

```bash
uv run python scripts/md_to_feishu.py file.md doc_id --image-mode skip
```

## 工作流程示例

### 完整上传流程（使用AI）

```python
from lib.feishu_md_uploader import FeishuMdUploader

# 1. 初始化上传器
uploader = FeishuMdUploader()

# 2. 转换MD为JSON
result = uploader.convert_md_to_json(
    md_file=Path('example.md'),
    doc_id='your_doc_id'
)

# 3. 准备MCP调用
mcp_calls = uploader.prepare_mcp_calls(result)

# 4. AI执行MCP调用
# 循环处理每个批次
for batch in mcp_calls['batches']:
    # 调用 mcp__feishu-docker__batch_create_feishu_blocks
    # 参数: batch['mcpParams']
    pass

# 5. 上传图片
for img in mcp_calls['images']:
    # 从批次响应获取blockId
    # 调用 mcp__feishu-docker__upload_and_bind_image_to_block
    pass
```

### 使用便捷函数

```python
from lib.feishu_md_uploader import upload_md_to_feishu

# 一键生成上传指令
instructions = upload_md_to_feishu('example.md', 'doc_id')

# 指令包含：
# - 文件信息
# - 批次详情
# - 完整的MCP调用参数
# - 图片上传说明
```

## 测试

### 运行测试

```bash
# 全部测试
uv run pytest tests/

# 特定测试文件
uv run pytest tests/test_md_to_feishu.py -v

# 带覆盖率报告
uv run pytest --cov=scripts --cov=lib tests/
```

### 测试覆盖的功能

- ✅ 基本Markdown元素转换（标题、段落、列表）
- ✅ 代码块和语言识别
- ✅ 文本样式（粗体、斜体、代码、删除线）
- ✅ 分批处理（大文件）
- ✅ 图片处理（本地和网络）
- ✅ 错误处理
- ⏸️ 超长段落分割（待优化）

## 故障排查

### 常见问题

**Q: 转换失败，提示"File not found"**

A: 检查文件路径是否正确，使用绝对路径或相对于当前工作目录的路径。

**Q: 图片未上传**

A:
1. 确认使用 `--image-mode local`
2. 检查图片文件是否存在
3. 图片路径应相对于MD文件目录

**Q: 代码块语言识别错误**

A: 检查代码块语言标识是否在支持列表中（见 `scripts/md_to_feishu.py` 的 `LANGUAGE_MAP`）

**Q: uv sync失败**

A:
1. 确认Python版本 >= 3.8.1
2. 升级uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
3. 清理缓存：`rm -rf .venv uv.lock && uv sync`

### 调试技巧

```bash
# 启用详细日志
uv run python scripts/md_to_feishu.py file.md doc_id -v

# 检查JSON输出
cat /tmp/feishu_blocks.json | jq '.'

# 查看特定批次
cat /tmp/feishu_blocks.json | jq '.batches[0]'
```

## 性能优化

### 大文件处理

对于超大文件（>10MB）：

1. **调整批次大小**
```bash
--batch-size 100  # 增加批次大小减少API调用
```

2. **跳过图片**
```bash
--image-mode skip  # 先上传文本，后续单独处理图片
```

3. **分段上传**
将大文件分割为多个小文件，分别上传到不同文档。

## 扩展开发

### 添加新的Markdown元素支持

1. 在 `_process_tokens` 中添加新的token类型处理
2. 实现对应的处理方法（如 `_process_table`）
3. 映射到飞书block格式
4. 添加测试用例

### 自定义语言映射

编辑 `scripts/md_to_feishu.py` 中的 `LANGUAGE_MAP`：

```python
LANGUAGE_MAP = {
    'python': 49,
    'mylang': 1,  # 添加自定义语言
    # ...
}
```

## 下一步

- 查看 [README.md](README.md) 了解项目概览
- 查看 [examples/](examples/) 目录中的示例文件
- 阅读代码注释了解实现细节
