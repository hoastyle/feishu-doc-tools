# feishu-doc-tools 项目状态

**更新日期**: 2025-01-18
**项目名称**: feishu-doc-tools (原名 md-to-feishu)
**版本**: v0.1.0
**状态**: ✅ Phase 2 已完成

---

## 🎯 项目定位

**核心功能**: 将本地 Markdown 文档批量创建/迁移到飞书

**核心优势**:
- ✅ 高效批量处理
- ✅ 零 AI token 占用
- ✅ 并行上传优化（5-10x 性能）
- ✅ 完整的 Wiki 和 Bitable 支持

**与 Feishu-MCP 的关系**:
- **feishu-doc-tools**: 批量创建/迁移工具
- **Feishu-MCP**: AI 辅助编辑工具
- **定位**: 互补协作，不是竞争

---

## 📊 功能模块

### 1. 文档创建（95% 完整）

- ✅ 单个文档创建
- ✅ 批量文件夹上传
- ✅ Wiki 知识库创建
- ✅ 批量 Wiki 创建
- ✅ 并行上传优化

### 2. Bitable 多维表格（100% 完整）

- ✅ 创建 Bitable 应用
- ✅ 创建数据表
- ✅ 插入/获取/更新/删除记录
- ✅ 字段类型自动检测
- ✅ Markdown 表格转换

### 3. 查询与导航（85% 完整）

- ✅ 列出所有 Wiki 空间
- ✅ 按名称查找知识库（新增）
- ✅ 按路径查找节点（新增）
- ✅ 获取节点列表
- ✅ 获取根文件夹信息
- ⚠️ 按名称查找文档（缺失）

### 4. 下载功能（0% - 缺失）

- ❌ 下载单个文档
- ❌ 批量下载 Wiki
- ❌ 导出为 Markdown
- ❌ Bitable 数据导出

### 5. 同步功能（0% - 暂不需要）

- ❌ 双向同步
- ❌ 增量同步
- ❌ 冲突检测

---

## 🔧 CLI 工具清单

| 工具 | 功能 | 新增功能 |
|------|------|---------|
| `create_feishu_doc.py` | 创建云文档 | - |
| `batch_create_docs.py` | 批量创建云文档 | - |
| `create_wiki_doc.py` | 创建 Wiki 文档 | ✅ --space-name, --wiki-path |
| `batch_create_wiki_docs.py` | 批量创建 Wiki | ✅ --space-name, --wiki-path |
| `md_table_to_bitable.py` | 表格转 Bitable | - |
| `md_to_feishu.py` | 核心转换脚本 | - |
| `get_root_info.py` | 获取根信息 | - |
| `list_folders.py` | 列出文件夹 | - |
| `test_api_connectivity.py` | 测试 API 连接 | - |

---

## 📝 文档结构

```
docs/
├── QUICK_START.md              # 快速开始指南（更新）
├── FEISHU_MCP_INTEGRATION.md   # 与 Feishu-MCP 集成（新增）
├── PHASE2_PLAN.md              # Phase 2 实施计划（新增）
├── FEATURE_GAPS.md             # 功能完整性分析（新增）
├── RENAMING.md                 # 项目重命名说明（新增）
├── BATCH_OPERATIONS.md         # 批量操作指南
├── BITABLE_OPERATIONS.md       # Bitable 操作指南
├── PERFORMANCE_OPTIMIZATION.md # 性能优化指南
├── API_OPERATIONS.md           # API 完整参考
├── TROUBLESHOOTING.md          # 故障排除指南
├── USAGE.md                    # 基本使用说明
├── DESIGN.md                   # 系统设计原理
├── IMPLEMENTATION_PLAN.md      # 实现计划
├── IMPLEMENTATION_SUMMARY_CN.md # 功能总结
└── BUGFIX_SUMMARY.md          # Bug 修复总结
```

---

## 🚀 使用示例

### 上传到 Wiki（新方式）

```bash
# 按名称指定知识库
uv run python scripts/create_wiki_doc.py README.md --space-name "产品文档"

# 按路径指定层级
uv run python scripts/create_wiki_doc.py api.md \
  --space-name "产品文档" \
  --wiki-path "/API/参考"
```

### 批量上传

```bash
# 批量上传到指定路径
uv run python scripts/batch_create_wiki_docs.py ./docs \
  --space-name "产品文档" \
  --wiki-path "/开发文档"
```

---

## ⚙️ 环境配置

### 必需环境变量

```bash
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
```

### 可选环境变量

```bash
FEISHU_DEFAULT_FOLDER=fldcnxxxxx  # 默认云文件夹
FEISHU_DEFAULT_WIKI_SPACE=123456  # 默认 Wiki 空间
```

---

## 🎓 关键设计决策

### 1. 参数并存策略

- 保留所有原有参数（`--space-id`, `--parent-token`）
- 新增便捷参数（`--space-name`, `--wiki-path`）
- 用户使用时二选一（互斥验证）

### 2. 向后兼容

- 所有原有参数和行为保持不变
- 新参数是可选的
- 现有脚本和用法完全兼容

### 3. 用户体验优先

- 按名称查找比手动查找 ID 更友好
- 路径式层级比 token 更直观
- 错误信息明确提示问题所在

---

## 📊 性能基准

| 文档大小 | 上传时间 | 优化后 |
|---------|---------|--------|
| 小型 (<50 blocks) | <5s | <3s (1.7x) |
| 中型 (50-200) | <30s | <8s (3.8x) |
| 大型 (200-1000) | <180s | <30s (6x) |
| 超大 (1000+) | <600s | <75s (8x) |

---

## 🔮 未来计划

### Phase 1: 下载功能（待定）

- `get_document_content()` - 获取文档内容
- `export_to_markdown()` - 导出为 Markdown
- `scripts/download_doc.py` - 下载工具
- `scripts/download_wiki.py` - 批量下载 Wiki

### 其他改进

- 更友好的错误提示
- 更详细的日志输出
- 配置文件支持
- Web UI（可选）

---

**最后更新**: 2025-01-18
**维护者**: Claude Code
**许可证**: MIT
