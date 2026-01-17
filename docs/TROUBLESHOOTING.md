# 故障排查指南

本文档记录了常见问题及其解决方案。

## 问题1：pytest 模块未找到

**症状：**
```
ModuleNotFoundError: No module named 'pytest'
```

**原因：**
pytest 是开发依赖，需要用 `--extra dev` 标志安装。

**解决方案：**
```bash
# 安装包括开发依赖的所有包
uv sync --extra dev

# 然后运行测试
uv run pytest tests/
```

**预防：**
- 首次设置项目时始终使用 `uv sync --extra dev`
- 在文档中明确说明开发依赖的安装方法

---

## 问题2：Feishu API 返回 HTTP 400 - "max len is 50"

**症状：**
```
ERROR: API Error: Failed to create blocks: HTTP 400
Response: {"field_violations":[{"field":"children","description":"the max len is 50"}]}
```

**原因：**
飞书API对单个请求中的块数有硬限制：最多50个块。原代码尝试一次发送110个块，导致验证失败。

**解决方案：**
修复 `batch_create_blocks()` 方法以自动分批：

1. 添加 `batch_size` 参数（默认50，最大50）
2. 将输入块分成多个50块的批次
3. 逐批发送请求
4. 聚合所有结果

**代码变更：**
```python
def batch_create_blocks(
    self,
    doc_id: str,
    blocks: List[Dict[str, Any]],
    parent_id: Optional[str] = None,
    index: int = 0,
    batch_size: int = 50  # 新增参数
) -> Dict[str, Any]:
    # ... 强制执行最大50块的限制
    batch_size = min(batch_size, 50)

    # ... 分批处理
    for batch_start in range(0, len(blocks), batch_size):
        # 处理每个50块的批次
```

**测试验证：**
- 110个块的文档现在分成3个批次（50+50+10）
- 每个批次单独发送和验证
- 所有批次成功后聚合结果

---

## 问题3：代码块缺少必需字段

**症状：**
```
field_violations: [{"field":"children[*].code.elements","description":"children[*].code.elements is required"}]
```

**原因：**
飞书 API 要求代码块包含 `elements` 字段，但原代码的 `_format_code_block()` 没有提供该字段。

**解决方案：**
在代码块格式化中添加 `elements` 字段：

```python
def _format_code_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
    """Format code block for API"""
    code_config = options.get("code", {})
    code = code_config.get("code", "")
    language = code_config.get("language", 1)  # 改为1（PlainText）

    return {
        "block_type": 3,
        "code": {
            "code": code,
            "language": language,
            "elements": [{  # 新增必需字段
                "text": code,
                "style": {}
            }]
        }
    }
```

**影响：**
- 所有代码块现在包含正确的元素结构
- 兼容飞书API的所有版本

---

## 问题4：环境配置问题

### 问题4a：找不到 .env 文件

**症状：**
```
ValueError: FEISHU_APP_ID environment variable not set
```

**解决方案：**
```bash
# 在项目根目录创建 .env 文件
cp .env.example .env

# 编辑 .env 文件并填入凭证
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
```

### 问题4b：凭证无效

**症状：**
```
FeishuApiAuthError: Failed to get tenant token: ...
```

**解决方案：**
1. 验证 APP_ID 和 APP_SECRET 正确
2. 确保应用已启用 API 权限
3. 检查应用的有效期是否过期
4. 参考飞书官方文档获取最新凭证

---

## 问题5：批量创建时部分文档失败

**症状：**
```
Total Files:    10
✅ Successful:  8
❌ Failed:      2
```

**解决方案：**
查看失败列表中的错误消息：

```python
for failure in result['failures']:
    print(f"Failed: {failure['file']}: {failure['error']}")
```

**常见原因和解决方案：**

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `No such file or directory` | 文件不存在 | 检查文件路径和文件是否存在 |
| `Failed to create document` | API错误 | 检查凭证、权限、磁盘空间 |
| `Could not convert` | Markdown格式问题 | 验证Markdown文件格式是否正确 |
| `Invalid folder token` | 文件夹token错误 | 获取正确的文件夹token |

**重试失败的文件：**
```bash
# 只重试特定文件
python scripts/create_feishu_doc.py path/to/failed_file.md

# 或查看失败原因后重试整个文件夹
python scripts/batch_create_docs.py ./docs -v  # 启用详细日志
```

---

## 问题6：性能和超时问题

**症状：**
```
Timeout waiting for API response
```

**解决方案：**

1. **检查网络连接：**
   ```bash
   python scripts/test_api_connectivity.py
   ```

2. **减少批大小（如有效）：**
   ```bash
   # 设置环境变量（仅用于测试）
   export FEISHU_BATCH_SIZE=30
   uv run python scripts/batch_create_docs.py ./docs
   ```

3. **增加超时时间：**
   ```python
   # 在代码中修改
   client = FeishuApiClient.from_env()
   client.session.timeout = 60  # 增加到60秒
   ```

4. **检查飞书服务状态：**
   - 访问飞书官方状态页面
   - 检查是否有服务中断

---

## 问题7：图片上传失败

**症状：**
```
Failed to upload image: ...
ERROR: Failed to bind image: ...
```

**常见原因和解决方案：**

| 原因 | 解决方案 |
|------|--------|
| 文件不存在 | 检查本地图片路径 |
| 格式不支持 | 转换为PNG/JPG/GIF/WebP |
| 文件过大 | 压缩图片（<10MB） |
| URL无法访问 | 检查网络图片URL是否有效 |
| 权限问题 | 检查文件读取权限 |

**测试图片上传：**
```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

# 测试本地图片
try:
    result = client.upload_and_bind_image(
        doc_id="doxcnxxxxx",
        block_id="block_id",
        image_path_or_url="/path/to/image.png"
    )
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {e}")
```

---

## 调试技巧

### 启用详细日志

```bash
# 方式1：使用 CLI 详细模式
python scripts/create_feishu_doc.py README.md -v

# 方式2：Python 代码
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 检查 API 响应

```python
# 在代码中添加调试输出
import json
response_text = response.json()
print(json.dumps(response_text, indent=2, ensure_ascii=False))
```

### 验证 Markdown 转换

```bash
# 检查转换输出
python scripts/md_to_feishu.py README.md doxcnxxxxx \
  --output /tmp/blocks.json

# 查看生成的块
python -c "import json; print(json.dumps(json.load(open('/tmp/blocks.json')), indent=2, ensure_ascii=False)[:2000])"
```

### 测试 API 连接

```bash
# 使用内置连通性测试
python scripts/test_api_connectivity.py
```

---

## 最佳实践

### 1. 验证前准备
```bash
# 总是先验证凭证和连接
python scripts/test_api_connectivity.py

# 验证文件存在
ls -lh README.md

# 验证Markdown格式
python -c "import markdown; markdown.markdown(open('README.md').read())"
```

### 2. 小规模测试
```bash
# 先用单个文件测试
python scripts/create_feishu_doc.py README.md --title "测试"

# 然后批量创建
python scripts/batch_create_docs.py ./docs
```

### 3. 启用日志记录
```bash
# 捕获详细日志以便调试
python scripts/batch_create_docs.py ./docs -v > batch_create.log 2>&1

# 查看日志
tail -f batch_create.log
```

### 4. 监控进度
```bash
# 对大量文件，在另一个终端监控
watch -n 5 "ls -l /path/to/docs | wc -l"
```

---

## 获取帮助

### 检查资源

1. **API参考：** `docs/API_OPERATIONS.md`
2. **批量操作：** `docs/BATCH_OPERATIONS.md`
3. **实现计划：** `docs/IMPLEMENTATION_PLAN.md`
4. **飞书官方API：** https://open.feishu.cn/document/server-docs

### 报告问题

提交问题时，请包括：
1. 完整的错误消息
2. 详细的日志输出（使用 `-v` 标志）
3. 再现步骤
4. 环境信息（Python版本、uv版本等）

```bash
# 收集诊断信息
python -c "import sys; print(f'Python {sys.version}')"
uv --version
python scripts/test_api_connectivity.py
```

---

**最后更新：** 2026-01-17
**版本：** 1.0
