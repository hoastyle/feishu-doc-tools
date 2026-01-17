#!/usr/bin/env python3
"""
List accessible folders in Feishu Drive.

This script helps you find folder tokens that you can use for document creation.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient, FeishuApiClientError

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """List accessible folders."""
    try:
        # Initialize client
        client = FeishuApiClient.from_env()

        print("=" * 60)
        print("📂 飞书文件夹列表")
        print("=" * 60)

        # Try to get root folder
        try:
            root_token = client.get_root_folder_token()
            print(f"\n📁 应用根文件夹: {root_token}")

            # List contents
            print(f"\n正在列出根文件夹内容...")
            items = client.list_folder_contents(root_token)

            if items:
                print(f"\n找到 {len(items)} 个项目:")
                for i, item in enumerate(items, 1):
                    name = item.get('name', 'Unknown')
                    token = item.get('token', '')
                    type_ = item.get('type', 'unknown')
                    icon = '📁' if type_ == 'folder' else '📄'

                    print(f"\n{i}. {icon} {name}")
                    print(f"   类型: {type_}")
                    print(f"   Token: {token}")

                    if type_ == 'folder':
                        # Try to list subfolder contents
                        try:
                            sub_items = client.list_folder_contents(token)
                            print(f"   包含: {len(sub_items)} 个项目")
                        except Exception as e:
                            print(f"   (无法访问子内容: {e})")
            else:
                print("根文件夹为空")

        except FeishuApiClientError as e:
            print(f"\n❌ 无法访问根文件夹: {e}")
            print("\n💡 这可能是因为:")
            print("   1. 应用没有足够的权限")
            print("   2. 需要使用 user_access_token 而不是 tenant_access_token")
            print("\n📝 建议的操作:")
            print("   1. 在飞书云文档中手动创建一个文件夹")
            print("   2. 从 URL 复制文件夹 token")
            print("   3. 添加到 .env: FEISHU_DEFAULT_FOLDER_TOKEN=<token>")

        print("\n" + "=" * 60)
        print("✅ 完成")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
