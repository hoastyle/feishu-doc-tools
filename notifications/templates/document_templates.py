"""Document-specific template factories for feishu-doc-tools.

This module provides pre-configured template factories for document operations,
making it easy to create consistent notifications for document lifecycle events.
Each factory function returns a CardTemplate ready to be sent.
"""

from typing import Optional, Dict, Any
from .builder import CardBuilder, CardTemplate


class DocumentTemplates:
    """Factory class for creating document-specific notification templates.

    This class provides static methods for creating templates for common document
    operations like creation, modification, deletion, and synchronization.

    Color scheme:
        - Wathet (light blue): Running/in-progress operations
        - Green: Successful operations
        - Red: Failed operations
        - Orange: Analysis/comparison operations
    """

    @staticmethod
    def document_created(
        doc_name: str,
        creator: str,
        doc_url: Optional[str] = None,
        doc_type: Optional[str] = None,
        folder: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CardTemplate:
        """Create template for document creation notification.

        Uses green color for successful creation.

        Args:
            doc_name: Name of the created document
            creator: Username of the creator
            doc_url: URL to the document (optional)
            doc_type: Type of document (e.g., "Markdown", "Wiki") (optional)
            folder: Folder path where document was created (optional)
            metadata: Additional metadata to display (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.document_created(
            ...     doc_name="API Documentation",
            ...     creator="Alice",
            ...     doc_url="https://feishu.cn/docs/xxx",
            ...     doc_type="Wiki"
            ... )
        """
        builder = CardBuilder().header(
            "文档已创建", status="success", color="green"
        )

        # Main info
        info_lines = [f"**文档名称**: {doc_name}", f"**创建者**: {creator}"]

        if doc_type:
            info_lines.append(f"**文档类型**: {doc_type}")

        builder.markdown("\n".join(info_lines))

        # Location info in columns
        if folder or doc_url:
            cols = builder.columns()
            if folder:
                cols.column("存储位置", folder, width="weighted")
            if doc_url:
                cols.column("文档链接", f"[查看文档]({doc_url})", width="weighted")
            cols.end_columns()

        # Optional metadata
        if metadata:
            import json

            metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)
            builder.collapsible("详细信息", f"```json\n{metadata_str}\n```")

        return builder.build()

    @staticmethod
    def document_modified(
        doc_name: str,
        modifier: str,
        changes: Optional[str] = None,
        doc_url: Optional[str] = None,
        change_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CardTemplate:
        """Create template for document modification notification.

        Uses wathet (blue) color for modification events.

        Args:
            doc_name: Name of the modified document
            modifier: Username of the modifier
            changes: Description of changes made (optional)
            doc_url: URL to the document (optional)
            change_count: Number of changes (optional)
            metadata: Additional metadata to display (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.document_modified(
            ...     doc_name="API Documentation",
            ...     modifier="Bob",
            ...     changes="Added new endpoints section",
            ...     change_count=5
            ... )
        """
        builder = CardBuilder().header(
            "文档已更新", status="updated", color="blue"
        )

        # Main info
        info_lines = [f"**文档名称**: {doc_name}", f"**修改者**: {modifier}"]

        if change_count is not None:
            info_lines.append(f"**变更数量**: {change_count}")

        builder.markdown("\n".join(info_lines))

        # Changes details
        if changes:
            builder.divider()
            builder.note(f"变更说明: {changes}")

        # Document link
        if doc_url:
            builder.divider()
            builder.markdown(f"[查看文档]({doc_url})")

        # Optional metadata
        if metadata:
            import json

            metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)
            builder.collapsible("详细信息", f"```json\n{metadata_str}\n```")

        return builder.build()

    @staticmethod
    def document_deleted(
        doc_name: str,
        deleter: str,
        doc_type: Optional[str] = None,
        folder: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> CardTemplate:
        """Create template for document deletion notification.

        Uses orange color for deletion events (warning).

        Args:
            doc_name: Name of the deleted document
            deleter: Username of the deleter
            doc_type: Type of document (optional)
            folder: Folder path where document was located (optional)
            reason: Reason for deletion (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.document_deleted(
            ...     doc_name="Old Documentation",
            ...     deleter="Admin",
            ...     reason="Outdated content"
            ... )
        """
        builder = CardBuilder().header(
            "文档已删除", status="deleted", color="orange"
        )

        # Main info
        info_lines = [f"**文档名称**: {doc_name}", f"**删除者**: {deleter}"]

        if doc_type:
            info_lines.append(f"**文档类型**: {doc_type}")

        if folder:
            info_lines.append(f"**原位置**: {folder}")

        builder.markdown("\n".join(info_lines))

        # Deletion reason
        if reason:
            builder.divider()
            builder.note(f"删除原因: {reason}")

        return builder.build()

    @staticmethod
    def sync_started(
        source: str,
        destination: str,
        file_count: Optional[int] = None,
        sync_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CardTemplate:
        """Create template for synchronization start notification.

        Uses wathet (blue) color for running operations.

        Args:
            source: Source location
            destination: Destination location
            file_count: Number of files to sync (optional)
            sync_type: Type of sync (e.g., "full", "incremental") (optional)
            metadata: Additional metadata to display (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.sync_started(
            ...     source="local/docs",
            ...     destination="Feishu Wiki",
            ...     file_count=10,
            ...     sync_type="incremental"
            ... )
        """
        builder = CardBuilder().header(
            "同步已开始", status="running", color="wathet"
        )

        # Sync info in columns
        cols = builder.columns()
        cols.column("源位置", source, width="weighted")
        cols.column("目标位置", destination, width="weighted")
        cols.end_columns()

        # Additional info
        info_lines = []
        if file_count is not None:
            info_lines.append(f"**待同步文件**: {file_count}")
        if sync_type:
            info_lines.append(f"**同步类型**: {sync_type}")

        if info_lines:
            builder.divider()
            builder.markdown("\n".join(info_lines))

        # Optional metadata
        if metadata:
            import json

            metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)
            builder.collapsible("详细信息", f"```json\n{metadata_str}\n```")

        return builder.build()

    @staticmethod
    def sync_completed(
        source: str,
        destination: str,
        synced_count: int,
        duration: Optional[str] = None,
        failed_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CardTemplate:
        """Create template for synchronization completion notification.

        Uses green color for successful completion.

        Args:
            source: Source location
            destination: Destination location
            synced_count: Number of files successfully synced
            duration: Time taken for sync (optional)
            failed_count: Number of files that failed to sync (optional)
            metadata: Additional metadata to display (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.sync_completed(
            ...     source="local/docs",
            ...     destination="Feishu Wiki",
            ...     synced_count=9,
            ...     duration="2m 15s",
            ...     failed_count=1
            ... )
        """
        builder = CardBuilder().header(
            "同步已完成", status="success", color="green"
        )

        # Sync info in columns
        cols = builder.columns()
        cols.column("源位置", source, width="weighted")
        cols.column("目标位置", destination, width="weighted")
        cols.end_columns()

        # Results
        builder.divider()
        result_lines = [f"**成功同步**: {synced_count} 个文件"]

        if failed_count is not None and failed_count > 0:
            result_lines.append(f"**失败**: {failed_count} 个文件")

        if duration:
            result_lines.append(f"**耗时**: {duration}")

        builder.markdown("\n".join(result_lines))

        # Optional metadata
        if metadata:
            import json

            metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)
            builder.collapsible("详细信息", f"```json\n{metadata_str}\n```")

        return builder.build()

    @staticmethod
    def sync_failed(
        source: str,
        destination: str,
        error_message: str,
        synced_count: Optional[int] = None,
        total_count: Optional[int] = None,
    ) -> CardTemplate:
        """Create template for synchronization failure notification.

        Uses red color for failure.

        Args:
            source: Source location
            destination: Destination location
            error_message: Error message describing the failure
            synced_count: Number of files synced before failure (optional)
            total_count: Total number of files to sync (optional)

        Returns:
            CardTemplate ready to be sent

        Example:
            >>> template = DocumentTemplates.sync_failed(
            ...     source="local/docs",
            ...     destination="Feishu Wiki",
            ...     error_message="Network connection lost",
            ...     synced_count=5,
            ...     total_count=10
            ... )
        """
        builder = CardBuilder().header(
            "同步失败", status="failed", color="red"
        )

        # Sync info in columns
        cols = builder.columns()
        cols.column("源位置", source, width="weighted")
        cols.column("目标位置", destination, width="weighted")
        cols.end_columns()

        # Progress info if available
        if synced_count is not None or total_count is not None:
            builder.divider()
            if synced_count is not None and total_count is not None:
                builder.markdown(
                    f"**同步进度**: {synced_count}/{total_count} 个文件"
                )
            elif synced_count is not None:
                builder.markdown(f"**已同步**: {synced_count} 个文件")

        # Error details
        builder.divider()
        builder.collapsible("错误详情", error_message)

        return builder.build()
