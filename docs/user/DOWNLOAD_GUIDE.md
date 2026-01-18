# 下载功能完整指南

**更新日期**: 2026-01-18
**版本**: v0.2.1 (新增 Wiki 结构预览)
**用途**: 面向终端用户的完整下载功能指南

---

## 📋 目录

- [概述](#概述)
- [Wiki 结构预览 (list_wiki_tree.py)](#wiki-结构预览-list_wiki_treepy)
- [单文档下载 (download_doc.py)](#单文档下载-download_docpy)
- [批量下载 (download_wiki.py)](#批量下载-download_wikipy)
- [常见场景](#常见场景)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 概述

feishu-doc-tools 提供了三个强大的 Wiki 工具：

1. **list_wiki_tree.py** - 预览 Wiki 层次结构（不下载内容）
2. **download_doc.py** - 下载单个文档
3. **download_wiki.py** - 批量下载 Wiki 空间

所有工具都支持**按名称和路径定位**，完全**对称于上传功能**的体验。

### 核心优势

- ✅ **对称设计**: 上传和下载使用相同的定位方式
- ✅ **灵活定位**: 支持 ID、名称、路径三种方式
- ✅ **结构预览**: 快速查看 Wiki 层次结构
- ✅ **部分下载**: 支持指定起始路径和递归控制
- ✅ **用户友好**: 无需手动查找文档 ID
- ✅ **错误清晰**: 提供详细的错误提示和建议

---

## Wiki 结构预览 (list_wiki_tree.py)

**用途**: 快速预览 Wiki 空间的层次结构，不下载任何内容

### 基本用法

```bash
# 查看个人知识库
uv run python scripts/list_wiki_tree.py --personal

# 查看指定空间
uv run python scripts/list_wiki_tree.py -s "产品文档"

# 限制深度
uv run python scripts/list_wiki_tree.py -s "产品文档" -d 2

# 从指定路径开始
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API"
```

### 输出示例

```
📚 Wiki Space: 产品文档

🌳 Tree Structure:
============================================================
📂 首页
📂 项目
    ├── 📄 项目流程
    └── 📄 标书确认
📂 API文档
    ├── 📄 REST API
    └── 📄 GraphQL API
============================================================

📊 Total Nodes (shown): 6
```

### 图标说明

- 📂 **目录** - 包含子节点
- 📄 **文档** - 叶子节点（无子节点）

### 主要参数

| 参数 | 短选项 | 说明 | 示例 |
|------|--------|------|------|
| `--space-name` | `-s` | Wiki 空间名称 | `-s "产品文档"` |
| `--space-id` | - | Wiki 空间 ID | `--space-id 748***` |
| `--personal` | `-P` | 个人知识库 | `-P` |
| `--start-path` | `-S` | 起始路径 | `-S "/API"` |
| `--depth` | `-d` | 深度控制 | `-d 2` |
| `--debug` | - | 调试模式 | `--debug` |

### 使用场景

1. **下载前预览** - 确认内容结构后再下载
2. **快速查找** - 定位文档的完整路径
3. **结构分析** - 了解 Wiki 的组织方式
4. **零开销** - 不占用存储空间，快速响应

**详细指南**: [LIST_WIKI_TREE_GUIDE.md](../guides/LIST_WIKI_TREE_GUIDE.md)

---

## 单文档下载 (download_doc.py)

### 方法一：直接使用文档 ID（原有方法）

```bash
uv run python scripts/download_doc.py <doc_id> <output_file>
```

**示例**：
```bash
# 下载文档到 output.md
uv run python scripts/download_doc.py doxcnRl4G0HhekLFjfvcPnabcdef output.md
```

**适用场景**：
- 你已经知道文档 ID
- 快速下载单个文档

---

### 方法二：按空间名称 + 路径定位（推荐）

```bash
uv run python scripts/download_doc.py \
  --space-name "知识库名称" \
  --wiki-path "/层级/路径/文档名" \
  -o <output_file>
```

**示例**：
```bash
# 下载指定路径的文档
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/参考/REST API" \
  -o rest_api.md

# 自动生成文件名（从文档标题）
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/参考/REST API"
# 输出: REST_API.md
```

**适用场景**：
- 你知道文档在知识库中的完整路径
- 需要精确定位文档
- 与上传操作对称（同样的路径）

---

### 方法三：按空间名称 + 文档名搜索（便捷）⭐

```bash
uv run python scripts/download_doc.py \
  --space-name "知识库名称" \
  --doc-name "文档名" \
  [-o <output_file>]
```

**功能特点**：
- 🔍 **递归搜索** - 搜索整个 Wiki 空间
- 🎯 **交互选择** - 找到多个时提示用户选择
- ⚡ **快速查找** - 无需知道完整路径

#### 示例 1：单个匹配

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "API Overview" \
  -o api_overview.md
```

**何时使用**：文档名称唯一

#### 示例 2：多个匹配（交互选择）

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "README"
```

**输出**：
```
Found 3 documents named 'README':

  [1] /README
      Type: doc, Has children: False
  [2] /API/README
      Type: doc, Has children: True
  [3] /SDK/Python/README
      Type: doc, Has children: False

Please select a document:
Enter number (1-3): 2
```

**何时使用**：多个文档同名，需要选择

#### 示例 3：自动生成文件名

```bash
uv run python scripts/download_doc.py \
  --space-name "Engineering" \
  --doc-name "Architecture Diagram"
# 输出: Architecture_Diagram.md
```

#### 示例 4：详细日志

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "Getting Started" \
  -v \
  -o getting_started.md
```

显示搜索进度和详细信息。

#### 使用场景对比

| 场景 | 使用 `--doc-name` | 使用 `--wiki-path` |
|------|------------------|-------------------|
| 不知道完整路径 | ✅ | ❌ |
| 自动化脚本 | ❌ | ✅ |
| 快速执行 | ⚠️ | ✅ |
| 确定性行为 | ❌ | ✅ |
| 交互式选择 | ✅ | ❌ |

---

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `doc_id` | 文档 ID | 方法一必需 |
| `output` | 输出文件路径 | 方法一必需 |
| `--space-name` | 知识库名称 | 方法二/三必需 |
| `--wiki-path` | 完整路径 | 方法二必需 |
| `--doc-name` | 文档名称（递归搜索）| 方法三必需 |
| `-o, --output-file` | 输出文件 | 方法二/三可选 |
| `--app-id` | 应用 ID | 可选 |
| `--app-secret` | 应用密钥 | 可选 |
| `-v, --verbose` | 详细日志 | 可选 |

---

## 批量下载 (download_wiki.py)

### 方法一：下载整个知识库

```bash
uv run python scripts/download_wiki.py \
  --space-name "知识库名称" \
  <output_dir>
```

**示例**：
```bash
# 下载整个产品文档知识库
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  ./output

# 下载个人知识库
uv run python scripts/download_wiki.py \
  --personal \
  ./my_docs
```

**适用场景**：
- 完整备份知识库
- 初次迁移文档
- 需要所有文档

---

### 方法二：从指定路径开始递归下载（推荐）

```bash
uv run python scripts/download_wiki.py \
  --space-name "知识库名称" \
  --start-path "/起始/路径" \
  <output_dir>
```

**示例**：
```bash
# 只下载 API 文档部分（包含所有子文档）
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API/参考" \
  ./api_docs

# 从特定层级开始
uv run python scripts/download_wiki.py \
  --space-name "开发文档" \
  --start-path "/后端/数据库" \
  ./database_docs
```

**适用场景**：
- 只需要特定模块的文档
- 避免下载整个大型知识库
- 部分备份

---

### 方法三：仅下载直接子文档（非递归）

```bash
uv run python scripts/download_wiki.py \
  --space-name "知识库名称" \
  --start-path "/路径" \
  --no-recursive \
  <output_dir>
```

**示例**：
```bash
# 只下载 API 目录下的直接子文档，不递归子目录
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API" \
  --no-recursive \
  ./api_direct

# 下载根目录的文档（不含子目录）
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --no-recursive \
  ./root_docs
```

**适用场景**：
- 只需要某一层级的文档
- 避免递归下载大量子文档
- 快速查看某个目录的内容

---

### 方法四：使用 Token（传统方法）

```bash
# 按 Space ID
uv run python scripts/download_wiki.py \
  --space-id <space_id> \
  <output_dir>

# 按 Space ID + Parent Token
uv run python scripts/download_wiki.py \
  --space-id <space_id> \
  --parent-token <node_token> \
  <output_dir>
```

**适用场景**：
- 你已经有 ID 和 Token
- 自动化脚本
- 向后兼容

---

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `output_dir` | 输出目录 | 是 |
| `--space-name` | 知识库名称 | 推荐 |
| `--space-id` | 知识库 ID | 或 |
| `--personal` | 个人知识库 | 或 |
| `--start-path` | 起始路径 | 可选 |
| `--parent-token` | 起始节点 Token | 可选 |
| `--no-recursive` | 禁用递归 | 可选 |
| `--app-id` | 应用 ID | 可选 |
| `--app-secret` | 应用密钥 | 可选 |
| `-v, --verbose` | 详细日志 | 可选 |

---

## 常见场景

### 场景 1：备份整个个人知识库

```bash
uv run python scripts/download_wiki.py \
  --personal \
  ./backup/my_library
```

---

### 场景 2：下载特定项目的 API 文档

```bash
uv run python scripts/download_wiki.py \
  --space-name "项目 A 文档" \
  --start-path "/技术文档/API" \
  ./project_a_api
```

---

### 场景 3：下载单个重要文档（知道路径）

```bash
uv run python scripts/download_doc.py \
  --space-name "架构设计" \
  --wiki-path "/核心系统/微服务架构设计" \
  -o microservices.md
```

---

### 场景 4：下载单个文档（不知道完整路径）⭐

```bash
# 先用名称搜索找到文档
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "Onboarding Guide"

# 如果有多个，交互选择
# 如果只有一个，直接下载
```

---

### 场景 5：查看某个目录有哪些文档（不递归）

```bash
uv run python scripts/download_wiki.py \
  --space-name "产品手册" \
  --start-path "/用户指南" \
  --no-recursive \
  ./preview
```

---

### 场景 6：预览后下载（推荐工作流）

```bash
# 1. 先预览结构
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API"

# 2. 确认后下载
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API" \
  ./api_docs
```

---

### 场景 7：按相同路径下载后再上传（对称操作）

```bash
# 1. 下载
uv run python scripts/download_doc.py \
  --space-name "源知识库" \
  --wiki-path "/API/REST API" \
  -o api.md

# 2. 编辑 api.md

# 3. 上传到相同路径
uv run python scripts/create_wiki_doc.py api.md \
  --space-name "源知识库" \
  --wiki-path "/API"
```

---

## 错误处理

### 错误 1：知识库不存在

```
ValueError: Wiki space not found: 产品文档
```

**解决方法**：
1. 检查知识库名称拼写
2. 确认你有访问权限
3. 使用 `get_root_info.py` 查看可用知识库

```bash
uv run python scripts/get_root_info.py
```

---

### 错误 2：路径不存在

```
FeishuApiRequestError: 路径不存在: '/API/参考/不存在'
在节点 'API/参考' 下找不到 '不存在'
```

**解决方法**：
1. 检查路径拼写
2. 确认路径是否正确
3. 使用 `list_wiki_tree.py` 查看层级结构

```bash
uv run python scripts/list_wiki_tree.py -s "产品文档"
```

---

### 错误 3：文档未找到（使用 --doc-name）

```
ERROR: Document not found: MyDoc
Searched entire wiki space 'MySpace'
```

**解决方法**：
- 检查文档名称拼写（区分大小写）
- 确认在正确的空间搜索
- 使用 Wiki 网页界面确认文档存在
- 尝试使用 `--wiki-path` 如果知道路径

---

### 错误 4：找到多个同名文档（自动化场景）

```
WARNING: Found 3 documents with name 'API', using first one
```

**解决方法**：
使用 `--wiki-path` 指定完整路径而不是 `--doc-name`

```bash
# 而不是交互式选择
uv run python scripts/download_doc.py \
  --space-name "Docs" \
  --wiki-path "/API/REST API"  # 精确路径
```

---

### 错误 5：节点不是文档

```
ValueError: Node 'API 目录' is not a document (type: unknown)
```

**解决方法**：
该节点是目录而不是文档，使用 `download_wiki.py` 下载其子文档

---

### 错误 6：大空间搜索缓慢

使用 `--wiki-path` 进行更快的直接访问：

```bash
# 而不是在大型 Wiki 中搜索
uv run python scripts/download_doc.py \
  --space-name "Large Wiki" \
  --wiki-path "/Section/Subsection/Document"
```

---

## 最佳实践

### 1. 推荐工作流：预览 → 下载

```bash
# Step 1: 预览结构
uv run python scripts/list_wiki_tree.py -s "产品文档"

# Step 2: 确认后下载
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API" \
  ./api_docs
```

---

### 2. 优先使用名称和路径

❌ **不推荐**：
```bash
# 需要手动查找 ID
uv run python scripts/download_doc.py doxcnxxxxx output.md
```

✅ **推荐**：
```bash
# 直观清晰
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/REST API" \
  -o output.md
```

---

### 3. 使用 --start-path 而不是 --parent-token

❌ **不推荐**：
```bash
uv run python scripts/download_wiki.py \
  --space-id 74812***88644 \
  --parent-token nodcnxxxxx \
  ./output
```

✅ **推荐**：
```bash
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API/参考" \
  ./output
```

---

### 4. 合理使用递归控制

- **需要所有子文档**：默认递归（不指定 `--no-recursive`）
- **只需要某一层**：使用 `--no-recursive`
- **预览目录内容**：使用 `list_wiki_tree.py` 快速查看

---

### 5. 保持对称性

上传和下载使用相同的路径参数：

```bash
# 上传
uv run python scripts/create_wiki_doc.py document.md \
  --space-name "知识库" \
  --wiki-path "/目录"

# 下载（对称）
uv run python scripts/download_doc.py \
  --space-name "知识库" \
  --wiki-path "/目录/document" \
  -o document.md
```

---

### 6. 使用详细日志排查问题

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/REST API" \
  -o output.md \
  -v
```

详细日志会显示：
- 查找知识库的过程
- 路径解析的每一步
- 文档下载的进度

---

### 7. 单文档下载：先用 --doc-name 探索，后用 --wiki-path

```bash
# Step 1: 探索和发现
uv run python scripts/download_doc.py \
  --space-name "Project Docs" \
  --doc-name "Installation"

# Step 2: 确认路径后使用精确路径
uv run python scripts/download_doc.py \
  --space-name "Project Docs" \
  --wiki-path "/Setup/Installation"
```

---

## 对比表：上传 vs 下载

| 操作 | 上传 | 下载 |
|------|------|------|
| **单文档** | `create_wiki_doc.py` | `download_doc.py` |
| **批量** | `batch_create_wiki_docs.py` | `download_wiki.py` |
| **结构预览** | N/A | `list_wiki_tree.py` |
| **按名称** | `--space-name` | `--space-name` ✅ |
| **按路径** | `--wiki-path` | `--wiki-path` ✅ |
| **递归** | 自动 | `--recursive` (默认) ✅ |
| **非递归** | N/A | `--no-recursive` ✅ |

---

## 工具选择指南

**只想查看结构？** → 用 `list_wiki_tree.py` ⭐ **不下载内容**
**需要 1 个文档？** → 用 `download_doc.py`
**需要多个文档？** → 用 `download_wiki.py`

### 详细对比

| 维度 | list_wiki_tree | download_doc | download_wiki |
|------|---------------|-------------|---------------|
| **操作对象** | Wiki空间/目录（只读） | 单个文档 | Wiki空间/目录 |
| **输出形式** | 终端树形显示 | 单个Markdown文件 | Markdown文件目录 |
| **操作粒度** | 结构查看 | 精确定位 | 批量处理 |
| **下载内容** | ❌ 不下载 | ✅ 下载单个 | ✅ 批量下载 |
| **递归搜索** | ❌ 不支持 | ✅ 支持（-n参数） | ❌ 不支持 |
| **深度控制** | ✅ 支持（-d参数） | ❌ 不支持 | ✅ 支持（-d参数） |
| **目录结构** | ✅ 树形显示 | N/A | ✅ 自动保持 |
| **交互式选择** | ❌ 不支持 | ✅ 支持 | ❌ 不支持 |
| **文件名控制** | N/A | ✅ 精确控制 | ⚠️ 自动生成 |
| **批量处理** | N/A | ❌ 单个 | ✅ 批量 |
| **部分操作** | ✅ 支持（-S参数） | ❌ 不支持 | ✅ 支持（-S参数） |
| **速度** | ⚡ 最快（不下载） | 🚀 快 | 📦 较慢 |
| **存储占用** | ❌ 零占用 | ✅ 单文件 | ⚠️ 多文件 |

---

## 相关文档

- **快速开始**: [QUICK_START.md](QUICK_START.md)
- **详细技术参考**: [../guides/DOWNLOAD_REFERENCE.md](../guides/DOWNLOAD_REFERENCE.md)
- **list_wiki_tree 详细指南**: [../guides/LIST_WIKI_TREE_GUIDE.md](../guides/LIST_WIKI_TREE_GUIDE.md)
- **API 操作**: [API_OPERATIONS.md](API_OPERATIONS.md)
- **批量操作**: [BATCH_OPERATIONS.md](BATCH_OPERATIONS.md)
- **故障排查**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 总结

### 新增功能 (v0.2.1)

1. ✅ **list_wiki_tree.py** - Wiki 结构预览工具
2. ✅ **download_doc.py** 递归搜索（`--doc-name`）
3. ✅ **download_doc.py** 交互式多文档选择
4. ✅ **download_wiki.py** 支持 `--start-path`
5. ✅ **download_wiki.py** 支持 `--no-recursive`
6. ✅ 自动文件名生成（从文档标题）
7. ✅ 完整的错误提示和建议

### 核心优势

- 🎯 **对称设计**: 下载和上传使用相同的参数
- 🚀 **用户友好**: 无需手动查找 ID
- 🔍 **灵活定位**: 支持多种定位方式
- ⚡ **部分下载**: 支持指定起始点和递归控制
- 🌳 **结构预览**: 零开销快速查看层次结构

---

**版本历史**：
- v0.2.1 (2026-01-18) - 新增 Wiki 结构预览和递归搜索
- v0.2.0 (2026-01-18) - 用户体验改进
- v0.1.0 (2026-01-18) - 初始版本
