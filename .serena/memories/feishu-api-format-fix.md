# 飞书 API 格式修复 - 会话总结

**日期**: 2026-01-17
**会话类型**: 故障诊断和修复
**状态**: ✅ 完成

## 问题描述

用户运行 `create_feishu_doc.py` 上传 README.md 到飞书时遇到 HTTP 400 错误：
```
ERROR: API Error: Failed to create blocks: HTTP 400
Response: {"code":1770001,"msg":"invalid param",...}
```

## 诊断过程

### 1. 初始假设（错误）
- 怀疑是批量大小超过 50 块限制
- 怀疑是空 text 元素导致参数无效
- 检查发现批处理逻辑正常工作

### 2. 关键发现
通过对比 MCP feishu-docker 工具的成功调用，发现根本原因是 **API 请求格式错误**。

**错误格式** (我们的代码):
```json
{
  "elements": [{
    "text": "内容",
    "style": {"bold": true}
  }]
}
```

**正确格式** (飞书 API 要求):
```json
{
  "elements": [{
    "text_run": {
      "content": "内容",
      "text_element_style": {
        "bold": true,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "inline_code": false
      }
    }
  }]
}
```

## 修复内容

### 修改的文件
`lib/feishu_api_client.py`

### 修复的方法

1. **`_format_text_block()`**
   - 改用 `text_run` → `content` 格式
   - 改用 `text_element_style` 并包含所有必需字段
   - 过滤空字符串元素

2. **`_format_heading_block()`**
   - 修正 block_type: heading1=3, heading2=4, ..., heading9=11
   - 使用动态字段名: `heading1`, `heading2`, etc.
   - 改用 `text_run` 格式

3. **`_format_code_block()`**
   - 修正 block_type: 14
   - 改用 `text_run` → `content` 格式
   - 正确的 `style` 结构: `{language, wrap}`

4. **`_format_list_block()`**
   - 修正 block_type: bullet=12, ordered=13
   - 使用动态字段名: `bullet` 或 `ordered`
   - 改用 `text_run` 格式

5. **`_convert_text_style()`**
   - 所有样式字段必须存在（默认 false）
   - 字段完整列表: bold, italic, underline, strikethrough, inline_code

### 添加的调试功能
- 错误时自动保存 payload 到 `/tmp/feishu_error_payload.json`

## 飞书 API Block Type 映射

| Block 类型 | block_type 编号 | 字段名 |
|-----------|----------------|--------|
| Text | 2 | `text` |
| Heading1 | 3 | `heading1` |
| Heading2 | 4 | `heading2` |
| ... | 5-11 | `heading3-9` |
| Bullet List | 12 | `bullet` |
| Ordered List | 13 | `ordered` |
| Code | 14 | `code` |

## 测试验证

**测试命令**:
```bash
uv run python scripts/create_feishu_doc.py README.md --title "修复后测试"
```

**测试结果**:
```
✅ 文档创建成功
✅ 110 个块全部上传
✅ 自动分批: 50 + 50 + 10
✅ 文档 URL: https://feishu.cn/docx/Kv2ddekz6odGS2x4tNrccufhnbf
```

## 关键技术要点

### 1. 飞书 API 格式要求严格
- 元素必须使用 `text_run` → `content` 结构
- 所有样式字段必须显式声明（不能省略）
- Block type 和字段名必须完全匹配

### 2. 调试策略
- 使用 MCP feishu-docker 工具作为正确格式参考
- 对比成功和失败的请求格式
- 逐步简化测试（从 110 块 → 50 块 → 3 块 → 1 块）
- 保存完整 payload 用于离线分析

### 3. 错误代码含义
- `1770001` "invalid param": 参数格式错误
- `1770024` "invalid operation": 操作不允许（如无权限）

## 经验教训

1. **不要假设 API 格式**：即使测试通过，实际 API 格式可能不同
2. **使用工作的参考实现**：MCP 工具是验证正确格式的最佳方式
3. **逐步简化问题**：从大到小缩小问题范围
4. **保存调试数据**：完整的 payload 对离线分析很有帮助

## 后续工作

- ✅ 所有功能已恢复正常
- ✅ 批量上传工作正常
- ⏸️ 需要更新测试用例以匹配新的 API 格式
- ⏸️ 需要更新文档说明正确的 block 格式

## Git 提交

**未提交的更改**:
```bash
M lib/feishu_api_client.py  # 修复了所有块格式化方法
```

**建议提交信息**:
```
fix: Correct Feishu API block format for all block types

- Fix text_run format: use content + text_element_style
- Fix block_type numbers: heading=3-11, bullet=12, ordered=13, code=14
- Fix heading field names: use heading1, heading2, etc.
- Add debug payload save on API errors
- Filter empty text elements

Resolves HTTP 400 "invalid param" errors when creating documents.
Verified with 110-block README.md upload.
```

---

**会话状态**: ✅ 完成并验证
**下次会话**: 可以安全使用，所有功能正常
