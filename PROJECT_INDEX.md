# Project Index: feishu-doc-tools

**Generated**: 2025-01-18
**Version**: v0.2.1
**Purpose**: 飞书文档管理工具 - 批量创建/迁移、Wiki 知识库、多维表格、下载导出

---

## 📁 Project Structure

```
feishu-doc-tools/
├── scripts/                  # 15 个 CLI 工具
│   ├── md_to_feishu.py              # 核心转换脚本
│   ├── md_to_feishu_upload.py        # 统一上传脚本
│   ├── create_feishu_doc.py          # 创建单个云文档
│   ├── batch_create_docs.py           # 批量创建云文档
│   ├── create_wiki_doc.py            # 创建单个 Wiki 文档
│   ├── batch_create_wiki_docs.py        # 批量创建 Wiki 文档
│   ├── download_doc.py ⭐              # 下载单个文档（新）
│   ├── download_wiki.py ⭐            # 批量下载 Wiki（新）
│   ├── list_wiki_tree.py ⭐           # 预览 Wiki 结构（新）
│   ├── md_table_to_bitable.py         # 表格转 Bitable
│   ├── get_root_info.py               # 获取工作区信息
│   ├── list_folders.py                 # 列出文件夹
│   └── test_api_connectivity.py      # API 连接测试
├── lib/
│   ├── feishu_api_client.py            # 直连 API 客户端
│   ├── feishu_md_uploader.py           # 飞书转换工具
│   └── wiki_operations.py               # Wiki 操作共享库
├── docs/
│   ├── user/                          # 用户文档（6 个）
│   ├── guides/                        # 专题指南（2 个）
│   ├── design/                        # 设计文档（5 个）
│   └── INDEX.md                      # 文档中心
├── tests/                           # 测试套件
├── pyproject.toml                   # uv 项目配置
└── README.md                        # 项目说明
```

---

## 🚀 Entry Points

### CLI Tools（scripts/）

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `md_to_feishu.py` | 核心转换脚本 | Markdown → 飞书 block JSON |
| `md_to_feishu_upload.py` | 统一上传脚本 | 转换 + 上传一体化 |
| `create_feishu_doc.py` | 创建单个云文档 | 快速创建文档 |
| `batch_create_docs.py` | 批量创建云文档 | 文件夹迁移 |
| `create_wiki_doc.py` | 创建单个 Wiki 文档 | 知识库维护 |
| `batch_create_wiki_docs.py` | 批量创建 Wiki 文档 | 知识库迁移 |
| `download_doc.py` ⭐ | 下载单个文档 | 文档备份/导出 |
| `download_wiki.py` ⭐ | 批量下载 Wiki | 知识库备份 |
| `list_wiki_tree.py` ⭐ | 预览 Wiki 结构 | 层次结构查看 |
| `md_table_to_bitable.py` | 表格转 Bitable | 数据管理 |
| `get_root_info.py` | 获取根信息 | 环境配置 |
| `list_folders.py` | 列出文件夹 | 结构查看 |
| `test_api_connectivity.py` | 测试 API 连接 | 问题诊断 |

### Python API（lib/）

| 模块 | 用途 |
|------|------|
| `FeishuApiClient` | 直连 API 客户端，支持批处理、图片上传、并行处理 |
| `FeishuMdUploader` | Markdown → 飞书 block JSON 转换工具 |

---

## 📦 Core Modules

### Module: FeishuApiClient
**Path**: `lib/feishu_api_client.py`
**Purpose**: 飞书 Open API 直连客户端
**Exports**: 27 个方法

**主要功能**：
- 文档操作 API（3 个方法）: batch_create_blocks, get_document_blocks, get_document_info
- 文件夹操作 API（4 个方法）: get_folders, create_folder, get_folder_info, delete_folder
- Wiki 操作 API（5 个方法）: get_wiki_node_list, resolve_wiki_path, create_wiki_node, delete_wiki_node, get_wiki_space_list
- Bitable 操作 API（6 个方法）: create_bitable_app, create_bitable_table, add_record, get_records, update_record, delete_record
- 图片操作 API（2 个方法）: upload_image_block
- 并行上传 API（2 个方法）: batch_create_blocks_parallel, upload_images_parallel

**性能优化**：
- 批处理自动分批（50 blocks/批）
- 并行上传（5-10x 速度提升）
- 连接池优化
- 线程安全 Token

### Module: FeishuMdUploader
**Path**: `lib/feishu_md_uploader.py`
**Purpose**: Markdown 到飞书 block 格式转换

**支持元素**：
- 标题（h1-h6）
- 段落/文本样式
- 代码块（50+ 语言）
- 列表（有序/无序）
- 图片（本地/网络）
- 表格（飞书表格）
- 数学公式
- Mermaid 图表

---

## 🔧 Configuration

**依赖管理**：`pyproject.toml`

**核心依赖**：
- `markdown-it-py >= 3.0.0` - Markdown 解析器
- `mdit-py-plugins >= 0.4.0` - Markdown 插件
- `requests >= 2.28.0` - HTTP 客户端
- `python-dotenv >= 1.0.0` - 环境变量管理

**开发依赖**：
- `pytest >= 7.0.0` - 测试框架
- `pytest-cov >= 4.0.0` - 覆盖率
- `black >= 23.0.0` - 代码格式化
- `mypy >= 1.0.0` - 类型检查

**环境变量**：
```bash
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_DEFAULT_FOLDER=fldcnxxxxx    # 可选
FEISHU_DEFAULT_WIKI_SPACE=123456    # 可选
```

---

## 📚 Documentation

### 用户文档（user/）
- `QUICK_START.md` - 快速开始指南（10 分钟）
- `DOWNLOAD_GUIDE.md` - 下载功能完整指南（15 分钟）
- `BATCH_OPERATIONS.md` - 批量操作指南（15 分钟）
- `BITABLE_OPERATIONS.md` - Bitable 操作指南（10 分钟）
- `API_OPERATIONS.md` - API 完整参考（20 分钟）
- `PERFORMANCE_OPTIMIZATION.md` - 性能优化指南（15 分钟）
- `TROUBLESHOOTING.md` - 故障排除指南（10 分钟）

### 专题指南（guides/）
- `DOWNLOAD_REFERENCE.md` - 下载功能技术参考（20 分钟）
- `LIST_WIKI_TREE_GUIDE.md` - Wiki 结构预览工具详解（15 分钟）

### 设计文档（design/）
- `DESIGN.md` - 系统架构设计（30 分钟）
- `DIRECT_API_MODE.md` - 直连 API 模式（10 分钟）
- `FEISHU_MCP_INTEGRATION.md` - MCP 集成说明（15 分钟）
- `UNIFIED_WIKI_PATH_SEMANTICS.md` - 参数语义统一（10 分钟）
- `FEATURE_GAPS.md` - 功能限制说明（10 分钟）

### 文档中心
- `docs/INDEX.md` - 文档导航索引

---

## 🧪 Test Coverage

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/test_md_to_feishu.py -v

# 测试覆盖率
uv run pytest --cov=scripts --cov=lib tests/
```

---

## 📝 Quick Start

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境变量
```bash
export FEISHU_APP_ID="cli_xxxxx"
export FEISHU_APP_SECRET="xxxxx"
```

### 3. 测试 API 连接
```bash
uv run python scripts/test_api_connectivity.py
```

### 4. 上传第一个文档
```bash
uv run python scripts/create_feishu_doc.py README.md
```

---

## 🚀 快速命令参考

### 上传操作
```bash
# 创建单个文档
uv run python scripts/create_feishu_doc.py file.md

# 批量上传
uv run python scripts/batch_create_docs.py ./docs

# 创建 Wiki 文档
uv run python scripts/create_wiki_doc.py file.md --space-name "产品文档"

# 批量创建 Wiki
uv run python scripts/batch_create_wiki_docs.py ./docs --space-name "产品文档"
```

### 下载操作
```bash
# 按路径下载
uv run python scripts/download_doc.py -s "空间" -p "/路径" output.md

# 按名称下载
uv run python scripts/download_doc.py -s "空间" -n "文档名" output.md

# 批量下载 Wiki
uv run python scripts/download_wiki.py --personal ./backup
```

### 查看操作
```bash
# 预览 Wiki 结构
uv run python scripts/list_wiki_tree.py --personal

# 限制深度
uv run python scripts/list_wiki_tree.py -s "空间" -d 2

# 从指定路径开始
uv run python scripts/list_wiki_tree.py -s "空间" -S "/API"
```

---

## 📊 Performance Benchmarks

### 文档上传性能

| 文档大小 | 串行耗时 | 并行耗时 | 性能提升 |
|---------|----------|----------|----------|
| 小型 (<50 blocks) | ~3s | ~2s | 1.5x |
| 中型 (50-200 blocks) | ~30s | ~8s | 3.8x |
| 大型 (200-1000 blocks) | ~180s | ~30s | 6x |
| 超大 (1000+ blocks) | ~600s | ~75s | 8x |

### Wiki 树遍历性能

| Wiki 大小 | 顺序耗时 | 并行（5 workers）| 提升 |
|----------|----------|----------------|------|
| 小型 (<10 节点) | ~1s | ~0.3s | 3x |
| 中型 (10-50 节点) | ~8s | ~2s | 4x |
| 大型 (50-100 节点) | ~30s | ~6s | 5x |
| 超大 (100+ 节点) | ~60s+ | ~10s | 6x+ |

---

## 🔗 Related Projects

### 互补工具
- **[Feishu-MCP](https://github.com/your-username/Feishu-MCP)** - 飞书 MCP 服务器
  - 用于 AI 辅助编辑、智能修改
  - 与本工具互补使用

### 依赖库
- **[markdown-it-py](https://github.com/executablebooks/markdown-it-py)** - Python Markdown 解析器
- **[requests](https://github.com/psf/requests)** - HTTP 客户端

---

## 📜 License

MIT License - 详见 [LICENSE](LICENSE)

---

**最后更新**: 2025-01-18
**版本**: v0.2.1
**状态**: ✅ 生产就绪
