# 项目重命名说明

## 概述

**旧名称**: `md-to-feishu`
**新名称**: `feishu-doc-tools`
**重命名日期**: 2025-01-18
**版本**: v0.1.0

---

## 为什么重命名？

### 原名称的问题

`md-to-feishu` 这个名称存在以下局限：

1. **功能范围不准确**
   - 名称暗示"只能上传 Markdown 文档"
   - 实际上支持多种功能：批量创建、Wiki、Bitable、迁移等

2. **定位过于狭窄**
   - "md-to" 看起来像单向转换工具
   - 实际上是完整的飞书文档管理工具套件

3. **不利于未来扩展**
   - 如果添加其他格式支持（如 HTML、Word），名称会变得不准确
   - 无法体现"工具套件"的特点

### 新名称的优势

`feishu-doc-tools` 更好地反映了项目定位：

1. **准确性**
   - 明确说明是"飞书文档工具"
   - 不限定具体格式，便于扩展

2. **完整性**
   - "tools"（复数）体现工具套件特性
   - 涵盖所有功能：创建、迁移、Wiki、Bitable

3. **可扩展性**
   - 未来可以添加新格式支持
   - 可以添加新的工具类型

---

## 功能对比

| 功能类别 | 旧名称暗示 | 实际功能 | 新名称体现 |
|---------|-----------|---------|-----------|
| 文档上传 | ✅ 主要功能 | ✅ 支持 | ✅ 准确 |
| 批量操作 | ❌ 未体现 | ✅ 支持 | ✅ "tools" 复数 |
| Wiki 管理 | ❌ 未体现 | ✅ 支持 | ✅ 准确 |
| Bitable | ❌ 未体现 | ✅ 支持 | ✅ 准确 |
| 性能优化 | ❌ 未体现 | ✅ 并行上传 | ✅ 准确 |
| 企业场景 | ❌ 未体现 | ✅ 团队协作 | ✅ 准确 |

---

## 影响范围

### 代码变更

| 文件 | 变更内容 |
|------|---------|
| `pyproject.toml` | 项目名称: `md-to-feishu` → `feishu-doc-tools`<br>项目描述: 更新为完整功能描述 |
| `.env.example` | 注释标题更新 |
| `uv.lock` | 重新生成，引用新包名 |

### 命令变更

所有命令示例从 `python scripts/xxx.py` 更新为 `uv run python scripts/xxx.py`：

```bash
# 旧方式（已弃用）
python scripts/create_feishu_doc.py README.md

# 新方式（推荐）
uv run python scripts/create_feishu_doc.py README.md
```

### 文档变更

所有文档已更新，包括：
- README.md
- docs/QUICK_START.md
- docs/BATCH_OPERATIONS.md
- docs/BITABLE_OPERATIONS.md
- docs/PERFORMANCE_OPTIMIZATION.md
- docs/API_OPERATIONS.md
- docs/FEISHU_MCP_INTEGRATION.md
- 所有 CLI 工具的 epilog 说明

---

## 迁移指南

### 对于用户

1. **更新命令**
   ```bash
   # 旧命令
   python scripts/create_feishu_doc.py README.md

   # 新命令
   uv run python scripts/create_feishu_doc.py README.md
   ```

2. **更新依赖**
   ```bash
   # 如果使用旧版本，需要重新安装
   rm -rf .venv uv.lock
   uv sync
   ```

3. **更新脚本**
   - 搜索所有使用 `python scripts/` 的脚本
   - 替换为 `uv run python scripts/`

### 对于开发者

1. **Git 仓库**
   - 仓库名称建议改为 `feishu-doc-tools`
   - 更新 CI/CD 配置（如有）

2. **导入路径**
   ```python
   # 旧导入（如果存在）
   from md_to_feishu import ...

   # 新导入（如果需要）
   from feishu_doc_tools import ...
   ```

3. **发布配置**
   - PyPI 包名: `feishu-doc-tools`
   - 更新所有发布配置文件

---

## 兼容性说明

### 向后兼容

- ✅ **环境变量**: 无变化（`FEISHU_APP_ID`, `FEISHU_APP_SECRET` 等）
- ✅ **API 接口**: 无变化（`lib/feishu_api_client.py`）
- ✅ **配置文件**: 无变化（`.env.example`）
- ✅ **脚本功能**: 无变化（所有脚本参数和行为）

### 不兼容项

- ❌ **包名**: Python 包名已更改
- ❌ **命令方式**: 必须使用 `uv run python` 而非直接 `python`
- ❌ **导入路径**: 如果有直接导入包的代码需要更新

---

## 常见问题

### Q1: 我的旧版本还能用吗？

**A**: 是的，旧版本功能上完全可用，但建议迁移到新版本以获得更好的体验。

### Q2: 必须使用 `uv run python` 吗？

**A**: 推荐使用，但也可以直接用 `python`。使用 `uv` 确保依赖版本正确。

### Q3: 我已经安装了旧版本怎么办？

**A**:
```bash
# 卸载旧版本
pip uninstall md-to-feishu

# 安装新版本
uv sync
```

### Q4: Git 历史会丢失吗？

**A**: 不会。本次重命名只更新了代码内容，Git 历史完全保留。

### Q5: 文档中的链接还能用吗？

**A**: 所有文档链接已更新，使用新的文件名和包名。

---

## 未来计划

基于新名称 `feishu-doc-tools`，未来可能添加：

1. **更多格式支持**
   - HTML → 飞书文档
   - Word → 飞书文档
   - 导出飞书文档为其他格式

2. **更多工具类型**
   - 文档分析工具
   - 批量修改工具
   - 权限管理工具

3. **更好的集成**
   - 飞书应用集成
   - CI/CD 集成
   - Webhook 集成

---

## 相关链接

- [项目主页](README.md)
- [快速开始](QUICK_START.md)
- [功能对比](FEISHU_MCP_INTEGRATION.md)
- [更新日志](../CHANGELOG.md) (如存在)

---

**最后更新**: 2025-01-18
**维护状态**: ✅ 活跃维护中
