#!/usr/bin/env python3
"""
飞书用户认证设置脚本

简化 OAuth 授权流程，自动处理授权码交换和令牌存储

使用方法:
    1. 运行脚本: uv run python scripts/setup_user_auth.py
    2. 在浏览器中访问生成的授权 URL
    3. 完成授权后，从回调 URL 中复制授权码
    4. 将授权码粘贴到脚本中
    5. 脚本自动交换令牌并更新 .env 文件
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from lib.feishu_api_client import FeishuApiClient, AuthMode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def get_env_file_path() -> Path:
    """获取 .env 文件路径"""
    cwd = Path.cwd()
    script_dir = Path(__file__).parent.parent

    # 查找 .env 文件
    for env_path in [
        cwd / ".env",
        script_dir / ".env",
    ]:
        if env_path.exists():
            return env_path

    # 如果不存在，返回项目根目录的 .env
    return script_dir / ".env"


def update_env_file(env_path: Path, refresh_token: str) -> bool:
    """更新 .env 文件中的用户认证配置

    Args:
        env_path: .env 文件路径
        refresh_token: 刷新令牌

    Returns:
        是否成功更新
    """
    try:
        # 读取现有内容
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        # 更新或添加配置
        updated = False
        new_lines = []

        # 检查是否已存在 FEISHU_AUTH_MODE
        has_auth_mode = any("FEISHU_AUTH_MODE" in line for line in lines)
        # 检查是否已存在 FEISHU_USER_REFRESH_TOKEN
        has_refresh_token = any("FEISHU_USER_REFRESH_TOKEN" in line for line in lines)

        for line in lines:
            if "FEISHU_AUTH_MODE" in line and not line.strip().startswith("#"):
                new_lines.append(f"FEISHU_AUTH_MODE=user\n")
                updated = True
            elif "FEISHU_USER_REFRESH_TOKEN" in line and not line.strip().startswith("#"):
                new_lines.append(f"FEISHU_USER_REFRESH_TOKEN={refresh_token}\n")
                updated = True
            else:
                new_lines.append(line)

        # 如果没有这些配置，添加到文件末尾
        if not has_auth_mode:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append("FEISHU_AUTH_MODE=user\n")
            updated = True

        if not has_refresh_token:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"FEISHU_USER_REFRESH_TOKEN={refresh_token}\n")
            updated = True

        # 写回文件
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True

    except Exception as e:
        logger.error(f"更新 .env 文件失败: {e}")
        return False


def main():
    """主函数"""
    print_section("飞书用户认证设置")

    # 加载环境变量
    env_path = get_env_file_path()
    if env_path.exists():
        logger.info(f"加载环境变量: {env_path}")
        load_dotenv(env_path)

    try:
        # 创建客户端（使用 tenant 模式进行 OAuth 流程）
        client = FeishuApiClient.from_env(env_path)

        print("\n✓ 应用凭证验证成功")

        # 生成 OAuth 授权 URL
        print_section("步骤 1: 获取授权 URL")

        # 提示用户配置重定向 URI
        print("\n⚠️  前置条件:")
        print("  请确保已在飞书开发者后台配置重定向 URI:")
        print("  应用 > 开发配置 > 安全设置 > 重定向 URL")
        print("  添加: http://localhost:3333/callback")

        redirect_uri = input("\n重定向 URI [默认: http://localhost:3333/callback]: ").strip()
        if not redirect_uri:
            redirect_uri = "http://localhost:3333/callback"

        oauth_url = client.generate_oauth_url(redirect_uri=redirect_uri)

        print("\n请访问以下 URL 进行授权:")
        print(f"\n{oauth_url}\n")

        # 等待用户输入授权码
        print_section("步骤 2: 输入授权码")
        print("\n完成授权后，从浏览器地址栏的回调 URL 中复制 'code' 参数")
        print("\n示例回调 URL:")
        print("http://localhost:3333/callback?code=xxx&state=yyy")
        print("\n请复制 'code=' 后面的内容\n")

        authorization_code = input("授权码: ").strip()

        if not authorization_code:
            logger.error("授权码不能为空")
            sys.exit(1)

        # 交换令牌
        print_section("步骤 3: 交换令牌")

        try:
            result = client.exchange_authorization_code(authorization_code)

            print("\n✓ 令牌交换成功!")
            print(f"\n用户信息:")
            print(f"  姓名: {result['name']}")
            print(f"  Open ID: {result['open_id']}")
            print(f"  邮箱: {result.get('email', '未设置')}")
            print(f"\n令牌信息:")
            print(f"  Access Token: {result['access_token'][:30]}...")
            print(f"  Refresh Token: {result['refresh_token'][:30]}...")
            print(f"  过期时间: {result['expires_in']} 秒")

            # 保存令牌到 .env 文件
            print_section("步骤 4: 保存配置")

            if update_env_file(env_path, result['refresh_token']):
                print(f"\n✓ 配置已保存到: {env_path}")
                print("\n更新后的配置:")
                print("  FEISHU_AUTH_MODE=user")
                print(f"  FEISHU_USER_REFRESH_TOKEN={result['refresh_token'][:30]}...")
            else:
                print("\n✗ 自动保存失败，请手动添加以下内容到 .env 文件:")
                print(f"\n  FEISHU_AUTH_MODE=user")
                print(f"  FEISHU_USER_REFRESH_TOKEN={result['refresh_token']}")

            # 验证配置
            print_section("步骤 5: 验证配置")

            print("\n正在验证用户认证...")
            test_client = FeishuApiClient.from_env(env_path)
            if test_client.auth_mode == AuthMode.USER:
                try:
                    user_info = test_client.get_user_info()
                    print("\n✓ 用户认证验证成功!")
                    print(f"  当前用户: {user_info.get('name')} ({user_info.get('email')})")
                except Exception as e:
                    print(f"\n⚠️  验证失败: {e}")
                    print("  请检查配置是否正确")

            print_section("完成")
            print("\n✓ 用户认证设置完成!")
            print("\n现在可以使用用户身份调用飞书 API:")
            print("  uv run python scripts/create_wiki_doc.py README.md --personal")
            print("\n创建的文档将属于您，而非应用。")

        except Exception as e:
            logger.error(f"令牌交换失败: {e}")
            print("\n可能的原因:")
            print("  1. 授权码已过期或已使用")
            print("  2. redirect_uri 与开发者后台配置不一致")
            print("  3. 应用凭证错误")
            sys.exit(1)

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        print("\n请确保:")
        print("  1. .env 文件中配置了 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        print("  2. 应用凭证有效")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
