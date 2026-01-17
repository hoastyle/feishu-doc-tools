"""
Feishu Markdown Uploader

使用MCP工具将Markdown文件上传到飞书文档的封装类。
这个类负责协调转换脚本和MCP工具调用。
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional


class FeishuMdUploader:
    """Markdown到飞书文档上传器"""

    def __init__(self, script_path: Optional[Path] = None):
        """
        初始化上传器

        Args:
            script_path: 转换脚本路径，默认为scripts/md_to_feishu.py
        """
        if script_path is None:
            # 默认脚本路径（相对于项目根目录）
            self.script_path = Path(__file__).parent.parent / "scripts" / "md_to_feishu.py"
        else:
            self.script_path = script_path

        if not self.script_path.exists():
            raise FileNotFoundError(f"Conversion script not found: {self.script_path}")

    def convert_md_to_json(
        self,
        md_file: Path,
        doc_id: str,
        output_path: Optional[Path] = None,
        batch_size: int = 50,
        image_mode: str = 'local',
        max_text_length: int = 2000
    ) -> Dict[str, Any]:
        """
        调用转换脚本将MD转为JSON

        Args:
            md_file: Markdown文件路径
            doc_id: 飞书文档ID
            output_path: 输出JSON路径
            batch_size: 每批blocks数量
            image_mode: 图片处理模式
            max_text_length: 单个text block最大长度

        Returns:
            转换结果字典
        """
        if output_path is None:
            output_path = Path("/tmp/feishu_blocks.json")

        # 构建命令
        cmd = [
            "python",
            str(self.script_path),
            str(md_file),
            doc_id,
            "--output", str(output_path),
            "--batch-size", str(batch_size),
            "--image-mode", image_mode,
            "--max-text-length", str(max_text_length)
        ]

        # 执行转换
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Conversion failed: {result.stderr}")

        # 解析stdout中的结果摘要
        try:
            summary = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse conversion output: {result.stdout}")

        if not summary.get('success'):
            raise RuntimeError(f"Conversion failed: {summary.get('error')}")

        # 读取完整的JSON文件
        with output_path.open('r', encoding='utf-8') as f:
            full_result = json.load(f)

        return full_result

    def prepare_mcp_calls(self, conversion_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备MCP工具调用的数据结构

        Args:
            conversion_result: 转换结果

        Returns:
            包含MCP调用指令的字典
        """
        doc_id = conversion_result['documentId']
        batches = conversion_result['batches']
        images = conversion_result['images']

        return {
            'documentId': doc_id,
            'totalBatches': len(batches),
            'totalImages': len(images),
            'batches': [
                {
                    'batchIndex': batch['batchIndex'],
                    'startIndex': batch['startIndex'],
                    'blockCount': len(batch['blocks']),
                    'mcpTool': 'mcp__feishu-docker__batch_create_feishu_blocks',
                    'mcpParams': {
                        'documentId': doc_id,
                        'parentBlockId': doc_id,
                        'index': batch['startIndex'],
                        'blocks': batch['blocks']
                    }
                }
                for batch in batches
            ],
            'images': [
                {
                    'blockIndex': img['blockIndex'],
                    'batchIndex': img['batchIndex'],
                    'localPath': img['localPath'],
                    'mcpTool': 'mcp__feishu-docker__upload_and_bind_image_to_block',
                    # 注意：blockId需要在批次创建后获取
                    'needsBlockId': True
                }
                for img in images
            ]
        }

    def generate_upload_instructions(self, md_file: Path, doc_id: str) -> str:
        """
        生成上传指令文档（供AI使用）

        Args:
            md_file: Markdown文件路径
            doc_id: 飞书文档ID

        Returns:
            AI可执行的上传步骤说明
        """
        # 转换为JSON
        conversion_result = self.convert_md_to_json(md_file, doc_id)

        # 准备MCP调用
        mcp_calls = self.prepare_mcp_calls(conversion_result)

        # 生成指令文档
        instructions = f"""
# Markdown上传到飞书文档指令

## 文件信息
- Markdown文件: {md_file}
- 目标文档ID: {doc_id}
- 总Blocks数: {conversion_result['metadata']['totalBlocks']}
- 总批次数: {conversion_result['metadata']['totalBatches']}
- 总图片数: {conversion_result['metadata']['totalImages']}

## 执行步骤

### 第1步：批量创建Blocks（共{len(mcp_calls['batches'])}批）

"""
        for batch_info in mcp_calls['batches']:
            instructions += f"""
#### 批次 {batch_info['batchIndex'] + 1}/{len(mcp_calls['batches'])}
- startIndex: {batch_info['startIndex']}
- blockCount: {batch_info['blockCount']}

调用MCP工具：
```
工具名: {batch_info['mcpTool']}
参数: {json.dumps(batch_info['mcpParams'], ensure_ascii=False, indent=2)}
```

"""

        if mcp_calls['images']:
            instructions += f"""
### 第2步：上传图片（共{len(mcp_calls['images'])}张）

**注意**: 需要先从第1步的响应中获取对应block的blockId

"""
            for i, img_info in enumerate(mcp_calls['images'], 1):
                instructions += f"""
#### 图片 {i}/{len(mcp_calls['images'])}
- 本地路径: {img_info['localPath']}
- blockIndex: {img_info['blockIndex']}（在批次{img_info['batchIndex']}中）

调用MCP工具：
```
工具名: {img_info['mcpTool']}
参数:
{{
  "documentId": "{doc_id}",
  "images": [
    {{
      "blockId": "<从批次响应中获取>",
      "imagePathOrUrl": "{img_info['localPath']}"
    }}
  ]
}}
```

"""

        instructions += """
## 完成提示

上传完成后，向用户报告：
- ✓ 已上传 X 个blocks（Y批次）
- ✓ 已上传 Z 张图片
- ✓ 文档链接：https://xxx.feishu.cn/docx/{doc_id}
"""

        return instructions


# 便捷函数，供AI直接调用
def upload_md_to_feishu(md_file: str, doc_id: str) -> str:
    """
    将Markdown文件上传到飞书文档

    这是一个简化的接口函数，供AI助手直接调用。
    它会生成详细的MCP调用指令，AI需要按照指令执行。

    Args:
        md_file: Markdown文件路径（字符串）
        doc_id: 飞书文档ID

    Returns:
        上传指令文档

    Example:
        >>> instructions = upload_md_to_feishu("example.md", "doc123")
        >>> print(instructions)  # AI读取指令并执行MCP调用
    """
    uploader = FeishuMdUploader()
    return uploader.generate_upload_instructions(Path(md_file), doc_id)
