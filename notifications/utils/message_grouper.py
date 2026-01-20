#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Message Grouper - 消息分组合并系统
智能合并相似通知，减少通知轰炸
"""

import time
import hashlib
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class GroupingStrategy(Enum):
    """分组策略枚举"""
    BY_PROJECT = "by_project"
    BY_EVENT_TYPE = "by_event_type"
    BY_CHANNEL = "by_channel"
    BY_CONTENT = "by_content"
    BY_TIME_WINDOW = "by_time_window"
    BY_SIMILARITY = "by_similarity"


class MergeAction(Enum):
    """合并动作枚举"""
    MERGE = "merge"          # 合并消息
    GROUP = "group"          # 加入分组
    SUPPRESS = "suppress"    # 抑制消息
    ESCALATE = "escalate"    # 升级发送


@dataclass
class MessageGroup:
    """消息组数据结构

    Attributes:
        group_id: 分组唯一标识
        strategy: 分组策略
        messages: 消息列表
        created_at: 创建时间（Unix时间戳）
        last_updated: 最后更新时间
        channel: 通道名称
        event_type: 事件类型
        project: 项目名称
        merge_count: 合并计数
        priority: 优先级（1-4）
    """
    group_id: str
    strategy: GroupingStrategy
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    channel: str = ""
    event_type: str = ""
    project: str = ""
    merge_count: int = 0
    priority: int = 1

    def add_message(self, message: Dict[str, Any]) -> None:
        """添加消息到组

        Args:
            message: 消息数据
        """
        self.messages.append(message)
        self.last_updated = time.time()
        self.merge_count += 1

        # 更新优先级（取最高优先级）
        msg_priority = message.get('priority', 1)
        if isinstance(msg_priority, str):
            # 转换字符串优先级到数字
            priority_map = {'low': 1, 'normal': 2, 'high': 3, 'critical': 4}
            msg_priority = priority_map.get(msg_priority.lower(), 2)

        self.priority = max(self.priority, msg_priority)

    def get_age(self) -> float:
        """获取组年龄（秒）

        Returns:
            分组创建至今的秒数
        """
        return time.time() - self.created_at

    def get_idle_time(self) -> float:
        """获取闲置时间（秒）

        Returns:
            最后更新至今的秒数
        """
        return time.time() - self.last_updated


class MessageGrouper:
    """消息分组合并器

    核心功能：
    1. 时间窗口分组 - 在指定时间窗口内合并消息
    2. 内容相似度分组 - 合并内容相似的消息
    3. 批量发送逻辑 - 达到阈值时批量发送
    4. 智能清理 - 定期清理过期分组

    Example:
        >>> config = {
        ...     'group_window': 300,
        ...     'max_group_size': 10,
        ...     'similarity_threshold': 0.8
        ... }
        >>> grouper = MessageGrouper(config)
        >>>
        >>> # 检查消息是否应该分组
        >>> should_group, group_id, action = grouper.should_group_message(message)
        >>> if should_group:
        ...     grouper.add_message_to_group(group_id, message)
        >>>
        >>> # 获取准备发送的分组
        >>> ready_groups = grouper.get_ready_groups()
        >>> for group in ready_groups:
        ...     merged_msg = grouper.merge_group_messages(group)
        ...     # 发送合并后的消息
    """

    def __init__(
        self,
        group_window: int = 300,
        max_group_size: int = 10,
        max_groups: int = 50,
        send_threshold: int = 5,
        send_timeout: int = 60,
        similarity_threshold: float = 0.8
    ):
        """初始化消息分组器

        Args:
            group_window: 分组时间窗口（秒），默认300秒（5分钟）
            max_group_size: 最大分组大小，默认10条消息
            max_groups: 最大同时活跃分组数，默认50
            send_threshold: 发送阈值（消息数），默认5条
            send_timeout: 发送超时（秒），默认60秒
            similarity_threshold: 相似度阈值，默认0.8
        """
        self.group_window = group_window
        self.max_group_size = max_group_size
        self.max_groups = max_groups
        self.send_threshold = send_threshold
        self.send_timeout = send_timeout
        self.similarity_threshold = similarity_threshold

        # 活跃的消息组
        self.active_groups: Dict[str, MessageGroup] = {}

        # 统计信息
        self.stats = {
            'groups_created': 0,
            'messages_grouped': 0,
            'messages_merged': 0,
            'groups_sent': 0
        }

        # 清理定时器
        self._last_cleanup = time.time()

    def should_group_message(
        self,
        message: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], MergeAction]:
        """检查消息是否应该分组

        Args:
            message: 消息数据，需包含以下字段：
                - event_type: 事件类型
                - channel: 通道名称
                - project: 项目名称（可选）
                - priority: 优先级（可选）
                - content: 内容（可选）

        Returns:
            (是否分组, 分组ID, 合并动作) 的元组

        Example:
            >>> message = {
            ...     'event_type': 'task_completion',
            ...     'channel': 'webhook',
            ...     'project': 'my-project'
            ... }
            >>> should_group, group_id, action = grouper.should_group_message(message)
            >>> print(f"Should group: {should_group}, Action: {action}")
        """
        # 定期清理过期组
        self._periodic_cleanup()

        event_type = message.get('event_type', 'unknown')
        channel = message.get('channel', 'unknown')
        project = message.get('project', 'unknown')

        # 1. 查找现有组
        existing_group_id = self._find_matching_group(message)
        if existing_group_id:
            group = self.active_groups[existing_group_id]

            # 检查组是否已满
            if len(group.messages) >= self.max_group_size:
                # 立即发送当前组，创建新组
                return False, existing_group_id, MergeAction.ESCALATE

            # 检查组是否超时
            if group.get_age() > self.send_timeout:
                return False, existing_group_id, MergeAction.ESCALATE

            return True, existing_group_id, MergeAction.GROUP

        # 2. 检查是否应该创建新组
        if self._should_create_group(message):
            group_id = self._create_group(message)
            return True, group_id, MergeAction.GROUP

        # 3. 不分组，直接发送
        return False, None, MergeAction.MERGE

    def add_message_to_group(self, group_id: str, message: Dict[str, Any]) -> bool:
        """将消息添加到分组

        Args:
            group_id: 分组ID
            message: 消息数据

        Returns:
            是否成功添加

        Example:
            >>> success = grouper.add_message_to_group("group_123", message)
            >>> if success:
            ...     print("Message added to group")
        """
        if group_id not in self.active_groups:
            return False

        group = self.active_groups[group_id]
        group.add_message(message)

        self.stats['messages_grouped'] += 1

        return True

    def get_ready_groups(self) -> List[MessageGroup]:
        """获取准备发送的分组

        Returns:
            准备发送的分组列表

        Example:
            >>> ready_groups = grouper.get_ready_groups()
            >>> for group in ready_groups:
            ...     print(f"Group {group.group_id}: {len(group.messages)} messages")
        """
        ready_groups = []
        groups_to_remove = []

        for group_id, group in self.active_groups.items():
            if self._should_send_group(group):
                ready_groups.append(group)
                groups_to_remove.append(group_id)

        # 移除已发送的分组
        for group_id in groups_to_remove:
            if group_id in self.active_groups:
                del self.active_groups[group_id]
                self.stats['groups_sent'] += 1

        return ready_groups

    def merge_group_messages(self, group: MessageGroup) -> Dict[str, Any]:
        """合并分组中的消息

        Args:
            group: 消息分组

        Returns:
            合并后的消息数据

        Example:
            >>> merged_msg = grouper.merge_group_messages(group)
            >>> print(merged_msg['title'])
            '📋 5 条消息已合并'
        """
        if not group.messages:
            return {}

        event_type = group.event_type

        # 基础合并信息
        merged_message = {
            'event_type': f"{event_type}_group",
            'event_id': f"group_{group.group_id}",
            'channel': group.channel,
            'project': group.project,
            'priority': group.priority,
            'group_info': {
                'message_count': len(group.messages),
                'time_span': group.get_age(),
                'strategy': group.strategy.value,
                'group_id': group.group_id
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 根据事件类型定制合并逻辑
        if event_type == 'task_completion':
            merged_message.update(self._merge_task_completions(group))
        elif event_type == 'error_occurred':
            merged_message.update(self._merge_errors(group))
        else:
            merged_message.update(self._merge_generic(group))

        self.stats['messages_merged'] += len(group.messages)

        return merged_message

    def get_grouper_stats(self) -> Dict[str, Any]:
        """获取分组器统计信息

        Returns:
            统计信息字典

        Example:
            >>> stats = grouper.get_grouper_stats()
            >>> print(f"Active groups: {stats['active_groups']}")
            >>> print(f"Total grouped: {stats['stats']['messages_grouped']}")
        """
        return {
            'stats': self.stats.copy(),
            'active_groups': len(self.active_groups),
            'group_details': [
                {
                    'group_id': group.group_id,
                    'event_type': group.event_type,
                    'message_count': len(group.messages),
                    'age': group.get_age(),
                    'idle_time': group.get_idle_time(),
                    'strategy': group.strategy.value,
                    'priority': group.priority
                }
                for group in self.active_groups.values()
            ]
        }

    # ==================== 私有方法 ====================

    def _find_matching_group(self, message: Dict[str, Any]) -> Optional[str]:
        """查找匹配的现有分组"""
        event_type = message.get('event_type', '')

        for group_id, group in self.active_groups.items():
            if self._messages_match(message, group):
                return group_id

        return None

    def _messages_match(self, message: Dict[str, Any], group: MessageGroup) -> bool:
        """检查消息是否匹配分组"""
        # 基本匹配：事件类型和通道相同
        if (message.get('event_type') != group.event_type or
            message.get('channel') != group.channel):
            return False

        # 时间窗口检查
        if group.get_age() >= self.group_window:
            return False

        # 项目匹配（如果指定）
        if message.get('project') and group.project:
            if message.get('project') != group.project:
                return False

        # 内容相似度检查
        if group.messages and group.strategy == GroupingStrategy.BY_SIMILARITY:
            recent_messages = group.messages[-3:]  # 检查最近3条
            return any(self._content_similar(message, msg) for msg in recent_messages)

        return True

    def _content_similar(self, msg1: Dict[str, Any], msg2: Dict[str, Any]) -> bool:
        """检查两条消息内容是否相似

        使用 Jaccard 相似度计算
        """
        def get_content_tokens(msg: Dict[str, Any]) -> set:
            """提取消息的内容token"""
            content_parts = [
                str(msg.get('event_type', '')),
                str(msg.get('project', '')),
                str(msg.get('operation', '')),
                str(msg.get('status', '')),
                str(msg.get('title', '')),
                str(msg.get('content', ''))
            ]
            content = ' '.join(filter(None, content_parts))
            return set(content.lower().split())

        tokens1 = get_content_tokens(msg1)
        tokens2 = get_content_tokens(msg2)

        if not tokens1 or not tokens2:
            return False

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity >= self.similarity_threshold

    def _should_create_group(self, message: Dict[str, Any]) -> bool:
        """检查是否应该创建新分组"""
        # 检查是否达到最大分组数
        if len(self.active_groups) >= self.max_groups:
            # 清理过期分组
            self._cleanup_expired_groups()

            if len(self.active_groups) >= self.max_groups:
                return False

        return True

    def _create_group(self, message: Dict[str, Any]) -> str:
        """创建新的消息分组"""
        event_type = message.get('event_type', 'unknown')
        channel = message.get('channel', 'unknown')
        project = message.get('project', 'unknown')

        # 生成分组ID
        timestamp = int(time.time())
        content_hash = hashlib.md5(
            f"{event_type}:{channel}:{project}".encode()
        ).hexdigest()[:8]
        group_id = f"{event_type}_{content_hash}_{timestamp}"

        # 确定分组策略
        strategy = GroupingStrategy.BY_TIME_WINDOW

        # 创建分组
        group = MessageGroup(
            group_id=group_id,
            strategy=strategy,
            channel=channel,
            event_type=event_type,
            project=project
        )

        self.active_groups[group_id] = group
        self.stats['groups_created'] += 1

        return group_id

    def _should_send_group(self, group: MessageGroup) -> bool:
        """检查分组是否应该发送"""
        # 检查消息数量阈值
        if len(group.messages) >= self.send_threshold:
            return True

        # 检查超时
        if group.get_age() >= self.send_timeout:
            return True

        # 检查优先级升级（HIGH及以上优先级）
        if group.priority >= 3 and len(group.messages) >= 2:
            return True

        return False

    def _merge_task_completions(self, group: MessageGroup) -> Dict[str, Any]:
        """合并任务完成消息"""
        projects = list(set(
            msg.get('project', '') for msg in group.messages if msg.get('project')
        ))
        tasks = [
            msg.get('task', msg.get('operation', ''))
            for msg in group.messages
        ]

        return {
            'title': f'✅ {len(tasks)} 个任务已完成',
            'content': f'项目 {", ".join(projects)} 的多个任务已完成',
            'completed_tasks': len(tasks),
            'tasks': tasks[:5],  # 最多显示5个
            'projects': projects,
            'status': 'success'
        }

    def _merge_errors(self, group: MessageGroup) -> Dict[str, Any]:
        """合并错误消息"""
        error_types = list(set(
            msg.get('error_type', '') for msg in group.messages if msg.get('error_type')
        ))
        error_messages = [
            msg.get('error_message', msg.get('content', ''))
            for msg in group.messages
        ]

        return {
            'title': f'❌ 发现 {len(error_messages)} 个错误',
            'content': f'错误类型: {", ".join(error_types)}' if error_types else '发现多个错误',
            'error_count': len(error_messages),
            'error_types': error_types,
            'recent_errors': error_messages[-3:],  # 最近3个错误
            'status': 'error'
        }

    def _merge_generic(self, group: MessageGroup) -> Dict[str, Any]:
        """通用消息合并"""
        return {
            'title': f'📋 {group.event_type} 事件汇总',
            'content': f'收到 {len(group.messages)} 条 {group.event_type} 事件',
            'message_count': len(group.messages),
            'event_type': group.event_type,
            'first_message': group.messages[0] if group.messages else {},
            'last_message': group.messages[-1] if group.messages else {},
            'status': 'info'
        }

    def _periodic_cleanup(self) -> None:
        """定期清理"""
        current_time = time.time()

        # 每5分钟清理一次
        if current_time - self._last_cleanup > 300:
            self._cleanup_expired_groups()
            self._last_cleanup = current_time

    def _cleanup_expired_groups(self) -> None:
        """清理过期的分组"""
        expired_groups = []

        # 超时时间的3倍作为过期阈值
        max_age = self.send_timeout * 3

        for group_id, group in self.active_groups.items():
            if group.get_age() > max_age:
                expired_groups.append(group_id)

        for group_id in expired_groups:
            if group_id in self.active_groups:
                del self.active_groups[group_id]
