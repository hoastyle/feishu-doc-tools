# Phase 2: 用户体验改进实施计划

## 📋 计划概述

**目标**: 改进用户体验，让用户不需要手动查找 ID 和 token

**关键原则**:
1. ✅ **保留所有原有参数** - 不破坏现有功能
2. ✅ **新增便捷参数** - 提供更友好的使用方式
3. ✅ **参数互斥选择** - 新旧参数二选一
4. ✅ **向后兼容** - 现有脚本和用法完全兼容

---

## 🎯 参数设计

### Wiki 空间指定

| 参数 | 类型 | 说明 | 优先级 |
|------|------|------|--------|
| `--space-id` | 原有 | 直接指定知识库 ID | 保留 |
| `--space-name` | **新增** | 按名称查找知识库 | 新增 |

**使用规则**:
```bash
# 方式1: 使用 space-id（原有）
uv run python scripts/create_wiki_doc.py README.md --space-id 74812***88644

# 方式2: 使用 space-name（新增）
uv run python scripts/create_wiki_doc.py README.md --space-name "产品文档"

# ❌ 错误：不能同时使用
uv run python scripts/create_wiki_doc.py README.md --space-id xxx --space-name "xxx"
```

**验证逻辑**:
- 如果 `--space-id` 和 `--space-name` 都未提供 → 报错
- 如果 `--space-id` 和 `--space-name` 都提供了 → 报错
- 如果只提供其中一个 → 正常执行

---

### Wiki 节点层级指定

| 参数 | 类型 | 说明 | 优先级 |
|------|------|------|--------|
| `--parent-token` | 原有 | 直接指定父节点 token | 保留 |
| `--wiki-path` | **新增** | 按路径指定层级（如 "/API/参考"） | 新增 |

**使用规则**:
```bash
# 方式1: 使用 parent-token（原有）
uv run python scripts/create_wiki_doc.py api.md --parent-token nodcnXXX --space-id 74812***

# 方式2: 使用 wiki-path（新增）
uv run python scripts/create_wiki_doc.py api.md --wiki-path "/产品文档/API/参考" --space-name "产品文档"

# ❌ 错误：不能同时使用
uv run python scripts/create_wiki_doc.py api.md --parent-token xxx --wiki-path "/xxx"
```

**路径格式**:
- 以 `/` 开头表示从根节点开始
- 不以 `/` 开头表示从指定父节点开始（如果有父节点上下文）
- 路径中的空格需要用引号包裹

**验证逻辑**:
- 如果 `--parent-token` 和 `--wiki-path` 都提供了 → 报错
- 如果都不提供 → 创建在根节点（原有行为）
- 如果只提供其中一个 → 正常执行

---

## 🔧 技术实现

### 1. 新增 API 方法

#### 1.1 按名称查找知识库

```python
def find_wiki_space_by_name(self, name: str) -> Optional[str]:
    """
    按名称查找知识库

    Args:
        name: 知识库名称

    Returns:
        space_id 或 None

    Raises:
        FeishuApiRequestError: 找到多个匹配的知识库
    """
    spaces = self.get_all_wiki_spaces()

    # 查找完全匹配
    matches = [s for s in spaces if s.get("name") == name]

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0].get("space_id")
    else:
        # 多个匹配，返回详细信息让用户选择
        raise FeishuApiRequestError(
            f"找到多个名为 '{name}' 的知识库，请使用 --space-id 指定：\n" +
            "\n".join([f"  - {s['name']} (ID: {s['space_id']})" for s in matches])
        )
```

#### 1.2 获取 Wiki 节点列表

```python
def get_wiki_node_list(
    self,
    space_id: str,
    parent_node_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取 Wiki 节点列表

    Args:
        space_id: 知识库 ID
        parent_node_token: 父节点 token，None 表示获取根节点

    Returns:
        节点列表

    API: GET /wiki/v2/spaces/{space_id}/nodes
    """
    url = f"{self.BASE_URL}/wiki/v2/spaces/{space_id}/nodes"
    params = {}
    if parent_node_token:
        params["parent_node_token"] = parent_node_token

    response = self.session.get(url, params=params, headers=self._get_headers())
    result = response.json()

    if result.get("code") != 0:
        raise FeishuApiRequestError(f"获取节点列表失败: {result.get('msg')}")

    return result.get("data", {}).get("items", [])
```

#### 1.3 按名称查找节点

```python
def find_wiki_node_by_name(
    self,
    space_id: str,
    name: str,
    parent_token: Optional[str] = None
) -> Optional[str]:
    """
    按名称查找 Wiki 节点

    Args:
        space_id: 知识库 ID
        name: 节点标题/名称
        parent_token: 父节点 token，None 表示从根节点查找

    Returns:
        node_token 或 None
    """
    nodes = self.get_wiki_node_list(space_id, parent_token)

    # 查找匹配的节点（匹配 title 字段）
    matches = [n for n in nodes if n.get("title") == name]

    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0].get("node_token")
    else:
        # 多个同名节点，返回第一个
        logger.warning(f"找到多个名为 '{name}' 的节点，使用第一个")
        return matches[0].get("node_token")
```

#### 1.4 解析 Wiki 路径

```python
def resolve_wiki_path(
    self,
    space_id: str,
    path: str
) -> Optional[str]:
    """
    解析 Wiki 路径，返回最深层级节点的 token

    Args:
        space_id: 知识库 ID
        path: 路径，如 "/产品文档/API/参考" 或 "API/参考"

    Returns:
        最深层级节点的 token，如果路径不存在返回 None

    Raises:
        FeishuApiRequestError: 路径中间某个节点不存在
    """
    # 解析路径
    if path.startswith("/"):
        path = path[1:]  # 移除开头的 /

    parts = [p for p in path.split("/") if p]

    if not parts:
        return None  # 空路径

    # 逐级查找
    parent_token = None

    for i, part in enumerate(parts):
        node_token = self.find_wiki_node_by_name(space_id, part, parent_token)

        if node_token is None:
            raise FeishuApiRequestError(
                f"路径不存在: '{path}'\n"
                f"在节点 '{'/' .join(parts[:i])}' 下找不到 '{part}'"
            )

        parent_token = node_token

    return parent_token
```

---

### 2. CLI 参数增强

#### 2.1 create_wiki_doc.py

```python
parser.add_argument(
    "--space-id",
    type=str,
    help="知识库 ID（与 --space-name 二选一）"
)

parser.add_argument(
    "--space-name",
    type=str,
    help="知识库名称（与 --space-id 二选一）"
)

parser.add_argument(
    "--parent-token",
    type=str,
    help="父节点 token（与 --wiki-path 二选一）"
)

parser.add_argument(
    "--wiki-path",
    type=str,
    help="Wiki 路径，如 '/API/参考'（与 --parent-token 二选一）"
)

# 验证逻辑
def validate_args(args):
    # space-id 和 space-name 互斥验证
    if args.space_id and args.space_name:
        parser.error("--space-id 和 --space-name 不能同时使用，请只选择一个")

    if not args.space_id and not args.space_name and not args.list_spaces:
        parser.error("必须指定 --space-id 或 --space-name")

    # parent-token 和 wiki-path 互斥验证
    if args.parent_token and args.wiki_path:
        parser.error("--parent-token 和 --wiki-path 不能同时使用，请只选择一个")

# 解析 space-name
space_id = args.space_id
if args.space_name:
    space_id = client.find_wiki_space_by_name(args.space_name)
    if not space_id:
        parser.error(f"找不到名为 '{args.space_name}' 的知识库")

# 解析 wiki-path
parent_token = args.parent_token
if args.wiki_path:
    parent_token = client.resolve_wiki_path(space_id, args.wiki_path)
```

#### 2.2 batch_create_wiki_docs.py

相同的逻辑应用于批量上传脚本。

---

## 📝 文档更新

### 使用示例

```bash
# 原有方式（仍然支持）
uv run python scripts/create_wiki_doc.py README.md \
  --space-id 74812***88644 \
  --parent-token nodcnXXX

# 新方式1: 按名称指定知识库
uv run python scripts/create_wiki_doc.py README.md \
  --space-name "产品文档"

# 新方式2: 按路径指定层级
uv run python scripts/create_wiki_doc.py api.md \
  --space-name "产品文档" \
  --wiki-path "/API/参考"

# 批量上传到指定路径
uv run python scripts/batch_create_wiki_docs.py ./docs \
  --space-name "产品文档" \
  --wiki-path "/开发文档"
```

---

## ✅ 验收标准

### 功能验收

- [ ] `find_wiki_space_by_name()` 能正确查找知识库
- [ ] `find_wiki_space_by_name()` 找不到时返回 None
- [ ] `find_wiki_space_by_name()` 多个匹配时抛出明确错误
- [ ] `get_wiki_node_list()` 能获取节点列表
- [ ] `find_wiki_node_by_name()` 能正确查找节点
- [ ] `resolve_wiki_path()` 能正确解析路径
- [ ] `resolve_wiki_path()` 路径不存在时抛出明确错误

### CLI 验收

- [ ] `--space-id` 和 `--space-name` 同时使用时报错
- [ ] 都不提供时报错
- [ ] 只提供其中一个时正常工作
- [ ] `--parent-token` 和 `--wiki-path` 同时使用时报错
- [ ] 都不提供时创建在根节点
- [ ] 只提供其中一个时正常工作

### 兼容性验收

- [ ] 所有原有参数和行为保持不变
- [ ] 现有脚本和用法完全兼容
- [ ] 不提供新参数时使用原有逻辑

---

## 📊 实施进度

| 任务 | 状态 | 说明 |
|------|------|------|
| 新增 API 方法 | 待实施 | 4个新方法 |
| 单元测试 | 待实施 | 测试覆盖 |
| create_wiki_doc.py 增强 | 待实施 | 参数和验证 |
| batch_create_wiki_docs.py 增强 | 待实施 | 参数和验证 |
| 文档更新 | 待实施 | 使用示例 |
| 集成测试 | 待实施 | 真实环境测试 |

**预计工作量**: 2-3 天
**风险**: 中等（需要真实 Wiki 空间测试）

---

## 🚀 后续计划

Phase 2 完成后，可以考虑：
- Phase 1: 下载功能（如需要）
- 更多用户体验改进
- 性能优化

---

**最后更新**: 2025-01-18
**状态**: 📋 计划中
**优先级**: 🔴 高
