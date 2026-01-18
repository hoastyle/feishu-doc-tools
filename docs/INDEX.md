# 📚 文档中心 - feishu-doc-tools

**最后更新**: 2026-01-19
**版本**: v0.2.1
**🔧 技术索引**: [PROJECT_INDEX.md](../PROJECT_INDEX.md)

---

## 🚀 快速导航

### 新手入门
- [QUICK_START.md](user/QUICK_START.md) - **从这里开始！** 10分钟快速上手

### 核心功能
- [DOWNLOAD_GUIDE.md](user/DOWNLOAD_GUIDE.md) ⭐ **新增功能** - 下载文档和Wiki批量备份
- [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md) - 批量创建和迁移
- [BITABLE_OPERATIONS.md](user/BITABLE_OPERATIONS.md) - 多维表格操作
- [API_OPERATIONS.md](user/API_OPERATIONS.md) - API完整参考

### 专题指南
- [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md) - 下载功能技术参考
- [LIST_WIKI_TREE_GUIDE.md](guides/LIST_WIKI_TREE_GUIDE.md) - Wiki结构预览工具详解

### 故障排除
- [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) - 常见问题和解决方案
- [PERFORMANCE_OPTIMIZATION.md](user/PERFORMANCE_OPTIMIZATION.md) - 性能优化指南

### 设计和架构
- [DESIGN.md](design/DESIGN.md) - 架构设计说明
- [DIRECT_API_MODE.md](design/DIRECT_API_MODE.md) - 直连API模式
- [FEISHU_MCP_INTEGRATION.md](design/FEISHU_MCP_INTEGRATION.md) - MCP集成说明
- [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md) - 参数语义统一指南

### 技术文档 (technical/)
- [TENANT_TO_USER_AUTH_MIGRATION.md](technical/TENANT_TO_USER_AUTH_MIGRATION.md) - OAuth 认证迁移完整技术文档

---

## 📋 完整文档列表

### 用户文档 (user/)
| 文档 | 说明 | 页数 |
|------|------|------|
| [QUICK_START.md](user/QUICK_START.md) | 10分钟快速上手指南 | ~100 |
| [DOWNLOAD_GUIDE.md](user/DOWNLOAD_GUIDE.md) | 下载功能完整指南 | ~600 |
| [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md) | 批量操作指南 | ~300 |
| [BITABLE_OPERATIONS.md](user/BITABLE_OPERATIONS.md) | 多维表格操作 | ~300 |
| [API_OPERATIONS.md](user/API_OPERATIONS.md) | API完整参考 | ~350 |
| [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) | 常见问题解答 | ~250 |
| [PERFORMANCE_OPTIMIZATION.md](user/PERFORMANCE_OPTIMIZATION.md) | 性能优化指南 | ~280 |

### 专题指南 (guides/)
| 文档 | 说明 | 重点 |
|------|------|------|
| [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md) | 下载功能技术参考 | 开发者和技术用户 |
| [LIST_WIKI_TREE_GUIDE.md](guides/LIST_WIKI_TREE_GUIDE.md) | Wiki结构预览工具详解 | 树形结构查看 |

### 设计文档 (design/)
| 文档 | 说明 | 重点 |
|------|------|------|
| [DESIGN.md](design/DESIGN.md) | 系统架构设计 | 整体设计思路 |
| [DIRECT_API_MODE.md](design/DIRECT_API_MODE.md) | 直连API模式 | 无AI的直接调用 |
| [FEISHU_MCP_INTEGRATION.md](design/FEISHU_MCP_INTEGRATION.md) | MCP服务器集成 | Feishu-MCP使用 |
| [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md) | 参数语义统一指南 | 从v0.2.0迁移 |
| [FEATURE_GAPS.md](design/FEATURE_GAPS.md) | 功能限制说明 | 已知限制和workaround |

### 技术文档 (technical/)
| 文档 | 说明 | 重点 |
|------|------|------|
| [TENANT_TO_USER_AUTH_MIGRATION.md](technical/TENANT_TO_USER_AUTH_MIGRATION.md) | OAuth 认证迁移技术文档 | Tenant → User Auth 完整迁移过程 |

### 归档文档 (archive/)
| 文档 | 说明 |
|------|------|
| [CHANGELOG_v0.2.1.md](archive/CHANGELOG_v0.2.1.md) | v0.2.1 版本变更日志 |
| [RECURSIVE_SEARCH_COMPLETE.md](archive/RECURSIVE_SEARCH_COMPLETE.md) | 递归搜索功能完成报告 |

---

## 🎯 按场景选择文档

### 我是新用户
1. 阅读: [QUICK_START.md](user/QUICK_START.md)
2. 然后: [DOWNLOAD_GUIDE.md](user/DOWNLOAD_GUIDE.md)（如果需要下载）
3. 或者: [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md)（如果需要批量操作）

### 我要下载文档
- 用户指南: [DOWNLOAD_GUIDE.md](user/DOWNLOAD_GUIDE.md)
- 技术参考: [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md)
- 工具选择: [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md) 中的工具对比

### 我要预览Wiki结构
- Wiki结构预览: [LIST_WIKI_TREE_GUIDE.md](guides/LIST_WIKI_TREE_GUIDE.md)
- 快速查看: `list_wiki_tree.py` 工具

### 我要批量操作
- 创建文档: [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md)
- 迁移Wiki: [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md) 中的Wiki迁移部分

### 我要表格操作
- Markdown表格转Bitable: [BITABLE_OPERATIONS.md](user/BITABLE_OPERATIONS.md)

### 我要性能优化
- 大文件上传: [PERFORMANCE_OPTIMIZATION.md](user/PERFORMANCE_OPTIMIZATION.md)
- 并行处理: [PERFORMANCE_OPTIMIZATION.md](user/PERFORMANCE_OPTIMIZATION.md)

### 我要了解v0.2.1的改变
1. 参数统一: [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md)
2. 优化报告: [archive/deprecated/OPTIMIZATION_COMPLETE.md](archive/deprecated/OPTIMIZATION_COMPLETE.md)

### 我遇到了问题
- 首先查看: [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md)
- 功能限制: [FEATURE_GAPS.md](design/FEATURE_GAPS.md)

### 我是开发者
- 技术参考: [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md)
- 架构设计: [DESIGN.md](design/DESIGN.md)
- 参数语义: [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md)
- OAuth 迁移: [TENANT_TO_USER_AUTH_MIGRATION.md](technical/TENANT_TO_USER_AUTH_MIGRATION.md)
- 技术索引: [PROJECT_INDEX.md](../PROJECT_INDEX.md)

---

## 📊 文档统计

| 分类 | 数量 | 总页数 |
|------|------|--------|
| 用户文档 | 7 | ~2180 |
| 专题指南 | 2 | ~650 |
| 设计文档 | 5 | ~850 |
| 技术文档 | 1 | ~1310 |
| 归档文档 | 3 | ~250 |
| **总计** | **18** | **~5240** |

---

## 🔄 版本历史

### v0.2.1 (2026-01-18)
- 完全重构下载功能
- 参数语义统一
- 添加递归搜索和深度控制
- 新增 Wiki 层次结构预览工具（list_wiki_tree.py）
- 文档结构优化：user/、guides/、design/ 分类

### v0.2.0 (2026-01-17)
- Phase 1下载功能
- 基本API操作

### v0.1.0 (2025-12-15)
- 初始版本

---

## 📚 推荐阅读顺序

### 快速了解项目
1. [README.md](../README.md) - 项目概览（5分钟）
2. [QUICK_START.md](user/QUICK_START.md) - 快速开始（10分钟）

### 深入学习功能
3. [DOWNLOAD_GUIDE.md](user/DOWNLOAD_GUIDE.md) - 下载功能（15分钟）
4. [BATCH_OPERATIONS.md](user/BATCH_OPERATIONS.md) - 批量操作（15分钟）
5. [API_OPERATIONS.md](user/API_OPERATIONS.md) - API参考（20分钟）

### 了解改进
6. [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md) - 参数语义统一（10分钟）

### 实战应用
7. [DOWNLOAD_REFERENCE.md](guides/DOWNLOAD_REFERENCE.md) - 技术参考（20分钟）
8. [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) - 问题解决（10分钟）

---

## 🆘 获取帮助

### 不同情况下的求助方式

| 情况 | 查看文档 |
|------|---------|
| 不知道从哪开始 | [QUICK_START.md](user/QUICK_START.md) |
| 下载不工作 | [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) |
| 需要预览Wiki结构 | [LIST_WIKI_TREE_GUIDE.md](guides/LIST_WIKI_TREE_GUIDE.md) |
| 参数不清楚 | [UNIFIED_WIKI_PATH_SEMANTICS.md](design/UNIFIED_WIKI_PATH_SEMANTICS.md) |
| 想理解整个系统 | [DESIGN.md](design/DESIGN.md) |
| 需要API文档 | [API_OPERATIONS.md](user/API_OPERATIONS.md) |
| 性能有问题 | [PERFORMANCE_OPTIMIZATION.md](user/PERFORMANCE_OPTIMIZATION.md) |
| 我是开发者 | [PROJECT_INDEX.md](../PROJECT_INDEX.md) |

---

## ✅ 文档完整性检查

- [x] 快速开始文档
- [x] 下载功能文档
- [x] 批量操作文档
- [x] 表格操作文档
- [x] API参考文档
- [x] 故障排除文档
- [x] 性能优化文档
- [x] 设计架构文档
- [x] 专题指南
- [x] 文档分类整理

---

**最后更新**: 2026-01-19
**版本**: v0.2.1
**状态**: ✅ 生产就绪
