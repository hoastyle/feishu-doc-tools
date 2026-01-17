#!/usr/bin/env python3
"""
Markdown to Feishu Blocks Converter

将Markdown文件转换为飞书文档blocks的JSON表示，不占用AI模型上下文。
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

try:
    from markdown_it import MarkdownIt
    from markdown_it.token import Token
except ImportError:
    print("Error: markdown-it-py not found. Install it with: pip install markdown-it-py", file=sys.stderr)
    sys.exit(1)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# 代码语言映射表（Markdown → 飞书language code）
LANGUAGE_MAP = {
    'python': 49, 'py': 49,
    'javascript': 30, 'js': 30,
    'typescript': 63, 'ts': 63,
    'java': 29,
    'cpp': 9, 'c++': 9,
    'c': 10,
    'go': 22, 'golang': 22,
    'rust': 53, 'rs': 53,
    'bash': 7, 'sh': 7,
    'shell': 60,
    'json': 28,
    'html': 24,
    'css': 12,
    'sql': 56,
    'yaml': 67, 'yml': 67,
    'xml': 66,
    'markdown': 39, 'md': 39,
    'dockerfile': 18,
    'php': 43,
    'ruby': 52, 'rb': 52,
    'swift': 61,
    'kotlin': 32,
    'scala': 57,
    'r': 50,
    'perl': 44,
    'lua': 36,
    'matlab': 37,
}


class MarkdownToFeishuConverter:
    """Markdown转飞书blocks转换器"""

    def __init__(
        self,
        md_file: Path,
        doc_id: str,
        batch_size: int = 200,
        image_mode: str = 'local',
        max_text_length: int = 2000
    ):
        self.md_file = md_file
        self.doc_id = doc_id
        self.batch_size = batch_size
        self.image_mode = image_mode
        self.max_text_length = max_text_length

        self.blocks: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        self.md_parser = MarkdownIt().enable('table')

    def convert(self) -> Dict[str, Any]:
        """执行转换"""
        try:
            # 读取Markdown文件
            content = self.md_file.read_text(encoding='utf-8')
            logger.info(f"Read file: {self.md_file} ({len(content)} chars)")

            # 解析Markdown
            tokens = self.md_parser.parse(content)
            logger.info(f"Parsed {len(tokens)} tokens")

            # 转换为飞书blocks
            self._process_tokens(tokens)
            logger.info(f"Generated {len(self.blocks)} blocks")

            # 分批
            batches = self._create_batches()
            logger.info(f"Created {len(batches)} batches")

            # 生成上传说明
            upload_instructions = self._generate_upload_instructions(batches)

            # 构建结果
            result = {
                'success': True,
                'documentId': self.doc_id,
                'batches': batches,
                'images': self.images,
                'metadata': {
                    'totalBlocks': len(self.blocks),
                    'totalBatches': len(batches),
                    'totalImages': len(self.images)
                },
                'uploadInstructions': upload_instructions
            }

            return result

        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'errorType': type(e).__name__
            }

    def _process_tokens(self, tokens: List[Token]):
        """处理token列表"""
        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == 'heading_open':
                # 处理标题
                level = int(token.tag[1])  # h1 -> 1
                i = self._process_heading(tokens, i, level)
            elif token.type == 'paragraph_open':
                # 处理段落
                i = self._process_paragraph(tokens, i)
            elif token.type == 'fence':
                # 处理代码块
                self._process_code_block(token)
                i += 1
            elif token.type == 'bullet_list_open':
                # 处理无序列表
                i = self._process_list(tokens, i, ordered=False)
            elif token.type == 'ordered_list_open':
                # 处理有序列表
                i = self._process_list(tokens, i, ordered=True)
            elif token.type == 'blockquote_open':
                # 处理引用
                i = self._process_blockquote(tokens, i)
            elif token.type == 'table_open':
                # 处理表格
                i = self._process_table(tokens, i)
            else:
                i += 1

    def _process_heading(self, tokens: List[Token], start_idx: int, level: int) -> int:
        """处理标题"""
        # heading_open -> inline -> heading_close
        inline_token = tokens[start_idx + 1]
        content = self._extract_inline_text(inline_token)

        block = {
            'blockType': f'heading{level}',
            'options': {
                'heading': {
                    'level': level,
                    'content': content
                }
            }
        }
        self.blocks.append(block)

        return start_idx + 3  # 跳过3个token

    def _process_paragraph(self, tokens: List[Token], start_idx: int) -> int:
        """处理段落"""
        # paragraph_open -> inline -> paragraph_close
        inline_token = tokens[start_idx + 1]
        text_styles = self._extract_inline_styles(inline_token)

        # 如果段落为空（例如只包含被跳过的网络图片），则跳过
        if not text_styles or all(not style.get('text', '').strip() for style in text_styles):
            return start_idx + 3

        # 检查是否需要分割长段落
        total_length = sum(len(style.get('text', '')) for style in text_styles)
        if total_length > self.max_text_length:
            # 分割为多个block
            self._split_long_paragraph(text_styles)
        else:
            block = {
                'blockType': 'text',
                'options': {
                    'text': {
                        'textStyles': text_styles,
                        'align': 1
                    }
                }
            }
            self.blocks.append(block)

        return start_idx + 3

    def _process_code_block(self, token: Token):
        """处理代码块"""
        code = token.content.rstrip('\n')
        lang_str = token.info.strip()
        language = LANGUAGE_MAP.get(lang_str.lower(), 1)  # 默认PlainText

        block = {
            'blockType': 'code',
            'options': {
                'code': {
                    'code': code,
                    'language': language,
                    'wrap': False
                }
            }
        }
        self.blocks.append(block)

    def _process_list(self, tokens: List[Token], start_idx: int, ordered: bool) -> int:
        """处理列表"""
        i = start_idx + 1

        while i < len(tokens):
            token = tokens[i]

            if token.type == 'bullet_list_close' or token.type == 'ordered_list_close':
                return i + 1

            if token.type == 'list_item_open':
                # list_item_open -> paragraph_open -> inline -> paragraph_close -> list_item_close
                inline_token = tokens[i + 2]
                content = self._extract_inline_text(inline_token)

                block = {
                    'blockType': 'list',
                    'options': {
                        'list': {
                            'content': content,
                            'isOrdered': ordered,
                            'align': 1
                        }
                    }
                }
                self.blocks.append(block)

                i += 5  # 跳过list item的所有token
            else:
                i += 1

        return i

    def _process_blockquote(self, tokens: List[Token], start_idx: int) -> int:
        """处理引用（转为带前缀的text block）"""
        i = start_idx + 1
        quote_lines = []

        while i < len(tokens):
            token = tokens[i]

            if token.type == 'blockquote_close':
                break

            if token.type == 'paragraph_open':
                inline_token = tokens[i + 1]
                text = self._extract_inline_text(inline_token)
                quote_lines.append(text)
                i += 3
            else:
                i += 1

        # 合并为一个text block，每行加"> "前缀
        content = '\n'.join(f"> {line}" for line in quote_lines)

        block = {
            'blockType': 'text',
            'options': {
                'text': {
                    'textStyles': [{'text': content, 'style': {}}],
                    'align': 1
                }
            }
        }
        self.blocks.append(block)

        return i + 1

    def _process_table(self, tokens: List[Token], start_idx: int) -> int:
        """处理表格

        飞书表格需要使用 descendants API：
        - block_type: 31 表格主块
        - block_type: 32 表格单元格
        - block_type: 2  单元格内文本
        """
        i = start_idx + 1
        headers = []
        rows = []

        # 解析表格结构
        while i < len(tokens):
            token = tokens[i]

            if token.type == 'table_close':
                break

            # 解析表头
            if token.type == 'thead_open':
                i += 1  # 跳过 thead_open
                i += 1  # 跳过 tr_open
                while i < len(tokens) and tokens[i].type != 'tr_close':
                    if tokens[i].type == 'th_open':
                        # 获取单元格内容
                        inline_token = tokens[i + 1]
                        cell_text = self._extract_inline_text(inline_token)
                        headers.append(cell_text)
                        i += 3  # 跳过 th_open, inline, th_close
                    else:
                        i += 1
                i += 2  # 跳过 tr_close, thead_close

            # 解析表格内容行
            elif token.type == 'tbody_open':
                i += 1  # 跳过 tbody_open
                while i < len(tokens) and tokens[i].type != 'tbody_close':
                    if tokens[i].type == 'tr_open':
                        row = []
                        i += 1  # 跳过 tr_open
                        while i < len(tokens) and tokens[i].type != 'tr_close':
                            if tokens[i].type == 'td_open':
                                inline_token = tokens[i + 1]
                                cell_text = self._extract_inline_text(inline_token)
                                row.append(cell_text)
                                i += 3  # 跳过 td_open, inline, td_close
                            else:
                                i += 1
                        rows.append(row)
                        i += 1  # 跳过 tr_close
                    else:
                        i += 1
            else:
                i += 1

        # 生成表格配置
        column_size = len(headers) if headers else 0
        row_size = len(rows) + (1 if headers else 0)  # 包括表头行

        if column_size == 0 or row_size == 0:
            logger.warning("Empty table detected, skipping")
            return i + 1

        # 创建表格块（使用特殊标记，表示需要用 descendants API）
        table_block = {
            'blockType': 'table',
            'options': {
                'table': {
                    'columnSize': column_size,
                    'rowSize': row_size,
                    'cells': []
                }
            }
        }

        # 添加表头单元格
        for col_idx, header_text in enumerate(headers):
            table_block['options']['table']['cells'].append({
                'coordinate': {'row': 0, 'column': col_idx},
                'content': {
                    'blockType': 'text',
                    'options': {
                        'text': {
                            'textStyles': [{'text': header_text, 'style': {'bold': True}}],
                            'align': 1
                        }
                    }
                }
            })

        # 添加数据行单元格
        for row_idx, row_data in enumerate(rows):
            for col_idx, cell_text in enumerate(row_data):
                table_block['options']['table']['cells'].append({
                    'coordinate': {'row': row_idx + 1, 'column': col_idx},
                    'content': {
                        'blockType': 'text',
                        'options': {
                            'text': {
                                'textStyles': [{'text': cell_text, 'style': {}}],
                                'align': 1
                            }
                        }
                    }
                })

        self.blocks.append(table_block)
        logger.info(f"Created table: {row_size}x{column_size}")

        return i + 1

    def _extract_inline_text(self, inline_token: Token) -> str:
        """提取inline token的纯文本"""
        if not inline_token.children:
            return inline_token.content

        texts = []
        for child in inline_token.children:
            if child.type == 'text':
                texts.append(child.content)
            elif child.type == 'code_inline':
                texts.append(f"`{child.content}`")
            elif child.type in ['strong_open', 'em_open', 'link_open']:
                continue
            elif child.type in ['strong_close', 'em_close', 'link_close']:
                continue
            elif child.type == 'image':
                texts.append(f"[图片: {child.attrGet('alt') or 'image'}]")

        return ''.join(texts)

    def _extract_inline_styles(self, inline_token: Token) -> List[Dict[str, Any]]:
        """提取inline token的样式化文本"""
        if not inline_token.children:
            return [{'text': inline_token.content, 'style': {}}]

        styles = []
        current_style = {}
        current_text = []

        for child in inline_token.children:
            if child.type == 'text':
                current_text.append(child.content)
            elif child.type == 'code_inline':
                # 先保存当前文本
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                # 添加代码样式
                styles.append({
                    'text': child.content,
                    'style': {**current_style, 'inline_code': True}
                })
            elif child.type == 'strong_open':
                # 保存当前文本并更新样式
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style['bold'] = True
            elif child.type == 'strong_close':
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style.pop('bold', None)
            elif child.type == 'em_open':
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style['italic'] = True
            elif child.type == 'em_close':
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style.pop('italic', None)
            elif child.type == 's_open':
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style['strikethrough'] = True
            elif child.type == 's_close':
                if current_text:
                    styles.append({
                        'text': ''.join(current_text),
                        'style': current_style.copy()
                    })
                    current_text = []
                current_style.pop('strikethrough', None)
            elif child.type == 'image':
                # 处理图片
                self._handle_image(child, len(self.blocks))

        # 保存剩余文本
        if current_text:
            styles.append({
                'text': ''.join(current_text),
                'style': current_style
            })

        return styles if styles else [{'text': '', 'style': {}}]

    def _handle_image(self, token: Token, block_index: int):
        """处理图片"""
        src = token.attrGet('src')
        alt = token.attrGet('alt') or 'image'

        if not src:
            return

        # 判断是网络图片还是本地图片
        if src.startswith(('http://', 'https://')):
            if self.image_mode == 'local':
                logger.warning(f"Network image in local mode: {src}")
                return
            elif self.image_mode == 'skip':
                return
            # download模式暂不实现
        else:
            # 本地图片：解析相对路径
            local_path = (self.md_file.parent / src).resolve()
            if not local_path.exists():
                logger.warning(f"Image not found: {local_path}")
                return

            # 先创建空image block
            image_block = {
                'blockType': 'image',
                'options': {
                    'image': {}
                }
            }
            self.blocks.append(image_block)

            # 记录图片信息
            self.images.append({
                'blockIndex': len(self.blocks) - 1,
                'batchIndex': -1,  # 稍后计算
                'localPath': str(local_path),
                'altText': alt
            })

    def _split_long_paragraph(self, text_styles: List[Dict[str, Any]]):
        """分割超长段落"""
        current_chunk = []
        current_length = 0

        for style in text_styles:
            text = style.get('text', '')
            text_len = len(text)

            if current_length + text_len > self.max_text_length and current_chunk:
                # 创建一个block
                block = {
                    'blockType': 'text',
                    'options': {
                        'text': {
                            'textStyles': current_chunk,
                            'align': 1
                        }
                    }
                }
                self.blocks.append(block)
                current_chunk = []
                current_length = 0

            current_chunk.append(style)
            current_length += text_len

        # 添加最后一个chunk
        if current_chunk:
            block = {
                'blockType': 'text',
                'options': {
                    'text': {
                        'textStyles': current_chunk,
                        'align': 1
                    }
                }
            }
            self.blocks.append(block)

    def _create_batches(self) -> List[Dict[str, Any]]:
        """创建批次"""
        batches = []

        for i in range(0, len(self.blocks), self.batch_size):
            batch_blocks = self.blocks[i:i + self.batch_size]
            batch_index = len(batches)

            batches.append({
                'batchIndex': batch_index,
                'startIndex': i,
                'blocks': batch_blocks
            })

            # 更新图片的batch索引
            for img in self.images:
                if i <= img['blockIndex'] < i + self.batch_size:
                    img['batchIndex'] = batch_index

        return batches

    def _generate_upload_instructions(self, batches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成上传说明和一键脚本

        Returns:
            包含建议和脚本的上传说明字典
        """
        total_blocks = len(self.blocks)
        total_batches = len(batches)

        # 智能批次大小建议
        if total_blocks <= 200:
            recommended_batch_size = total_blocks  # 一次上传
            mcp_calls = 1
        elif total_blocks <= 1000:
            recommended_batch_size = 200
            mcp_calls = (total_blocks + 199) // 200
        else:
            recommended_batch_size = 500
            mcp_calls = (total_blocks + 499) // 500

        # 生成一键上传脚本
        script_lines = [
            "#!/bin/bash",
            "#",
            "# 飞书文档一键上传脚本",
            f"# 文档ID: {self.doc_id}",
            f"# 总blocks: {total_blocks}",
            f"# 批次数: {total_batches}",
            "#",
            "# 使用方法:",
            "# 1. 确保已安装 feishu-docker MCP",
            "# 2. 在 Claude Code 中执行以下命令:",
            "#",
            "",
            "DOC_ID=\"" + self.doc_id + "\"",
            "START_INDEX=0",
            ""
        ]

        current_idx = 0
        for i, batch in enumerate(batches):
            batch_num = i + 1
            block_count = len(batch['blocks'])
            script_lines.extend([
                f"# 批次 {batch_num}/{total_batches}: 索引 {current_idx}, {block_count} blocks",
                f"# 第{batch_num}次MCP调用，将批次数据保存到 /tmp/batch_{batch_num}.json",
                f'echo \'批次 {batch_num}/{total_batches}: 索引=$START_INDEX, blocks={block_count}\'',
                f"START_INDEX=$((START_INDEX + {block_count}))",
                ""
            ])
            current_idx += block_count

        script_lines.extend([
            "",
            "echo \"\"",
            "echo \"所有批次上传完成！\"",
            "echo \"总计上传: $START_INDEX blocks\"",
            ""
        ])

        upload_script = "\n".join(script_lines)

        # 生成 Claude Code 上传命令示例
        claude_commands = []
        current_index = 0
        for i, batch in enumerate(batches):
            batch_num = i + 1
            batch_file = f"/tmp/batch_{batch_num}.json"
            block_count = len(batch['blocks'])
            claude_commands.append(
                f"# 批次 {batch_num}/{total_batches}: index={current_index}, {block_count} blocks\n"
                f"# 将以下内容保存到 {batch_file}:\n"
                f"# {json.dumps(batch['blocks'], ensure_ascii=False)[:100]}...\n"
                f"# 然后执行:\n"
                f"# mcp__feishu-docker__batch_create_feishu_blocks(documentId=\"{self.doc_id}\", parentBlockId=\"{self.doc_id}\", index={current_index}, blocks=<从 {batch_file} 读取>)\n"
            )
            current_index += block_count

        return {
            'recommendedBatchSize': recommended_batch_size,
            'currentBatchSize': self.batch_size,
            'totalMcpCalls': total_batches,
            'recommendedMcpCalls': mcp_calls,
            'optimizationPotential': {
                'currentCalls': total_batches,
                'recommendedCalls': mcp_calls,
                'reductionPercent': int((1 - mcp_calls / total_batches) * 100) if total_batches > 0 else 0
            },
            'uploadScript': upload_script,
            'claudeCommands': claude_commands
        }


def main():
    parser = argparse.ArgumentParser(
        description='Convert Markdown file to Feishu document blocks JSON'
    )
    parser.add_argument('md_file', type=Path, help='Path to Markdown file')
    parser.add_argument('doc_id', type=str, help='Feishu document ID')
    parser.add_argument('--output', type=Path, default=Path('/tmp/feishu_blocks.json'),
                        help='Output JSON file path (default: /tmp/feishu_blocks.json)')
    parser.add_argument('--batch-size', type=int, default=200,
                        help='Blocks per batch (default: 200)')
    parser.add_argument('--image-mode', choices=['local', 'download', 'skip'], default='local',
                        help='Image handling mode (default: local)')
    parser.add_argument('--max-text-length', type=int, default=2000,
                        help='Max text length per block (default: 2000)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # 验证输入文件
    if not args.md_file.exists():
        print(json.dumps({
            'success': False,
            'error': f'File not found: {args.md_file}',
            'errorType': 'FileNotFoundError'
        }))
        sys.exit(1)

    # 转换
    converter = MarkdownToFeishuConverter(
        md_file=args.md_file,
        doc_id=args.doc_id,
        batch_size=args.batch_size,
        image_mode=args.image_mode,
        max_text_length=args.max_text_length
    )

    result = converter.convert()

    # 写入输出文件
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Output written to: {args.output}")

    # 打印结果摘要到stdout
    if result['success']:
        print(json.dumps({
            'success': True,
            'output': str(args.output),
            'metadata': result['metadata']
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
