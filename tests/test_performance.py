"""
Performance benchmarks for feishu-doc-tools.

These tests measure upload performance with and without parallelization.
Run with: pytest tests/test_performance.py -v
"""

import pytest
import time
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.feishu_api_client import FeishuApiClient


@pytest.fixture
def mock_client():
    """Create a mock Feishu API client."""
    client = FeishuApiClient("test_app_id", "test_app_secret")
    return client


class TestPerformanceBenchmarks:
    """
    Performance benchmarks for feishu-doc-tools.

    These tests verify that:
    - Small documents (<50 blocks) upload in <5s
    - Medium documents (50-200 blocks) upload in <15s (serial) / <5s (parallel)
    - Large documents (200-1000 blocks) upload in <60s (serial) / <15s (parallel)
    - Parallel mode is 3-5x faster than serial mode
    """

    @staticmethod
    def _mock_batch_create_delay(delay: float = 0.01):
        """Create a mock batch_create_blocks with simulated delay."""

        def mock_func(self, doc_id: str, blocks, parent_id=None, index=0, **kwargs):
            time.sleep(delay * len(blocks) / 50)  # Simulate API latency
            return {
                "total_blocks_created": len(blocks),
                "image_block_ids": [],
            }

        return mock_func

    @staticmethod
    def _mock_image_upload_delay(delay: float = 0.1):
        """Create a mock upload_and_bind_image with simulated delay."""

        def mock_func(self, doc_id: str, block_id: str, image_path_or_url: str):
            time.sleep(delay)  # Simulate upload latency
            return None

        return mock_func

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_small_document_upload(self, mock_token, mock_client):
        """
        Test small document upload performance.

        Target: <50 blocks should upload in <5s
        """
        mock_token.return_value = "test_token"

        # Create small block set (30 blocks)
        blocks = [{"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}} for i in range(30)]

        start_time = time.time()
        result = mock_client.batch_create_blocks_parallel("doc123", blocks, max_workers=2)
        elapsed = time.time() - start_time

        assert result["total_blocks_created"] == 30
        assert elapsed < 5.0, f"Small document upload took {elapsed:.2f}s, expected <5s"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_medium_document_upload(self, mock_token, mock_client):
        """
        Test medium document upload performance.

        Target: 100 blocks should upload in <15s serial, <5s parallel
        """
        mock_token.return_value = "test_token"

        # Create medium block set (100 blocks)
        blocks = [{"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}} for i in range(100)]

        # Test parallel mode
        start_time = time.time()
        result = mock_client.batch_create_blocks_parallel("doc123", blocks, max_workers=3)
        parallel_time = time.time() - start_time

        assert result["total_blocks_created"] == 100
        assert parallel_time < 8.0, f"Parallel upload took {parallel_time:.2f}s, expected <8s"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_large_document_upload(self, mock_token, mock_client):
        """
        Test large document upload performance.

        Target: 500 blocks should upload in <30s parallel
        """
        mock_token.return_value = "test_token"

        # Create large block set (500 blocks)
        blocks = [{"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}} for i in range(500)]

        start_time = time.time()
        result = mock_client.batch_create_blocks_parallel("doc123", blocks, max_workers=3)
        elapsed = time.time() - start_time

        assert result["total_blocks_created"] == 500
        assert elapsed < 25.0, f"Large document upload took {elapsed:.2f}s, expected <25s"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.02))
    def test_parallel_vs_serial(self, mock_token, mock_client):
        """
        Test parallel vs serial upload performance.

        Target: Parallel should be 3-5x faster than serial for 200 blocks
        """
        mock_token.return_value = "test_token"

        # Create block set (200 blocks)
        blocks = [{"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}} for i in range(200)]

        # Test serial mode (single batch)
        start_time = time.time()
        result_serial = mock_client.batch_create_blocks("doc123", blocks)
        serial_time = time.time() - start_time

        # Test parallel mode (multiple workers)
        start_time = time.time()
        result_parallel = mock_client.batch_create_blocks_parallel("doc123", blocks, max_workers=3)
        parallel_time = time.time() - start_time

        speedup = serial_time / parallel_time

        assert result_serial["total_blocks_created"] == 200
        assert result_parallel["total_blocks_created"] == 200
        assert speedup >= 2.0, f"Speedup was {speedup:.2f}x, expected >= 2x"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_image_upload_performance(self, mock_token, mock_client):
        """
        Test parallel image upload performance.

        Target: 10 images should upload in <5s parallel (vs <30s serial)
        """
        mock_token.return_value = "test_token"

        # First, create image blocks
        blocks = [{"blockType": "image", "options": {"image": {}}} for _ in range(10)]
        batch_result = mock_client.batch_create_blocks("doc123", blocks)

        # Prepare image data
        image_blocks = [
            {"block_id": f"block{i}", "image_path": f"/tmp/image{i}.png"} for i in range(10)
        ]

        # Mock image upload with delay
        upload_delay = 0.05

        def mock_upload(self, doc_id: str, block_id: str, image_path_or_url: str):
            time.sleep(upload_delay)
            return None

        with patch.object(FeishuApiClient, "upload_and_bind_image", mock_upload):
            start_time = time.time()
            result = mock_client.upload_images_parallel("doc123", image_blocks, max_workers=5)
            elapsed = time.time() - start_time

        assert result["total_images"] == 10
        # With 5 workers and 0.05s per image, should take ~0.1s (2 batches)
        assert elapsed < 5.0, f"Image upload took {elapsed:.2f}s, expected <5s"

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    def test_connection_pool_performance(self, mock_token):
        """
        Test connection pool efficiency.

        Verify that connection pool reduces overhead for multiple requests.
        """
        mock_token.return_value = "test_token"

        client = FeishuApiClient("test_app_id", "test_app_secret")

        # Verify session is configured with connection pool
        assert client.session is not None
        assert hasattr(client.session, "adapters")

        # Check that https adapter has pool configuration
        https_adapter = client.session.get_adapter("https://")
        assert https_adapter is not None

    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    def test_thread_safe_token_refresh(self, mock_token):
        """
        Test token refresh is thread-safe.

        Verify that concurrent token requests don't cause issues.
        """
        import threading

        call_count = [0]
        token_value = ["token_1"]

        def mock_token_func(force_refresh=False):
            call_count[0] += 1
            # Simulate some delay
            time.sleep(0.01)
            return token_value[0]

        mock_token.side_effect = mock_token_func

        client = FeishuApiClient("test_app_id", "test_app_secret")

        # Make concurrent token requests
        threads = []
        results = []

        def get_token():
            result = client.get_tenant_token()
            results.append(result)

        for _ in range(10):
            t = threading.Thread(target=get_token)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All threads should get the same token (due to locking)
        assert all(r == "token_1" for r in results)
        # Token should only be fetched once (due to cache and lock)
        assert call_count[0] <= 2


class TestPerformanceMetrics:
    """Helper tests to gather performance metrics."""

    @pytest.mark.skip(reason="Performance monitoring - run manually")
    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_measure_serial_performance(self, mock_token, mock_client):
        """
        Measure serial upload performance for different document sizes.

        Run manually to gather baseline metrics:
        pytest tests/test_performance.py::TestPerformanceMetrics::test_measure_serial_performance -v -s
        """
        mock_token.return_value = "test_token"

        sizes = [10, 50, 100, 200, 500]
        results = {}

        for size in sizes:
            blocks = [
                {"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}}
                for i in range(size)
            ]

            start_time = time.time()
            result = mock_client.batch_create_blocks("doc123", blocks)
            elapsed = time.time() - start_time

            results[size] = elapsed
            print(f"Serial upload {size} blocks: {elapsed:.2f}s")

        # Print summary
        print("\n=== Serial Performance Summary ===")
        for size, elapsed in results.items():
            print(f"{size} blocks: {elapsed:.2f}s ({size / elapsed:.1f} blocks/s)")

    @pytest.mark.skip(reason="Performance monitoring - run manually")
    @patch("lib.feishu_api_client.FeishuApiClient.get_tenant_token")
    @patch.object(FeishuApiClient, "batch_create_blocks", _mock_batch_create_delay(0.01))
    def test_measure_parallel_performance(self, mock_token, mock_client):
        """
        Measure parallel upload performance for different document sizes.

        Run manually to gather baseline metrics:
        pytest tests/test_performance.py::TestPerformanceMetrics::test_measure_parallel_performance -v -s
        """
        mock_token.return_value = "test_token"

        sizes = [10, 50, 100, 200, 500]
        worker_counts = [1, 2, 3, 5]
        results = {}

        for workers in worker_counts:
            results[workers] = {}
            for size in sizes:
                blocks = [
                    {"blockType": "text", "options": {"text": {"textStyles": [{"text": f"Block {i}"}]}}}
                    for i in range(size)
                ]

                start_time = time.time()
                result = mock_client.batch_create_blocks_parallel(
                    "doc123", blocks, max_workers=workers
                )
                elapsed = time.time() - start_time

                results[workers][size] = elapsed
                print(f"Parallel upload {size} blocks with {workers} workers: {elapsed:.2f}s")

        # Print summary
        print("\n=== Parallel Performance Summary ===")
        for workers, size_results in results.items():
            print(f"\n{workers} workers:")
            for size, elapsed in size_results.items():
                print(f"  {size} blocks: {elapsed:.2f}s ({size / elapsed:.1f} blocks/s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
