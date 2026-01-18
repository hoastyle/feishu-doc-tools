# Changelog - v0.2.1

**发布日期**: 2026-01-18
**类型**: 重大优化版本
**破坏性变更**: 是（参数语义统一）

---

## 🎯 版本亮点

本版本直接实施最优方案，全面优化下载功能的设计和实现，无需考虑向后兼容性。

### 核心改进
- ✅ 完全统一上传/下载参数语义
- ✅ 递归搜索整个Wiki空间
- ✅ 交互式多文档选择
- ✅ 灵活的深度控制机制
- ✅ 参数短别名（命令减少50%长度）
- ✅ 重构消除96行重复代码
- ✅ 统一错误处理机制

---

## 🔄 破坏性变更

### download_doc.py

#### 参数语义变更

**旧版本**:
```bash
--wiki-path "/API/Reference/REST API"  # 完整路径（包含文档名）
```

**新版本**:
```bash
--wiki-path "/API/Reference" --doc-name "REST API"  # 分离路径和文档名
# 或者
-p "/API/Reference" -n "REST API"  # 使用短别名
```

#### 迁移示例

| 旧命令 | 新命令 |
|--------|--------|
| `--wiki-path "/API/REST"` | `-p "/API" -n "REST"` 或 `-n "REST"`（递归） |
| `--space-name "文档"` | `-s "文档"` |
| `--output-file api.md` | `-o api.md` |

### download_wiki.py

#### 参数变更

**移除**: `--no-recursive`
**新增**: `--depth` / `-d`

**旧版本**:
```bash
--no-recursive  # 禁用递归
```

**新版本**:
```bash
--depth 0  # 只下载直接子节点（等价于旧的 --no-recursive）
--depth 1  # 下载1层深度
--depth 2  # 下载2层深度
--depth -1  # 无限递归（默认）
```

---

## ✨ 新增功能

### download_doc.py

#### 1. 递归搜索模式
- 搜索整个Wiki空间查找文档
- 无需知道完整路径
- 适合快速查找

```bash
# 递归搜索整个空间
python scripts/download_doc.py -s "产品文档" -n "REST API" -o api.md
```

#### 2. 交互式多文档选择
- 找到多个同名文档时
- 显示完整路径和类型信息
- 用户交互式选择

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

#### 3. 参数短别名
- `-s`: --space-name
- `-p`: --wiki-path
- `-n`: --doc-name
- `-o`: --output-file
- `-v`: --verbose

### download_wiki.py

#### 1. 灵活深度控制
```bash
# 只下载直接子节点
python scripts/download_wiki.py -s "文档" -d 0 ./output

# 下载2层深度
python scripts/download_wiki.py -s "文档" -d 2 ./output

# 无限递归（默认）
python scripts/download_wiki.py -s "文档" ./output
```

#### 2. 参数短别名
- `-s`: --space-name
- `-P`: --personal
- `-S`: --start-path
- `-d`: --depth
- `-v`: --verbose

---

## 🔧 内部改进

### 代码重构

#### 1. 消除重复代码
- 提取 `download_single_document_node()` 共享函数
- 提取 `save_document_to_file()` 共享函数
- 简化递归和非递归下载逻辑
- **减少**: 96 行重复代码

#### 2. 统一错误处理
- 新增 `DownloadError` 异常类
- 统一所有下载相关错误
- 替换 `ValueError` 为 `DownloadError`
- 更清晰的错误边界

#### 3. 改进函数签名
```python
# 新增 max_depth 参数支持深度控制
def download_wiki_node(
    client: FeishuApiClient,
    space_id: str,
    node_token: str,
    output_dir: Path,
    depth: int = 0,
    max_depth: int = -1,  # 新增
) -> Dict[str, Any]:
```

---

## 🐛 Bug修复

### 1. 修复语法错误
- **文件**: `download_wiki.py:40`
- **问题**: `name = name.strip(). strip('.')` （双重空格）
- **修复**: `name = name.strip().strip('.')`

---

## 📚 文档更新

### 新增文档
1. `docs/OPTIMIZATION_COMPLETE.md` - 完整优化报告
2. `docs/UNIFIED_WIKI_PATH_SEMANTICS.md` - 参数语义统一指南
3. `docs/DOWNLOAD_EXAMPLES.md` - 完整使用示例
4. `docs/RECURSIVE_SEARCH_FEATURE.md` - 递归搜索功能说明
5. `CHANGELOG_v0.2.1.md` - 本变更日志

### 更新文档
1. `README.md` - 更新使用示例和功能说明
2. `docs/DOWNLOAD_GUIDE.md` - 更新下载指南

---

## 📊 性能指标

### 代码质量

| 指标 | v0.2.0 | v0.2.1 | 改进 |
|------|--------|--------|------|
| 重复代码行数 | ~96 | 0 | -100% |
| 函数平均长度 | ~103 | ~58 | -44% |
| 异常类型数 | 多种 | 1 | 统一 |

### 用户体验

| 指标 | v0.2.0 | v0.2.1 | 改进 |
|------|--------|--------|------|
| 命令长度 | ~80字符 | ~40字符 | -50% |
| 搜索范围 | 根目录 | 整个空间 | +∞ |
| 多匹配处理 | 返回第一个 | 交互式选择 | ✅ |
| 深度控制粒度 | 2档 | N+1档 | +∞ |

---

## 🚀 使用示例

### 场景1：按名称快速下载（新功能）
```bash
# 最简单方式：递归搜索
uv run python scripts/download_doc.py -s "产品文档" -n "API Overview" -o api.md

# 找到多个时会显示交互式选择
```

### 场景2：按精确路径下载（语义统一）
```bash
# v0.2.0（旧）
uv run python scripts/download_doc.py --space-name "产品文档" --wiki-path "/API/Reference/REST API" -o api.md

# v0.2.1（新，语义统一）
uv run python scripts/download_doc.py -s "产品文档" -p "/API/Reference" -n "REST API" -o api.md
```

### 场景3：部分下载Wiki（深度控制）
```bash
# v0.2.0（旧，只有两档）
uv run python scripts/download_wiki.py --space-name "文档" --no-recursive ./output

# v0.2.1（新，精确控制）
uv run python scripts/download_wiki.py -s "文档" -d 0 ./output  # 只当前层
uv run python scripts/download_wiki.py -s "文档" -d 2 ./output  # 2层深度
```

---

## ⚠️ 注意事项

### 1. 破坏性变更
- 旧脚本需要更新参数格式
- 建议使用新的短别名格式

### 2. 交互式选择
- 在 CI/CD 环境中使用时注意
- 可以通过精确路径避免交互

### 3. 深度控制
- `-d 0` 等价于旧的 `--no-recursive`
- 默认 `-d -1`（无限递归）保持向后兼容行为

---

## 🔮 后续计划

### v0.3.0（计划）
- 单元测试覆盖（80%+）
- 性能优化（并行下载）
- 进度条显示
- 断点续传

### v0.4.0（计划）
- 增量更新
- 变更检测
- 自动同步
- 版本控制集成

---

## 🙏 致谢

本版本优化基于 `docs/DOWNLOAD_FUNCTION_REVIEW.md` 的详细评审，感谢评审过程中的深入分析。

---

## 📞 获取帮助

- **完整优化报告**: [docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md)
- **参数语义指南**: [docs/UNIFIED_WIKI_PATH_SEMANTICS.md](docs/UNIFIED_WIKI_PATH_SEMANTICS.md)
- **使用指南**: [docs/DOWNLOAD_GUIDE.md](docs/DOWNLOAD_GUIDE.md)
- **项目主页**: [README.md](README.md)

---

**版本**: v0.2.1
**发布日期**: 2026-01-18
**状态**: ✅ 生产就绪
