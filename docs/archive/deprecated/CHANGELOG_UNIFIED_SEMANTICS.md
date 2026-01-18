# 统一 --wiki-path 参数语义 - 变更日志

## 版本信息

- **版本**: v0.2.0
- **日期**: 2026-01-18
- **变更类型**: Breaking Change (向后兼容性断裂)

## 变更概述

统一了 `create_wiki_doc.py` (上传) 和 `download_doc.py` (下载) 中 `--wiki-path` 参数的语义，使其在两个操作中具有一致的含义。

## 核心变更

### 之前的行为 (不一致)

**上传 (`create_wiki_doc.py`)**:
```bash
--wiki-path "/API/Reference"  # 父目录路径
# 文档创建在 /API/Reference 下
```

**下载 (`download_doc.py` - 旧版本)**:
```bash
--wiki-path "/API/Reference/REST API"  # 完整路径（包含文档名）
# 下载路径为 /API/Reference/REST API 的文档
```

### 现在的行为 (统一)

**上传 (`create_wiki_doc.py`)** - 无变更:
```bash
--wiki-path "/API/Reference"  # 父目录路径
# 文档创建在 /API/Reference 下
```

**下载 (`download_doc.py` - 新版本)**:
```bash
--wiki-path "/API/Reference"  # 父目录路径（与上传一致）
--doc-name "REST API"          # 文档名（必需）
# 在 /API/Reference 目录下查找名为 "REST API" 的文档
```

## 关键变更点

### 1. 参数语义变更

**`--wiki-path` 参数**:
- **原来**: 在下载时表示完整路径（包含文档名）
- **现在**: 始终表示父目录路径（不包含文档名）

**`--doc-name` 参数**:
- **原来**: 可选参数，作为 `--wiki-path` 的替代方案
- **现在**: 必需参数（除非使用递归搜索模式）

### 2. 新增功能

#### 递归搜索模式

当省略 `--wiki-path` 参数时，系统会递归搜索整个知识空间：

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "REST API"
```

**特性**:
- 在整个知识空间中查找文档
- 如果找到多个同名文档，提供交互式选择界面
- 适用于不确定文档具体位置的场景

#### 多文档选择界面

当递归搜索找到多个同名文档时，会显示选择界面：

```
Found 3 documents named 'REST API':

  [1] /产品文档/API/REST API
      Type: doc, Has children: False
  [2] /技术文档/API/REST API
      Type: doc, Has children: False
  [3] /内部文档/REST API
      Type: doc, Has children: False

Please select a document:
Enter number (1-3):
```

### 3. 错误处理改进

#### 缺少必需参数

```bash
# 错误用法
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference"

# 错误提示
ValueError: --doc-name is required
Usage examples:
  1. Search within parent directory:
     --space-name '产品文档' --wiki-path '/API/Reference' --doc-name 'REST API'
  2. Search entire space recursively:
     --space-name '产品文档' --doc-name 'REST API'
```

#### 路径不存在

```bash
# 错误提示
ValueError: Parent directory not found: /NotExist/Path
```

#### 文档不存在

```bash
# 错误提示
ValueError: Document 'NotExist' not found under /API/Reference
Available documents in this directory:
  - REST API
  - GraphQL API
  - SDK Documentation
```

## 迁移指南

### 对于现有用户

如果您之前使用的是旧版本的 `download_doc.py`，需要按以下方式调整：

#### 迁移步骤 1: 拆分完整路径

**旧版本**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference/REST API"
```

**新版本 (方法 1 - 精确路径)**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "REST API"
```

**新版本 (方法 2 - 递归搜索)**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "REST API"
```

#### 迁移步骤 2: 选择搜索策略

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 文档位置明确 | 使用 `--wiki-path` + `--doc-name` | 快速、精确 |
| 文档位置不确定 | 仅使用 `--doc-name` | 递归搜索整个空间 |
| 可能有同名文档 | 使用 `--wiki-path` + `--doc-name` | 避免歧义 |

### 自动化脚本迁移

如果您有自动化脚本使用旧版本的参数格式，可以使用以下方法进行迁移：

#### 方法 1: 手动拆分路径

```bash
#!/bin/bash
# 旧版本参数
FULL_PATH="/API/Reference/REST API"

# 拆分为父目录和文档名
PARENT_PATH=$(dirname "$FULL_PATH")
DOC_NAME=$(basename "$FULL_PATH")

# 使用新版本参数
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "$PARENT_PATH" \
  --doc-name "$DOC_NAME"
```

#### 方法 2: 使用递归搜索（简化）

```bash
#!/bin/bash
# 只需要文档名
DOC_NAME="REST API"

# 使用递归搜索
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "$DOC_NAME"
```

## 技术实现

### 核心函数变更

**`resolve_document_id()` 函数**:

```python
def resolve_document_id(
    client: FeishuApiClient,
    space_name: Optional[str] = None,
    wiki_path: Optional[str] = None,  # 父目录路径
    doc_name: Optional[str] = None,    # 文档名（必需）
) -> Tuple[str, str]:
    """
    UNIFIED SEMANTICS (matches create_wiki_doc.py):
    - --wiki-path: Parent directory path (e.g., "/API/Reference")
    - --doc-name: Document name (required)

    When --wiki-path is provided: searches for doc_name under that directory
    When --wiki-path is omitted: searches for doc_name recursively in entire space
    """
```

**搜索逻辑**:

1. **情况 1: 提供 `--wiki-path`**
   - 解析父目录路径获取 `parent_token`
   - 获取该目录下的所有节点
   - 查找标题匹配 `doc_name` 的节点

2. **情况 2: 未提供 `--wiki-path`**
   - 从根节点开始递归搜索
   - 收集所有匹配的文档
   - 如果找到多个，提供选择界面

### 新增辅助函数

```python
def find_document_by_name_recursive(
    client: FeishuApiClient,
    space_id: str,
    doc_name: str,
    parent_token: Optional[str] = None,
    current_path: str = "",
) -> List[Dict]:
    """
    Recursively search for documents by name in a wiki space.
    """
```

## 优势分析

### 1. 一致性

**优势**:
- 上传和下载使用相同的参数语义
- 减少学习曲线和认知负担
- 更容易记忆和理解

**示例**:
```bash
# 上传
uv run python scripts/create_wiki_doc.py api.md \
  --space-name "产品文档" \
  --wiki-path "/API/Reference"

# 下载（对称）
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "api"
```

### 2. 清晰性

**优势**:
- `--wiki-path` 始终表示"位置"（父目录）
- `--doc-name` 或文件名表示"内容"（文档本身）
- 职责明确，不会混淆

### 3. 灵活性

**优势**:
- 可以精确指定父目录（快速、明确）
- 也可以递归搜索（便捷、容错）
- 多个同名文档时提供选择

### 4. 可维护性

**优势**:
- 代码逻辑更清晰
- 错误提示更准确
- 未来扩展更容易

## 测试验证

### 单元测试

新增测试用例覆盖：
- ✅ 使用 `--wiki-path` + `--doc-name` 的精确搜索
- ✅ 仅使用 `--doc-name` 的递归搜索
- ✅ 多文档选择界面
- ✅ 错误处理和提示

### 集成测试

验证场景：
- ✅ 上传后立即下载（参数对称性）
- ✅ 在不同深度的目录中下载
- ✅ 递归搜索整个知识空间
- ✅ 处理同名文档的情况

## 文档更新

### 新增文档

1. **[docs/UNIFIED_WIKI_PATH_SEMANTICS.md](/home/howie/Software/utility/Reference/md-to-feishu/docs/UNIFIED_WIKI_PATH_SEMANTICS.md)**
   - 完整的参数语义说明
   - 使用示例和最佳实践
   - 错误处理指南

2. **本文档** - 变更日志和迁移指南

### 更新文档

1. **[README.md](/home/howie/Software/utility/Reference/md-to-feishu/README.md)**
   - 更新场景 7 的示例
   - 添加统一语义文档链接

2. **[scripts/download_doc.py](/home/howie/Software/utility/Reference/md-to-feishu/scripts/download_doc.py)**
   - 更新帮助文本
   - 添加详细示例

## 已知限制

### 1. 向后兼容性

**限制**: 旧版本的脚本使用完整路径的方式不再支持

**影响**: 现有自动化脚本需要修改

**解决方案**: 参考"迁移指南"部分

### 2. 交互式选择

**限制**: 在非交互式环境（如 CI/CD）中，多文档选择会失败

**影响**: 自动化流程需要明确指定路径

**解决方案**: 使用 `--wiki-path` 参数精确指定父目录

## 未来计划

### 短期 (v0.2.x)

- [ ] 添加 `--non-interactive` 参数用于自动化场景
- [ ] 添加 `--first` 参数自动选择第一个匹配项
- [ ] 改进错误提示的本地化

### 中期 (v0.3.x)

- [ ] 支持正则表达式搜索文档名
- [ ] 添加文档缓存机制提高搜索速度
- [ ] 支持批量下载时的路径模式匹配

### 长期 (v1.0+)

- [ ] 图形化界面支持
- [ ] 配置文件支持（预设空间和路径）
- [ ] 历史记录和快速重用

## 参考资料

### 相关文档

- [统一的 --wiki-path 参数语义](UNIFIED_WIKI_PATH_SEMANTICS.md)
- [README.md](../README.md)
- [下载功能审查报告](DOWNLOAD_FUNCTION_REVIEW.md)

### 代码文件

- [scripts/download_doc.py](/home/howie/Software/utility/Reference/md-to-feishu/scripts/download_doc.py)
- [scripts/create_wiki_doc.py](/home/howie/Software/utility/Reference/md-to-feishu/scripts/create_wiki_doc.py)
- [scripts/download_doc_old.py](/home/howie/Software/utility/Reference/md-to-feishu/scripts/download_doc_old.py) (备份)

## 贡献者

- **作者**: Claude Code
- **审核**: Human Reviewer
- **测试**: Automated Test Suite

## 许可证

MIT License - 与项目主许可证相同

---

**最后更新**: 2026-01-18
**文档版本**: 1.0
