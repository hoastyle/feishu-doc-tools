"""
Feishu API Client - Direct API integration for feishu-doc-tools

This module provides direct access to Feishu (Lark) Open API without going through MCP.
For the "direct upload without modification" use case, this is more efficient than MCP.

API Documentation:
- Authentication: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
- Batch Create Blocks: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/batch_create
- Image Upload: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/image-block/create
"""

import os
import json
import base64
import logging
import threading
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

import requests
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class AuthMode(Enum):
    """
    飞书 API 认证模式

    TENANT: 使用 tenant_access_token（应用身份，默认）
    USER: 使用 user_access_token（用户身份，需要 OAuth 授权）
    """

    TENANT = "tenant"
    USER = "user"


class BitableFieldType:
    """
    Feishu Bitable field type constants.

    Reference: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/field
    """

    TEXT = 1          # 单行文本
    NUMBER = 2        # 数字
    SINGLE_SELECT = 4 # 单选
    MULTI_SELECT = 5  # 多选
    DATE = 5          # 日期
    DATETIME = 6      # 日期时间
    PERSON = 7        # 人员
    CHECKBOX = 11     # 复选框
    URL = 15          # 超链接
    PHONE = 13        # 电话
    EMAIL = 14        # 邮箱
    PROGRESS = 18     # 进度


class FeishuApiClientError(Exception):
    """Base exception for Feishu API client errors"""

    pass


class FeishuApiAuthError(FeishuApiClientError):
    """Authentication related errors"""

    pass


class FeishuApiRequestError(FeishuApiClientError):
    """API request errors"""

    pass


class FeishuApiClient:
    """
    Direct Feishu API client for uploading Markdown to Feishu documents.

    This client handles:
    1. Authentication (tenant_access_token)
    2. Batch block creation
    3. Image upload and binding
    4. Parallel uploads for improved performance

    Usage:
        client = FeishuApiClient.from_env()
        result = client.upload_blocks("doc_id", blocks)
    """

    # API Endpoints
    BASE_URL = "https://open.feishu.cn/open-apis"
    AUTH_ENDPOINT = "/auth/v3/tenant_access_token/internal"
    BLOCKS_ENDPOINT_TEMPLATE = "/docx/v1/documents/{doc_id}/blocks/{parent_id}/children"
    IMAGE_UPLOAD_ENDPOINT = "/docx/v1/media/upload"

    # User Authentication Endpoints (Updated to v2 API)
    # 授权端点使用 accounts.feishu.cn 域名（不是 open.feishu.cn）
    USER_AUTH_BASE_URL = "https://accounts.feishu.cn/open-apis"
    USER_AUTH_ENDPOINT = "/authen/v1/authorize"
    USER_TOKEN_ENDPOINT = "/authen/v2/oauth/token"  # Updated to v2
    USER_REFRESH_ENDPOINT = "/authen/v2/oauth/token"  # Same endpoint, different grant_type
    USER_INFO_ENDPOINT = "/authen/v1/user_info"

    # Token cache (class-level for thread-safe access)
    _token_cache: Optional[Dict[str, str]] = None
    _token_expire_time: Optional[int] = None
    _token_lock = threading.Lock()

    # Performance tuning constants
    MAX_BATCH_WORKERS = 3  # Maximum parallel batch uploads
    MAX_IMAGE_WORKERS = 5  # Maximum parallel image uploads

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        auth_mode: AuthMode = AuthMode.TENANT,
        user_refresh_token: Optional[str] = None,
    ):
        """
        Initialize Feishu API client with connection pooling.

        Args:
            app_id: Feishu app ID (cli_xxxxx)
            app_secret: Feishu app secret
            auth_mode: Authentication mode (TENANT or USER)
            user_refresh_token: Refresh token for user authentication (required if auth_mode=USER)
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.auth_mode = auth_mode

        # User authentication state
        self._user_access_token: Optional[str] = None
        self._user_refresh_token: Optional[str] = user_refresh_token
        self._user_token_expire_time: Optional[int] = None
        # Use RLock (reentrant lock) to allow nested lock acquisition
        # This is needed because refresh_user_token() calls set_user_token() while holding the lock
        self._user_token_lock = threading.RLock()

        # Try to load user tokens from environment if using user mode
        if auth_mode == AuthMode.USER and not user_refresh_token:
            self._user_refresh_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json; charset=utf-8"})

        # Configure connection pool with retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        # Retry configuration with compatibility for different urllib3 versions
        retry_kwargs = {
            "total": 3,
            "backoff_factor": 0.5,
            "status_forcelist": [429, 500, 502, 503, 504],
        }

        # Use allowed_methods for urllib3 >= 2.0, method_whitelist for older versions
        try:
            retry_strategy = Retry(
                **retry_kwargs,
                allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            )
        except TypeError:
            # Fall back to method_whitelist for older urllib3
            retry_strategy = Retry(
                **retry_kwargs,
                method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            )

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy,
        )

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "FeishuApiClient":
        """
        Create client from environment variables.

        This method will automatically search for .env files in the following order:
        1. Custom env_file path (if provided)
        2. .env in current working directory
        3. .env in project root (parent of scripts/ directory)
        4. ../Feishu-MCP/.env (shared with Feishu-MCP project)

        Environment variables:
            FEISHU_APP_ID: Feishu app ID
            FEISHU_APP_SECRET: Feishu app secret
            FEISHU_AUTH_TYPE or FEISHU_AUTH_MODE: Authentication mode (tenant or user, default: tenant)
            FEISHU_USER_REFRESH_TOKEN: Refresh token for user authentication (if auth_mode=user)

        Args:
            env_file: Optional path to custom .env file

        Returns:
            FeishuApiClient instance

        Raises:
            ValueError: If environment variables are not set

        Example:
            >>> # Auto-discover .env files
            >>> client = FeishuApiClient.from_env()
            >>> # Or specify custom path
            >>> client = FeishuApiClient.from_env("/path/to/.env")
        """
        # Try to load .env file(s) if credentials not already in environment
        if not (os.environ.get("FEISHU_APP_ID") or os.environ.get("FEISHU_APPID")):
            env_paths = []

            if env_file:
                env_paths = [Path(env_file)]
            else:
                # Auto-discover .env files
                cwd = Path.cwd()
                script_dir = Path(__file__).parent.parent  # Project root

                env_paths = [
                    cwd / ".env",
                    script_dir / ".env",
                    script_dir.parent / "Feishu-MCP" / ".env",
                ]

            # Try each path until one works
            for env_path in env_paths:
                if env_path.exists():
                    logger.info(f"Loading environment from: {env_path}")
                    load_dotenv(env_path, override=True)
                    break

        # Read credentials (with fallback names)
        app_id = os.environ.get("FEISHU_APP_ID") or os.environ.get("FEISHU_APPID")
        app_secret = os.environ.get("FEISHU_APP_SECRET") or os.environ.get("FEISHU_APPSECRET")

        if not app_id:
            raise ValueError(
                "FEISHU_APP_ID environment variable not set.\n"
                "Please set it in one of the following ways:\n"
                "  1. Export: export FEISHU_APP_ID=cli_xxxxx\n"
                "  2. Create .env file: FEISHU_APP_ID=cli_xxxxx\n"
                "  3. Or pass app_id directly to FeishuApiClient(app_id=..., app_secret=...)\n"
                "  4. Or use ../Feishu-MCP/.env (auto-detected)"
            )
        if not app_secret:
            raise ValueError(
                "FEISHU_APP_SECRET environment variable not set.\n"
                "Please set it in one of the following ways:\n"
                "  1. Export: export FEISHU_APP_SECRET=xxxxx\n"
                "  2. Create .env file: FEISHU_APP_SECRET=xxxxx\n"
                "  3. Or pass app_secret directly to FeishuApiClient(app_id=..., app_secret=...)\n"
                "  4. Or use ../Feishu-MCP/.env (auto-detected)"
            )

        # Determine authentication mode
        # Support both FEISHU_AUTH_TYPE (compatible with Feishu-MCP) and FEISHU_AUTH_MODE
        auth_mode_str = os.environ.get("FEISHU_AUTH_TYPE") or os.environ.get("FEISHU_AUTH_MODE", "tenant")
        auth_mode_str = auth_mode_str.lower()
        auth_mode = AuthMode.USER if auth_mode_str == "user" else AuthMode.TENANT

        # Get user refresh token if using user mode
        user_refresh_token = None
        if auth_mode == AuthMode.USER:
            user_refresh_token = os.environ.get("FEISHU_USER_REFRESH_TOKEN")
            if not user_refresh_token:
                logger.warning(
                    "FEISHU_AUTH_TYPE/FEISHU_AUTH_MODE=user but FEISHU_USER_REFRESH_TOKEN not set. "
                    "You'll need to call set_user_token() or exchange_authorization_code() first."
                )

        return cls(app_id, app_secret, auth_mode=auth_mode, user_refresh_token=user_refresh_token)

    def get_default_folder_token(self) -> Optional[str]:
        """
        Get default folder token from environment variable.

        This allows users to specify their personal cloud document folder
        as the default location for creating documents.

        Returns:
            Folder token from FEISHU_DEFAULT_FOLDER_TOKEN env var, or None

        Example:
            >>> # Set in .env file:
            >>> # FEISHU_DEFAULT_FOLDER_TOKEN=fldcnxxxxx
            >>> token = client.get_default_folder_token()
        """
        return os.environ.get("FEISHU_DEFAULT_FOLDER_TOKEN")

    def get_tenant_token(self, force_refresh: bool = False) -> str:
        """
        Get or refresh tenant_access_token (thread-safe).

        Tokens are cached for 2 hours (7200 seconds).
        If force_refresh is True, always get a new token.

        Args:
            force_refresh: Force token refresh even if cached

        Returns:
            tenant_access_token

        Raises:
            FeishuApiAuthError: If authentication fails
        """
        import time

        current_time = int(time.time())

        # Check cache with lock for thread safety
        with self._token_lock:
            if not force_refresh and self._token_cache and self._token_expire_time:
                if current_time < self._token_expire_time - 300:  # Refresh 5 min before expiry
                    logger.debug("Using cached token")
                    return self._token_cache.get("tenant_access_token", "")

            # Request new token (still within lock to prevent duplicate requests)
            url = f"{self.BASE_URL}{self.AUTH_ENDPOINT}"
            payload = {"app_id": self.app_id, "app_secret": self.app_secret}

            logger.debug(f"Requesting tenant token from {url}")
            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code != 200:
                raise FeishuApiAuthError(f"Failed to get tenant token: HTTP {response.status_code}")

            data = response.json()

            if data.get("code") != 0:
                raise FeishuApiAuthError(
                    f"Failed to get tenant token: {data.get('msg', 'Unknown error')}"
                )

            token = data.get("tenant_access_token")
            expire = data.get("expire", 7200)

            if not token:
                raise FeishuApiAuthError("No tenant_access_token in response")

            # Cache token (within lock)
            self._token_cache = {"tenant_access_token": token}
            self._token_expire_time = current_time + expire

            logger.info(f"Successfully obtained tenant token, expires in {expire}s")
            return token

    # ========================================================================
    # User Authentication Methods
    # ========================================================================

    def set_user_token(self, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 7140):
        """
        直接设置用户访问令牌（用于已获得的令牌）

        Args:
            access_token: 用户访问令牌
            refresh_token: 刷新令牌（可选）
            expires_in: 过期时间（秒，默认约2小时）

        Example:
            >>> client.set_user_token(
            ...     access_token="eyJhbGci...",
            ...     refresh_token="ur-oQ0mMq6...",
            ...     expires_in=7140
            ... )
        """
        with self._user_token_lock:
            self._user_access_token = access_token
            self._user_refresh_token = refresh_token
            self._user_token_expire_time = int(time.time()) + expires_in
            logger.info("User access token set successfully")

    def exchange_authorization_code(
        self, authorization_code: str, redirect_uri: str = "http://localhost:3333/callback"
    ) -> Dict[str, Any]:
        """
        使用授权码换取用户访问令牌

        Note:
            根据飞书 v2 API 文档：
            https://open.feishu.cn/document/authentication-management/access-token/get-user-access-token
            - 令牌端点使用 /authen/v2/oauth/token
            - v2 API 响应直接在响应体中返回字段（不在 data 对象中）
            - 用户信息需要通过单独的 API 调用获取
            - redirect_uri 参数必须与授权请求中的 redirect_uri 一致（错误码 20071）

        Args:
            authorization_code: OAuth 授权流程中获取的授权码
            redirect_uri: OAuth 回调地址（必须与授权时使用的一致）

        Returns:
            {
                "access_token": "eyJhbGci...",
                "refresh_token": "ur-oQ0mMq6...",
                "expires_in": 7140,
                "refresh_token_expires_in": 604800,
                "name": "用户姓名",
                "open_id": "ou_xxx",
                "email": "user@example.com"
            }

        Raises:
            FeishuApiAuthError: 如果令牌交换失败

        Example:
            >>> result = client.exchange_authorization_code("your_auth_code")
            >>> print(f"用户: {result['name']}")
            >>> print(f"令牌: {result['access_token'][:20]}...")
        """
        url = f"{self.BASE_URL}{self.USER_TOKEN_ENDPOINT}"
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri,  # Required: must match the redirect_uri in authorization request
        }

        logger.info("Exchanging authorization code for user access token")
        response = self.session.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            raise FeishuApiAuthError(f"Token exchange failed: HTTP {response.status_code}")

        data = response.json()

        if data.get("code") != 0:
            error_msg = data.get("msg", "Unknown error")
            raise FeishuApiAuthError(f"Token exchange failed: {error_msg}")

        # v2 API: 字段直接在响应体中，不在 data 对象中
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 7200)
        refresh_token_expires_in = data.get("refresh_token_expires_in", 604800)

        if not access_token:
            raise FeishuApiAuthError("No access_token in response")

        # Store tokens
        self.set_user_token(access_token, refresh_token, expires_in)

        # Get user information (requires separate API call)
        user_info = {}
        try:
            user_info = self.get_user_info()
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")

        # Return token information
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "refresh_token_expires_in": refresh_token_expires_in,
            "name": user_info.get("name"),
            "open_id": user_info.get("open_id"),
            "email": user_info.get("email"),
            "user_id": user_info.get("user_id"),
        }

    def get_user_token(self, force_refresh: bool = False) -> str:
        """
        获取或刷新用户访问令牌（线程安全）

        令牌会被缓存约2小时。
        如果 force_refresh 为 True，则强制刷新令牌。

        Args:
            force_refresh: 即使有缓存也强制刷新令牌

        Returns:
            user_access_token

        Raises:
            FeishuApiAuthError: 如果认证失败或没有可用的刷新令牌

        Example:
            >>> token = client.get_user_token()
        """
        current_time = int(time.time())

        with self._user_token_lock:
            # Check cache with lock for thread safety
            if not force_refresh and self._user_access_token and self._user_token_expire_time:
                if current_time < self._user_token_expire_time - 300:  # Refresh 5 min before expiry
                    logger.debug("Using cached user access token")
                    return self._user_access_token

            # Try to refresh if we have a refresh token
            if self._user_refresh_token:
                logger.info("Refreshing user access token")
                try:
                    return self.refresh_user_token()
                except FeishuApiAuthError as e:
                    logger.error(f"Failed to refresh user token: {e}")
                    # Continue to error below

            # No valid token available
            raise FeishuApiAuthError(
                "No valid user access token available. "
                "Please either: 1) Call exchange_authorization_code() with an authorization code, "
                "2) Call set_user_token() with a valid token, or "
                "3) Set FEISHU_USER_REFRESH_TOKEN in environment."
            )

    def refresh_user_token(self) -> str:
        """
        使用刷新令牌获取新的用户访问令牌

        Note:
            根据飞书 v2 API 文档：
            https://open.feishu.cn/document/authentication-management/access-token/refresh-user-access-token
            刷新令牌需要包含 client_id 和 client_secret

        Returns:
            新的用户访问令牌

        Raises:
            FeishuApiAuthError: 如果刷新失败

        Example:
            >>> new_token = client.refresh_user_token()
        """
        if not self._user_refresh_token:
            raise FeishuApiAuthError("No refresh token available")

        url = f"{self.BASE_URL}{self.USER_REFRESH_ENDPOINT}"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "refresh_token": self._user_refresh_token,
        }

        logger.debug("Requesting user token refresh")
        response = self.session.post(url, json=payload, timeout=10)

        logger.debug(f"Refresh response: status={response.status_code}")

        if response.status_code != 200:
            raise FeishuApiAuthError(f"Token refresh failed: HTTP {response.status_code}")

        logger.debug("Parsing JSON response...")
        data = response.json()
        logger.debug(f"Response data keys: {list(data.keys())}")

        if data.get("code") != 0:
            error_msg = data.get("msg", "Unknown error")
            raise FeishuApiAuthError(f"Token refresh failed: {error_msg}")

        # v2 API 直接在响应体中返回字段（不在 data 对象中）
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in", 7140)

        logger.debug(f"Extracted tokens: has_access={bool(access_token)}, has_refresh={bool(refresh_token)}")

        if not access_token:
            raise FeishuApiAuthError("No access_token in refresh response")

        logger.debug("Calling set_user_token...")
        # Update stored tokens
        self.set_user_token(access_token, refresh_token, expires_in)
        logger.debug("set_user_token completed")

        # 重要：将新的 refresh_token 保存到 .env 文件
        # 因为飞书的 refresh_token 只能使用一次，必须保存新token
        if refresh_token:
            logger.debug("Calling _update_env_refresh_token...")
            self._update_env_refresh_token(refresh_token)
            logger.debug("_update_env_refresh_token completed")

        logger.info(f"User access token refreshed successfully, expires in {expires_in}s")
        return access_token

    def _update_env_refresh_token(self, new_refresh_token: str):
        """
        更新 .env 文件中的 FEISHU_USER_REFRESH_TOKEN

        Note:
            飞书的 refresh_token 只能使用一次。每次刷新后，都会返回新的 refresh_token。
            必须将新的 refresh_token 保存到 .env 文件，否则下次启动时会使用已撤销的 token。

        Args:
            new_refresh_token: 新的 refresh token
        """
        import os
        from pathlib import Path

        logger.debug("Starting to update .env file with new refresh_token")

        # 查找 .env 文件
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            # 如果当前目录没有，尝试项目根目录
            possible_paths = [
                Path(__file__).parent.parent / ".env",
                Path.cwd().parent / ".env",
            ]
            for path in possible_paths:
                if path.exists():
                    env_path = path
                    break
            else:
                logger.warning(f"Could not find .env file to update refresh_token")
                return

        logger.debug(f"Found .env file at: {env_path}")

        try:
            # 读取现有内容
            logger.debug("Reading .env file...")
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            logger.debug(f"Read {len(lines)} lines from .env")

            # 更新 FEISHU_USER_REFRESH_TOKEN
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('FEISHU_USER_REFRESH_TOKEN='):
                    lines[i] = f'FEISHU_USER_REFRESH_TOKEN={new_refresh_token}\n'
                    updated = True
                    logger.debug(f"Updated line {i}")
                    break

            # 如果没有找到，添加到末尾
            if not updated:
                lines.append(f'\nFEISHU_USER_REFRESH_TOKEN={new_refresh_token}\n')
                logger.debug("Appended new FEISHU_USER_REFRESH_TOKEN line")

            # 写回文件
            logger.debug("Writing updated content back to .env...")
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            logger.info(f"Updated FEISHU_USER_REFRESH_TOKEN in {env_path}")
            logger.debug("_update_env_refresh_token completed successfully")

        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            # 不抛出异常，避免影响主流程
            logger.debug("Continuing despite .env update failure")

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取当前用户信息

        Returns:
            {
                "name": "用户姓名",
                "en_name": "英文名",
                "open_id": "ou_xxx",
                "union_id": "on_xxx",
                "email": "user@example.com",
                "user_id": "xxx",
                "mobile": "+86xxx",
                "avatar_url": "https://..."
            }

        Raises:
            FeishuApiAuthError: 如果获取用户信息失败

        Example:
            >>> info = client.get_user_info()
            >>> print(f"用户: {info['name']} ({info['email']})")
        """
        token = self.get_user_token()
        url = f"{self.BASE_URL}{self.USER_INFO_ENDPOINT}"
        headers = {"Authorization": f"Bearer {token}"}

        logger.debug("Fetching user info")
        response = self.session.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiAuthError(f"Failed to get user info: HTTP {response.status_code}")

        data = response.json()

        if data.get("code") != 0:
            error_msg = data.get("msg", "Unknown error")
            raise FeishuApiAuthError(f"Failed to get user info: {error_msg}")

        user_info = data.get("data", {})
        logger.info(f"Got user info for: {user_info.get('name', 'Unknown')}")
        return user_info

    def generate_oauth_url(
        self, redirect_uri: str = "http://localhost:3333/callback", state: Optional[str] = None
    ) -> str:
        """
        生成 OAuth 授权 URL

        Args:
            redirect_uri: OAuth 回调地址
            state: 状态参数（用于防止 CSRF 攻击）

        Returns:
            OAuth 授权 URL

        Note:
            根据 https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code
            - 授权端点使用 accounts.feishu.cn 域名，参数名使用 client_id（不是 app_id）
            - state 参数采用 Base64 编码的 JSON（与 Feishu-MCP 保持一致）
            - 编码内容包含 app_id, timestamp, redirect_uri，用于回调验证

        Example:
            >>> url = client.generate_oauth_url()
            >>> print(f"请访问: {url}")
        """
        import base64
        import json
        import time

        # 权限范围：文档和 Wiki 的只读权限 + offline_access（用于获取 refresh_token）
        # 参考: https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code
        # 注意：wiki:wiki 不是有效权限，只使用 wiki:wiki:readonly
        scope = "docx:document docx:document:readonly wiki:wiki:readonly offline_access"

        # 生成 state 参数（采用 Feishu-MCP 的 Base64 编码方案）
        # 将必要信息编码到 state 中，便于回调时验证和使用
        if not state:
            import base64
            import json
            import time

            state_data = {
                "app_id": self.app_id,
                "timestamp": int(time.time()),
                "redirect_uri": redirect_uri,
            }
            # Base64 编码（与 Feishu-MCP 一致）
            # 使用 separators 确保紧凑格式（无空格），与 TypeScript 的 JSON.stringify() 一致
            state_json = json.dumps(state_data, separators=(',', ':'))
            state = base64.b64encode(state_json.encode()).decode()

        # 参数名称：使用 client_id（不是 app_id）
        # URL 编码规则（参考 Feishu-MCP）：
        # - redirect_uri 和 scope 需要 URL 编码
        # - state 不需要 URL 编码（Base64 字符串可以直接使用）
        from urllib.parse import quote

        # 使用 USER_AUTH_BASE_URL（accounts.feishu.cn）而不是 BASE_URL（open.feishu.cn）
        url = f"{self.USER_AUTH_BASE_URL}{self.USER_AUTH_ENDPOINT}?"
        url += f"client_id={self.app_id}"
        url += f"&redirect_uri={quote(redirect_uri, safe='')}"
        url += f"&scope={quote(scope, safe='')}"
        url += f"&response_type=code"
        url += f"&state={state}"  # state 不进行 URL 编码（与 Feishu-MCP 一致）

        return url

    # ========================================================================
    # Token Management
    # ========================================================================

    def _get_token(self) -> str:
        """
        根据认证模式获取相应的令牌

        Returns:
            访问令牌（tenant_access_token 或 user_access_token）

        Raises:
            FeishuApiAuthError: 如果获取令牌失败

        Example:
            >>> token = client._get_token()  # 内部方法
        """
        if self.auth_mode == AuthMode.USER:
            return self.get_user_token()
        else:
            return self.get_tenant_token()

    def create_document(
        self, title: str, folder_token: Optional[str] = None, doc_type: str = "docx"
    ) -> Dict[str, Any]:
        """
        Create a new Feishu document.

        API endpoint: POST /docx/v1/documents

        Args:
            title: Document title
            folder_token: Parent folder token (None = root folder)
            doc_type: Document type ("docx" only, others planned)

        Returns:
            {
                "document_id": "doxcnxxxxx",
                "url": "https://feishu.cn/docx/doxcnxxxxx",
                "title": "Document Title",
                "revision_id": 1
            }

        Raises:
            FeishuApiRequestError: If document creation fails

        Example:
            >>> result = client.create_document("My Document", folder_token="fldcnxxxxx")
            >>> print(result["url"])
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/docx/v1/documents"

        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating document: {title}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create document: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create document: {result.get('msg', 'Unknown error')}"
            )

        doc_data = result.get("data", {}).get("document", {})
        doc_id = doc_data.get("document_id")

        logger.info(f"Successfully created document: {doc_id}")

        return {
            "document_id": doc_id,
            "url": f"https://feishu.cn/docx/{doc_id}",
            "title": doc_data.get("title", title),
            "revision_id": doc_data.get("revision_id"),
        }

    def get_root_folder_token(self) -> str:
        """
        Get root folder token for current workspace.

        API endpoint: GET /drive/explorer/v2/root_folder/meta

        Returns:
            Root folder token

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> root_token = client.get_root_folder_token()
        """
        token = self._get_token()
        # Use the correct API endpoint (v2 explorer, not v1 drive)
        url = f"{self.BASE_URL}/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {token}"}

        logger.info("Fetching root folder token using v2 explorer API")
        response = self.session.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to get root folder: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to get root folder: {result.get('msg', 'Unknown error')}"
            )

        # Extract folder token from response
        # The v2 API returns: { "data": { "token": "fldcnxxxxx" } }
        data = result.get("data", {})
        folder_token = data.get("token")

        if not folder_token:
            raise FeishuApiRequestError("No folder_token in root folder response")

        logger.info(f"Root folder token: {folder_token}")
        return folder_token

    def get_current_user_id(self) -> str:
        """
        Get current user's ID from tenant info.

        API endpoint: GET /contact/v3/users/batch_get_id

        Returns:
            Current user's open_id

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> user_id = client.get_current_user_id()
            >>> print(f"Current user: {user_id}")
        """
        token = self._get_token()

        # First, we need to get the user_id. Since we're using service account,
        # we can get the current user by calling the permission API with our own auth.
        # Alternative approach: Use the contact API to get user info.

        # For simplicity, we'll use a different approach:
        # Get user info from the permission list of a test document or use user info endpoint

        # Actually, for a tenant access token (app), we need the user to provide their user_id
        # or we can get it from the environment variable.
        user_id = os.environ.get("FEISHU_USER_ID")

        if user_id:
            logger.debug(f"Using user_id from environment: {user_id}")
            return user_id

        # Try to get from user info endpoint (requires proper permissions)
        url = f"{self.BASE_URL}/contact/v3/users/me"
        headers = {"Authorization": f"Bearer {token}"}

        logger.info("Fetching current user info")
        response = self.session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                user_data = result.get("data", {}).get("user", {})
                user_id = user_data.get("open_id")
                if user_id:
                    logger.info(f"Current user ID: {user_id}")
                    return user_id

        raise FeishuApiRequestError(
            "Could not determine current user ID. Please set FEISHU_USER_ID environment variable.\n"
            "You can find your user_id in Feishu: Settings > Profile > Copy User ID"
        )

    def set_document_permission(
        self, document_id: str, user_id: str, permission: str = "edit", notify: bool = False
    ) -> Dict[str, Any]:
        """
        Set permission for a user on a document.

        API endpoint: POST /docx/v1/documents/{doc_id}/permissions

        Args:
            document_id: Document ID (doxcnxxxxx)
            user_id: User's open_id to grant permission to
            permission: Permission level - "view", "edit", or "admin"
            notify: Whether to notify the user

        Returns:
            {"success": true, "permission_id": "..."}

        Raises:
            FeishuApiRequestError: If permission setting fails

        Example:
            >>> client.set_document_permission("doxcnxxxxx", "ou_xxxxx", "edit")
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/docx/v1/documents/{document_id}/permissions/invite"

        # Build permission request
        # Note: Feishu uses different API for permissions, using invite endpoint
        payload = {
            "invite_type": "userid",
            "invite_messages": [{"user_id": user_id, "perm_type": permission, "notify": notify}],
        }

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Setting {permission} permission for user {user_id} on document {document_id}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to set permission: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to set permission: {result.get('msg', 'Unknown error')}"
            )

        logger.info(f"Successfully set {permission} permission for user {user_id}")
        return {"success": True, "permission": permission}

    def create_folder(self, name: str, parent_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a folder in Feishu Drive.

        API endpoint: POST /drive/v1/folders

        Args:
            name: Folder name
            parent_token: Parent folder token (None = root)

        Returns:
            {
                "folder_token": "fldcnxxxxx",
                "name": "Folder Name",
                "url": "https://feishu.cn/drive/folder/fldcnxxxxx"
            }

        Raises:
            FeishuApiRequestError: If folder creation fails

        Example:
            >>> result = client.create_folder("My Folder")
            >>> print(result["folder_token"])
        """
        token = self._get_token()

        if parent_token is None:
            parent_token = self.get_root_folder_token()

        url = f"{self.BASE_URL}/drive/v1/folders"

        payload = {"name": name, "folder_token": parent_token}

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating folder: {name}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create folder: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create folder: {result.get('msg', 'Unknown error')}"
            )

        folder_data = result.get("data", {}).get("folder", {})
        folder_token = folder_data.get("folder_token")

        logger.info(f"Successfully created folder: {folder_token}")

        return {
            "folder_token": folder_token,
            "name": folder_data.get("name", name),
            "url": f"https://feishu.cn/drive/folder/{folder_token}",
        }

    def list_folder_contents(self, folder_token: str, page_size: int = 200) -> List[Dict[str, Any]]:
        """
        List files and folders in a folder.

        API endpoint: GET /drive/v1/files?folder_token={folder_token}

        Args:
            folder_token: Parent folder token
            page_size: Number of items per page (max 200)

        Returns:
            List of files/folders with metadata

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> items = client.list_folder_contents("fldcnxxxxx")
            >>> for item in items:
            ...     print(item["name"], item["type"])
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/drive/v1/files"
        params = {
            "folder_token": folder_token,
            "page_size": page_size,
            "order_by": "EditedTime",  # Fixed: Capitalized according to API spec
            "direction": "DESC",  # Fixed: Capitalized according to API spec
        }

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Listing folder contents: {folder_token}")
        response = self.session.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to list folder: HTTP {response.status_code}\n" f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to list folder: {result.get('msg', 'Unknown error')}"
            )

        items = result.get("data", {}).get("items", [])
        logger.info(f"Found {len(items)} items in folder")

        return items

    def get_all_wiki_spaces(self, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        Get all wiki spaces (handles pagination automatically).

        API endpoint: GET /wiki/v2/spaces

        Args:
            page_size: Number of items per page (default 20)

        Returns:
            List of all wiki spaces with metadata

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> spaces = client.get_all_wiki_spaces()
            >>> for space in spaces:
            ...     print(space["name"], space["space_id"])
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/wiki/v2/spaces"
        headers = {"Authorization": f"Bearer {token}"}

        all_items = []
        page_token = None
        has_more = True

        logger.info("Fetching all wiki spaces...")

        while has_more:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token

            response = self.session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                raise FeishuApiRequestError(
                    f"Failed to get wiki spaces: HTTP {response.status_code}\n"
                    f"Response: {response.text}"
                )

            result = response.json()

            if result.get("code") != 0:
                raise FeishuApiRequestError(
                    f"Failed to get wiki spaces: {result.get('msg', 'Unknown error')}"
                )

            data = result.get("data", {})
            items = data.get("items", [])
            all_items.extend(items)

            has_more = data.get("has_more", False)
            page_token = data.get("page_token")

            logger.debug(f"Fetched {len(items)} spaces, total: {len(all_items)}")

        logger.info(f"Found {len(all_items)} wiki spaces total")
        return all_items

    def find_wiki_space_by_name(self, name: str) -> Optional[str]:
        """
        Find a wiki space by its name.

        This method searches through all available wiki spaces and returns
        the space_id of the first space that matches the given name.

        Args:
            name: Wiki space name to search for

        Returns:
            space_id if found, None otherwise

        Raises:
            FeishuApiRequestError: If multiple spaces with the same name are found

        Example:
            >>> # Find a space by name
            >>> space_id = client.find_wiki_space_by_name("Product Docs")
            >>> if space_id:
            ...     print(f"Found space ID: {space_id}")
            ... else:
            ...     print("Space not found")
        """
        spaces = self.get_all_wiki_spaces()

        # Find exact matches
        matches = [s for s in spaces if s.get("name") == name]

        if len(matches) == 0:
            logger.warning(f"No wiki space found with name: {name}")
            return None
        elif len(matches) == 1:
            space_id = matches[0].get("space_id")
            logger.info(f"Found wiki space '{name}' with ID: {space_id}")
            return space_id
        else:
            # Multiple matches - provide detailed error
            space_list = "\n".join([
                f"  - {s.get('name')} (ID: {s.get('space_id')}, Type: {s.get('space_type')})"
                for s in matches
            ])
            raise FeishuApiRequestError(
                f"找到多个名为 '{name}' 的知识库，请使用 --space-id 指定：\n{space_list}"
            )

    def get_wiki_node_list(
        self,
        space_id: str,
        parent_node_token: Optional[str] = None,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get list of wiki nodes in a space.

        API endpoint: GET /wiki/v2/spaces/{space_id}/nodes

        Args:
            space_id: Wiki space ID
            parent_node_token: Parent node token (None for root level)
            page_size: Number of items per page (default 50)

        Returns:
            List of wiki nodes with metadata

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> # Get root level nodes
            >>> nodes = client.get_wiki_node_list(space_id="74812***88644")
            >>> for node in nodes:
            ...     print(node["title"], node["node_token"])
            >>>
            >>> # Get child nodes
            >>> children = client.get_wiki_node_list(
            ...     space_id="74812***88644",
            ...     parent_node_token="nodcn***"
            ... )
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/wiki/v2/spaces/{space_id}/nodes"
        headers = {"Authorization": f"Bearer {token}"}

        all_items = []
        page_token = None
        has_more = True

        logger.debug(f"Fetching wiki nodes for space {space_id}...")

        while has_more:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            if parent_node_token:
                params["parent_node_token"] = parent_node_token

            response = self.session.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                raise FeishuApiRequestError(
                    f"Failed to get wiki nodes: HTTP {response.status_code}\n"
                    f"Response: {response.text}"
                )

            result = response.json()

            if result.get("code") != 0:
                raise FeishuApiRequestError(
                    f"Failed to get wiki nodes: {result.get('msg', 'Unknown error')}"
                )

            data = result.get("data", {})
            items = data.get("items", [])
            all_items.extend(items)

            has_more = data.get("has_more", False)
            page_token = data.get("page_token")

            logger.debug(f"Fetched {len(items)} nodes, total: {len(all_items)}")

        logger.debug(f"Found {len(all_items)} wiki nodes total")
        return all_items

    def find_wiki_node_by_name(
        self,
        space_id: str,
        name: str,
        parent_token: Optional[str] = None
    ) -> Optional[str]:
        """
        Find a wiki node by its title within a space.

        Args:
            space_id: Wiki space ID
            name: Node title to search for
            parent_token: Parent node token (None for root level search)

        Returns:
            node_token if found, None otherwise

        Example:
            >>> # Find node at root level
            >>> token = client.find_wiki_node_by_name(
            ...     space_id="74812***88644",
            ...     name="API Reference"
            ... )
            >>>
            >>> # Find child node
            >>> child_token = client.find_wiki_node_by_name(
            ...     space_id="74812***88644",
            ...     name="Endpoints",
            ...     parent_token=token
            ... )
        """
        nodes = self.get_wiki_node_list(space_id, parent_token)

        # Find matches by title
        matches = [n for n in nodes if n.get("title") == name]

        if len(matches) == 0:
            logger.debug(f"No wiki node found with title: {name}")
            return None
        elif len(matches) == 1:
            node_token = matches[0].get("node_token")
            logger.debug(f"Found wiki node '{name}' with token: {node_token}")
            return node_token
        else:
            # Multiple matches - use the first one
            node_token = matches[0].get("node_token")
            logger.warning(
                f"Found {len(matches)} nodes named '{name}', using first one "
                f"(token: {node_token})"
            )
            return node_token

    def resolve_wiki_path(self, space_id: str, path: str) -> Optional[str]:
        """
        Resolve a wiki path and return the deepest node's token.

        This method navigates through the wiki space node hierarchy following
        the given path and returns the token of the final node.

        Args:
            space_id: Wiki space ID
            path: Path string like "/API/Reference" or "API/Reference"

        Returns:
            node_token of the deepest node, None if path is empty

        Raises:
            FeishuApiRequestError: If any node in the path doesn't exist

        Example:
            >>> # Resolve absolute path (from root)
            >>> token = client.resolve_wiki_path(
            ...     space_id="74812***88644",
            ...     path="/产品文档/API/参考"
            ... )
            >>>
            >>> # Resolve relative path
            >>> token = client.resolve_wiki_path(
            ...     space_id="74812***88644",
            ...     path="API/Reference"
            ... )
        """
        # Parse path
        if path.startswith("/"):
            path = path[1:]  # Remove leading slash

        parts = [p for p in path.split("/") if p]

        if not parts:
            return None  # Empty path

        logger.debug(f"Resolving wiki path: /{'/'.join(parts)}")

        # Navigate through each level
        parent_token = None

        for i, part in enumerate(parts):
            node_token = self.find_wiki_node_by_name(space_id, part, parent_token)

            if node_token is None:
                # Build error message with context
                current_path = "/".join(parts[:i]) if i > 0 else "(root)"
                raise FeishuApiRequestError(
                    f"路径不存在: '/{'/'.join(parts)}'\n"
                    f"在节点 '{current_path}' 下找不到 '{part}'"
                )

            parent_token = node_token
            logger.debug(f"  → '{part}' -> {node_token}")

        logger.info(f"Resolved path to node token: {parent_token}")
        return parent_token

    def create_wiki_space(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new wiki space.

        API endpoint: POST /wiki/v2/spaces

        Args:
            name: Wiki space name
            description: Wiki space description (optional)

        Returns:
            Dictionary with space_id and other space information

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> # Create a basic wiki space
            >>> space = client.create_wiki_space("My Project")
            >>> print(f"Space ID: {space['space_id']}")
            >>>
            >>> # Create with description
            >>> space = client.create_wiki_space(
            ...     "Technical Documentation",
            ...     description="Documentation for internal projects"
            ... )
            >>> print(f"Created space: {space['name']} ({space['space_id']})")
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/wiki/v2/spaces"
        payload = {"name": name}

        if description:
            payload["description"] = description

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating wiki space: {name}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create wiki space: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create wiki space: {result.get('msg', 'Unknown error')}"
            )

        # Extract space info
        space_data = result.get("data", {}).get("space", {})
        space_id = space_data.get("space_id")

        logger.info(f"Wiki space created successfully: {name} (space_id={space_id})")

        return {
            "space_id": space_id,
            "name": space_data.get("name", name),
            "description": space_data.get("description", description),
            "url": f"https://feishu.cn/wiki/{space_id}" if space_id else None,
            **space_data,  # Include all other fields from the API response
        }

    def get_my_library(self, lang: str = "en") -> Dict[str, Any]:
        """
        Get "My Library" (personal knowledge base) information.

        API endpoint: GET /wiki/v2/spaces/my_library

        Args:
            lang: Language code (default "en")

        Returns:
            My library space information

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> my_lib = client.get_my_library()
            >>> print(f"My Library ID: {my_lib['space_id']}")
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/wiki/v2/spaces/my_library"
        params = {"lang": lang}
        headers = {"Authorization": f"Bearer {token}"}

        logger.info("Fetching My Library info...")
        response = self.session.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to get My Library: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to get My Library: {result.get('msg', 'Unknown error')}"
            )

        space_data = result.get("data", {}).get("space", {})
        logger.info(f"My Library found: {space_data.get('name')}")

        return space_data

    def get_comprehensive_info(self) -> Dict[str, Any]:
        """
        Get comprehensive Feishu workspace information.

        This combines multiple API calls to provide:
        - Root folder info (user's cloud drive root)
        - All wiki spaces
        - My Library (personal knowledge base)

        Similar to feishu-docker MCP's get_feishu_root_folder_info tool.

        Returns:
            Dictionary with root_folder, wiki_spaces, and my_library keys

        Example:
            >>> info = client.get_comprehensive_info()
            >>> print(f"Root token: {info['root_folder']['token']}")
            >>> print(f"Wiki spaces: {len(info['wiki_spaces'])}")
        """
        result = {
            "root_folder": None,
            "wiki_spaces": None,
            "my_library": None,
        }

        # Get root folder info
        try:
            token = self._get_token()
            import requests

            url = f"{self.BASE_URL}/drive/explorer/v2/root_folder/meta"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                result["root_folder"] = data.get("data", {})
            else:
                result["root_folder"] = {"error": data.get("msg", "Unknown error")}
        except Exception as e:
            result["root_folder"] = {"error": str(e)}

        # Get all wiki spaces
        try:
            result["wiki_spaces"] = self.get_all_wiki_spaces()
        except Exception as e:
            result["wiki_spaces"] = []
            logger.error(f"Failed to get wiki spaces: {e}")

        # Get My Library
        try:
            result["my_library"] = self.get_my_library()
        except Exception as e:
            result["my_library"] = {"error": str(e)}
            logger.error(f"Failed to get My Library: {e}")

        return result

    def create_wiki_node(
        self, space_id: str, title: str, parent_node_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new wiki node (document) in a wiki space.

        API endpoint: POST /wiki/v2/spaces/{space_id}/nodes

        Args:
            space_id: Wiki space ID (e.g., '7516222021840306180')
            title: Node/document title
            parent_node_token: Parent node token (optional, creates at root if not provided)

        Returns:
            Dictionary with node_token, obj_token (document_id), and other node info

        Raises:
            FeishuApiRequestError: If request fails

        Example:
            >>> # Create in "个人知识库" space at root
            >>> node = client.create_wiki_node("7516222021840306180", "My Doc")
            >>> print(f"Document ID: {node['obj_token']}")
            >>>
            >>> # Create as child of another node
            >>> node = client.create_wiki_node(
            ...     "7516222021840306180",
            ...     "Child Doc",
            ...     parent_node_token="nodcnxxxxx"
            ... )
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/wiki/v2/spaces/{space_id}/nodes"
        payload = {"title": title, "obj_type": "docx", "node_type": "origin"}

        if parent_node_token:
            payload["parent_node_token"] = parent_node_token

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating wiki node in space {space_id}: {title}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create wiki node: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create wiki node: {result.get('msg', 'Unknown error')}"
            )

        # Extract node info
        node = result.get("data", {}).get("node", {})
        node_token = node.get("node_token")
        obj_token = node.get("obj_token")  # This is the document_id

        logger.info(
            f"Wiki node created successfully: node_token={node_token}, obj_token={obj_token}"
        )

        return {
            "node_token": node_token,
            "obj_token": obj_token,
            "document_id": obj_token,
            "title": node.get("title", title),
            "space_id": space_id,
            "url": f"https://feishu.cn/wiki/{node_token}" if node_token else None,
        }

    # ========== Bitable API Methods ==========

    def create_bitable(
        self, name: str, folder_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Bitable (multidimensional table) application.

        API endpoint: POST /bitable/v1/apps

        Args:
            name: Bitable application name
            folder_token: Optional folder token to create in specific folder

        Returns:
            Dictionary with app_id, name, and url

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> # Create Bitable in default location
            >>> bitable = client.create_bitable("My Data")
            >>> print(f"App ID: {bitable['app_id']}")
            >>>
            >>> # Create in specific folder
            >>> bitable = client.create_bitable("My Data", folder_token="fldcnxxxxx")
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps"
        payload = {"name": name}
        if folder_token:
            payload["folder_token"] = folder_token

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating Bitable: {name}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create Bitable: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create Bitable: {result.get('msg', 'Unknown error')}"
            )

        app = result.get("data", {}).get("app", {})
        app_id = app.get("app_id")

        logger.info(f"Bitable created successfully: app_id={app_id}, name={name}")

        return {
            "app_id": app_id,
            "name": name,
            "url": f"https://feishu.cn/base/{app_id}" if app_id else None,
        }

    def create_table(
        self,
        app_id: str,
        table_name: str,
        fields: List[Dict[str, Any]],
        default_view: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new data table in a Bitable application.

        API endpoint: POST /bitable/v1/apps/{app_id}/tables

        Args:
            app_id: Bitable application ID
            table_name: Table name
            fields: List of field definitions, each with:
                - field_name: Field name
                - type: Field type (use BitableFieldType constants)
                - options: Optional field-specific options
            default_view: Whether to create default view

        Returns:
            Dictionary with table_id, table_name, and field info

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> fields = [
            ...     {"field_name": "Name", "type": BitableFieldType.TEXT},
            ...     {"field_name": "Age", "type": BitableFieldType.NUMBER},
            ...     {"field_name": "Status", "type": BitableFieldType.SINGLE_SELECT},
            ... ]
            >>> table = client.create_table("app123", "People", fields)
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps/{app_id}/tables"

        # Build field configurations
        field_configs = []
        for field in fields:
            config = {
                "field_name": field["field_name"],
                "type": field["type"],
            }
            if "options" in field:
                config["options"] = field["options"]
            field_configs.append(config)

        payload = {
            "table": {
                "name": table_name,
                "default_view_name": "Table View" if default_view else None,
            },
            "fields": field_configs,
        }

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Creating table '{table_name}' in app {app_id}")
        response = self.session.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to create table: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create table: {result.get('msg', 'Unknown error')}"
            )

        table = result.get("data", {}).get("table", {})
        table_id = table.get("table_id")

        logger.info(f"Table created successfully: table_id={table_id}, name={table_name}")

        return {
            "table_id": table_id,
            "table_name": table_name,
            "app_id": app_id,
            "fields": result.get("data", {}).get("fields", []),
        }

    def insert_records(
        self, app_id: str, table_id: str, records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Insert records into a Bitable table.

        API endpoint: POST /bitable/v1/apps/{app_id}/tables/{table_id}/records

        Args:
            app_id: Bitable application ID
            table_id: Table ID
            records: List of records to insert, each record is a dict of
                     field_name -> value mappings

        Returns:
            Dictionary with created record IDs and count

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> records = [
            ...     {"fields": {"Name": "Alice", "Age": 30}},
            ...     {"fields": {"Name": "Bob", "Age": 25}},
            ... ]
            >>> result = client.insert_records("app123", "table456", records)
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps/{app_id}/tables/{table_id}/records"

        payload = {"records": records}

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Inserting {len(records)} records into table {table_id}")
        response = self.session.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to insert records: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to insert records: {result.get('msg', 'Unknown error')}"
            )

        created_records = result.get("data", {}).get("records", [])
        record_ids = [r.get("record_id") for r in created_records]

        logger.info(f"Inserted {len(record_ids)} records successfully")

        return {
            "record_ids": record_ids,
            "total_records": len(record_ids),
            "records": created_records,
        }

    def get_table_records(
        self,
        app_id: str,
        table_id: str,
        page_size: int = 100,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get records from a Bitable table.

        API endpoint: GET /bitable/v1/apps/{app_id}/tables/{table_id}/records

        Args:
            app_id: Bitable application ID
            table_id: Table ID
            page_size: Number of records per page (max 500)
            page_token: Token for pagination (from previous response)

        Returns:
            Dictionary with records list, has_more flag, and page_token

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> # Get first page
            >>> page1 = client.get_table_records("app123", "table456", page_size=100)
            >>> for record in page1["records"]:
            ...     print(record["fields"])
            >>>
            >>> # Get next page
            >>> if page1["has_more"]:
            ...     page2 = client.get_table_records(
            ...         "app123", "table456", page_token=page1["page_token"]
            ...     )
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps/{app_id}/tables/{table_id}/records"
        params = {"page_size": min(page_size, 500)}
        if page_token:
            params["page_token"] = page_token

        headers = {"Authorization": f"Bearer {token}"}

        response = self.session.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to get table records: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to get table records: {result.get('msg', 'Unknown error')}"
            )

        data = result.get("data", {})
        records = data.get("items", [])

        logger.info(f"Retrieved {len(records)} records from table {table_id}")

        return {
            "records": records,
            "has_more": data.get("has_more", False),
            "page_token": data.get("page_token"),
            "total_records": len(records),
        }

    def update_record(
        self, app_id: str, table_id: str, record_id: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a single record in a Bitable table.

        API endpoint: PUT /bitable/v1/apps/{app_id}/tables/{table_id}/records/{record_id}

        Args:
            app_id: Bitable application ID
            table_id: Table ID
            record_id: Record ID to update
            fields: Field name -> value mappings to update

        Returns:
            Dictionary with updated record data

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> updated = client.update_record(
            ...     "app123", "table456", "rec789", {"Name": "Alice Updated", "Age": 31}
            ... )
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps/{app_id}/tables/{table_id}/records/{record_id}"

        payload = {"fields": fields}

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Updating record {record_id} in table {table_id}")
        response = self.session.put(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to update record: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to update record: {result.get('msg', 'Unknown error')}"
            )

        record = result.get("data", {}).get("record", {})

        logger.info(f"Record {record_id} updated successfully")

        return {
            "record_id": record_id,
            "record": record,
            "fields": record.get("fields", {}),
        }

    def delete_record(
        self, app_id: str, table_id: str, record_id: str
    ) -> Dict[str, Any]:
        """
        Delete a single record from a Bitable table.

        API endpoint: DELETE /bitable/v1/apps/{app_id}/tables/{table_id}/records/{record_id}

        Args:
            app_id: Bitable application ID
            table_id: Table ID
            record_id: Record ID to delete

        Returns:
            Dictionary with deletion confirmation

        Raises:
            FeishuApiRequestError: If API request fails

        Example:
            >>> result = client.delete_record("app123", "table456", "rec789")
            >>> assert result["success"]
        """
        token = self._get_token()

        url = f"{self.BASE_URL}/bitable/v1/apps/{app_id}/tables/{table_id}/records/{record_id}"

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Deleting record {record_id} from table {table_id}")
        response = self.session.delete(url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to delete record: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to delete record: {result.get('msg', 'Unknown error')}"
            )

        logger.info(f"Record {record_id} deleted successfully")

        return {
            "success": True,
            "record_id": record_id,
        }

    # ========== End Bitable API Methods ==========

    # ========== Parallel Upload Methods ==========

    def batch_create_blocks_parallel(
        self,
        doc_id: str,
        blocks: List[Dict[str, Any]],
        parent_id: Optional[str] = None,
        index: int = 0,
        batch_size: int = 50,
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Batch create blocks in parallel for improved performance.

        This method splits blocks into batches and uploads them concurrently
        using ThreadPoolExecutor. Expected 5-10x performance improvement
        for large documents.

        Args:
            doc_id: Document ID
            blocks: List of block configurations
            parent_id: Parent block ID (default: doc_id for root level)
            index: Insertion index (default: 0 for beginning)
            batch_size: Maximum blocks per API request (default: 50)
            max_workers: Maximum parallel workers (default: self.MAX_BATCH_WORKERS)

        Returns:
            Dictionary with upload statistics

        Raises:
            FeishuApiRequestError: If any batch upload fails

        Example:
            >>> result = client.batch_create_blocks_parallel(
            ...     "doc123", blocks, max_workers=3
            ... )
            >>> print(f"Uploaded {result['total_blocks']} blocks")
        """
        if max_workers is None:
            max_workers = self.MAX_BATCH_WORKERS

        # First pass: format all blocks
        formatted_blocks = [
            self._format_block(block["blockType"], block.get("options", {}))
            for block in blocks
        ]

        # Split into batches
        all_batches = []
        for i in range(0, len(formatted_blocks), batch_size):
            batch_blocks = formatted_blocks[i : i + batch_size]
            all_batches.append(
                {"blocks": batch_blocks, "startIndex": index + i, "batchIndex": len(all_batches)}
            )

        if not all_batches:
            return {"total_blocks_created": 0, "total_batches": 0, "image_block_ids": []}

        logger.info(
            f"Uploading {len(formatted_blocks)} blocks in {len(all_batches)} "
            f"batches with {max_workers} workers"
        )

        # Upload batches in parallel
        total_blocks_created = 0
        all_image_block_ids = []

        def upload_single_batch(batch_data: Dict[str, Any]) -> Dict[str, Any]:
            """Upload a single batch and return result."""
            batch_index = batch_data["batchIndex"]
            blocks = batch_data["blocks"]
            start_index = batch_data["startIndex"]

            logger.info(f"Uploading batch {batch_index + 1}/{len(all_batches)}")

            result = self.batch_create_blocks(
                doc_id=doc_id, blocks=blocks, parent_id=parent_id, index=start_index
            )

            return {
                "batch_index": batch_index,
                "blocks_created": result.get("total_blocks_created", 0),
                "image_block_ids": result.get("image_block_ids", []),
            }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch upload tasks
            future_to_batch = {
                executor.submit(upload_single_batch, batch): batch
                for batch in all_batches
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                try:
                    result = future.result()
                    total_blocks_created += result["blocks_created"]
                    all_image_block_ids.extend(result["image_block_ids"])
                except Exception as e:
                    batch = future_to_batch[future]
                    logger.error(
                        f"Batch {batch['batchIndex']} failed: {e}. "
                        f"Consider reducing max_workers."
                    )
                    raise

        logger.info(f"Parallel upload complete: {total_blocks_created} blocks created")

        return {
            "total_blocks_created": total_blocks_created,
            "total_batches": len(all_batches),
            "image_block_ids": all_image_block_ids,
        }

    def upload_images_parallel(
        self,
        doc_id: str,
        image_blocks: List[Dict[str, str]],
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Upload multiple images in parallel for improved performance.

        Expected 3-5x performance improvement for documents with many images.

        Args:
            doc_id: Document ID
            image_blocks: List of dicts with 'block_id' and 'image_path' keys
            max_workers: Maximum parallel workers (default: self.MAX_IMAGE_WORKERS)

        Returns:
            Dictionary with upload statistics

        Raises:
            FeishuApiRequestError: If image upload fails

        Example:
            >>> images = [
            ...     {"block_id": "block1", "image_path": "/path/to/image1.png"},
            ...     {"block_id": "block2", "image_path": "/path/to/image2.png"},
            ... ]
            >>> result = client.upload_images_parallel("doc123", images)
            >>> print(f"Uploaded {result['total_images']} images")
        """
        if max_workers is None:
            max_workers = self.MAX_IMAGE_WORKERS

        if not image_blocks:
            return {"total_images": 0, "failed_images": 0}

        logger.info(
            f"Uploading {len(image_blocks)} images in parallel "
            f"with {max_workers} workers"
        )

        total_uploaded = 0
        total_failed = 0

        def upload_single_image(image_data: Dict[str, str]) -> Dict[str, Any]:
            """Upload a single image and return result."""
            block_id = image_data["block_id"]
            image_path = image_data["image_path"]

            try:
                self.upload_and_bind_image(
                    doc_id=doc_id, block_id=block_id, image_path_or_url=image_path
                )
                return {"success": True, "block_id": block_id, "path": image_path}
            except Exception as e:
                logger.error(f"Failed to upload image {image_path}: {e}")
                return {"success": False, "block_id": block_id, "path": image_path, "error": str(e)}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all image upload tasks
            future_to_image = {
                executor.submit(upload_single_image, img): img for img in image_blocks
            }

            # Collect results as they complete
            for future in as_completed(future_to_image):
                try:
                    result = future.result()
                    if result["success"]:
                        total_uploaded += 1
                    else:
                        total_failed += 1
                except Exception as e:
                    img = future_to_image[future]
                    logger.error(f"Unexpected error uploading {img['image_path']}: {e}")
                    total_failed += 1

        logger.info(
            f"Parallel image upload complete: {total_uploaded} uploaded, "
            f"{total_failed} failed"
        )

        return {
            "total_images": total_uploaded,
            "failed_images": total_failed,
        }

    # ========== End Parallel Upload Methods ==========

    def batch_create_blocks(
        self,
        doc_id: str,
        blocks: List[Dict[str, Any]],
        parent_id: Optional[str] = None,
        index: int = 0,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Batch create blocks in a Feishu document.

        API endpoint: POST /docx/v1/documents/{doc_id}/blocks/{parent_id}/children

        Args:
            doc_id: Document ID
            blocks: List of block configurations (from md_to_feishu.py output)
            parent_id: Parent block ID (default: doc_id for root level)
            index: Insertion index (default: 0 for beginning)
            batch_size: Maximum blocks per API request (default: 50, max: 50)

        Returns:
            API response with created block information

        Raises:
            FeishuApiRequestError: If API request fails

        Note:
            Feishu API has a hard limit of 50 blocks per request.
            Larger batches are automatically split and processed sequentially.

        Block format:
            {
                "blockType": "text|heading|code|list|image",
                "options": {
                    # Type-specific options
                    # text: {"text": {"textStyles": [{"text": "..."}]}}
                    # heading: {"heading": {"level": 1, "content": "..."}}
                    # code: {"code": {"code": "...", "language": 49}}
                    # list: {"list": {"content": "...", "isOrdered": false}}
                    # image: {"image": {"align": 2}}
                }
            }
        """
        token = self._get_token()

        # Enforce API limit: max 50 blocks per request
        batch_size = min(batch_size, 50)

        # Use doc_id as parent_id if not specified (root level)
        if parent_id is None:
            parent_id = doc_id

        # Process blocks sequentially, handling tables separately
        all_image_block_ids = []
        current_index = index

        i = 0
        while i < len(blocks):
            block = blocks[i]
            block_type = block.get("blockType", "")

            # Handle tables separately
            if block_type == "table":
                options = block.get("options", {})
                table_config = options.get("table", {})
                logger.info(
                    f"Creating table at index {current_index}: {table_config.get('rowSize')}x{table_config.get('columnSize')}"
                )
                self.create_table_block(doc_id, table_config, parent_id, current_index)
                current_index += 1
                i += 1
                continue

            # Collect non-table blocks into a batch
            children = []
            image_block_indices = []

            while i < len(blocks) and len(children) < batch_size:
                block = blocks[i]
                block_type = block.get("blockType", "")

                # Stop if we encounter a table
                if block_type == "table":
                    break

                options = block.get("options", {})

                if block_type == "text":
                    children.append(self._format_text_block(options))
                elif block_type.startswith("heading"):
                    children.append(self._format_heading_block(block_type, options))
                elif block_type == "code":
                    children.append(self._format_code_block(options))
                elif block_type == "list":
                    children.append(self._format_list_block(options))
                elif block_type == "image":
                    children.append(self._format_image_block(options))
                    image_block_indices.append(len(children) - 1)
                elif block_type == "board":
                    children.append(self._format_board_block(options))
                else:
                    logger.warning(f"Unknown block type: {block_type}, skipping")
                    i += 1
                    continue

                i += 1

            # Skip if no children collected
            if not children:
                continue

            # Prepare request for this batch
            endpoint = self.BLOCKS_ENDPOINT_TEMPLATE.format(doc_id=doc_id, parent_id=parent_id)
            url = f"{self.BASE_URL}{endpoint}?document_revision_id=-1"

            payload = {"children": children, "index": current_index}

            headers = {"Authorization": f"Bearer {token}"}

            logger.info(f"Creating {len(children)} blocks at index {current_index}")
            logger.debug(f"Request payload: {json.dumps(payload, ensure_ascii=False)[:500]}...")

            # Make request for this batch
            response = self.session.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                # Save payload for debugging
                debug_file = "/tmp/feishu_error_payload.json"
                with open(debug_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                logger.error(f"Request payload saved to: {debug_file}")

                raise FeishuApiRequestError(
                    f"Failed to create blocks: HTTP {response.status_code}\n"
                    f"Response: {response.text}"
                )

            result = response.json()

            if result.get("code") != 0:
                raise FeishuApiRequestError(
                    f"Failed to create blocks: {result.get('msg', 'Unknown error')}\n"
                    f"Error code: {result.get('code')}"
                )

            logger.info(f"Successfully created {len(children)} blocks")

            # Extract image block IDs from this batch
            image_block_ids = self._extract_image_block_ids(result, image_block_indices)
            all_image_block_ids.extend(image_block_ids)

            # Update index for next batch
            current_index += len(children)

        # Return aggregate result
        return {
            "code": 0,
            "data": {},
            "image_block_ids": all_image_block_ids,
            "total_blocks_created": len(blocks),
        }

    def upload_and_bind_image(
        self, doc_id: str, block_id: str, image_path_or_url: str, file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an image and bind it to an existing image block.

        This is a two-step process:
        1. Upload image to get file_token
        2. Set the image block content with the file_token

        Args:
            doc_id: Document ID
            block_id: Target image block ID
            image_path_or_url: Local file path or HTTP(S) URL
            file_name: Optional file name (auto-detected for local files)

        Returns:
            API response

        Raises:
            FeishuApiRequestError: If upload or binding fails
        """
        token = self._get_token()

        # Step 1: Upload image
        logger.info(f"Uploading image: {image_path_or_url}")

        if image_path_or_url.startswith(("http://", "https://")):
            # For URL, we'll use the URL directly (Feishu will fetch it)
            file_token = image_path_or_url
        else:
            # Local file - read and upload
            file_token = self._upload_image_file(image_path_or_url, file_name, token)

        # Step 2: Bind to block
        logger.info(f"Binding image to block {block_id}")

        endpoint = f"/docx/v1/documents/{doc_id}/blocks/{block_id}/image"
        url = f"{self.BASE_URL}{endpoint}"

        payload = {"file_token": file_token}

        headers = {"Authorization": f"Bearer {token}"}

        response = self.session.put(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to bind image: HTTP {response.status_code}\n" f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to bind image: {result.get('msg', 'Unknown error')}"
            )

        logger.info(f"Successfully bound image to block {block_id}")
        return result

    def _upload_image_file(self, file_path: str, file_name: Optional[str], token: str) -> str:
        """Upload local image file and return file_token"""
        path = Path(file_path)

        if not path.exists():
            raise FeishuApiRequestError(f"Image file not found: {file_path}")

        # Determine file name
        if not file_name:
            file_name = path.name

        # Read file
        with path.open("rb") as f:
            file_content = f.read()

        # Detect MIME type
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "image/png"

        # Upload
        url = f"{self.BASE_URL}{self.IMAGE_UPLOAD_ENDPOINT}"

        files = {"file": (file_name, file_content, mime_type)}

        headers = {"Authorization": f"Bearer {token}"}

        # Remove Content-Type from session headers for multipart
        headers.pop("Content-Type", None)

        response = self.session.post(url, files=files, headers=headers, timeout=60)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to upload image: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to upload image: {result.get('msg', 'Unknown error')}"
            )

        file_token = result.get("data", {}).get("file_token")

        if not file_token:
            raise FeishuApiRequestError("No file_token in upload response")

        logger.info(f"Successfully uploaded image, file_token: {file_token}")
        return file_token

    def _format_text_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format text block for API"""
        text_config = options.get("text", {})
        text_styles = text_config.get("textStyles", [])
        align = text_config.get("align", 1)

        # Convert text styles to API format
        text_elements = []
        for style in text_styles:
            text_content = style.get("text", "")
            equation_content = style.get("equation", "")

            # Skip only if both content and equation are empty/missing
            if not text_content and not equation_content:
                continue

            # Convert to Feishu API format
            if equation_content:
                # Equation element
                text_elements.append({"equation": equation_content})
            else:
                # Text run element (allow empty strings as per Feishu API requirement)
                text_element_style = self._convert_text_style(style.get("style", {}))
                text_elements.append(
                    {
                        "text_run": {
                            "content": text_content,
                            "text_element_style": text_element_style,
                        }
                    }
                )

        # Feishu API requires at least one element, even for empty cells
        if not text_elements:
            text_elements.append({"text_run": {"content": ""}})

        return {
            "block_type": 2,  # Text block type
            "text": {"elements": text_elements, "style": {"align": align}},
        }

    def _format_heading_block(self, block_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format heading block for API"""
        # Extract level from block_type (e.g., "heading1" -> 1)
        if block_type.startswith("heading"):
            level = int(block_type[-1])
        else:
            level = 1

        heading_config = options.get("heading", {})
        content = heading_config.get("content", "")
        align = heading_config.get("align", 1)

        # Feishu API block_type codes: heading1-9 use block_type 3-11
        feishu_block_type = 2 + level  # heading1 = 3, heading2 = 4, etc.

        # Heading field name matches level
        heading_field = f"heading{level}"

        return {
            "block_type": feishu_block_type,
            heading_field: {
                "elements": [
                    {
                        "text_run": {
                            "content": content,
                            "text_element_style": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "inline_code": False,
                            },
                        }
                    }
                ],
                "style": {"align": align},
            },
        }

    def _format_code_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format code block for API"""
        code_config = options.get("code", {})
        code = code_config.get("code", "")
        language = code_config.get("language", 1)  # 1 = PlainText (Feishu API standard)
        wrap = code_config.get("wrap", False)

        return {
            "block_type": 14,  # Code block type
            "code": {
                "elements": [
                    {
                        "text_run": {
                            "content": code,
                            "text_element_style": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "inline_code": False,
                            },
                        }
                    }
                ],
                "style": {"language": language, "wrap": wrap},
            },
        }

    def _format_list_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format list block for API"""
        list_config = options.get("list", {})
        content = list_config.get("content", "")
        is_ordered = list_config.get("isOrdered", False)
        align = list_config.get("align", 1)

        # Block types: 12 = bullet (unordered), 13 = ordered
        block_type = 13 if is_ordered else 12
        list_field = "ordered" if is_ordered else "bullet"

        return {
            "block_type": block_type,
            list_field: {
                "elements": [
                    {
                        "text_run": {
                            "content": content,
                            "text_element_style": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "inline_code": False,
                            },
                        }
                    }
                ],
                "style": {"align": align},
            },
        }

    def _format_image_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Format image block placeholder for API"""
        image_config = options.get("image", {})
        align = image_config.get("align", 2)  # Default center

        return {"block_type": 27, "image": {"align": align}}  # Image block type (from MCP source)

    def _format_board_block(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format whiteboard/board block for API.

        Args:
            options: Board options dictionary containing:
                - board: Board configuration with optional width, height

        Returns:
            Formatted board block for API

        Example:
            >>> options = {"board": {"width": 800, "height": 600}}
            >>> block = client._format_board_block(options)
        """
        board_config = options.get("board", {})
        align = board_config.get("align", 2)  # Default center

        board_data = {"align": align}

        # Add optional dimensions if provided
        if "width" in board_config:
            board_data["width"] = board_config["width"]
        if "height" in board_config:
            board_data["height"] = board_config["height"]

        return {"block_type": 43, "board": board_data}  # Whiteboard block type

    def create_table_block(
        self,
        doc_id: str,
        table_config: Dict[str, Any],
        parent_id: Optional[str] = None,
        index: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a table block in a Feishu document using the descendants API.

        Args:
            doc_id: Document ID
            table_config: Table configuration with columnSize, rowSize, and cells
            parent_id: Parent block ID (default: doc_id for root level)
            index: Insertion index

        Returns:
            API response with created table information

        Format:
            {
                "columnSize": 3,
                "rowSize": 3,
                "cells": [
                    {
                        "coordinate": {"row": 0, "column": 0},
                        "content": {
                            "blockType": "text",
                            "options": {...}
                        }
                    },
                    ...
                ]
            }
        """
        token = self._get_token()

        if parent_id is None:
            parent_id = doc_id

        column_size = table_config.get("columnSize", 0)
        row_size = table_config.get("rowSize", 0)
        cells_config = table_config.get("cells", [])

        # 生成唯一 ID
        import time

        table_id = f"table_{int(time.time() * 1000)}"

        # 创建 descendants 数组
        descendants = []
        table_cells = []

        # 创建表格主块
        table_block = {
            "block_id": table_id,
            "block_type": 31,  # 表格
            "table": {"property": {"row_size": row_size, "column_size": column_size}},
            "children": [],
        }

        # 创建所有单元格
        for row in range(row_size):
            for col in range(column_size):
                cell_id = f"{table_id}_cell_{row}_{col}"
                table_cells.append(cell_id)

                # 查找该单元格的配置
                cell_config = None
                for cfg in cells_config:
                    coord = cfg.get("coordinate", {})
                    if coord.get("row") == row and coord.get("column") == col:
                        cell_config = cfg
                        break

                # 创建单元格内容
                if cell_config:
                    content = cell_config.get("content", {})
                    block_type = content.get("blockType", "text")
                    options = content.get("options", {})

                    # 格式化内容块
                    if block_type == "text":
                        content_block = self._format_text_block(options)
                    else:
                        # 默认使用空文本
                        content_block = self._format_text_block(
                            {"text": {"textStyles": [{"text": "", "style": {}}], "align": 1}}
                        )
                else:
                    # 空单元格
                    content_block = self._format_text_block(
                        {"text": {"textStyles": [{"text": "", "style": {}}], "align": 1}}
                    )

                # 单元格内容 ID
                cell_content_id = f"{cell_id}_content"

                # 创建单元格块
                cell_block = {
                    "block_id": cell_id,
                    "block_type": 32,  # 表格单元格
                    "table_cell": {},
                    "children": [cell_content_id],
                }

                # 创建单元格内容块
                cell_content_block = {"block_id": cell_content_id, **content_block, "children": []}

                descendants.append(cell_block)
                descendants.append(cell_content_block)

        # 更新表格主块的 children
        table_block["children"] = table_cells

        # 表格块放在最前面
        descendants.insert(0, table_block)

        # 构建请求 - 使用 /descendant endpoint (与官方文档不符，但部分场景可用)
        endpoint = f"/docx/v1/documents/{doc_id}/blocks/{parent_id}/descendant?document_revision_id=-1"
        url = f"{self.BASE_URL}{endpoint}"

        payload = {"children_id": [table_id], "descendants": descendants, "index": index}

        headers = {"Authorization": f"Bearer {token}"}

        logger.info(
            f"Creating table: {row_size}x{column_size} with {len(cells_config)} configured cells"
        )
        logger.debug(f"Table payload size: {len(json.dumps(payload))} bytes")

        response = self.session.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            # Save payload for debugging
            debug_file = "/tmp/feishu_table_error_payload.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.error(f"Table request payload saved to: {debug_file}")

            raise FeishuApiRequestError(
                f"Failed to create table: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to create table: {result.get('msg', 'Unknown error')}\n"
                f"Error code: {result.get('code')}"
            )

        logger.info(f"Successfully created table: {row_size}x{column_size}")

        return result

    def _convert_text_style(self, style: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text style from Markdown to API format"""
        # Feishu API requires all style fields to be present
        api_style = {
            "bold": style.get("bold", False),
            "italic": style.get("italic", False),
            "underline": style.get("underline", False),
            "strikethrough": style.get("strikethrough", False),
            "inline_code": style.get("inline_code", False),
        }

        # Text color (optional)
        text_color = style.get("text_color")
        if text_color is not None:
            api_style["text_color"] = text_color

        # Background color (optional)
        bg_color = style.get("background_color")
        if bg_color is not None:
            api_style["background_color"] = bg_color

        return api_style

    def _extract_image_block_ids(self, result: Dict[str, Any], indices: List[int]) -> List[str]:
        """Extract image block IDs from API response"""
        block_ids = []

        # The response should contain created blocks with their IDs
        children = result.get("children", [])

        for i, child in enumerate(children):
            # Check if this is an image block (block_type == 27)
            if child.get("block_type") == 27:
                block_id = child.get("block_id")
                if block_id:
                    block_ids.append(block_id)

        logger.info(f"Extracted {len(block_ids)} image block IDs")
        return block_ids

    def get_document_blocks(
        self,
        doc_id: str,
        page_size: int = 500,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all blocks from a Feishu document.

        Args:
            doc_id: Document ID
            page_size: Number of blocks per page (max 500)
            page_token: Token for pagination

        Returns:
            API response with blocks data:
            {
                "has_more": bool,
                "page_token": str,
                "items": [
                    {
                        "block_id": str,
                        "block_type": int,
                        "parent_id": str,
                        "children": List[str],
                        "text": {...},  # For text blocks
                        "heading1": {...},  # For heading blocks
                        ...
                    }
                ]
            }
        """
        token = self._get_token()

        endpoint = f"/docx/v1/documents/{doc_id}/blocks"
        url = f"{self.BASE_URL}{endpoint}"

        params = {
            "page_size": min(page_size, 500),  # Max 500 per API docs
            "document_revision_id": -1,  # Latest version
        }

        if page_token:
            params["page_token"] = page_token

        headers = {"Authorization": f"Bearer {token}"}

        logger.debug(f"Fetching blocks from document: {doc_id}")
        response = self.session.get(url, params=params, headers=headers, timeout=30)

        if response.status_code != 200:
            raise FeishuApiRequestError(
                f"Failed to get document blocks: HTTP {response.status_code}\n"
                f"Response: {response.text}"
            )

        result = response.json()

        if result.get("code") != 0:
            raise FeishuApiRequestError(
                f"Failed to get document blocks: {result.get('msg', 'Unknown error')}\n"
                f"Error code: {result.get('code')}"
            )

        data = result.get("data", {})
        items = data.get("items", [])
        has_more = data.get("has_more", False)

        logger.info(f"Retrieved {len(items)} blocks, has_more: {has_more}")

        return data

    def get_all_document_blocks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get ALL blocks from a document, handling pagination automatically.

        Args:
            doc_id: Document ID

        Returns:
            List of all blocks in the document
        """
        all_blocks = []
        page_token = None
        page_count = 0

        logger.info(f"Fetching all blocks from document: {doc_id}")

        while True:
            page_count += 1
            logger.debug(f"Fetching page {page_count}...")

            data = self.get_document_blocks(doc_id, page_token=page_token)
            items = data.get("items", [])
            all_blocks.extend(items)

            has_more = data.get("has_more", False)
            if not has_more:
                break

            page_token = data.get("page_token")
            if not page_token:
                logger.warning("has_more is True but no page_token returned")
                break

        logger.info(f"Retrieved {len(all_blocks)} blocks total from {page_count} pages")
        return all_blocks


def upload_markdown_to_feishu(
    md_file: str,
    doc_id: str,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    parallel: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to upload Markdown file to Feishu.

    This function:
    1. Converts Markdown to blocks using md_to_feishu.py
    2. Uploads blocks using FeishuApiClient
    3. Uploads images if any

    Args:
        md_file: Path to Markdown file
        doc_id: Feishu document ID
        app_id: Feishu app ID (or use FEISHU_APP_ID env var)
        app_secret: Feishu app secret (or use FEISHU_APP_SECRET env var)
        parallel: Use parallel uploads for better performance (default: False)

    Returns:
        Upload result with document link and statistics

    Raises:
        FileNotFoundError: If md_file not found
        FeishuApiClientError: If API operations fail

    Example:
        >>> # Serial upload (default)
        >>> result = upload_markdown_to_feishu("README.md", "doxcnxxxxx")
        >>> print(f"Uploaded {result['total_blocks']} blocks")
        >>>
        >>> # Parallel upload (faster for large documents)
        >>> result = upload_markdown_to_feishu("README.md", "doxcnxxxxx", parallel=True)
        >>> print(f"Document: https://feishu.cn/docx/{doc_id}")
    """
    from scripts.md_to_feishu import MarkdownToFeishuConverter

    # Step 1: Convert Markdown to blocks
    logger.info(f"Converting Markdown file: {md_file}")
    converter = MarkdownToFeishuConverter(md_file=Path(md_file), doc_id=doc_id)

    conversion_result = converter.convert()

    if not conversion_result.get("success"):
        raise RuntimeError(
            f"Failed to convert Markdown: {conversion_result.get('error', 'Unknown error')}"
        )

    # Step 2: Create API client
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Step 3: Upload blocks (serial or parallel)
    all_batches = conversion_result.get("batches", [])
    all_images = conversion_result.get("images", [])

    total_blocks = 0
    total_images = 0
    created_image_block_ids: List[str] = []

    if parallel and len(all_batches) > 1:
        # Parallel upload for better performance
        logger.info("Using parallel upload mode")

        # Flatten all blocks from batches
        all_blocks = []
        for batch in all_batches:
            all_blocks.extend(batch["blocks"])

        batch_result = client.batch_create_blocks_parallel(doc_id=doc_id, blocks=all_blocks)
        total_blocks = batch_result.get("total_blocks_created", 0)
        created_image_block_ids = batch_result.get("image_block_ids", [])
    else:
        # Serial upload (original behavior)
        for batch in all_batches:
            batch_index = batch["batchIndex"]
            blocks = batch["blocks"]
            start_index = batch["startIndex"]

            logger.info(f"Uploading batch {batch_index + 1}/{len(all_batches)}")

            result = client.batch_create_blocks(doc_id=doc_id, blocks=blocks, index=start_index)

            total_blocks += result.get("total_blocks_created", 0)

            # Collect image block IDs
            image_block_ids = result.get("image_block_ids", [])
            created_image_block_ids.extend(image_block_ids)

    # Step 4: Upload images (serial or parallel)
    if all_images and created_image_block_ids:
        if parallel and len(all_images) > 1:
            # Parallel image upload
            logger.info(f"Uploading {len(all_images)} images in parallel")

            # Prepare image block data
            image_blocks = []
            for i, image_info in enumerate(all_images):
                if i < len(created_image_block_ids):
                    image_blocks.append(
                        {
                            "block_id": created_image_block_ids[i],
                            "image_path": image_info["localPath"],
                        }
                    )

            image_result = client.upload_images_parallel(doc_id=doc_id, image_blocks=image_blocks)
            total_images = image_result.get("total_images", 0)

            # Log failed images
            failed = image_result.get("failed_images", 0)
            if failed > 0:
                logger.warning(f"{failed} image(s) failed to upload")
        else:
            # Serial image upload (original behavior)
            logger.info(f"Uploading {len(all_images)} images")

            for i, image_info in enumerate(all_images):
                block_index = image_info["blockIndex"]
                local_path = image_info["localPath"]

                # Find corresponding image block ID
                # (This assumes image blocks are created in the same order)
                if i < len(created_image_block_ids):
                    block_id = created_image_block_ids[i]

                    logger.info(f"Uploading image {i + 1}/{len(all_images)}: {local_path}")

                    try:
                        client.upload_and_bind_image(
                            doc_id=doc_id, block_id=block_id, image_path_or_url=local_path
                        )
                        total_images += 1
                    except Exception as e:
                        logger.error(f"Failed to upload image {local_path}: {e}")
                        # Continue with other images

    # Return result
    return {
        "success": True,
        "document_id": doc_id,
        "document_url": f"https://feishu.cn/docx/{doc_id}",
        "total_blocks": total_blocks,
        "total_images": total_images,
        "total_batches": len(all_batches),
        "parallel_mode": parallel,
    }


def create_document_from_markdown(
    md_file: str,
    title: Optional[str] = None,
    folder_token: Optional[str] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    add_permission: bool = False,
    user_id: Optional[str] = None,
    permission_level: str = "edit",
) -> Dict[str, Any]:
    """
    Create a new Feishu document and upload markdown content to it.

    This is the main entry point for "create document from markdown" workflow.

    Workflow:
    1. Create new document with given title
    2. Convert markdown to blocks
    3. Upload blocks to new document
    4. Upload images if any
    5. Optionally set permissions for current user

    Args:
        md_file: Path to markdown file
        title: Document title (default: filename without extension)
        folder_token: Parent folder (default: root)
        app_id: Feishu app ID (or use FEISHU_APP_ID env var)
        app_secret: Feishu app secret (or use FEISHU_APP_SECRET env var)
        add_permission: Whether to add edit permission for current user
        user_id: User ID to grant permission to (default: auto-detect or from FEISHU_USER_ID)
        permission_level: Permission level - "view", "edit", or "admin" (default: "edit")

    Returns:
        {
            "success": True,
            "document_id": "doxcnxxxxx",
            "document_url": "https://feishu.cn/docx/doxcnxxxxx",
            "title": "Document Title",
            "total_blocks": 50,
            "total_images": 3,
            "total_batches": 1,
            "permission_set": True  # If add_permission=True
        }

    Raises:
        FileNotFoundError: If md_file not found
        FeishuApiClientError: If API operations fail

    Example:
        >>> result = create_document_from_markdown("README.md", title="My Document")
        >>> print(f"Created: {result['document_url']}")
        >>> print(f"Blocks: {result['total_blocks']}")

        >>> # With permission for current user
        >>> result = create_document_from_markdown("README.md", add_permission=True)
    """
    # Step 1: Create document
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Use filename as title if not provided
    if title is None:
        title = Path(md_file).stem

    # Determine folder token: use provided folder, default folder, or None (app space)
    effective_folder_token = folder_token
    if effective_folder_token is None:
        # Try to use default folder from environment variable
        # This allows users to specify their personal cloud document folder
        effective_folder_token = client.get_default_folder_token()
        if effective_folder_token:
            logger.info(f"Using default folder from environment: {effective_folder_token}")
        else:
            logger.warning(
                "No folder_token specified and FEISHU_DEFAULT_FOLDER_TOKEN not set. "
                "Document will be created in application space (only app has access). "
                "Set FEISHU_DEFAULT_FOLDER_TOKEN to your cloud document folder token to fix this."
            )

    doc_result = client.create_document(title=title, folder_token=effective_folder_token)
    doc_id = doc_result["document_id"]

    # Step 2: Upload content to new document
    logger.info(f"Uploading content to new document: {doc_id}")

    upload_result = upload_markdown_to_feishu(
        md_file=md_file, doc_id=doc_id, app_id=app_id, app_secret=app_secret
    )

    # Step 3: Set permission if requested
    permission_set = False
    if add_permission:
        try:
            # Get user ID if not provided
            if user_id is None:
                user_id = client.get_current_user_id()

            client.set_document_permission(
                document_id=doc_id, user_id=user_id, permission=permission_level, notify=False
            )
            permission_set = True
            logger.info(f"Successfully set {permission_level} permission for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to set permission: {e}")
            logger.warning(
                "You may need to manually set permissions in Feishu or set FEISHU_USER_ID environment variable"
            )

    # Step 4: Return combined result
    return {
        "success": True,
        "document_id": doc_id,
        "document_url": doc_result["url"],
        "title": doc_result["title"],
        "total_blocks": upload_result.get("total_blocks", 0),
        "total_images": upload_result.get("total_images", 0),
        "total_batches": upload_result.get("total_batches", 0),
        "permission_set": permission_set,
    }


def batch_create_documents_from_folder(
    folder_path: str,
    feishu_folder_token: Optional[str] = None,
    pattern: str = "*.md",
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Batch create Feishu documents from local folder.

    Scans folder for markdown files and creates a Feishu document for each one.

    Workflow:
    1. Scan local folder for files matching pattern
    2. For each file: create document + upload content
    3. Return summary with success/failure counts

    Args:
        folder_path: Path to local folder with markdown files
        feishu_folder_token: Target folder in Feishu (default: root)
        pattern: File glob pattern (default: "*.md")
        app_id: Feishu app ID (or use FEISHU_APP_ID env var)
        app_secret: Feishu app secret (or use FEISHU_APP_SECRET env var)

    Returns:
        {
            "success": True,
            "total_files": 10,
            "successful": 9,
            "failed": 1,
            "documents": [
                {
                    "file": "doc1.md",
                    "document_id": "doxcnxxxxx",
                    "url": "https://feishu.cn/docx/doxcnxxxxx",
                    "blocks": 50,
                    "images": 3
                },
                ...
            ],
            "failures": [
                {
                    "file": "doc2.md",
                    "error": "..."
                }
            ]
        }

    Raises:
        FileNotFoundError: If folder not found
        FeishuApiClientError: If API operations fail

    Example:
        >>> result = batch_create_documents_from_folder("./docs")
        >>> print(f"Created {result['successful']}/{result['total_files']} documents")
        >>> for failure in result['failures']:
        ...     print(f"Failed: {failure['file']}: {failure['error']}")
    """
    # Step 1: Validate folder
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Step 2: Find markdown files
    md_files = sorted(folder.glob(pattern))
    logger.info(f"Found {len(md_files)} markdown files in {folder_path}")

    if not md_files:
        logger.warning(f"No files matching pattern '{pattern}' in {folder_path}")
        return {
            "success": True,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "documents": [],
            "failures": [],
        }

    # Step 3: Initialize client
    if app_id and app_secret:
        client = FeishuApiClient(app_id, app_secret)
    else:
        client = FeishuApiClient.from_env()

    # Step 4: Process each file
    documents = []
    failures = []

    for i, md_file in enumerate(md_files, 1):
        try:
            logger.info(f"Processing {i}/{len(md_files)}: {md_file.name}")

            result = create_document_from_markdown(
                md_file=str(md_file),
                title=md_file.stem,
                folder_token=feishu_folder_token,
                app_id=app_id,
                app_secret=app_secret,
            )

            documents.append(
                {
                    "file": md_file.name,
                    "document_id": result["document_id"],
                    "url": result["document_url"],
                    "blocks": result.get("total_blocks", 0),
                    "images": result.get("total_images", 0),
                }
            )

            logger.info(f"✅ Created: {md_file.name}")

        except Exception as e:
            error_msg = str(e)
            failures.append({"file": md_file.name, "error": error_msg})
            logger.error(f"❌ Failed: {md_file.name}: {error_msg}")

    # Step 5: Return summary
    return {
        "success": len(failures) == 0,
        "total_files": len(md_files),
        "successful": len(documents),
        "failed": len(failures),
        "documents": documents,
        "failures": failures,
    }
