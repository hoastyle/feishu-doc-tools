"""
Feishu API Client - Direct API integration for md-to-feishu

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
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


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

    Usage:
        client = FeishuApiClient.from_env()
        result = client.upload_blocks("doc_id", blocks)
    """

    # API Endpoints
    BASE_URL = "https://open.feishu.cn/open-apis"
    AUTH_ENDPOINT = "/auth/v3/tenant_access_token/internal"
    BLOCKS_ENDPOINT_TEMPLATE = "/docx/v1/documents/{doc_id}/blocks/{parent_id}/children"
    IMAGE_UPLOAD_ENDPOINT = "/docx/v1/media/upload"

    # Token cache
    _token_cache: Optional[Dict[str, str]] = None
    _token_expire_time: Optional[int] = None

    def __init__(self, app_id: str, app_secret: str):
        """
        Initialize Feishu API client.

        Args:
            app_id: Feishu app ID (cli_xxxxx)
            app_secret: Feishu app secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json; charset=utf-8"})

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

        return cls(app_id, app_secret)

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
        Get or refresh tenant_access_token.

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

        # Check cache
        if not force_refresh and self._token_cache and self._token_expire_time:
            if current_time < self._token_expire_time - 300:  # Refresh 5 min before expiry
                logger.debug("Using cached token")
                return self._token_cache.get("tenant_access_token", "")

        # Request new token
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

        # Cache token
        self._token_cache = {"tenant_access_token": token}
        self._token_expire_time = current_time + expire

        logger.info(f"Successfully obtained tenant token, expires in {expire}s")
        return token

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()
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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
            token = self.get_tenant_token()
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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
        token = self.get_tenant_token()

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
            # Skip empty elements
            text_content = style.get("text", "")
            equation_content = style.get("equation", "")

            if not text_content and not equation_content:
                continue
            if text_content == "":
                continue

            # Convert to Feishu API format
            if equation_content:
                # Equation element
                text_elements.append({"equation": equation_content})
            else:
                # Text run element
                text_element_style = self._convert_text_style(style.get("style", {}))
                text_elements.append(
                    {
                        "text_run": {
                            "content": text_content,
                            "text_element_style": text_element_style,
                        }
                    }
                )

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
        token = self.get_tenant_token()

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

        # 构建请求
        endpoint = (
            f"/docx/v1/documents/{doc_id}/blocks/{parent_id}/descendant?document_revision_id=-1"
        )
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
        """Convert text style from md-to-feishu format to API format"""
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


def upload_markdown_to_feishu(
    md_file: str, doc_id: str, app_id: Optional[str] = None, app_secret: Optional[str] = None
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

    Returns:
        Upload result with document link and statistics

    Raises:
        FileNotFoundError: If md_file not found
        FeishuApiClientError: If API operations fail

    Example:
        >>> result = upload_markdown_to_feishu("README.md", "doxcnxxxxx")
        >>> print(f"Uploaded {result['total_blocks']} blocks")
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

    # Step 3: Upload blocks batch by batch
    all_batches = conversion_result.get("batches", [])
    all_images = conversion_result.get("images", [])

    total_blocks = 0
    total_images = 0
    created_image_block_ids: List[str] = []

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

    # Step 4: Upload images
    if all_images and created_image_block_ids:
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
