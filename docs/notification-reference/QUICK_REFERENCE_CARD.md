# Notification System Implementation - Quick Reference Card

## 📍 Document Locations

```
Full Reference Guide:  /tmp/notification_system_reference_guide.md  (41.6 KB)
Executive Summary:     /tmp/ANALYSIS_SUMMARY.md                     (15 KB)
Quick Reference:       /tmp/QUICK_REFERENCE_CARD.md                 (This file)

Source Code Locations:
  lark-webhook-notify:  /home/howie/Software/utility/Reference/lark-webhook-notify
  Claude-Code-Notifier: /home/howie/Software/utility/Reference/Claude-Code-Notifier
```

---

## 🎯 7 Core Patterns to Adopt

### 1️⃣ Building Blocks (blocks.py)
```python
# Pure functions returning dicts
Block = Dict[str, Any]

def markdown(content: str, **opts) -> Block
def header(*, title: str, status: str, color: str) -> Block
def column_set(columns: Iterable[Block], **opts) -> Block
def collapsible_panel(title: str, elements: Iterable[Block], **opts) -> Block
def card(*, elements: Iterable[Block], header: Block) -> Block
```

**File**: `notifications/blocks/blocks.py`
**Adoption**: ✅ ESSENTIAL

---

### 2️⃣ CardBuilder (templates.py)
```python
# Fluent builder pattern
class CardBuilder:
    def header(self, title, *, status, color) -> 'CardBuilder'
    def markdown(self, content, **opts) -> 'CardBuilder'
    def columns(self) -> ColumnBuilder
    def collapsible(self, title, content, **opts) -> 'CardBuilder'
    def build(self) -> GenericCardTemplate
```

**Example**:
```python
template = (CardBuilder(language="zh")
    .header("Document Modified", status="updated", color="blue")
    .markdown("**File**: path/to/file.md")
    .columns()
    .column("Editor", "Alice", width="auto")
    .end_columns()
    .collapsible("Changes", "- Added section")
    .build())
```

**File**: `notifications/templates/builder.py`
**Adoption**: ✅ ESSENTIAL

---

### 3️⃣ Workflow Templates (workflow_templates.py)
```python
# Domain-specific template factories
class DocumentTemplates:
    @staticmethod
    def document_created(doc_name, creator, ...) -> Template
    
    @staticmethod
    def document_modified(doc_name, modifier, changes) -> Template
    
    @staticmethod
    def sync_failed(doc_name, error_message) -> Template
```

**Phases**: START → PROGRESS → COMPLETE → FAILURE
**Colors**: Wathet (running), Green (success), Red (failure)

**File**: `notifications/templates/document_templates.py`
**Adoption**: ✅ ESSENTIAL

---

### 4️⃣ BaseChannel (channels/base.py)
```python
# Abstract notification channel
class BaseChannel(abc.ABC):
    @abstractmethod
    def send_notification(self, template_data: Dict, event_type: str) -> bool
    
    def send_permission_notification(self, data) -> bool
    def send_completion_notification(self, data) -> bool
    def send_error_notification(self, data) -> bool
    
    def is_enabled(self) -> bool
    def supports_rich_content(self) -> bool
    def get_max_content_length(self) -> int
```

**File**: `notifications/channels/base.py`
**Adoption**: ✅ ESSENTIAL

---

### 5️⃣ Message Grouper (utils/message_grouper.py)
```python
# Intelligent message deduplication
class MessageGrouper:
    def should_group_message(self, message) -> Tuple[bool, Optional[str], MergeAction]

# 6 strategies:
# BY_PROJECT, BY_EVENT_TYPE, BY_CONTENT, BY_TIME_WINDOW, BY_SIMILARITY, BY_CHANNEL
```

**Rules Example**:
```python
'document_modified': {
    'strategy': 'BY_TIME_WINDOW',
    'max_size': 10,
    'timeout': 300,  # 5 minutes
    'summary_template': 'batch_edits'
}
```

**File**: `notifications/utils/message_grouper.py`
**Adoption**: ✅ ESSENTIAL

---

### 6️⃣ Notification Throttle (utils/notification_throttle.py)
```python
# Multi-layer rate limiting
class NotificationThrottle:
    def should_allow_notification(self, request) -> Tuple[ThrottleAction, str, Optional[float]]

# 5 layers (in order):
# 1. Duplicate Detection    (5 min window)
# 2. Global Limits          (30/min, 300/hour)
# 3. Channel Limits         (Feishu: 20/min)
# 4. Event Limits           (Doc edits: 5/min)
# 5. Priority Weights       (CRITICAL: 1.0x, LOW: 0.3x)
```

**File**: `notifications/utils/notification_throttle.py`
**Adoption**: ✅ ESSENTIAL

---

### 7️⃣ Configuration (config/settings.py)
```python
# Pydantic-based hierarchical configuration
class NotificationSettings(BaseSettings):
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_prefix="FEISHU_",
        toml_file="feishu_notify.toml",
    )

# Precedence: CLI > ENV > TOML > Defaults
```

**File**: `notifications/config/settings.py`
**Adoption**: ✅ ESSENTIAL

---

## 🏗️ Recommended Directory Structure

```
feishu_doc_tools/
└── notifications/
    ├── blocks/
    │   ├── __init__.py
    │   └── blocks.py              # Building block functions
    │
    ├── channels/
    │   ├── __init__.py
    │   ├── base.py                # BaseChannel abstract
    │   ├── feishu.py              # FeishuDocChannel impl
    │   └── registry.py            # Channel registry
    │
    ├── templates/
    │   ├── __init__.py
    │   ├── builder.py             # CardBuilder
    │   ├── document_templates.py  # DocumentTemplates factory
    │   └── messages.py            # Translations & types
    │
    ├── utils/
    │   ├── __init__.py
    │   ├── message_grouper.py     # MessageGrouper
    │   ├── notification_throttle.py  # NotificationThrottle
    │   ├── cooldown_manager.py
    │   └── time_utils.py
    │
    ├── config/
    │   ├── __init__.py
    │   └── settings.py            # Pydantic settings
    │
    ├── notifier.py                # Core Notifier orchestrator
    └── __init__.py
```

---

## 📋 Event Types for feishu-doc-tools

```
Document Lifecycle:
  • document_created
  • document_modified
  • document_deleted
  • document_shared
  • document_permission_changed

Collaboration:
  • comment_added
  • comment_resolved
  • mention_received
  • viewer_added
  • collaborator_removed

System:
  • quota_exceeded
  • sync_failed
  • rate_limit_hit
  • operation_completed
  • error_occurred
```

---

## ⚙️ Rate Limiting Configuration

```python
rate_limits = {
    'global': {
        'max_per_minute': 30,
        'max_per_hour': 300,
        'burst_limit': 10,
        'burst_window': 10
    },
    'by_channel': {
        'feishu': {'max_per_minute': 20, 'max_per_hour': 200}
    },
    'by_event': {
        'document_modified': {'max_per_minute': 5, 'cooldown': 60},
        'comment_added': {'max_per_minute': 10, 'cooldown': 30},
        'error_occurred': {'max_per_minute': 3, 'cooldown': 120}
    },
    'priority_weights': {
        'CRITICAL': 1.0,    # No limit
        'HIGH': 0.8,        # Mild throttle
        'NORMAL': 0.6,      # Normal throttle
        'LOW': 0.3          # Strict throttle
    }
}
```

---

## 🎨 Color Coding Guide

| Color | Status | Use Case |
|-------|--------|----------|
| Wathet | Running | Start, In Progress |
| Green | Success | Complete, Done |
| Red | Failure | Error, Failed |
| Orange | Analysis | Comparison, Summary |
| Purple | Other | Special phases |
| Blue | Info | General info |

---

## 📦 Dependencies to Add

```toml
[project]
dependencies = [
    "pydantic>=2.11.7",           # Config validation
    "pydantic-settings>=2.10.1",  # Config management
    "httpx>=0.28.1",              # HTTP client
    "colorlog>=6.10.1",           # Colored logging
]

[project.optional-dependencies]
dev = [
    "pytest>=8.4.2",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
```

---

## ✅ Implementation Phases (4 Weeks)

### Week 1: Foundation
- [ ] blocks.py with Feishu block types
- [ ] CardBuilder implementation
- [ ] Pydantic configuration
- [ ] BaseChannel abstract class

### Week 2: Core Features
- [ ] FeishuDocChannel implementation
- [ ] DocumentTemplates factory
- [ ] MessageGrouper integration
- [ ] NotificationThrottle integration

### Week 3: Integration
- [ ] Wire into feishu-doc-tools main flow
- [ ] CLI commands
- [ ] Comprehensive tests
- [ ] Documentation

### Week 4+: Enhancement
- [ ] Multiple channel support
- [ ] Analytics dashboard
- [ ] User preferences
- [ ] Scheduled notifications

---

## 🔍 Key Files to Study (In Order)

**From lark-webhook-notify**:
1. `blocks.py` - Building block patterns (500 lines)
2. `templates.py` - CardBuilder & translations (600 lines)
3. `workflow_templates.py` - Template factories (700 lines)
4. `config.py` - Configuration hierarchy (160 lines)
5. `client.py` - Webhook client (250 lines)

**From Claude-Code-Notifier**:
1. `core/channels/base.py` - BaseChannel (150 lines)
2. `utils/message_grouper.py` - Grouping logic (400 lines)
3. `utils/notification_throttle.py` - Rate limiting (500 lines)
4. `core/notifier.py` - Core orchestrator (200 lines)
5. `core/config.py` - Configuration (200 lines)

---

## 🚀 Quick Start Template

```python
# notifications/notifier.py
from notifications.channels.base import BaseChannel
from notifications.utils.message_grouper import MessageGrouper
from notifications.utils.notification_throttle import NotificationThrottle
from notifications.config.settings import NotificationSettings

class Notifier:
    def __init__(self, config_path: Optional[str] = None):
        self.settings = NotificationSettings(_env_file=config_path)
        self.grouper = MessageGrouper(self.settings.model_dump())
        self.throttle = NotificationThrottle(self.settings.model_dump())
        self.channels: Dict[str, BaseChannel] = {}
        self._init_channels()
    
    def _init_channels(self):
        """Initialize enabled channels"""
        if self.settings.feishu.enabled:
            from notifications.channels.feishu import FeishuDocChannel
            self.channels['feishu'] = FeishuDocChannel(self.settings.feishu)
    
    def send(self, template, event_type: str, 
             channels: Optional[List[str]] = None) -> bool:
        """Send notification with grouping & throttling"""
        # 1. Check throttle
        action, reason, delay = self.throttle.should_allow_notification(...)
        if action != ThrottleAction.ALLOW:
            return False
        
        # 2. Check grouping
        should_group, group_id, merge_action = self.grouper.should_group_message(...)
        
        # 3. Send to channels
        for ch_name in (channels or self._get_default_channels(event_type)):
            if ch_name in self.channels:
                self.channels[ch_name].send_notification(template, event_type)
        
        return True
```

---

## 💡 Pro Tips

1. **Start Simple**: Begin with Feishu-only, add channels later
2. **Rate Limits**: Conservative defaults (5/min for edits), adjust after data
3. **Grouping**: Always enabled by default (reduces spam)
4. **Config**: Use TOML for users, ENV for CI/CD, CLI for testing
5. **Logging**: Log all decisions (allowed, blocked, grouped, merged)
6. **Testing**: Mock Feishu API, test throttle/grouper independently
7. **Monitoring**: Track stats (sent, blocked, grouped, merged, errors)

---

## ❌ Common Pitfalls to Avoid

1. ❌ Hardcoding card schemas → Use blocks functions
2. ❌ Skipping rate limiting → API will throttle you
3. ❌ Ignoring message grouping → Users will be spammed
4. ❌ Mixing config sources → Use clear hierarchy
5. ❌ Individual notifications for frequent events → Batch them
6. ❌ No duplicate detection → Same error multiple times
7. ❌ Ignoring priority levels → Can't escalate critical alerts

---

## 📞 Decision Matrix

| Question | Answer | Why |
|----------|--------|-----|
| Multiple channels at launch? | No, Feishu only | Design for extension (BaseChannel) |
| Rate limit aggressiveness? | Conservative (5/min edits) | Adjust based on usage data |
| Grouping enabled by default? | Yes | Reduces notification fatigue |
| YAML templates vs Python? | Python factories | More flexible, type-safe |
| Persistent message history? | Yes, SQLite | For analytics & debugging |
| User preferences UI? | Phase 2 | MVP just has sensible defaults |
| Scheduled notifications? | Phase 2 | MVP focuses on event-driven |

---

## 📊 Success Metrics

Track these statistics:
- Notifications sent (by event, channel, hour)
- Notifications blocked (by reason)
- Messages grouped (count, savings)
- Duplicate detections
- Rate limit hits
- Failed deliveries (by channel, reason)
- Average group wait time
- User satisfaction (future)

---

**Analysis Date**: 2025-01-20  
**Status**: ✅ Complete Reference Guide Available  
**Next Step**: Review full reference guide and start Phase 1 implementation

---

**For comprehensive details, see:**
- Full Guide: `/tmp/notification_system_reference_guide.md`
- Summary: `/tmp/ANALYSIS_SUMMARY.md`
