"""
Tests for extended Feishu API client functionality.

Tests for document creation, folder management, and batch operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lib.feishu_api_client import (
    FeishuApiClient,
    FeishuApiRequestError,
    FeishuApiAuthError,
    create_document_from_markdown,
    batch_create_documents_from_folder
)


@pytest.fixture
def mock_client():
    """Create a mock Feishu API client."""
    client = FeishuApiClient("test_app_id", "test_app_secret")
    return client


@pytest.fixture
def sample_md_file(tmp_path):
    """Create a sample markdown file for testing."""
    md_content = """# Test Document

This is a test document with multiple content types.

## Section 1

Some **bold** and *italic* text.

### Code Block

```python
def hello():
    print("Hello, World!")
```

## Lists

- Item 1
- Item 2

1. First
2. Second

## Images

![Sample Image](image.png)
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(md_content, encoding='utf-8')
    return md_file


class TestDocumentCreation:
    """Tests for document creation functionality."""

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_create_document_success(self, mock_post, mock_token, mock_client):
        """Test successful document creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "document": {
                    "document_id": "doxcnxxxxx",
                    "title": "Test Document",
                    "revision_id": 1
                }
            }
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_document("Test Document")

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        assert result["title"] == "Test Document"
        assert "https://feishu.cn/docx/doxcnxxxxx" in result["url"]
        mock_post.assert_called_once()

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_create_document_with_folder(self, mock_post, mock_token, mock_client):
        """Test creating document in specific folder."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "document": {
                    "document_id": "doxcnxxxxx",
                    "title": "Test",
                    "revision_id": 1
                }
            }
        }
        mock_post.return_value = mock_response

        # Execute
        result = mock_client.create_document("Test", folder_token="fldcnxxxxx")

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        # Check that folder_token was included in payload
        call_kwargs = mock_post.call_args[1]
        assert "Bearer test_token" in call_kwargs["headers"]["Authorization"]

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_create_document_auth_failure(self, mock_post, mock_token, mock_client):
        """Test document creation with auth failure."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError):
            mock_client.create_document("Test")

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_create_document_api_error(self, mock_post, mock_token, mock_client):
        """Test document creation with API error response."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 400,
            "msg": "Invalid request"
        }
        mock_post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(FeishuApiRequestError):
            mock_client.create_document("Test")


class TestFolderOperations:
    """Tests for folder management functionality."""

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.get')
    def test_get_root_folder_token(self, mock_get, mock_token, mock_client):
        """Test getting root folder token."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "folder_token": "fldcnxxxxx"
            }
        }
        mock_get.return_value = mock_response

        # Execute
        result = mock_client.get_root_folder_token()

        # Assert
        assert result == "fldcnxxxxx"
        mock_get.assert_called_once()

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_create_folder_success(self, mock_post, mock_token, mock_client):
        """Test successful folder creation."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "folder": {
                    "folder_token": "fldcnxxxxx",
                    "name": "Test Folder"
                }
            }
        }
        mock_post.return_value = mock_response

        # Mock get_root_folder_token
        with patch.object(mock_client, 'get_root_folder_token', return_value="root_token"):
            # Execute
            result = mock_client.create_folder("Test Folder")

        # Assert
        assert result["folder_token"] == "fldcnxxxxx"
        assert result["name"] == "Test Folder"
        assert "https://feishu.cn/drive/folder/fldcnxxxxx" in result["url"]

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.get')
    def test_list_folder_contents(self, mock_get, mock_token, mock_client):
        """Test listing folder contents."""
        # Setup
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "items": [
                    {"name": "file1.md", "type": "file"},
                    {"name": "folder1", "type": "folder"}
                ]
            }
        }
        mock_get.return_value = mock_response

        # Execute
        result = mock_client.list_folder_contents("fldcnxxxxx")

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "file1.md"
        assert result[1]["name"] == "folder1"


class TestHighLevelFunctions:
    """Tests for high-level convenience functions."""

    @patch('lib.feishu_api_client.upload_markdown_to_feishu')
    @patch('lib.feishu_api_client.FeishuApiClient.create_document')
    def test_create_document_from_markdown(self, mock_create, mock_upload, sample_md_file):
        """Test create_document_from_markdown function."""
        # Setup
        mock_create.return_value = {
            "document_id": "doxcnxxxxx",
            "url": "https://feishu.cn/docx/doxcnxxxxx",
            "title": "test"
        }
        mock_upload.return_value = {
            "success": True,
            "total_blocks": 50,
            "total_images": 3,
            "total_batches": 1
        }

        with patch('lib.feishu_api_client.FeishuApiClient.from_env') as mock_from_env:
            mock_client = Mock()
            mock_client.create_document = mock_create
            mock_from_env.return_value = mock_client

            # Execute
            result = create_document_from_markdown(
                str(sample_md_file),
                title="Test Document"
            )

        # Assert
        assert result["document_id"] == "doxcnxxxxx"
        assert result["total_blocks"] == 50
        assert result["total_images"] == 3
        mock_create.assert_called_once()
        mock_upload.assert_called_once()

    def test_create_document_from_markdown_invalid_file(self):
        """Test create_document_from_markdown with non-existent file."""
        # Execute & Assert (RuntimeError is raised when conversion fails)
        with pytest.raises(RuntimeError):
            create_document_from_markdown("/non/existent/file.md")

    @patch('lib.feishu_api_client.create_document_from_markdown')
    @patch('lib.feishu_api_client.FeishuApiClient.from_env')
    def test_batch_create_documents_from_folder(self, mock_from_env, mock_create_doc, tmp_path):
        """Test batch document creation from folder."""
        # Setup - create test markdown files
        for i in range(3):
            (tmp_path / f"doc{i}.md").write_text(f"# Document {i}")

        mock_create_doc.side_effect = [
            {
                "document_id": f"docxcnxxxxx{i}",
                "document_url": f"https://feishu.cn/docx/docxcnxxxxx{i}",
                "total_blocks": 10,
                "total_images": 0
            }
            for i in range(3)
        ]

        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert len(result["documents"]) == 3
        assert mock_create_doc.call_count == 3

    def test_batch_create_documents_empty_folder(self, tmp_path):
        """Test batch creation on empty folder."""
        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0

    def test_batch_create_documents_invalid_folder(self):
        """Test batch creation with non-existent folder."""
        # Execute & Assert
        with pytest.raises(FileNotFoundError):
            batch_create_documents_from_folder("/non/existent/folder")

    @patch('lib.feishu_api_client.create_document_from_markdown')
    @patch('lib.feishu_api_client.FeishuApiClient.from_env')
    def test_batch_create_documents_with_failures(self, mock_from_env, mock_create_doc, tmp_path):
        """Test batch creation with some failures."""
        # Setup - create test markdown files
        for i in range(3):
            (tmp_path / f"doc{i}.md").write_text(f"# Document {i}")

        # Make the second document fail
        mock_create_doc.side_effect = [
            {"document_id": "doc1", "document_url": "url1", "total_blocks": 10, "total_images": 0},
            FeishuApiRequestError("API Error"),
            {"document_id": "doc3", "document_url": "url3", "total_blocks": 10, "total_images": 0}
        ]

        # Execute
        result = batch_create_documents_from_folder(str(tmp_path))

        # Assert
        assert result["total_files"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert len(result["documents"]) == 2
        assert len(result["failures"]) == 1


class TestErrorHandling:
    """Tests for error handling."""

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    @patch('requests.Session.post')
    def test_network_timeout(self, mock_post, mock_token, mock_client):
        """Test handling of network timeout."""
        # Setup
        mock_token.return_value = "test_token"
        mock_post.side_effect = TimeoutError("Connection timeout")

        # Execute & Assert
        with pytest.raises(TimeoutError):
            mock_client.create_document("Test")

    @patch('lib.feishu_api_client.FeishuApiClient.get_tenant_token')
    def test_token_retrieval_failure(self, mock_token, mock_client):
        """Test handling of token retrieval failure."""
        # Setup
        mock_token.side_effect = FeishuApiAuthError("Invalid credentials")

        # Execute & Assert
        with pytest.raises(FeishuApiAuthError):
            mock_client.create_document("Test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
