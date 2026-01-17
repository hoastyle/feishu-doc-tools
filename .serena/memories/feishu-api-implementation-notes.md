# Feishu Wiki API Implementation Notes

**Date**: 2025-01-17  
**Category**: architecture  
**Tags**: [feishu-api, wiki, drive, authentication]

## API Endpoints Discovery

### Root Folder API (v2 vs v1)

**问题**：原来使用 v1 API 返回 404

```python
# ❌ 错误（v1）
url = f"{self.BASE_URL}/drive/v1/metas/root_folder_meta"
folder_token = result.get("data", {}).get("folder_token")

# ✅ 正确（v2）
url = f"{self.BASE_URL}/drive/explorer/v2/root_folder/meta"  
folder_token = result.get("data", {}).get("token")  # 注意字段名变化
```

**关键差异**：
- v1: `data.folder_token`
- v2: `data.token`

参考来源：feishu-docker MCP TypeScript 实现

### Wiki Space APIs

```python
# 获取所有 wiki spaces
GET /wiki/v2/spaces?page_size=20

# 获取"我的文档库"（注意：不是"个人知识库"）
GET /wiki/v2/spaces/my_library?lang=en

# 创建 wiki node
POST /wiki/v2/spaces/{space_id}/nodes
{
  "title": "文档标题",
  "obj_type": "docx",
  "node_type": "origin"
}

# 返回格式
{
  "node": {
    "node_token": "nodcnXXXXX",  # Wiki 节点 ID
    "obj_token": "doxcnXXXXX"   # 文档 ID（用于上传内容）
  }
}
```

## Authentication Types

### tenant_access_token (应用凭证)
- 使用 app_id + app_secret 获取
- 所有文档操作都使用此 token
- 文档会创建在"应用空间"（需要额外权限设置）

### user_access_token (用户凭证)
- 未实现
- feishu-docker MCP 也不使用此方式

## Document Creation Modes

### Drive Folder Mode
```bash
python scripts/create_feishu_doc.py README.md --folder fldcnXXXXX
```
- API: `POST /docx/v1/documents/create`
- 文档创建在云盘文件夹
- **权限问题**：默认只有应用有权限

### Wiki Space Mode (推荐)
```bash
python scripts/create_wiki_doc.py README.md --space-id 7516222021840306180
# 或
python scripts/create_wiki_doc.py README.md --personal
```
- API: `POST /wiki/v2/spaces/{space_id}/nodes`
- 文档创建在知识库
- **优势**：自动继承知识库权限

## Space ID Confusion

### Three Different "Personal" Spaces

1. **My Document Library** (API 返回)
   - Space ID: `7595982960864578519`
   - 来源: `GET /wiki/v2/spaces/my_library`
   - **不是用户实际使用的空间**

2. **个人知识库** (用户实际使用)
   - Space ID: `7516222021840306180`
   - 来源: `GET /wiki/v2/spaces` 列表中的"个人知识库"
   - **这是用户真正需要的**

3. **Root Folder**
   - Token: `nodcn9knoStvUiO9UqR1IgLe1Oe`
   - User ID: `7595919847049972666`
   - 来源: `GET /drive/explorer/v2/root_folder/meta`

## Implementation Detail

### --personal Flag Detection Logic

```python
def detect_personal_space():
    all_spaces = client.get_all_wiki_spaces()
    
    # 1. 精确匹配"个人知识库"
    for space in all_spaces:
        if space.get("name") == "个人知识库":
            return space.get("space_id")
    
    # 2. 模糊匹配（作为后备）
    for space in all_spaces:
        name = space.get("name", "")
        if "个人" in name or "知识库" in name or "Library" in name:
            return space.get("space_id")
    
    # 3. 未找到，显示所有可用空间
    logger.error("Could not find '个人知识库' space")
    for space in all_spaces:
        logger.info(f"  - {space.get('name')} (space_id: {space.get('space_id')})")
```

## Related Commits

- `91d28af`: feat: Add wiki space support and workspace info retrieval
- `24e5119`: feat: Add --personal flag for automatic personal knowledge base detection
- `20f105c`: fix: Correct Feishu API block format to match official specification

## Known Issues

### Block Upload HTTP 400
- **现象**: `examples/sample.md` 上传失败
- **错误**: `{"code":1770001,"msg":"invalid param"}`
- **状态**: 简单文件可成功，复杂文件失败
- **优先级**: 中等（有绕过方案：手动创建后上传）

## See Also

- `wiki-personal-flag-implementation.md`: 用户问题解决决策记录
- Feishu API 官方文档: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create
