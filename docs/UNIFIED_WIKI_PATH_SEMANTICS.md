# 统一的 --wiki-path 参数语义

## 概述

本文档描述了 `--wiki-path` 参数在上传 (`create_wiki_doc.py`) 和下载 (`download_doc.py`) 操作中的统一语义。

## 问题背景

**原来的不一致行为**:

- **上传时**: `--wiki-path "/API/Reference"` → 指定父目录（不包含文档名）
- **下载时**: `--wiki-path "/API/Reference/REST API"` → 指定完整路径（包含文档名）

这种不一致性导致用户混淆，难以理解和使用。

## 统一的语义规则

### 核心原则

`--wiki-path` **始终表示父目录路径**，不包含文档名本身。

### 参数组合

#### 上传操作 (`create_wiki_doc.py`)

```bash
# 完整语法
uv run python scripts/create_wiki_doc.py <markdown_file> \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  # 文档名自动从文件名获取
```

- `--wiki-path`: 父目录路径（文档将创建在此目录下）
- 文档名: 自动从 markdown 文件名推断
- 可选的 `--title` 参数可以覆盖文档名

**示例**:
```bash
# 在 /API/Reference 目录下创建文档
uv run python scripts/create_wiki_doc.py api_guide.md \
  --space-name "产品文档" \
  --wiki-path "/API/Reference"

# 结果: 在 /API/Reference 下创建名为 "api_guide" 的文档
```

#### 下载操作 (`download_doc.py`)

```bash
# 完整语法
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "REST API" \
  -o rest_api.md
```

- `--wiki-path`: 父目录路径（在此目录下搜索文档）
- `--doc-name`: **必需参数**，指定要下载的文档名
- `-o`: 可选，输出文件路径

**示例**:
```bash
# 从 /API/Reference 目录下载名为 "REST API" 的文档
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "REST API" \
  -o rest_api.md
```

## 使用方法对比

### 上传和下载同一文档

**场景**: 在 `/产品文档/API/Reference` 目录下上传和下载 "REST API" 文档

#### 上传
```bash
uv run python scripts/create_wiki_doc.py rest_api.md \
  --space-name "产品文档" \
  --wiki-path "/API/Reference"
```

#### 下载
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "REST API" \
  -o rest_api.md
```

**对称性**: 两个操作都使用 `--wiki-path "/API/Reference"` 来指定父目录。

## 便捷模式

### 下载时省略 --wiki-path（递归搜索）

如果不确定文档所在的具体目录，可以省略 `--wiki-path`，系统会递归搜索整个知识空间:

```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "REST API" \
  -o rest_api.md
```

**行为**:
- 在整个知识空间中递归搜索名为 "REST API" 的文档
- 如果找到多个同名文档，会列出所有匹配项让用户选择
- 如果只找到一个，直接使用

### 使用建议

| 场景 | 推荐方法 | 理由 |
|------|---------|------|
| 知道文档的具体位置 | 使用 `--wiki-path` | 搜索快速，结果明确 |
| 不确定文档位置 | 省略 `--wiki-path` | 递归搜索，找到后可选择 |
| 文档名可能重复 | 使用 `--wiki-path` | 避免歧义，精确定位 |

## 错误处理

### 常见错误和解决方法

#### 1. 下载时忘记提供 --doc-name

**错误**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference"
```

**提示**:
```
ValueError: --doc-name is required
Usage examples:
  1. Search within parent directory:
     --space-name '产品文档' --wiki-path '/API/Reference' --doc-name 'REST API'
  2. Search entire space recursively:
     --space-name '产品文档' --doc-name 'REST API'
```

**解决**: 添加 `--doc-name` 参数

#### 2. 父目录路径不存在

**错误**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/NotExist/Path" \
  --doc-name "REST API"
```

**提示**:
```
ValueError: Parent directory not found: /NotExist/Path
```

**解决**: 检查路径是否正确，使用正确的父目录路径

#### 3. 文档在指定目录下不存在

**错误**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "NotExist"
```

**提示**:
```
ValueError: Document 'NotExist' not found under /API/Reference
Available documents in this directory:
  - REST API
  - GraphQL API
  - SDK Documentation
```

**解决**:
- 检查文档名是否正确
- 或使用列出的可用文档名
- 或省略 `--wiki-path` 进行递归搜索

## 技术实现

### 关键函数: resolve_document_id()

```python
def resolve_document_id(
    client: FeishuApiClient,
    space_name: str = None,
    wiki_path: str = None,  # 父目录路径
    doc_name: str = None,    # 文档名（必需）
) -> tuple[str, str]:
    """
    UNIFIED SEMANTICS:
    - --wiki-path: Parent directory path (e.g., "/API/Reference")
    - --doc-name: Document name (required)

    When --wiki-path is provided: searches for doc_name under that directory
    When --wiki-path is omitted: searches for doc_name recursively in entire space
    """
```

### 搜索逻辑

**情况 1: 提供 --wiki-path**
1. 解析 `wiki_path` 获取父目录的 `parent_token`
2. 获取该目录下的所有节点
3. 查找标题匹配 `doc_name` 的节点
4. 返回找到的文档

**情况 2: 未提供 --wiki-path**
1. 从根节点开始递归搜索整个知识空间
2. 收集所有标题匹配 `doc_name` 的节点
3. 如果找到多个，让用户选择
4. 返回选择的文档

## 迁移指南

### 从旧版本迁移

如果您之前使用的是旧版本的下载脚本，需要调整参数:

**旧版本** (完整路径):
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference/REST API"
```

**新版本** (父目录 + 文档名):
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --wiki-path "/API/Reference" \
  --doc-name "REST API"
```

**或者使用递归搜索**:
```bash
uv run python scripts/download_doc.py \
  --space-name "产品文档" \
  --doc-name "REST API"
```

## 优势总结

### 1. **一致性**
- 上传和下载使用相同的参数语义
- 减少认知负担，更容易理解和记忆

### 2. **清晰性**
- `--wiki-path` 始终表示"位置"（父目录）
- `--doc-name` 或文件名表示"内容"（文档本身）
- 职责明确，不会混淆

### 3. **灵活性**
- 可以精确指定父目录（快速、明确）
- 也可以递归搜索（便捷、兼容不确定情况）
- 多个同名文档时提供选择界面

### 4. **可维护性**
- 参数含义统一，代码逻辑更清晰
- 错误提示更准确，用户体验更好
- 未来扩展更容易

## 参考

- 上传脚本: `/home/howie/Software/utility/Reference/md-to-feishu/scripts/create_wiki_doc.py`
- 下载脚本: `/home/howie/Software/utility/Reference/md-to-feishu/scripts/download_doc.py`
- 备份的旧版本: `/home/howie/Software/utility/Reference/md-to-feishu/scripts/download_doc_old.py`

## 版本历史

- **v0.2.0** (2026-01-18): 实现统一的 `--wiki-path` 语义
  - 修改 `download_doc.py` 使 `--wiki-path` 表示父目录
  - `--doc-name` 成为必需参数
  - 添加递归搜索支持
  - 添加多文档选择界面
