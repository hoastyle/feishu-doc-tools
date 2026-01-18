# Feishu Doc Tools

> **📚 完整文档**: [docs/QUICK_START.md](docs/QUICK_START.md) | **问题排查**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

将本地 Markdown 文件上传至飞书的工具套件，支持批量迁移、Wiki 知识库、多维表格等企业级场景。

---

## ✨ 核心特性

### 🚀 批量操作
- ✅ **批量创建文档** - 一键上传整个文件夹到飞书
- ✅ **批量 Wiki 迁移** - 批量上传到 Wiki 知识库
- ✅ **文档下载/导出** ⭐ - 下载飞书文档为 Markdown（新功能）
- ✅ **批量下载 Wiki** ⭐ - 批量下载知识库文档（新功能）
- ✅ **表格转 Bitable** - Markdown 表格自动转为多维表格
- ✅ **并行上传** - 大文档性能提升 5-10x

### 📖 完整格式支持
- ✅ 标题、段落、列表、代码块
- ✅ 图片（本地/网络）
- ✅ 表格（飞书表格）
- ✅ 数学公式
- ✅ Mermaid 图表（白板块）

### 🎯 灵活部署
- ✅ **零上下文占用** - 不占用 AI 模型 token
- ✅ **直连 API 模式** - 快速、低成本
- ✅ **CLI 工具集** - 多个专用脚本
- ✅ **Python API** - 便于集成

---

## 📊 功能对比：feishu-doc-tools vs Feishu-MCP

| 功能场景 | feishu-doc-tools | Feishu-MCP | 推荐 |
|---------|--------------|------------|------|
| **批量创建文档** | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| **批量上传文件夹** | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| **文档下载/导出** ⭐ | **✅ 原生支持** | **⚠️ 需手动** | **feishu-doc-tools** |
| **批量下载 Wiki** ⭐ | **✅ 原生支持** | **⚠️ 需循环** | **feishu-doc-tools** |
| **表格转 Bitable** | ✅ 专门工具 | ❌ 不支持 | feishu-doc-tools |
| **大文档上传** | ✅ 并行优化 (5-10x) | ⚠️ 较慢 | feishu-doc-tools |
| **AI 辅助编辑** | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| **智能内容修改** | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| **交互式操作** | ❌ CLI 工具 | ✅ 对话式 | Feishu-MCP |

**使用建议**: 两个工具互补使用
- **创建/迁移**: 使用 feishu-doc-tools（本工具）
- **编辑/维护**: 使用 Feishu-MCP

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

---

## 🚀 快速开始

### 安装依赖

```bash
# 安装依赖
uv sync

# 测试 API 连接
uv run python scripts/test_api_connectivity.py
```

### 常见使用场景

#### 场景 1：上传单个文档到云文档

```bash
uv run python scripts/create_feishu_doc.py README.md --title "项目文档"
```

#### 场景 2：批量上传文件夹到云文档

```bash
uv run python scripts/batch_create_docs.py ./docs
```

#### 场景 3：上传到 Wiki 知识库（推荐）

```bash
# 列出可用空间
uv run python scripts/create_wiki_doc.py --list-spaces

# 上传到指定空间
uv run python scripts/create_wiki_doc.py README.md --space-id 74812***88644

# 使用个人知识库（自动检测）
uv run python scripts/create_wiki_doc.py README.md --personal --auto-permission
```

#### 场景 4：批量上传到 Wiki

```bash
# 批量上传到 Wiki 空间
uv run python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644

# 批量上传到个人知识库
uv run python scripts/batch_create_wiki_docs.py ./docs --personal
```

#### 场景 5：Markdown 表格转多维表格

```bash
uv run python scripts/md_table_to_bitable.py data.md --auto-types
```

#### 场景 6：大文档快速上传（性能优化）

```bash
uv run python scripts/md_to_feishu.py 大文档.md --parallel
```

#### 场景 7：下载单个文档为 Markdown ⭐

```bash
# 按名称和路径下载（推荐）
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/REST API" \
  -o api.md

# 按文档 ID 下载
uv run python scripts/download_doc.py doxcnxxxxx output.md
```

#### 场景 8：批量下载 Wiki 知识库 ⭐

```bash
# 下载整个知识库
uv run python scripts/download_wiki.py --space-name "产品文档" ./backup

# 下载指定路径（部分下载）
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API/参考" \
  ./api_docs

# 下载个人知识库
uv run python scripts/download_wiki.py --personal ./my_backup
```

---

## 📁 CLI 工具完整清单

| 工具 | 功能 | 使用场景 |
|------|------|---------|
| `create_feishu_doc.py` | 创建单个云文档 | 快速创建 |
| `batch_create_docs.py` | 批量创建云文档 | 文件夹迁移 |
| `create_wiki_doc.py` | 创建单个 Wiki 文档 | 知识库维护 |
| `batch_create_wiki_docs.py` | 批量创建 Wiki 文档 | 知识库迁移 |
| **`download_doc.py`** ⭐ | **下载单个文档** | **文档备份/导出（新）** |
| **`download_wiki.py`** ⭐ | **批量下载 Wiki** | **知识库备份（新）** |
| `md_table_to_bitable.py` | 表格转 Bitable | 数据管理 |
| `md_to_feishu.py` | 上传到现有文档 | 内容更新 |
| `get_root_info.py` | 获取根信息 | 环境配置 |
| `list_folders.py` | 列出文件夹 | 结构查看 |
| `test_api_connectivity.py` | 测试 API 连接 | 问题诊断 |

---

## 📖 详细文档

| 文档 | 说明 |
|------|------|
| [docs/INDEX.md](docs/INDEX.md) | **📚 文档中心**（导航索引） |
| [docs/BATCH_OPERATIONS.md](docs/BATCH_OPERATIONS.md) | 批量操作完整指南 |
| [docs/BITABLE_OPERATIONS.md](docs/BITABLE_OPERATIONS.md) | Bitable 操作指南 |
| [docs/PERFORMANCE_OPTIMIZATION.md](docs/PERFORMANCE_OPTIMIZATION.md) | 性能优化指南 |
| [docs/API_OPERATIONS.md](docs/API_OPERATIONS.md) | API 完整参考 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 故障排除指南 |

## 支持的Markdown元素

| Markdown | 飞书Block | 说明 |
|----------|----------|------|
| `# Heading` | heading1-9 | 支持h1-h9 |
| 段落 | text | 支持粗体、斜体、代码等 |
| ` ```code``` ` | code | 自动识别语言 |
| `- 列表` | list | 有序/无序列表 |
| `![img](url)` | image | 本地/网络图片 |
| 表格 | table | 完整表格支持 |
| - | board | Whiteboard/画板（仅API支持）|

---

## 📂 项目结构

```
feishu-doc-tools/
├── scripts/                       # CLI 工具集
│   ├── md_to_feishu.py            # 核心转换脚本
│   ├── md_to_feishu_upload.py     # 统一上传脚本
│   ├── create_feishu_doc.py      # 创建云文档
│   ├── batch_create_docs.py      # 批量创建云文档
│   ├── create_wiki_doc.py         # 创建 Wiki 文档
│   ├── batch_create_wiki_docs.py  # 批量创建 Wiki 文档（新）
│   ├── md_table_to_bitable.py     # 表格转 Bitable（新）
│   ├── get_root_info.py           # 获取工作区信息
│   ├── list_folders.py            # 列出文件夹
│   └── test_api_connectivity.py  # API 测试
├── lib/
│   └── feishu_api_client.py      # 直连 API 客户端
│       ├── 文档操作 API (3)
│       ├── 文件夹操作 API (4)
│       ├── Wiki 操作 API (5)
│       ├── Bitable 操作 API (6)
│       ├── 图片操作 API (2)
│       └── 并行上传 API (2)
├── tests/
│   ├── test_md_to_feishu.py       # 转换测试
│   ├── test_feishu_api_extended.py  # API 测试
│   ├── test_table_to_bitable.py   # Bitable 测试（新）
│   └── test_performance.py        # 性能测试（新）
├── docs/                         # 完整文档
│   ├── INDEX.md                   # 文档中心（新）
│   ├── API_OPERATIONS.md
│   ├── BATCH_OPERATIONS.md
│   ├── BITABLE_OPERATIONS.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   ├── DESIGN.md
│   └── TROUBLESHOOTING.md
└── README.md                     # 本文件
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

---

## 🎯 开发状态

### Phase 1: 上传模式 ✅ 完成
- [x] 核心转换脚本
- [x] 工具类封装
- [x] 单元测试
- [x] 使用文档
- [x] uv 环境配置

### Phase 2: 创建和迁移模式 ✅ 完成
- [x] 文档创建 API
- [x] 文件夹管理 API
- [x] 单文档创建脚本
- [x] 批量创建脚本
- [x] API 参考文档
- [x] 批量操作指南

### Phase 3: Wiki 知识库 ✅ 完成
- [x] Wiki 空间 API
- [x] Wiki 节点 API
- [x] 个人知识库自动检测
- [x] 用户权限自动设置
- [x] Wiki 文档创建脚本
- [x] 批量 Wiki 上传脚本（新）

### Phase 4: Bitable 多维表格 ✅ 完成
- [x] Bitable 操作 API（6 个方法）
- [x] 字段类型常量（12 种类型）
- [x] 表格转 Bitable 脚本
- [x] 自动字段类型推断
- [x] Bitable 操作指南

### Phase 5: 性能优化 ✅ 完成
- [x] 并行批处理上传（5-10x 提升）
- [x] 并行图片上传（3-5x 提升）
- [x] 连接池优化
- [x] 线程安全 Token
- [x] 性能基准测试
- [x] 性能优化指南

---

## 📈 项目状态

### 功能完整度

**✅ 生产就绪** - 所有核心功能已完成并测试通过

**测试覆盖**:
```bash
# 新增测试
- TestBitableOperations: 15 个测试
- test_table_to_bitable.py: 10 个测试
- test_performance.py: 性能基准测试

# 总计: 40+ 个测试用例
```

### 支持的 Markdown 元素

| 元素 | 支持状态 | 说明 |
|------|---------|------|
| 标题 (h1-h6) | ✅ | 完整支持 |
| 段落/文本样式 | ✅ | 粗体、斜体、代码、删除线 |
| 代码块 | ✅ | 50+ 语言语法高亮 |
| 列表 | ✅ | 有序/无序 |
| 图片 | ✅ | 本地/网络图片 |
| 表格 | ✅ | 飞书表格 |
| 数学公式 | ✅ | LaTeX 格式 |
| Mermaid 图表 | ✅ | 白板块 |
| 引用块 | ✅ | 完整支持 |

### 性能指标

| 文档大小 | 串行耗时 | 并行耗时 | 提升 |
|---------|---------|---------|------|
| 小型 (<50 blocks) | ~3s | ~2s | 1.5x |
| 中型 (50-200) | ~30s | ~8s | 3.8x |
| 大型 (200-1000) | ~180s | ~30s | 6x |
| 超大 (1000+) | ~600s | ~75s | 8x |

---

## 🔗 相关项目

### 互补工具

- **[Feishu-MCP](https://github.com/yourusername/Feishu-MCP)** - 飞书 MCP 服务器
  - 用于 AI 辅助编辑、智能修改
  - 与本工具互补使用

### 依赖库

- **[markdown-it-py](https://github.com/executablebooks/markdown-it-py)** - Python Markdown 解析器
- **[requests](https://github.com/psf/requests)** - HTTP 客户端

---

## 📜 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范

- 遵循现有代码风格
- 添加测试覆盖新功能
- 更新相关文档

---

## 📞 获取帮助

- 📚 [文档中心](docs/INDEX.md)
- 🐛 [故障排除](docs/TROUBLESHOOTING.md)
- 💬 提交 [Issue](https://github.com/your-repo/issues)

---

**最后更新**: 2025-01-18
**版本**: v2.0
