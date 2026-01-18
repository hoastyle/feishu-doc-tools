# Project Index: feishu-doc-tools

**Generated**: 2026-01-19
**Version**: v0.2.1
**Purpose**: 飞书文档管理工具 - 批量创建/迁移、Wiki 知识库、多维表格、下载导出

---

## 📁 Project Structure

```
feishu-doc-tools/
├── scripts/                  # 27 个 CLI 工具 (6,916 行代码)
│   ├── 上传工具 (5 个)
│   │   ├── md_to_feishu.py              # 核心转换脚本
│   │   ├── md_to_feishu_upload.py       # 统一上传脚本
│   │   ├── create_feishu_doc.py         # 创建单个云文档
│   │   ├── batch_create_docs.py         # 批量创建云文档
│   │   └── create_wiki_doc.py           # 创建单个 Wiki 文档
│   │   └── batch_create_wiki_docs.py    # 批量创建 Wiki 文档
│   │
│   ├── 下载工具 (3 个) ⭐
│   │   ├── download_doc.py              # 下载单个文档
│   │   ├── download_wiki.py             # 批量下载 Wiki
│   │   └── list_wiki_tree.py            # 预览 Wiki 结构
│   │
│   ├── 数据工具 (1 个)
│   │   └── md_table_to_bitable.py       # 表格转 Bitable
│   │
│   ├── 调试工具 (4 个)
│   │   ├── test_api_connectivity.py     # API 连接测试
│   │   ├── get_root_info.py             # 获取工作区信息
│   │   ├── list_folders.py              # 列出文件夹
│   │   └── feishu_to_md.py              # 飞书转 Markdown
│   │
│   └── 认证工具 (14 个)
│       ├── setup_user_auth.py           # 用户认证设置
│       ├── diagnose_auth_flow.py        # 认证流诊断
│       ├── diagnose_oauth.py            # OAuth 诊断
│       ├── diagnose_refresh_token.py    # 刷新令牌诊断
│       ├── diagnose_app_status.py       # 应用状态诊断
│       ├── verify_user_auth.py          # 用户认证验证
│       ├── test_refresh_token_update.py # 刷新令牌测试
│       └── verify_state_fix.py          # 状态修复验证
│
├── lib/                      # 核心库模块 (2,462 行代码)
│   ├── feishu_api_client.py  # 直连 API 客户端
│   ├── feishu_md_uploader.py # 飞书转换工具
│   ├── wiki_operations.py    # Wiki 操作共享库
│   └── __init__.py
│
├── tests/                    # 测试套件 (4,130 行代码)
│   ├── test_md_to_feishu.py              # 转换测试
│   ├── test_feishu_api_extended.py      # API 测试
│   ├── test_table_to_bitable.py         # Bitable 测试
│   ├── test_performance.py              # 性能测试
│   ├── test_recursive_search.py         # 递归搜索测试
│   ├── test_user_auth.py                # 用户认证测试
│   ├── test_oauth_url.py                # OAuth URL 测试
│   ├── test_scope_permissions.py        # 权限范围测试
│   └── __init__.py
│
├── docs/                     # 完整文档
│   ├── INDEX.md                      # 文档中心
│   ├── user/                        # 用户文档 (7 个)
│   ├── guides/                      # 专题指南 (2 个)
│   ├── design/                      # 设计文档 (5 个)
│   ├── technical/                   # 技术文档 (1 个)
│   └── archive/                     # 归档文档 (3 个)
│
├── dev/                      # 开发工具
│   ├── app_status_checklist.json
│   └── oauth/
│
├── examples/                 # 示例文件
│   └── sample.md
│
├── pyproject.toml           # uv 项目配置
├── requirements.txt         # 依赖清单
└── README.md                # 项目说明
```

---

## 🚀 Entry Points

### CLI Tools（scripts/）

#### 上传工具

| 脚本 | 功能 | 使用场景 | 关键参数 |
|------|------|----------|---------|
| `md_to_feishu.py` | 核心转换脚本 | Markdown → 飞书 block JSON | `--parallel`, `--output` |
| `md_to_feishu_upload.py` | 统一上传脚本 | 转换 + 上传一体化 | `--title`, `--folder` |
| `create_feishu_doc.py` | 创建单个云文档 | 快速创建文档 | `--title`, `--parent-id` |
| `batch_create_docs.py` | 批量创建云文档 | 文件夹迁移 | `--recursive`, `--parallel` |
| `create_wiki_doc.py` | 创建单个 Wiki 文档 | 知识库维护 | `--space-id`, `--space-name`, `--personal` |
| `batch_create_wiki_docs.py` | 批量创建 Wiki 文档 | 知识库迁移 | `--space-name`, `--personal`, `--auto-permission` |

#### 下载工具 ⭐

| 脚本 | 功能 | 使用场景 | 关键参数 |
|------|------|----------|---------|
| `download_doc.py` | 下载单个文档 | 文档备份/导出 | `--space-name`, `--wiki-path`, `--doc-title` |
| `download_wiki.py` | 批量下载 Wiki | 知识库备份 | `--space-name`, `--personal`, `--start-path` |
| `list_wiki_tree.py` | 预览 Wiki 结构 | 层次结构查看 | `--space-name`, `--max-depth`, `--start-path` |

#### 数据工具

| 脚本 | 功能 | 使用场景 | 关键参数 |
|------|------|----------|---------|
| `md_table_to_bitable.py` | 表格转 Bitable | 数据管理 | `--auto-types`, `--create-app` |

#### 调试工具

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `test_api_connectivity.py` | 测试 API 连接 | 问题诊断 |
| `get_root_info.py` | 获取根信息 | 环境配置 |
| `list_folders.py` | 列出文件夹 | 结构查看 |
| `feishu_to_md.py` | 飞书转 Markdown | 格式转换 |

#### 认证工具

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `setup_user_auth.py` | 用户认证设置 | OAuth 授权流程 |
| `diagnose_auth_flow.py` | 认证流诊断 | 授权问题排查 |
| `diagnose_oauth.py` | OAuth 诊断 | 配置检查 |
| `diagnose_refresh_token.py` | 刷新令牌诊断 | 令牌更新问题 |
| `diagnose_app_status.py` | 应用状态诊断 | 应用可用性检查 |
| `verify_user_auth.py` | 用户认证验证 | 权限验证 |
| `test_refresh_token_update.py` | 刷新令牌测试 | 令牌刷新流程 |
| `verify_state_fix.py` | 状态修复验证 | 状态参数检查 |

---

### Python API（lib/）

| 模块 | 用途 | 主要类/函数 |
|------|------|-----------|
| `FeishuApiClient` | 直连 API 客户端 | 支持批处理、图片上传、并行处理 |
| `FeishuMdUploader` | Markdown → 飞书 block JSON 转换 | 支持所有 Markdown 元素 |
| `WikiOperations` | Wiki 操作共享库 | 空间解析、路径解析、节点查找 |

---

## 📦 Core Modules

### Module: FeishuApiClient

**Path**: `lib/feishu_api_client.py`
**Purpose**: 飞书 Open API 直连客户端
**Lines of Code**: ~1,800
**Exports**: 27+ methods, 3 enums, 3 exceptions

#### 主要功能

**认证管理**:
- `AuthMode` enum: TENANT, USER 认证模式
- `BitableFieldType` enum: 12 种字段类型常量
- `from_env()`: 从环境变量创建客户端
- `_get_tenant_access_token()`: 应用令牌获取
- `_get_user_access_token()`: 用户令牌获取

**文档操作 API** (3 个方法):
- `batch_create_blocks()`: 批量创建内容块
- `get_document_blocks()`: 获取文档结构
- `get_document_info()`: 获取文档元信息

**文件夹操作 API** (4 个方法):
- `get_folders()`: 列出文件夹
- `create_folder()`: 创建文件夹
- `get_folder_info()`: 获取文件夹信息
- `delete_folder()`: 删除文件夹

**Wiki 操作 API** (5 个方法):
- `get_wiki_node_list()`: 获取节点列表
- `resolve_wiki_path()`: 解析 Wiki 路径
- `create_wiki_node()`: 创建 Wiki 节点
- `delete_wiki_node()`: 删除 Wiki 节点
- `get_wiki_space_list()`: 获取 Wiki 空间列表

**Bitable 操作 API** (6 个方法):
- `create_bitable_app()`: 创建多维表格应用
- `create_bitable_table()`: 创建表格
- `add_record()`: 添加记录
- `get_records()`: 获取记录
- `update_record()`: 更新记录
- `delete_record()`: 删除记录

**图片操作 API** (2 个方法):
- `upload_image_block()`: 上传图片并创建块
- `get_image_resource()`: 下载图片资源

**并行上传 API** (2 个方法):
- `batch_create_blocks_parallel()`: 并行批量创建 (5-10x 提升)
- `upload_images_parallel()`: 并行图片上传 (3-5x 提升)

**辅助方法** (7 个):
- `get_root_info()`: 获取根目录信息
- `find_wiki_space_by_name()`: 按名称查找空间
- `find_wiki_node_by_path()`: 按路径查找节点
- `fetch_wiki_children_for_node()`: 获取子节点
- `list_wiki_tree()`: 递归列出 Wiki 树
- `search_document_blocks()`: 搜索文档块
- `download_document_content()`: 下载文档内容

#### 性能优化

- **批处理**: 自动分批（50 blocks/批）
- **并行上传**: 5-10x 速度提升
- **连接池**: 复用 HTTP 连接
- **线程安全**: Token 自动刷新机制
- **错误重试**: 指数退避策略

---

### Module: FeishuMdUploader

**Path**: `lib/feishu_md_uploader.py`
**Purpose**: Markdown 到飞书 block 格式转换
**Lines of Code**: ~400

#### 支持元素

- **标题**: h1-h9
- **段落/文本**: 粗体、斜体、代码、删除线
- **代码块**: 50+ 语言语法高亮
- **列表**: 有序/无序列表
- **图片**: 本地/网络图片
- **表格**: 飞书表格格式
- **数学公式**: LaTeX 格式
- **Mermaid 图表**: 白板块
- **引用块**: 完整支持

#### 主要方法

- `convert_md_to_blocks()`: Markdown → blocks 转换
- `process_node()`: 递归处理 AST 节点
- `extract_images()`: 提取图片引用
- `save_to_json()`: 保存为 JSON 格式

---

### Module: WikiOperations

**Path**: `lib/wiki_operations.py`
**Purpose**: Wiki 操作共享库
**Lines of Code**: ~300

#### 主要功能

**空间解析**:
- `resolve_space_id()`: 统一空间 ID 解析（支持 ID/名称/个人）

**路径解析**:
- `resolve_path_to_node()`: 路径 → 节点解析
- `find_node_by_path()`: 递归路径查找

**节点操作**:
- `fetch_node_children()`: 获取子节点
- `build_node_tree()`: 构建节点树
- `traverse_wiki_tree()`: 遍历 Wiki 树

**异常类型**:
- `WikiOperationsError`: 基础异常
- `SpaceNotFoundError`: 空间未找到
- `PathNotFoundError`: 路径未找到
- `DocumentNotFoundError`: 文档未找到

---

## 🔧 Configuration

### 项目配置

**依赖管理**: `pyproject.toml`

```toml
[project]
name = "feishu-doc-tools"
version = "0.2.0"
requires-python = ">=3.8.1"

[project.scripts]
feishu-doc-tools = "scripts.md_to_feishu:main"
```

### 核心依赖

```
markdown-it-py>=3.0.0      # Markdown 解析器
mdit-py-plugins>=0.4.0     # Markdown 插件
requests>=2.28.0           # HTTP 客户端
python-dotenv>=1.0.0       # 环境变量管理
```

### 开发依赖

```
pytest>=7.0.0              # 测试框架
pytest-cov>=4.0.0          # 覆盖率
black>=23.0.0              # 代码格式化
flake8>=6.0.0              # 代码检查
mypy>=1.0.0                # 类型检查
```

### 环境变量

#### 应用认证 (默认)

```bash
FEISHU_APP_ID=cli_xxxxx           # 应用 ID
FEISHU_APP_SECRET=xxxxx           # 应用密钥
FEISHU_DEFAULT_FOLDER=fldcnxxxxx  # 可选：默认文件夹
FEISHU_DEFAULT_WIKI_SPACE=123456  # 可选：默认 Wiki 空间
```

#### 用户认证 (OAuth)

```bash
# OAuth 配置
FEISHU_USER_AUTH_ENABLED=true     # 启用用户认证
FEISHU_REDIRECT_URI=http://localhost:8080/callback

# 令牌存储（自动生成）
FEISHU_ACCESS_TOKEN=xxxxx         # 访问令牌（2 小时有效）
FEISHU_REFRESH_TOKEN=xxxxx        # 刷新令牌（30 天有效）
FEISHU_TOKEN_EXPIRES_AT=1234567890  # 过期时间戳
```

---

## 📚 Documentation

### 文档统计

| 分类 | 数量 | 总页数 |
|------|------|--------|
| 用户文档 (user/) | 7 | ~2,180 |
| 专题指南 (guides/) | 2 | ~650 |
| 设计文档 (design/) | 5 | ~850 |
| 技术文档 (technical/) | 1 | ~1,310 |
| 归档文档 (archive/) | 3 | ~250 |
| **总计** | **18** | **~5,240** |

### 用户文档（user/）

| 文档 | 说明 | 阅读时间 |
|------|------|---------|
| `QUICK_START.md` | 10 分钟快速上手指南 | 10 分钟 |
| `DOWNLOAD_GUIDE.md` ⭐ | 下载功能完整指南 | 15 分钟 |
| `USER_AUTH_GUIDE.md` | 用户认证使用指南 | 12 分钟 |
| `BATCH_OPERATIONS.md` | 批量操作指南 | 15 分钟 |
| `BITABLE_OPERATIONS.md` | 多维表格操作 | 10 分钟 |
| `API_OPERATIONS.md` | API 完整参考 | 20 分钟 |
| `TROUBLESHOOTING.md` | 故障排除指南 | 10 分钟 |
| `PERFORMANCE_OPTIMIZATION.md` | 性能优化指南 | 15 分钟 |

### 专题指南（guides/）

| 文档 | 说明 | 目标读者 |
|------|------|---------|
| `DOWNLOAD_REFERENCE.md` | 下载功能技术参考 | 开发者和技术用户 |
| `LIST_WIKI_TREE_GUIDE.md` | Wiki 结构预览工具详解 | 所有用户 |

### 设计文档（design/）

| 文档 | 说明 | 重点 |
|------|------|------|
| `DESIGN.md` | 系统架构设计 | 整体设计思路 |
| `DIRECT_API_MODE.md` | 直连 API 模式 | 无 AI 的直接调用 |
| `FEISHU_MCP_INTEGRATION.md` | MCP 服务器集成 | Feishu-MCP 使用 |
| `UNIFIED_WIKI_PATH_SEMANTICS.md` | 参数语义统一指南 | 从 v0.2.0 迁移 |
| `FEATURE_GAPS.md` | 功能限制说明 | 已知限制和 workaround |

### 技术文档（technical/）

| 文档 | 说明 | 重点 |
|------|------|------|
| `TENANT_TO_USER_AUTH_MIGRATION.md` | OAuth 认证迁移技术文档 | Tenant → User Auth 完整迁移过程 |

### 归档文档（archive/）

| 文档 | 说明 |
|------|------|
| `CHANGELOG_v0.2.1.md` | v0.2.1 版本变更日志 |
| `RECURSIVE_SEARCH_COMPLETE.md` | 递归搜索功能完成报告 |

### 文档中心

- `docs/INDEX.md` - 文档导航索引

---

## 🧪 Test Coverage

### 测试文件

| 测试文件 | 覆盖范围 | 测试用例数 |
|---------|---------|-----------|
| `test_md_to_feishu.py` | Markdown 转换 | 15+ |
| `test_feishu_api_extended.py` | API 客户端 | 12+ |
| `test_table_to_bitable.py` | Bitable 操作 | 10+ |
| `test_performance.py` | 性能基准 | 8+ |
| `test_recursive_search.py` | 递归搜索 | 5+ |
| `test_user_auth.py` | 用户认证 | 6+ |
| `test_oauth_url.py` | OAuth URL | 4+ |
| `test_scope_permissions.py` | 权限范围 | 3+ |

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/test_md_to_feishu.py -v

# 测试覆盖率
uv run pytest --cov=scripts --cov=lib --cov-report=term-missing tests/

# 性能测试
uv run pytest tests/test_performance.py -v
```

### 代码统计

| 目录 | 文件数 | 代码行数 |
|------|-------|---------|
| scripts/ | 27 | 6,916 |
| lib/ | 4 | 2,462 |
| tests/ | 9 | 4,130 |
| **总计** | **40** | **13,508** |

---

## 📝 Quick Start

### 1. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
export FEISHU_APP_ID="cli_xxxxx"
export FEISHU_APP_SECRET="xxxxx"
```

### 3. 测试 API 连接

```bash
uv run python scripts/test_api_connectivity.py
```

### 4. 上传第一个文档

```bash
# 创建单个文档
uv run python scripts/create_feishu_doc.py README.md

# 批量上传
uv run python scripts/batch_create_docs.py ./docs
```

---

## 🚀 快速命令参考

### 上传操作

```bash
# 创建单个文档
uv run python scripts/create_feishu_doc.py file.md --title "文档标题"

# 批量上传文件夹
uv run python scripts/batch_create_docs.py ./docs --recursive --parallel

# 创建 Wiki 文档（按空间名称）
uv run python scripts/create_wiki_doc.py file.md --space-name "产品文档"

# 创建 Wiki 文档（个人知识库）
uv run python scripts/create_wiki_doc.py file.md --personal --auto-permission

# 批量创建 Wiki
uv run python scripts/batch_create_wiki_docs.py ./docs --space-name "产品文档"
```

### 下载操作 ⭐

```bash
# 按路径下载文档
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/REST API" \
  -o api.md

# 按文档标题下载
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-title "API 参考" \
  -o api.md

# 批量下载整个 Wiki 空间
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  ./backup

# 下载个人知识库
uv run python scripts/download_wiki.py --personal ./my_backup

# 部分下载（从指定路径开始）
uv run python scripts/download_wiki.py \
  --space-name "产品文档" \
  --start-path "/API/参考" \
  ./api_docs
```

### 查看操作

```bash
# 预览 Wiki 结构（完整）
uv run python scripts/list_wiki_tree.py --space-name "产品文档"

# 限制深度（只看 2 层）
uv run python scripts/list_wiki_tree.py --space-name "产品文档" --max-depth 2

# 从指定路径开始
uv run python scripts/list_wiki_tree.py --space-name "产品文档" --start-path "/API"

# 查看个人知识库
uv run python scripts/list_wiki_tree.py --personal
```

### 数据操作

```bash
# Markdown 表格转 Bitable
uv run python scripts/md_table_to_bitable.py data.md --auto-types --create-app
```

### 用户认证设置

```bash
# 启动用户认证流程
uv run python scripts/setup_user_auth.py

# 验证用户认证
uv run python scripts/verify_user_auth.py

# 诊断认证问题
uv run python scripts/diagnose_auth_flow.py
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

### Wiki 下载性能

| Wiki 大小 | 文档数 | 耗时 | 吞吐量 |
|----------|-------|------|--------|
| 小型 | <10 | ~5s | ~2 docs/s |
| 中型 | 10-50 | ~30s | ~1.5 docs/s |
| 大型 | 50-100 | ~90s | ~1 doc/s |
| 超大 | 100+ | ~3min | ~0.6 docs/s |

---

## 🔗 Related Projects

### 互补工具

- **[Feishu-MCP](https://github.com/your-username/Feishu-MCP)** - 飞书 MCP 服务器
  - 用于 AI 辅助编辑、智能修改
  - 与本工具互补使用

### 功能对比

| 功能场景 | feishu-doc-tools | Feishu-MCP | 推荐 |
|---------|----------------|------------|------|
| 批量创建文档 | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| 批量上传文件夹 | ✅ 原生支持 | ⚠️ 需要循环 | feishu-doc-tools |
| 文档下载/导出 | ✅ 原生支持 | ⚠️ 需手动 | feishu-doc-tools |
| 批量下载 Wiki | ✅ 原生支持 | ⚠️ 需循环 | feishu-doc-tools |
| 表格转 Bitable | ✅ 专门工具 | ❌ 不支持 | feishu-doc-tools |
| 大文档上传 | ✅ 并行优化 (5-10x) | ⚠️ 较慢 | feishu-doc-tools |
| AI 辅助编辑 | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| 智能内容修改 | ❌ 不支持 | ✅ 核心功能 | Feishu-MCP |
| 交互式操作 | ❌ CLI 工具 | ✅ 对话式 | Feishu-MCP |

### 依赖库

- **[markdown-it-py](https://github.com/executablebooks/markdown-it-py)** - Python Markdown 解析器
- **[requests](https://github.com/psf/requests)** - HTTP 客户端
- **[mdit-py-plugins](https://github.com/executablebooks/mdit-py-plugins)** - Markdown 插件集合

---

## 📜 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！

### 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范

- 遵循现有代码风格
- 添加测试覆盖新功能
- 更新相关文档
- 确保所有测试通过

---

**最后更新**: 2026-01-19
**版本**: v0.2.1
**状态**: ✅ 生产就绪
**维护**: 持续更新中
