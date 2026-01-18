# feishu-doc-tools 文档中心

> 🎯 **快速导航** | 按使用场景查找功能 | 📚 **完整文档** | 深入了解技术细节

---

## 🚀 快速开始（5分钟上手）

### 我想...

| 我想... | 使用工具 | 文档 |
|---------|---------|------|
| 上传单个文档到云文档 | `create_feishu_doc.py` | [快速上手](#快速上手) |
| 上传单个文档到 Wiki | `create_wiki_doc.py` | [Wiki 操作指南](#wiki-知识库操作) |
| 批量上传整个文件夹 | `batch_create_docs.py` | [批量操作](#批量操作) |
| 批量上传到 Wiki 空间 | `batch_create_wiki_docs.py` | [Wiki 操作指南](#wiki-知识库操作) |
| **下载单个文档** ⭐ | `download_doc.py` | [下载指南](DOWNLOAD_GUIDE.md) |
| **批量下载 Wiki** ⭐ | `download_wiki.py` | [下载指南](DOWNLOAD_GUIDE.md) |
| Markdown 表格转多维表格 | `md_table_to_bitable.py` | [Bitable 操作](#bitable-多维表格) |
| 大文档快速上传 | `--parallel` 标志 | [性能优化](#性能优化) |

### 最简单的使用

```bash
# 1. 配置环境
cp .env.example .env
# 编辑 .env，填入 FEISHU_APP_ID 和 FEISHU_APP_SECRET

# 2. 测试连接
uv run python scripts/test_api_connectivity.py

# 3a. 上传单个文档
uv run python scripts/create_feishu_doc.py README.md

# 3b. 批量上传文件夹
uv run python scripts/batch_create_docs.py ./docs
```

---

## 📚 完整文档目录

### 📖 入门指南

| 文档 | 说明 | 适用人群 |
|------|------|---------|
| [USAGE.md](USAGE.md) | 基本使用说明 | 新手用户 |
| [DESIGN.md](DESIGN.md) | 系统设计原理 | 开发者 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 常见问题解决 | 遇到问题时 |

### 🔧 功能操作指南

| 文档 | 内容 | 功能 |
|------|------|------|
| [BATCH_OPERATIONS.md](BATCH_OPERATIONS.md) | 批量操作完整指南 | 文件夹批量上传 |
| [DOWNLOAD_GUIDE.md](DOWNLOAD_GUIDE.md) ⭐ | **下载功能完整指南** | **单文档/批量下载** |
| [BITABLE_OPERATIONS.md](BITABLE_OPERATIONS.md) | Bitable 操作指南 | 表格转多维表格 |
| [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) | 性能优化指南 | 大文档加速上传 |
| [DIRECT_API_MODE.md](DIRECT_API_MODE.md) | 直连 API 模式 | 不依赖 AI/MCP |

### 🛠️ API 参考

| 文档 | 内容 | API 端点 |
|------|------|---------|
| [API_OPERATIONS.md](API_OPERATIONS.md) | 完整 API 参考 | 所有可用方法 |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 实现计划 | Phase 1/2/3 |

### 📋 项目管理

| 文档 | 内容 | 状态 |
|------|------|------|
| [IMPLEMENTATION_SUMMARY_CN.md](IMPLEMENTATION_SUMMARY_CN.md) | 功能总结中文版 | 完整功能清单 |
| [BUGFIX_SUMMARY.md](BUGFIX_SUMMARY.md) | Bug 修复总结 | 历史问题记录 |

---

## 🎯 核心功能详解

### 1. 文档创建

**工具**: `create_feishu_doc.py`

**用途**: 将本地 Markdown 文件创建为新的飞书文档

```bash
# 基础用法
uv run python scripts/create_feishu_doc.py README.md

# 指定标题和文件夹
uv run python scripts/create_feishu_doc.py README.md \
  --title "项目文档" \
  --folder fldcnxxxxx
```

**详细文档**: [BATCH_OPERATIONS.md](BATCH_OPERATIONS.md#单文档创建)

---

### 2. 批量操作

**工具**: `batch_create_docs.py`

**用途**: 批量上传整个文件夹到飞书云文档

```bash
# 批量上传
uv run python scripts/batch_create_docs.py ./docs

# 指定目标文件夹
uv run python scripts/batch_create_docs.py ./docs --folder fldcnxxxxx
```

**详细文档**: [BATCH_OPERATIONS.md](BATCH_OPERATIONS.md)

---

### 3. Wiki 知识库操作

#### 3.1 单文档上传到 Wiki

**工具**: `create_wiki_doc.py`

**新功能**: 支持按名称查找知识库和按路径指定层级

```bash
# 列出可用 Wiki 空间
uv run python scripts/create_wiki_doc.py --list-spaces

# 方式1: 使用 space-id（原有）
uv run python scripts/create_wiki_doc.py README.md --space-id 74812***88644

# 方式2: 使用 space-name（新！）- 按名称查找知识库
uv run python scripts/create_wiki_doc.py README.md --space-name "产品文档"

# 上传到个人知识库（自动检测）
uv run python scripts/create_wiki_doc.py README.md --personal

# 方式1: 使用 parent-token（原有）- 指定父节点
uv run python scripts/create_wiki_doc.py README.md \
  --space-id 74812***88644 \
  --parent-token nodcnxxxxx

# 方式2: 使用 wiki-path（新！）- 按路径指定层级
uv run python scripts/create_wiki_doc.py README.md \
  --space-name "产品文档" \
  --wiki-path "/API/参考"
```

**参数说明**:
- `--space-id` 和 `--space-name`: **二选一**，指定目标知识库
- `--parent-token` 和 `--wiki-path`: **二选一**，指定父节点位置

#### 3.2 批量上传到 Wiki

**工具**: `batch_create_wiki_docs.py`

**新功能**: 同样支持 `--space-name` 和 `--wiki-path`

```bash
# 方式1: 使用 space-id（原有）
uv run python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644

# 方式2: 使用 space-name（新！）
uv run python scripts/batch_create_wiki_docs.py ./docs --space-name "产品文档"

# 批量上传到个人知识库
uv run python scripts/batch_create_wiki_docs.py ./docs --personal

# 方式1: 使用 parent-token（原有）
uv run python scripts/batch_create_wiki_docs.py ./docs \
  --space-id 74812***88644 \
  --parent-token nodcnxxxxx

# 方式2: 使用 wiki-path（新！）- 批量上传到指定路径
uv run python scripts/batch_create_wiki_docs.py ./docs \
  --space-name "产品文档" \
  --wiki-path "/开发文档"
```

**注意事项**:
- `--space-id` 和 `--space-name` 不能同时使用
- `--parent-token` 和 `--wiki-path` 不能同时使用
- `--wiki-path` 格式: `/层级1/层级2/层级3`（以 `/` 开头表示从根节点开始）

**详细文档**: 见各工具的 `--help` 输出

---

### 4. Bitable 多维表格

**工具**: `md_table_to_bitable.py`

**用途**: 将 Markdown 表格转换为飞书多维表格，自动检测字段类型

```bash
# 基础转换
uv run python scripts/md_table_to_bitable.py data.md

# 自定义名称
uv run python scripts/md_table_to_bitable.py data.md --name "项目追踪表"

# 自动类型检测
uv run python scripts/md_table_to_bitable.py data.md --auto-types
```

**详细文档**: [BITABLE_OPERATIONS.md](BITABLE_OPERATIONS.md)

---

### 5. 性能优化

**用途**: 大文档快速上传（5-10x 性能提升）

```bash
# 启用并行上传
uv run python scripts/md_to_feishu.py 大文档.md --parallel
```

**详细文档**: [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)

---

## 🔗 集成方式

### 与 Feishu MCP 集成

对于文档更新和修改，推荐使用 **Feishu MCP**（更灵活的 AI 辅助编辑）：

```bash
# Feishu MCP 提供的功能：
# - AI 辅助编辑文档
# - 智能内容修改
# - 交互式文档操作
# - 自动化工作流
```

**使用建议**:
- **批量创建/迁移**: 使用 feishu-doc-tools（本工具）
- **内容更新/修改**: 使用 Feishu-MCP
- **混合模式**: 先用本工具创建，再用 MCP 维护

---

## 📊 功能对比表

| 功能 | feishu-doc-tools | Feishu-MCP | 推荐使用 |
|------|--------------|------------|---------|
| 批量创建文档 | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| 批量上传文件夹 | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| **文档下载/导出** ⭐ | **✅ 原生支持** | **⚠️ 需手动** | **feishu-doc-tools** |
| **批量下载 Wiki** ⭐ | **✅ 原生支持** | **⚠️ 需循环** | **feishu-doc-tools** |
| 表格转 Bitable | ✅ 专门工具 | ❌ 不支持 | feishu-doc-tools |
| 大文档上传 | ✅ 并行优化 | ⚠️ 较慢 | feishu-doc-tools |
| AI 辅助编辑 | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| 智能修改 | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| 交互式操作 | ❌ CLI 工具 | ✅ 对话式 | Feishu-MCP |

**结论**: 两个工具互补使用，发挥各自优势。

---

## 🛠️ CLI 工具完整清单

| 工具脚本 | 主要功能 | 使用场景 |
|---------|---------|---------|
| `create_feishu_doc.py` | 创建单个云文档 | 快速创建 |
| `batch_create_docs.py` | 批量创建云文档 | 文件夹迁移 |
| `create_wiki_doc.py` | 创建单个 Wiki 文档 | 知识库维护 |
| `batch_create_wiki_docs.py` | 批量创建 Wiki 文档 | 知识库迁移 |
| **`download_doc.py`** ⭐ | **下载单个文档** | **文档备份/导出** |
| **`download_wiki.py`** ⭐ | **批量下载 Wiki** | **知识库备份** |
| `md_table_to_bitable.py` | 表格转 Bitable | 数据管理 |
| `md_to_feishu.py` | 上传到现有文档 | 内容更新 |
| `get_root_info.py` | 获取根信息 | 环境配置 |
| `list_folders.py` | 列出文件夹 | 结构查看 |
| `test_api_connectivity.py` | 测试 API 连接 | 问题诊断 |

---

## 📝 配置说明

### 环境变量

```bash
# 必需配置
FEISHU_APP_ID=cli_xxxxx              # 飞书应用 ID
FEISHU_APP_SECRET=xxxxx               # 飞书应用密钥

# 可选配置
FEISHU_DEFAULT_FOLDER=fldcnxxxxx     # 默认云文件夹
FEISHU_AUTH_TYPE=tenant              # 认证类型
```

### 配置步骤

1. 复制配置模板
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入凭证

3. 测试连接
   ```bash
   uv run python scripts/test_api_connectivity.py
   ```

---

## 🔍 常见问题

### Q: 如何获取 space_id？

```bash
# 方法1: 列出所有 Wiki 空间
uv run python scripts/create_wiki_doc.py --list-spaces

# 方法2: 使用个人知识库（自动检测）
uv run python scripts/create_wiki_doc.py README.md --personal
```

### Q: 如何获取 folder_token？

```bash
# 获取根文件夹信息
uv run python scripts/get_root_info.py

# 列出文件夹内容
uv run python scripts/list_folders.py
```

### Q: 批量上传失败怎么办？

```bash
# 1. 启用详细日志
uv run python scripts/batch_create_docs.py ./docs -v

# 2. 检查文档
uv run python scripts/test_api_connectivity.py

# 3. 参考故障排除指南
# [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
```

---

## 📈 项目状态

### 已实现功能 ✅

- ✅ 文档创建（云文档 + Wiki）
- ✅ 批量操作（云文档 + Wiki）
- ✅ Bitable 多维表格
- ✅ 性能优化（并行上传）
- ✅ 完整测试覆盖
- ✅ 详细文档

### 技术指标

- **Python 版本**: 3.8+
- **测试覆盖**: 40+ 测试用例
- **文档完整性**: 100%
- **性能提升**: 5-10x（并行模式）

---

## 🤝 贡献与反馈

- 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 功能建议: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**最后更新**: 2025-01-18
**版本**: v2.0
