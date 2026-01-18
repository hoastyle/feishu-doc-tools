# Wiki 层次结构预览指南 (list_wiki_tree.py)

**创建日期**: 2026-01-18
**版本**: v0.3.0
**用途**: 快速预览 Wiki 知识库结构，不下载任何内容
**更新**: 2026-01-18 - 添加并行优化和性能统计

---

## 📋 快速开始

```bash
# 查看个人知识库（默认并行模式）
uv run python scripts/list_wiki_tree.py --personal

# 查看指定空间
uv run python scripts/list_wiki_tree.py -s "产品文档"

# 限制深度
uv run python scripts/list_wiki_tree.py -s "产品文档" -d 2

# 从指定路径开始
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API"

# 快速并行模式（10 workers）
uv run python scripts/list_wiki_tree.py -s "大型知识库" --max-workers 10

# 顺序模式（调试或小型 Wiki）
uv run python scripts/list_wiki_tree.py -s "产品文档" --max-workers 1
```

---

## 🎯 核心特性

### ✅ 树形显示
- 使用 Unicode 字符绘制树形结构
- 清晰的层次关系展示
- 自动缩进对齐

### ✅ 图标区分
- 📂 **目录** - 包含子节点
- 📄 **文档** - 叶子节点（无子节点）

### ✅ 灵活控制
- 深度控制（-d 参数）
- 起始路径（-S 参数）
- 调试模式（--debug）

### ✅ 零存储占用
- 不下载任何内容
- 仅读取节点元数据
- 快速响应

### ✅ 并行优化（NEW）
- 同级节点并行获取子节点
- 默认 5 个并行 worker
- 支持 1-20 个 worker 配置
- 性能提升：3-5x（取决于节点数量）

---

## 📊 输出示例

```
📚 Wiki Space: 产品文档

🌳 Tree Structure (parallel, max_workers=5):
============================================================
📂 首页
📂 项目
    ├── 📄 项目流程
    └── 📄 标书确认
📂 API文档
    ├── 📄 REST API
    ├── 📄 GraphQL API
    └── 📂 WebSocket
        └── 📄 协议说明
📄 README
============================================================

📊 Total Nodes (shown): 10
⏱️  API Call Time: 0.35s
⏱️  Tree Build Time: 2.15s
⏱️  Total Time: 2.50s
🚀 Parallel Mode: ~5x speedup potential
```

### 输出说明

- **API Call Time**: 获取根节点的时间
- **Tree Build Time**: 遍历树并获取子节点的总时间
- **Total Time**: 从开始到完成的总时间
- **Parallel Mode**: 并行模式下的预期加速比

---

## 🔧 参数说明

### 空间识别参数（三选一）

| 参数 | 短选项 | 说明 | 示例 |
|------|--------|------|------|
| `--space-name` | `-s` | Wiki 空间名称 | `-s "产品文档"` |
| `--space-id` | - | Wiki 空间 ID | `--space-id 74812***88644` |
| `--personal` | `-P` | 使用个人知识库 | `-P` |

### 可选参数

| 参数 | 短选项 | 默认值 | 说明 |
|------|--------|--------|------|
| `--start-path` | `-S` | 根路径 | 从指定路径开始显示 |
| `--depth` | `-d` | -1（无限） | 最大显示深度 |
| `--max-workers` | - | 5 | 并行 worker 数量（1=顺序，5=默认，10=快速）|
| `--debug` | - | False | 显示调试信息 |
| `--app-id` | - | 环境变量 | 飞书应用 ID |
| `--app-secret` | - | 环境变量 | 飞书应用密钥 |

### 并行模式说明（NEW）

| max_workers | 模式 | 适用场景 | 预期提升 |
|------------|------|----------|----------|
| 1 | 顺序 | 小型 Wiki 或调试 | 1x（基准）|
| 3-5 | 并行（推荐） | 中型 Wiki | 3-5x |
| 10-20 | 快速并行 | 大型 Wiki（100+ 节点）| 5-10x |

### 深度参数说明

| 值 | 含义 | 示例 |
|----|------|------|
| `-1` 或不指定 | 无限递归 | 显示所有层级 |
| `0` | 只显示根层级 | 只显示直接子节点 |
| `1` | 显示1层深度 | 根节点 + 1层子节点 |
| `2` | 显示2层深度 | 根节点 + 2层子节点 |
| `n` | 显示n层深度 | 根节点 + n层子节点 |

---

## 🎯 使用场景

### 场景 1: 快速了解 Wiki 结构

**需求**: 刚加入项目，想了解知识库的组织结构

```bash
uv run python scripts/list_wiki_tree.py -s "产品文档"
```

**优势**:
- 几秒钟内了解整体结构
- 不需要下载任何内容
- 清晰的层次关系

### 场景 2: 查找特定文档路径

**需求**: 知道文档名称，但不知道完整路径

```bash
# 先查看完整结构，找到文档位置
uv run python scripts/list_wiki_tree.py -s "产品文档" | grep "API设计"
```

### 场景 3: 下载前预览

**需求**: 下载前确认目录结构

```bash
# 1. 先预览结构
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API"

# 2. 确认后下载
uv run python scripts/download_wiki.py -s "产品文档" -S "/API" ./backup
```

### 场景 4: 限制深度查看

**需求**: 只关心顶层结构，不需要深层细节

```bash
# 只显示2层
uv run python scripts/list_wiki_tree.py -s "产品文档" -d 2
```

### 场景 5: 调试模式

**需求**: 查看 API 返回的原始数据

```bash
uv run python scripts/list_wiki_tree.py -s "产品文档" --debug
```

**输出示例**:
```
[DEBUG] 首页: type=origin, has_children=None, obj_token=FhBfdDH8JoDc4TxekgRcApWEnjf
[DEBUG] 首页: actual_children=0, is_doc=True
📄 首页
[DEBUG] 项目: type=origin, has_children=None, obj_token=FRPyducOdoIKv7xHQR8cQRten14
[DEBUG] 项目: actual_children=2, is_doc=False
📂 项目
```

---

## 🚀 高级用法

### 组合 1: 过滤特定节点

```bash
# 只查看包含 "API" 的节点
uv run python scripts/list_wiki_tree.py -s "产品文档" | grep "API"
```

### 组合 2: 统计节点数量

```bash
# 统计总节点数
uv run python scripts/list_wiki_tree.py -s "产品文档" | grep "📊 Total Nodes"
```

### 组合 3: 导出为文件

```bash
# 保存树形结构到文件
uv run python scripts/list_wiki_tree.py -s "产品文档" > structure.txt
```

### 组合 4: 与下载工具配合

```bash
# 1. 预览结构
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API" -d 1

# 2. 确认后下载
uv run python scripts/download_wiki.py -s "产品文档" -S "/API" -d 1 ./api_backup
```

---

## 💡 最佳实践

### 1. 先预览，后操作

**推荐流程**:
1. 使用 `list_wiki_tree.py` 预览结构
2. 确认目标路径和内容
3. 使用 `download_doc.py` 或 `download_wiki.py` 下载

**优势**:
- 避免下载不需要的内容
- 节省时间和带宽
- 确认目标路径正确

### 2. 使用深度控制

**大型 Wiki 空间**:
```bash
# 先看顶层结构（-d 1）
uv run python scripts/list_wiki_tree.py -s "大型知识库" -d 1

# 再深入感兴趣的分支
uv run python scripts/list_wiki_tree.py -s "大型知识库" -S "/感兴趣的分支"
```

### 3. 定期结构检查

**维护知识库健康**:
```bash
# 定期检查结构变化
uv run python scripts/list_wiki_tree.py --personal > structure_$(date +%Y%m%d).txt

# 对比历史结构
diff structure_20260101.txt structure_20260118.txt
```

---

## ⚠️ 注意事项

### 1. API 调用次数

- **优化后**: 每个节点只调用一次 `get_wiki_node_list` API（之前是 2 次）
- 同级节点**并行获取**，大幅减少总时间
- 使用 `-d` 参数限制深度可以进一步减少调用
- 使用 `--max-workers` 控制并行度（默认 5）

### 2. 权限要求

- 需要对目标 Wiki 空间的读取权限
- 个人知识库使用 `-P` 参数

### 3. 显示限制

- 终端宽度可能影响树形显示效果
- 超长标题可能显示不完整
- 建议在宽终端中使用

---

## 🐛 故障排除

### 问题 1: 只显示一层结构

**原因**: Wiki 节点的 `has_children` 字段为 `None`

**解决方案**:
- v0.2.1 已修复，自动检测子节点
- 确保 API 客户端版本正确

### 问题 2: 找不到 Wiki 空间

**错误信息**: `❌ Wiki space not found: xxx`

**解决方案**:
```bash
# 先列出可用空间
uv run python scripts/create_wiki_doc.py --list-spaces

# 使用正确的空间名或 ID
uv run python scripts/list_wiki_tree.py -s "正确的空间名"
```

### 问题 3: 路径不存在

**错误信息**: `❌ Path not found: /xxx`

**解决方案**:
```bash
# 不指定路径，查看根结构
uv run python scripts/list_wiki_tree.py -s "产品文档"

# 从根结构找到正确的路径
```

---

## 🔄 与其他工具的配合

### 与 download_doc.py 配合

```bash
# 1. 预览结构，找到文档路径
uv run python scripts/list_wiki_tree.py -s "产品文档" | grep "API设计"

# 2. 使用完整路径下载
uv run python scripts/download_doc.py -s "产品文档" -p "/API/API设计" -o api_design.md
```

### 与 download_wiki.py 配合

```bash
# 1. 预览目录结构
uv run python scripts/list_wiki_tree.py -s "产品文档" -S "/API" -d 2

# 2. 确认后批量下载
uv run python scripts/download_wiki.py -s "产品文档" -S "/API" -d 2 ./api_backup
```

---

## 📚 相关文档

- [DOWNLOAD_GUIDE.md](DOWNLOAD_GUIDE.md) - 下载功能完整指南
- [DOWNLOAD_SCRIPTS_COMPARISON.md](DOWNLOAD_SCRIPTS_COMPARISON.md) - 工具对比指南
- [UNIFIED_WIKI_PATH_SEMANTICS.md](UNIFIED_WIKI_PATH_SEMANTICS.md) - 参数语义指南
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除指南

---

## 🎓 实战案例

### 案例 1: 新人快速上手

**场景**: 新员工需要快速了解公司知识库结构

**操作**:
```bash
# 1. 查看完整结构
uv run python scripts/list_wiki_tree.py -s "公司知识库"

# 2. 重点关注部门相关内容
uv run python scripts/list_wiki_tree.py -s "公司知识库" | grep "研发部"
```

### 案例 2: 备份前确认

**场景**: 定期备份前确认内容变化

**操作**:
```bash
# 1. 预览当前结构
uv run python scripts/list_wiki_tree.py --personal > current.txt

# 2. 与上次备份对比
diff current.txt last_backup.txt

# 3. 确认后备份
uv run python scripts/download_wiki.py --personal ./backup_$(date +%Y%m%d)
```

### 案例 3: 文档迁移前检查

**场景**: 将 Wiki 内容迁移到新位置前检查结构

**操作**:
```bash
# 1. 检查源空间结构
uv run python scripts/list_wiki_tree.py -s "旧空间" > source.txt

# 2. 检查目标空间结构
uv run python scripts/list_wiki_tree.py -s "新空间" > target.txt

# 3. 对比差异
diff source.txt target.txt
```

---

**最后更新**: 2026-01-18
**版本**: v0.3.0
**状态**: ✅ 生产就绪
**新增**: 并行优化（3-5x 性能提升）
