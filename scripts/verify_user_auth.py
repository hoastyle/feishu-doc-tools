#!/usr/bin/env python3
"""
飞书用户认证验证脚本

验证 user_access_token API 端点的有效性

使用方法:
    1. 配置 .env 文件中的 FEISHU_APP_ID 和 FEISHU_APP_SECRET
    2. 运行: uv run python scripts/verify_user_auth.py
    3. 脚本将验证 OAuth 相关端点
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeishuUserAuthVerifier:
    """飞书用户认证验证器"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    # OAuth 相关端点（更新到 v2 API）
    # 授权端点使用 accounts.feishu.cn 域名
    OAUTH_AUTHORIZE_ENDPOINT = "/authen/v1/authorize"
    OAUTH_ACCESS_TOKEN_ENDPOINT = "/authen/v2/oauth/token"  # Updated to v2
    OAUTH_REFRESH_TOKEN_ENDPOINT = "/authen/v2/oauth/token"  # Updated to v2
    OAUTH_USER_INFO_ENDPOINT = "/authen/v1/user_info"

    # 原有端点
    TENANT_TOKEN_ENDPOINT = "/auth/v3/tenant_access_token/internal"

    def __init__(self, app_id: str, app_secret: str):
        """初始化验证器

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = requests.Session()

    def print_section(self, title: str):
        """打印分节标题"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def verify_endpoint_exists(self, endpoint: str, method: str = "GET") -> bool:
        """验证端点是否存在

        Args:
            endpoint: API 端点路径
            method: HTTP 方法

        Returns:
            端点是否有效
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            # 使用 HEAD 请求检查端点（不实际调用）
            response = self.session.head(url, timeout=10)

            # 如果 HEAD 不支持，尝试 GET
            if response.status_code == 405 or response.status_code == 404:
                response = self.session.request(method, url, timeout=10)

            # 401/403 说明端点存在但需要认证
            # 400/404 说明端点可能不存在或参数错误
            # 我们认为 401/403/400 都是端点存在的证明
            is_valid = response.status_code in [200, 400, 401, 403, 422]

            logger.info(f"端点 {method} {endpoint}: {response.status_code} - {'✓ 有效' if is_valid else '✗ 无效'}")

            return is_valid

        except requests.exceptions.RequestException as e:
            logger.error(f"端点验证失败 {endpoint}: {e}")
            return False

    def verify_tenant_token_flow(self) -> Dict[str, Any]:
        """验证现有的 tenant_token 流程

        Returns:
            验证结果字典
        """
        result = {
            "success": False,
            "token": None,
            "error": None
        }

        try:
            url = f"{self.BASE_URL}{self.TENANT_TOKEN_ENDPOINT}"
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }

            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                token = data.get("tenant_access_token")
                result["success"] = True
                result["token"] = token
                logger.info(f"✓ tenant_token 获取成功: {token[:20]}...")
            else:
                result["error"] = data.get("msg", "未知错误")
                logger.error(f"✗ tenant_token 获取失败: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"✗ tenant_token 获取异常: {e}")

        return result

    def verify_user_token_endpoints(self) -> Dict[str, bool]:
        """验证用户认证相关端点

        Returns:
            各端点的验证结果
        """
        results = {}

        endpoints = [
            ("OAuth 授权端点", self.OAUTH_AUTHORIZE_ENDPOINT, "GET"),
            ("获取用户令牌端点", self.OAUTH_ACCESS_TOKEN_ENDPOINT, "POST"),
            ("刷新用户令牌端点", self.OAUTH_REFRESH_TOKEN_ENDPOINT, "POST"),
            ("获取用户信息端点", self.OAUTH_USER_INFO_ENDPOINT, "GET"),
        ]

        for name, endpoint, method in endpoints:
            results[name] = self.verify_endpoint_exists(endpoint, method)

        return results

    def test_user_token_exchange(self, authorization_code: str) -> Dict[str, Any]:
        """测试使用授权码换取用户令牌

        Args:
            authorization_code: OAuth 授权码

        Returns:
            交换结果
        """
        result = {
            "success": False,
            "access_token": None,
            "refresh_token": None,
            "error": None
        }

        try:
            url = f"{self.BASE_URL}{self.OAUTH_ACCESS_TOKEN_ENDPOINT}"
            payload = {
                "grant_type": "authorization_code",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": authorization_code
            }

            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                token_data = data.get("data", {})
                result["success"] = True
                result["access_token"] = token_data.get("access_token")
                result["refresh_token"] = token_data.get("refresh_token")
                logger.info("✓ user_token 交换成功")
            else:
                result["error"] = data.get("msg", "未知错误")
                logger.error(f"✗ user_token 交换失败: {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"✗ user_token 交换异常: {e}")

        return result

    def generate_oauth_url(self, redirect_uri: str = "http://localhost:3333/callback") -> str:
        """生成 OAuth 授权 URL

        Args:
            redirect_uri: 回调地址

        Returns:
            授权 URL

        Note:
            使用 accounts.feishu.cn 域名，参数名使用 client_id
        """
        import random

        # 飞书 OAuth 授权所需的权限范围
        # 参考: https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code
        # 注意：wiki:wiki 不是有效权限，只使用 wiki:wiki:readonly
        scope = "docx:document docx:document:readonly wiki:wiki:readonly offline_access"

        # 使用纯数字 state（与官方 Go 代码一致）
        state = str(random.randint(1, 9007199254740991))

        # 必须使用 URLEncode 对所有参数值进行编码
        from urllib.parse import quote

        # 构建参数字典（所有值都需要 URL 编码）
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code",  # 必须是 "code"
            "state": state,
        }

        # 使用 accounts.feishu.cn 域名（不是 open.feishu.cn）
        auth_base_url = "https://accounts.feishu.cn/open-apis"
        url = f"{auth_base_url}{self.OAUTH_AUTHORIZE_ENDPOINT}?"
        # 正确的 URL 编码：所有参数值都需要编码（特别是 scope 中的空格）
        url += "&".join([f"{k}={quote(str(v), safe='')}" for k, v in params.items()])

        return url

    def run_full_verification(self):
        """运行完整的验证流程"""
        self.print_section("飞书用户认证验证")

        # 1. 验证应用凭证
        logger.info(f"应用 ID: {self.app_id}")
        logger.info(f"应用密钥: {self.app_secret[:10]}...")

        # 2. 验证 tenant_token 流程（基准测试）
        self.print_section("1. 验证现有 tenant_token 流程")
        tenant_result = self.verify_tenant_token_flow()

        if not tenant_result["success"]:
            logger.error("应用凭证验证失败，请检查 .env 配置")
            return

        # 3. 验证用户认证端点
        self.print_section("2. 验证用户认证端点")
        endpoint_results = self.verify_user_token_endpoints()

        valid_count = sum(1 for v in endpoint_results.values() if v)
        total_count = len(endpoint_results)
        logger.info(f"端点验证结果: {valid_count}/{total_count} 有效")

        # 4. 生成 OAuth 授权 URL
        self.print_section("3. OAuth 授权流程")
        oauth_url = self.generate_oauth_url()
        print("\n请按以下步骤测试 OAuth 流程:")
        print("\n1. 访问以下 URL 进行授权:")
        print(f"\n{oauth_url}\n")
        print("2. 在浏览器中完成授权")
        print("3. 从回调 URL 中复制 'code' 参数")
        print("4. 运行以下命令测试令牌交换:")
        print(f"\n   uv run python scripts/verify_user_auth.py --code <授权码>\n")

        # 5. 总结
        self.print_section("验证总结")
        print("\n✓ 验证完成:")
        print(f"  - tenant_token 流程: {'✓ 有效' if tenant_result['success'] else '✗ 无效'}")
        print(f"  - OAuth 端点: {valid_count}/{total_count} 有效")
        print("\n建议:")
        if all(endpoint_results.values()):
            print("  ✓ 所有用户认证端点有效，可以开始实现")
        else:
            print("  ! 部分端点可能不可用，建议先测试 OAuth 流程")

        return {
            "tenant_token": tenant_result,
            "endpoints": endpoint_results,
            "oauth_url": oauth_url
        }


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    app_id = os.environ.get("FEISHU_APP_ID") or os.environ.get("FEISHU_APPID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        logger.error("请设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        sys.exit(1)

    # 检查是否提供了授权码
    if len(sys.argv) > 1 and sys.argv[1] == "--code":
        if len(sys.argv) < 3:
            logger.error("请提供授权码: --code <授权码>")
            sys.exit(1)

        authorization_code = sys.argv[2]
        verifier = FeishuUserAuthVerifier(app_id, app_secret)

        verifier.print_section("测试用户令牌交换")
        result = verifier.test_user_token_exchange(authorization_code)

        if result["success"]:
            print("\n✓ 令牌交换成功!")
            print(f"  Access Token: {result['access_token'][:30]}...")
            print(f"  Refresh Token: {result['refresh_token'][:30]}...")

            # 测试获取用户信息
            verifier.print_section("测试获取用户信息")
            try:
                url = f"{verifier.BASE_URL}{verifier.OAUTH_USER_INFO_ENDPOINT}"
                headers = {"Authorization": f"Bearer {result['access_token']}"}
                response = verifier.session.get(url, headers=headers, timeout=10)
                data = response.json()

                if data.get("code") == 0:
                    user_info = data.get("data", {})
                    print("\n✓ 用户信息获取成功:")
                    print(f"  姓名: {user_info.get('name')}")
                    print(f"  Open ID: {user_info.get('open_id')}")
                    print(f"  邮箱: {user_info.get('email')}")
                else:
                    print(f"\n✗ 用户信息获取失败: {data.get('msg')}")
            except Exception as e:
                print(f"\n✗ 用户信息获取异常: {e}")
        else:
            print(f"\n✗ 令牌交换失败: {result['error']}")
            print("\n可能的原因:")
            print("  1. 授权码已过期或已使用")
            print("  2. redirect_uri 不匹配")
            print("  3. 应用凭证错误")

    else:
        # 运行完整验证
        verifier = FeishuUserAuthVerifier(app_id, app_secret)
        verifier.run_full_verification()


if __name__ == "__main__":
    main()
