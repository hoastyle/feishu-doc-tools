# 飞书表格创建 Bug 修复记录

**日期**: 2026-01-18
**问题**: 批量上传包含表格的文档时，所有包含表格的文档都失败，错误码 1770001 "invalid param"

## 问题分析

### 错误表现
- ✅ 不包含表格的文档：上传成功
- ❌ 包含表格的文档：全部失败（HTTP 400，错误码 1770001）
- 错误信息：`{"code":1770001,"msg":"invalid param"}`

### 根本原因

在 `lib/feishu_api_client.py` 的 `_format_text_block` 方法（第 2063-2066 行）中，代码会跳过空内容的单元格：

```python
if not text_content and not equation_content:
    continue
if text_content == "":  # ← 这行导致空字符串被跳过
    continue
```

这导致空单元格生成了**空的 elements 数组**：
```json
{
  "text": {
    "elements": [],  // ← 错误：空数组
    "style": {"align": 1}
  }
}
```

而根据飞书 API 官方文档，即使是空单元格也必须包含至少一个 text_run：
```json
{
  "text": {
    "elements": [{"text_run": {"content": ""}}]  // ← 正确：至少有一个空 text_run
  }
}
```

## 解决方案

修改 `_format_text_block` 方法：

1. **移除重复检查**：删除 `if text_content == "": continue`
2. **允许空字符串**：空字符串应该正常生成 text_run
3. **兜底保护**：如果 text_elements 最终为空，添加一个空的 text_run

```python
# 修改后的代码
for style in text_styles:
    text_content = style.get("text", "")
    equation_content = style.get("equation", "")

    # 只跳过完全没有内容的情况
    if not text_content and not equation_content:
        continue
    
    # 不再跳过空字符串！
    # ... 正常处理 ...

# 兜底：确保至少有一个元素
if not text_elements:
    text_elements.append({"text_run": {"content": ""}})
```

## 修复位置

- **文件**: `lib/feishu_api_client.py`
- **方法**: `_format_text_block` (第 2050-2087 行)
- **修改行**: 2063-2066, 2084-2086

## 影响范围

- ✅ 修复所有包含表格的文档上传失败问题
- ✅ 保持向后兼容（不影响现有功能）
- ✅ 符合飞书 API 官方规范

## 验证方法

```bash
# 测试包含表格的文档
uv run python scripts/batch_create_wiki_docs.py docs \
  --wiki-path "表格测试" \
  --space-name "个人知识库"

# 预期结果：所有文档（包括包含表格的）都能成功上传
```

## 相关文档

- 飞书 API 文档：https://open.feishu.cn/document/docs/docs/faq
- 官方示例：创建包含内容的表格块
- Context7 查询结果：TextElementData - TextRun 结构

## 教训

1. **遵循官方规范**：即使是空内容也要符合 API 要求
2. **测试边界情况**：空单元格是常见场景，必须测试
3. **善用工具**：Sequential Thinking + Context7 + Tavily 帮助快速定位问题
4. **保存错误 payload**：`/tmp/feishu_table_error_payload.json` 对调试至关重要

## 后续优化

- [ ] 添加单元测试覆盖空单元格场景
- [ ] 考虑添加 payload 验证器
- [ ] 更新文档说明空单元格的处理逻辑
