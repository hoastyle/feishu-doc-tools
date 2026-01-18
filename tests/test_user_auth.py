"""
用户认证功能测试

测试飞书 API 的 user_access_token 认证流程
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from lib.feishu_api_client import FeishuApiClient, AuthMode, FeishuApiAuthError


class TestAuthMode:
    """测试认证模式枚举"""

    def test_auth_mode_enum(self):
        """测试认证模式枚举值"""
        assert AuthMode.TENANT.value == "tenant"
        assert AuthMode.USER.value == "user"


class TestUserAuthInitialization:
    """测试用户认证初始化"""

    def test_init_with_tenant_mode(self):
        """测试使用租户模式初始化"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.TENANT)
        assert client.auth_mode == AuthMode.TENANT
        assert client._user_access_token is None
        assert client._user_refresh_token is None

    def test_init_with_user_mode_without_token(self):
        """测试使用用户模式初始化但无令牌"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        assert client.auth_mode == AuthMode.USER
        assert client._user_access_token is None
        assert client._user_refresh_token is None

    def test_init_with_user_mode_with_token(self):
        """测试使用用户模式初始化并提供令牌"""
        refresh_token = "ur-test_refresh_token"
        client = FeishuApiClient(
            "app_id",
            "app_secret",
            auth_mode=AuthMode.USER,
            user_refresh_token=refresh_token
        )
        assert client.auth_mode == AuthMode.USER
        assert client._user_refresh_token == refresh_token


class TestSetUserToken:
    """测试设置用户令牌"""

    def test_set_user_token(self):
        """测试设置用户访问令牌"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)

        access_token = "test_access_token"
        refresh_token = "test_refresh_token"

        client.set_user_token(access_token, refresh_token, expires_in=3600)

        assert client._user_access_token == access_token
        assert client._user_refresh_token == refresh_token
        assert client._user_token_expire_time is not None


class TestExchangeAuthorizationCode:
    """测试授权码交换"""

    @patch("lib.feishu_api_client.requests.Session.post")
    def test_exchange_authorization_code_success(self, mock_post):
        """测试成功交换授权码"""
        # Mock API 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 7140,
                "name": "测试用户",
                "open_id": "ou_test",
                "email": "test@example.com"
            }
        }
        mock_post.return_value = mock_response

        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        result = client.exchange_authorization_code("test_auth_code")

        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        assert result["name"] == "测试用户"
        assert client._user_access_token == "test_access_token"

    @patch("lib.feishu_api_client.requests.Session.post")
    def test_exchange_authorization_code_failure(self, mock_post):
        """测试交换授权码失败"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 40003,
            "msg": "authorization_code invalid"
        }
        mock_post.return_value = mock_response

        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)

        with pytest.raises(FeishuApiAuthError):
            client.exchange_authorization_code("invalid_code")


class TestGetUserToken:
    """测试获取用户令牌"""

    def test_get_user_token_from_cache(self):
        """测试从缓存获取用户令牌"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        client.set_user_token("cached_token", "refresh_token", expires_in=3600)

        token = client.get_user_token()

        assert token == "cached_token"

    def test_get_user_token_no_token_available(self):
        """测试没有可用令牌时抛出异常"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)

        with pytest.raises(FeishuApiAuthError):
            client.get_user_token()


class TestRefreshUserToken:
    """测试刷新用户令牌"""

    @patch("lib.feishu_api_client.requests.Session.post")
    def test_refresh_user_token_success(self, mock_post):
        """测试成功刷新用户令牌"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 7140
            }
        }
        mock_post.return_value = mock_response

        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        client._user_refresh_token = "old_refresh_token"

        new_token = client.refresh_user_token()

        assert new_token == "new_access_token"
        assert client._user_access_token == "new_access_token"
        assert client._user_refresh_token == "new_refresh_token"

    def test_refresh_user_token_no_refresh_token(self):
        """测试没有刷新令牌时抛出异常"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)

        with pytest.raises(FeishuApiAuthError):
            client.refresh_user_token()


class TestGetUserInfo:
    """测试获取用户信息"""

    @patch("lib.feishu_api_client.requests.Session.get")
    def test_get_user_info_success(self, mock_get):
        """测试成功获取用户信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "name": "测试用户",
                "open_id": "ou_test",
                "email": "test@example.com",
                "user_id": "12345"
            }
        }
        mock_get.return_value = mock_response

        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        client.set_user_token("test_token", "refresh_token", expires_in=3600)

        user_info = client.get_user_info()

        assert user_info["name"] == "测试用户"
        assert user_info["email"] == "test@example.com"


class TestGenerateOAuthUrl:
    """测试生成 OAuth URL"""

    def test_generate_oauth_url_default(self):
        """测试生成默认 OAuth URL"""
        client = FeishuApiClient("cli_test123", "app_secret", auth_mode=AuthMode.USER)

        url = client.generate_oauth_url()

        assert "https://open.feishu.cn/open-apis/authen/v1/authorize" in url
        assert "app_id=cli_test123" in url
        assert "redirect_uri=http://localhost:8080/callback" in url
        assert "scope=" in url

    def test_generate_oauth_url_custom_redirect(self):
        """测试生成自定义重定向 URI 的 OAuth URL"""
        client = FeishuApiClient("cli_test123", "app_secret", auth_mode=AuthMode.USER)

        url = client.generate_oauth_url(redirect_uri="https://example.com/callback")

        assert "redirect_uri=https://example.com/callback" in url


class TestGetToken:
    """测试获取令牌的统一方法"""

    @patch.object(FeishuApiClient, 'get_tenant_token')
    def test_get_token_tenant_mode(self, mock_get_tenant):
        """测试租户模式获取令牌"""
        mock_get_tenant.return_value = "tenant_token"

        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.TENANT)
        token = client._get_token()

        assert token == "tenant_token"
        mock_get_tenant.assert_called_once()

    def test_get_token_user_mode(self):
        """测试用户模式获取令牌"""
        client = FeishuApiClient("app_id", "app_secret", auth_mode=AuthMode.USER)
        client.set_user_token("user_token", "refresh_token", expires_in=3600)

        token = client._get_token()

        assert token == "user_token"


class TestFromEnv:
    """测试从环境变量加载"""

    @patch.dict(os.environ, {
        'FEISHU_APP_ID': 'cli_test123',
        'FEISHU_APP_SECRET': 'test_secret',
        'FEISHU_AUTH_MODE': 'user',
        'FEISHU_USER_REFRESH_TOKEN': 'refresh_token'
    })
    def test_from_env_user_mode(self):
        """测试从环境变量加载用户模式"""
        client = FeishuApiClient.from_env()

        assert client.auth_mode == AuthMode.USER
        assert client._user_refresh_token == "refresh_token"

    @patch.dict(os.environ, {
        'FEISHU_APP_ID': 'cli_test123',
        'FEISHU_APP_SECRET': 'test_secret'
    })
    def test_from_env_tenant_mode_default(self):
        """测试从环境变量加载默认租户模式"""
        client = FeishuApiClient.from_env()

        assert client.auth_mode == AuthMode.TENANT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
