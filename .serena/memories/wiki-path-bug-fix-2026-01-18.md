# Wiki Path 参数不生效 Bug 修复

**日期**: 2026-01-18
**问题**: 使用 `--wiki-path` 参数时，文档仍然创建在根目录，而不是指定的路径下

## 问题表现

```bash
# 指定了 wiki-path
uv run python scripts/batch_create_wiki_docs.py docs/test \
  --wiki-path "表格测试-220326" \
  --personal

# 日志显示路径解析成功
2026-01-18 08:52:11,775 - INFO - Resolving wiki path: 表格测试-220326
2026-01-18 08:52:12,315 - INFO - Resolved path to node token: FTz7wpiDeiMcGDkWTVucZREGnjg
2026-01-18 08:52:12,315 - INFO -   Resolved to parent token: FTz7wpiDeiMcGDkWTVucZREGnjg

# 但是文档仍然创建在根目录下
```

## 根本原因

在 `scripts/batch_create_wiki_docs.py` 的 `main` 函数中：

**第 319-323 行**：正确解析了 wiki-path
```python
parent_token = args.parent_token
if args.wiki_path:
    client = FeishuApiClient.from_env() if not args.app_id else FeishuApiClient(args.app_id, args.app_secret)
    logger.info(f"Resolving wiki path: {args.wiki_path}")
    try:
        parent_token = client.resolve_wiki_path(space_id, args.wiki_path)  # ✅ 正确解析
        logger.info(f"  Resolved to parent token: {parent_token}")
    except Exception as e:
        parser.error(str(e))
```

**第 333 行**：传递了错误的变量
```python
result = batch_create_wiki_docs(
    folder_path=args.folder,
    space_id=space_id,
    parent_token=args.parent_token,  # ❌ 错误！应该是 parent_token
    pattern=args.pattern,
    ...
)
```

## 问题分析

1. 局部变量 `parent_token` 被正确赋值为解析后的 node token
2. 但调用函数时传递的是 `args.parent_token`（原始命令行参数，为 None）
3. 因此文档创建时没有使用解析后的 parent token，导致创建在根目录

## 解决方案

修改第 333 行，使用解析后的 `parent_token` 而不是 `args.parent_token`：

```python
result = batch_create_wiki_docs(
    folder_path=args.folder,
    space_id=space_id,
    parent_token=parent_token,  # ✅ 使用解析后的值
    pattern=args.pattern,
    ...
)
```

## 修复位置

- **文件**: `scripts/batch_create_wiki_docs.py`
- **函数**: `main`
- **行号**: 333

## 影响范围

- ✅ 修复 `--wiki-path` 参数不生效的问题
- ✅ `--parent-token` 参数不受影响（因为它直接赋值给 parent_token）
- ✅ 向后兼容，不影响现有功能

## 验证方法

```bash
# 测试 wiki-path 参数
uv run python scripts/batch_create_wiki_docs.py docs/test \
  --wiki-path "表格测试-220326" \
  --personal

# 预期结果：文档应该创建在 "表格测试-220326" 节点下，而不是根目录
```

## 相关修复

同一会话中还修复了：
- 表格创建失败的 bug（空单元格问题）

## 教训

1. **变量命名要清晰**：局部变量和参数同名容易混淆
2. **代码审查的重要性**：这种简单的变量错误应该在 code review 中发现
3. **测试覆盖**：应该有集成测试覆盖 wiki-path 参数的场景
