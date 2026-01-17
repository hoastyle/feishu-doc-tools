# Wiki Personal Flag Implementation

**Date**: 2025-01-17
**Category**: decision
**Tags**: [wiki, personal-knowledge-base, permissions, ux-improvement]

## Problem

用户使用 `create_feishu_doc.py` 创建的文档只有应用有权限，用户没有权限访问。

**原始问题**：
> "uv run python scripts/create_feishu_doc.py README.md --title '我的文档'创建的文档，只有应用有权限，我没有权限。该如何解决？"

## Root Cause Analysis

### 问题1：应用空间 vs 个人空间
- 默认使用 `tenant_access_token` 创建文档，会创建在"应用空间"
- 应用空间只有应用有权限，用户无法访问

### 问题2：API 返回错误的"个人知识库"
`get_my_library()` API 返回的是 "My Document Library" (space_id: `7595982960864578519`)，而不是用户实际使用的中文"个人知识库" (space_id: `7516222021840306180`)

**数据对比**：
```python
# get_my_library() 返回
{
  "space_id": "7595982960864578519",
  "name": "My Document Library"
}

# 用户实际需要的
{
  "space_id": "7516222021840306180", 
  "name": "个人知识库"
}
```

## Solution

### 实现：`--personal` 和 `--auto-permission` 标志

**scripts/create_wiki_doc.py**:

```python
# --personal: 自动检测"个人知识库"
if args.personal:
    all_spaces = client.get_all_wiki_spaces()
    for space in all_spaces:
        if space.get("name") == "个人知识库":
            space_id = space.get("space_id")
            break

# --auto-permission: 自动设置用户权限
if add_user_permission:
    info = client.get_comprehensive_info()
    user_id = info.get("root_folder", {}).get("user_id")
    client.set_document_permission(doc_id, user_id, "view")
    client.set_document_permission(doc_id, user_id, "edit")
```

## Usage

### 之前（手动方式）
```bash
# 需要先查找 space_id
python scripts/create_wiki_doc.py --list-spaces

# 然后手动指定
python scripts/create_wiki_doc.py README.md --space-id 7516222021840306180
```

### 现在（一键方式）
```bash
python scripts/create_wiki_doc.py README.md --personal --auto-permission
```

## Verification

**测试结果**：
```bash
$ python scripts/create_wiki_doc.py /tmp/test_simple.md --personal

✓ Detected '个人知识库': 个人知识库 (space_id: 7516222021840306180)
✅ Wiki Document Created Successfully
Document ID:     XvuwdhlApoXfIuxzLWBc4v8wnbf
Wiki URL:        https://feishu.cn/wiki/ZKUjwwFVEizOPukBDHJcn4acnfc
```

## Technical Notes

### Wiki 文档创建流程
1. 创建 wiki node：`POST /wiki/v2/spaces/{space_id}/nodes`
   - 返回 `node_token` 和 `obj_token` (document_id)
2. 上传内容：`POST /docx/v1/documents/{doc_id}/blocks/{parent_id}/children`

### 用户权限获取
```python
def get_comprehensive_info(self):
    # 调用 /drive/explorer/v2/root_folder/meta
    # 返回 user_id: "7595919847049972666"
```

### Known Issues
- `examples/sample.md` 上传时仍遇到 HTTP 400 错误（block 格式问题）
- 简单 markdown 文件可以正常上传

## Related Files

- `scripts/create_wiki_doc.py`: 添加 --personal 和 --auto-permission 参数
- `scripts/md_to_feishu_upload.py`: 修复参数名称错误
- `lib/feishu_api_client.py`: Wiki API 方法（之前提交）
- `README.md`: 更新使用说明

## Commit

```
24e5119 feat: Add --personal flag for automatic personal knowledge base detection
```

## Next Steps

- [ ] 调查 sample.md 上传失败的根本原因
- [ ] 考虑添加 `--list-spaces` 的更友好输出格式
- [ ] 文档化不同的 wiki space 类型差异
