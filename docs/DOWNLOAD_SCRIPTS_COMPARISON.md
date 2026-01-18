# download_doc vs download_wiki vs list_wiki_tree 详细对比

**创建日期**: 2026-01-18
**版本**: v0.2.1
**用途**: 帮助用户选择合适的工具

---

## 📋 快速决策指南

**只想查看结构？** → 用 `list_wiki_tree.py` ⭐ **不下载内容**
**只需要1个文档？** → 用 `download_doc.py`
**需要多个文档或备份？** → 用 `download_wiki.py`

---

## 🎯 核心定位区别

### list_wiki_tree.py - Wiki结构预览工具 🌳 **（新增）**

**核心定位**: **树形显示 Wiki 层次结构**，不下载任何内容，仅查看结构

**关键特性**:
- ✅ 树形显示完整层次结构
- ✅ 区分目录（📂）和文档（📄）
- ✅ 支持深度控制（-d参数）
- ✅ 支持指定起始路径（-S参数）
- ✅ 快速预览，不占用存储空间

### download_doc.py - 单文档精确下载工具 📄

**核心定位**: 精确下载**单个文档**，适合有明确目标的场景

**关键特性**:
- ✅ 精确定位单个文档
- ✅ 支持递归搜索（独有功能）
- ✅ 交互式多文档选择
- ✅ 灵活的文件名控制

### download_wiki.py - 批量Wiki下载工具 📚

**核心定位**: 批量下载**整个Wiki空间或指定目录**，适合知识库备份和迁移

**关键特性**:
- ✅ 批量下载大量文档
- ✅ 保持目录结构
- ✅ 灵活的深度控制
- ✅ 部分目录下载

---

## 📊 详细功能对比表

| 维度 | list_wiki_tree | download_doc | download_wiki | 胜出 |
|------|---------------|-------------|---------------|------|
| **操作对象** | Wiki空间/目录（只读） | 单个文档 | Wiki空间/目录 | - |
| **输出形式** | 终端树形显示 | 单个Markdown文件 | Markdown文件目录 | - |
| **操作粒度** | 结构查看 | 精确定位 | 批量处理 | - |
| **下载内容** | ❌ 不下载 | ✅ 下载单个 | ✅ 批量下载 | - |
| **递归搜索** | ❌ 不支持 | ✅ 支持（-n参数） | ❌ 不支持 | download_doc |
| **深度控制** | ✅ 支持（-d参数） | ❌ 不支持 | ✅ 支持（-d参数） | list_wiki_tree/download_wiki |
| **目录结构** | ✅ 树形显示 | ❌ 不保持 | ✅ 自动保持 | - |
| **交互式选择** | ❌ 不支持 | ✅ 支持 | ❌ 不支持 | download_doc |
| **文件名控制** | N/A | ✅ 精确控制 | ⚠️ 自动生成 | download_doc |
| **批量处理** | N/A | ❌ 单个 | ✅ 批量 | download_wiki |
| **部分操作** | ✅ 支持（-S参数） | ❌ 不支持 | ✅ 支持（-S参数） | list_wiki_tree/download_wiki |
| **速度** | ⚡ 最快（不下载） | 🚀 快 | 📦 较慢 | list_wiki_tree |
| **存储占用** | ❌ 零占用 | ✅ 单文件 | ⚠️ 多文件 | list_wiki_tree |

---

## 🔍 参数设计对比

### download_doc 参数结构

```bash
# 方法1：直接ID（最原始）
download_doc.py <doc_id> <output>

# 方法2：路径定位（推荐）
download_doc.py -s "空间名" -p "/完整/路径" [-o output]

# 方法3：名称搜索（便捷，独有功能）
download_doc.py -s "空间名" -n "文档名" [-o output]
```

**核心参数**:
| 参数 | 短选项 | 说明 | 示例 |
|------|--------|------|------|
| `--space-name` | `-s` | Wiki空间名 | `-s "产品文档"` |
| `--wiki-path` | `-p` | 父路径 + 文档名 | `-p "/API/REST API"` |
| `--doc-name` | `-n` | 文档名（递归搜索） | `-n "API设计"` |
| `--output-file` | `-o` | 输出文件路径 | `-o api.md` |
| `doc_id` | - | 文档ID（位置参数） | `doxcnxxxxx` |

### download_wiki 参数结构

```bash
# 基础用法
download_wiki.py <output_dir>

# 指定空间
download_wiki.py -s "空间名" <output_dir>

# 指定起始路径（部分下载）
download_wiki.py -s "空间名" -S "/起始/路径" <output_dir>

# 控制深度（新增于v0.2.1）
download_wiki.py -s "空间名" -d 2 <output_dir>  # 只下载2层
```

**核心参数**:
| 参数 | 短选项 | 说明 | 示例 |
|------|--------|------|------|
| `--space-name` | `-s` | Wiki空间名 | `-s "产品文档"` |
| `--personal` | `-P` | 个人知识库 | `-P` |
| `--start-path` | `-S` | 起始路径 | `-S "/API"` |
| `--depth` | `-d` | 深度控制 | `-d 2` |
| `output_dir` | - | 输出目录（必需） | `./backup` |

### list_wiki_tree 参数结构 **（新增）**

```bash
# 查看完整结构
list_wiki_tree.py -s "空间名"

# 控制深度
list_wiki_tree.py -s "空间名" -d 2  # 只显示2层

# 指定起始路径
list_wiki_tree.py -s "空间名" -S "/API"

# 查看个人知识库
list_wiki_tree.py --personal
```

**核心参数**:
| 参数 | 短选项 | 说明 | 示例 |
|------|--------|------|------|
| `--space-name` | `-s` | Wiki空间名 | `-s "产品文档"` |
| `--space-id` | - | Wiki空间ID | `--space-id 748***` |
| `--personal` | `-P` | 个人知识库 | `-P` |
| `--start-path` | `-S` | 起始路径 | `-S "/API"` |
| `--depth` | `-d` | 深度控制 | `-d 2` |
| `--debug` | - | 调试模式 | `--debug` |

---

## 🎯 使用场景矩阵

### 场景 0: 预览 Wiki 层次结构 **（新增）**

**需求**: 快速查看 Wiki 空间的目录结构，不下载内容

**list_wiki_tree** ✅ **唯一选择**
```bash
list_wiki_tree.py -s "产品文档"
```

**输出示例**:
```
📂 产品文档
├── 📂 API
│   ├── 📄 REST API
│   └── 📄 GraphQL API
└── 📄 README
```

**特性**:
- 树形显示完整结构
- 区分目录（📂）和文档（📄）
- 不占用存储空间
- 速度最快（不下载内容）

**download_doc/download_wiki** ❌ **不适合**
- 会下载内容，占用空间和时间

---

### 场景 1: 下载单个已知文档

**需求**: 只需要某个特定的API文档

**download_doc** ✅ **最佳选择**
```bash
download_doc.py -s "产品文档" -p "/API/REST" -o rest_api.md
```
- 精确快速
- 输出可控
- 效率最高

**download_wiki** ❌ **不适合**
- 会下载整个目录
- 效率低
- 资源浪费

---

### 场景 2: 递归搜索文档

**需求**: 知道文档名但不知道完整路径

**download_doc** ✅ **独有功能**
```bash
# 搜索整个Wiki空间
download_doc.py -s "产品文档" -n "API文档" -o api.md
```

**特性**:
- 深度优先搜索整个空间
- 找到多个同名文档时交互式选择
- 显示完整路径便于识别

**交互式选择示例**:
```
Found 3 documents named 'README':

  [1] /README
      Type: doc, Has children: False
  [2] /API/README
      Type: doc, Has children: True
  [3] /SDK/Python/README
      Type: doc, Has children: False

Please select a document:
Enter number (1-3):
```

**download_wiki** ❌ **不支持**
- 没有递归搜索功能
- 必须指定精确路径或ID

---

### 场景 3: 备份整个知识库

**需求**: 定期备份产品文档库

**download_doc** ❌ **不适合**
- 只能单个下载
- 需要编写循环脚本
- 效率极低

**download_wiki** ✅ **最佳选择**
```bash
download_wiki.py -s "产品文档" ./backup/$(date +%Y%m%d)
```

**特性**:
- 递归下载所有文档
- 保持目录结构
- 自动处理文件名冲突
- 适合自动化备份

---

### 场景 4: 部分下载（特定目录）

**需求**: 下载API目录下的所有文档

**download_doc** ⚠️ **可以但繁琐**
```bash
# 需要多次执行，效率低
download_doc.py -s "文档" -p "/API/REST" -o 01_rest.md
download_doc.py -s "文档" -p "/API/GraphQL" -o 02_graphql.md
download_doc.py -s "文档" -p "/API/WebSocket" -o 03_websocket.md
```

**download_wiki** ✅ **最佳选择**
```bash
# 一次性下载整个目录
download_wiki.py -s "文档" -S "/API" ./api_backup
```

---

### 场景 5: 预览目录结构

**需求**: 快速查看某个目录下有哪些文档

**download_doc** ❌ **不支持**

**download_wiki** ✅ **支持（-d 0）**
```bash
download_wiki.py -s "产品文档" -S "/API" -d 0 ./preview
```

**特性**:
- 只下载直接子节点
- 不递归下载子目录
- 快速了解目录结构

---

### 场景 6: 控制下载深度

**需求**: 只需要下载2层深度的文档

**download_doc** ❌ **不支持**

**download_wiki** ✅ **支持（-d参数）**
```bash
# v0.2.1新增功能
download_wiki.py -s "文档" -d 2 ./output  # 下载2层深度
download_wiki.py -s "文档" -d 1 ./output  # 只下载1层深度
download_wiki.py -s "文档" -d -1 ./output # 无限递归（默认）
```

---

## 🌳 决策树

```
需要下载飞书文档
    │
    ├─ 只需要1个文档？
    │   └─ YES → download_doc.py
    │              │
    │              ├─ 知道完整路径？ → 用 -p 指定路径
    │              └─ 只知道名称？ → 用 -n 递归搜索
    │
    ├─ 需要多个文档？
    │   │
    │   ├─ 这些文档在同一目录下？
    │   │   └─ YES → download_wiki.py
    │   │              │
    │   │              ├─ 需要子目录？ → 默认递归或 -d 2
    │   │              └─ 不需要子目录？ → -d 0
    │   │
    │   └─ 这些文档在不同位置？
    │       │
    │       ├─ 都知道具体路径？
    │       │   └─ YES → download_wiki.py 分批下载
    │       │              或脚本循环调用 download_doc.py
    │       │
    │       └─ 只知道名称？
    │           └─ YES → 手动使用 download_doc.py -n
    │                      （多次执行）
    │
    └─ 需要备份整个Wiki？
        └─ YES → download_wiki.py
                   │
                   ├─ 整个空间？ → 直接指定空间名
                   ├─ 特定分支？ → 用 -S 指定起始路径
                   └─ 个人知识库？ → 用 -P
```

---

## 💡 最佳实践建议

### 什么时候使用 download_doc？

✅ **推荐场景**:
1. 快速获取某个特定文档
2. 文档名已知但路径未知（递归搜索）
3. 需要精确控制输出文件名
4. 单文档的导出/迁移
5. 需要交互式选择同名文档

❌ **不推荐场景**:
1. 需要下载多个相关文档（用download_wiki）
2. 需要备份整个目录（用download_wiki）
3. 需要保持目录结构（用download_wiki）

---

### 什么时候使用 download_wiki？

✅ **推荐场景**:
1. 知识库定期备份
2. 批量迁移文档
3. 下载整个专题目录
4. 部分下载（-S 指定路径）
5. 控制下载深度（-d参数）

❌ **不推荐场景**:
1. 只需要单个文档（用download_doc更快）
2. 需要递归搜索文档名（download_doc独有）
3. 需要精确控制单个文件名（download_doc更好）
4. 只想查看结构（用list_wiki_tree不下载内容）

---

### 什么时候使用 list_wiki_tree？ **（新增）**

✅ **推荐场景**:
1. 快速查看 Wiki 空间结构
2. 下载前预览内容布局
3. 了解目录层次关系
4. 寻找特定文档路径
5. 不想占用存储空间

❌ **不推荐场景**:
1. 需要实际下载内容（用download_doc/download_wiki）
2. 需要文档内容编辑（先下载再编辑）

---

## 🔄 互补关系

三个工具实际上是**互补关系**，而非竞争关系：

### 功能互补矩阵

| 功能 | list_wiki_tree | download_doc | download_wiki | 建议 |
|------|---------------|-------------|---------------|------|
| 结构预览 | ✅ 独有 | ❌ | ⚠️（需下载） | 用list_wiki_tree |
| 单文档精确下载 | ❌ | ✅ | ⚠️ | 用download_doc |
| 递归搜索文档 | ❌ | ✅ | ❌ | 用download_doc |
| 批量下载目录 | ❌ | ❌ | ✅ | 用download_wiki |
| 深度控制 | ✅ | ❌ | ✅ | list_wiki_tree/download_wiki |
| 知识库备份 | ❌ | ❌ | ✅ | 用download_wiki |
| 零存储占用 | ✅ | ❌ | ❌ | 用list_wiki_tree |
| 交互式选择 | ❌ | ✅ | ❌ | 用download_doc |

---

## 🎓 实战组合使用

### 组合1: 备份前先预览 **（优化）**

```bash
# 1. 先用list_wiki_tree预览目录结构（不下载内容）⭐
list_wiki_tree.py -s "产品文档" -S "/API"

# 2. 查看树形结构确认内容

# 3. 再用download_wiki完整下载
download_wiki.py -s "产品文档" -S "/API" ./full_backup
```

**优势**:
- list_wiki_tree 不占用存储空间
- 快速显示完整层次结构
- 确认后再下载，节省时间和带宽

### 组合2: 批量下载特定文档

```bash
# 编写脚本循环调用download_doc
#!/bin/bash
docs=("API设计" "数据库设计" "部署文档")
for doc in "${docs[@]}"; do
  download_doc.py -s "产品文档" -n "$doc" -o "${doc}.md"
done
```

### 组合3: 增量备份策略

```bash
# 1. 使用download_wiki备份整个知识库（每周）
download_wiki.py -s "产品文档" -d 2 ./weekly_backup

# 2. 使用download_doc更新关键文档（每日）
download_doc.py -s "产品文档" -p "/API/核心" -o daily_core.md
```

---

## 📊 参数速查卡

### download_doc 关键参数速查

| 参数 | 短选项 | 必需 | 说明 | 示例 |
|------|--------|------|------|------|
| `doc_id` | - | 方法1 | 文档ID | `doxcnxxxxx` |
| `--space-name` | `-s` | 方法2/3 | Wiki空间名 | `-s "产品文档"` |
| `--wiki-path` | `-p` | 方法2 | 父路径+文档名 | `-p "/API/REST"` |
| `--doc-name` | `-n` | 方法3 | 文档名（递归） | `-n "API设计"` |
| `--output-file` | `-o` | 可选 | 输出文件 | `-o api.md` |
| `--verbose` | `-v` | 否 | 详细日志 | `-v` |

### download_wiki 关键参数速查

| 参数 | 短选项 | 必需 | 说明 | 示例 |
|------|--------|------|------|------|
| `output_dir` | - | 是 | 输出目录 | `./backup` |
| `--space-name` | `-s` | 推荐 | Wiki空间名 | `-s "产品文档"` |
| `--personal` | `-P` | 替代 | 个人知识库 | `-P` |
| `--start-path` | `-S` | 否 | 起始路径 | `-S "/API"` |
| `--depth` | `-d` | 否 | 深度控制 | `-d 2` |
| `--verbose` | `-v` | 否 | 详细日志 | `-v` |

### list_wiki_tree 关键参数速查 **（新增）**

| 参数 | 短选项 | 必需 | 说明 | 示例 |
|------|--------|------|------|------|
| `--space-name` | `-s` | 推荐* | Wiki空间名 | `-s "产品文档"` |
| `--space-id` | - | 替代 | Wiki空间ID | `--space-id 748***` |
| `--personal` | `-P` | 替代 | 个人知识库 | `-P` |
| `--start-path` | `-S` | 否 | 起始路径 | `-S "/API"` |
| `--depth` | `-d` | 否 | 深度控制 | `-d 2` |
| `--debug` | - | 否 | 调试模式 | `--debug` |

*注：需指定空间名、空间ID或使用个人知识库之一

---

## 🎯 总结

### list_wiki_tree = 望远镜 🔭 **（新增）**
- **预览**: 快速查看 Wiki 结构
- **直观**: 树形显示层次关系
- **零占用**: 不下载内容，不占空间
- **独有**: 结构预览专用工具

### download_doc = 狙击枪 🎯
- **精准**: 精确定位单个文档
- **灵活**: 支持路径定位和名称搜索
- **快速**: 单文档下载效率高
- **独有**: 递归搜索和交互式选择

### download_wiki = 渔船 🚢
- **批量大**: 一次下载大量文档
- **可控**: 深度控制和路径过滤
- **结构化**: 保持目录层级
- **高效**: 批量处理性能优

**核心原则**: 选对工具 = 事半功倍！

---

## 📚 相关文档

- [DOWNLOAD_GUIDE.md](DOWNLOAD_GUIDE.md) - 下载功能完整指南
- [DOWNLOAD_EXAMPLES.md](DOWNLOAD_EXAMPLES.md) - 完整使用示例
- [UNIFIED_WIKI_PATH_SEMANTICS.md](UNIFIED_WIKI_PATH_SEMANTICS.md) - 参数语义指南
- [OPTIMIZATION_COMPLETE.md](OPTIMIZATION_COMPLETE.md) - v0.2.1优化报告

---

**最后更新**: 2026-01-18
**版本**: v0.2.1
**状态**: ✅ 生产就绪
