# Notification System Architecture Analysis - Summary

## 📋 Complete Analysis Document

**Full Reference Guide Location:**
```
/tmp/notification_system_reference_guide.md
```

**Document Size:** 41.6 KB (5 comprehensive parts)

---

## 🎯 Quick Executive Summary

### Two Reference Projects Analyzed

#### 1. **lark-webhook-notify** (Lark/Feishu Webhook Library)
- **Purpose**: Sending rich card notifications to Feishu via webhooks
- **GitHub**: https://github.com/BobAnkh/lark-webhook-notify
- **Key Strengths**:
  - ✅ Composable building block architecture
  - ✅ Fluent CardBuilder pattern with method chaining
  - ✅ Pre-built workflow templates (start, progress, complete, failure)
  - ✅ Multi-language support (Chinese/English)
  - ✅ Clean configuration hierarchy (CLI → ENV → TOML → Defaults)
  - ✅ Minimal dependencies (colorlog, httpx, pydantic)

#### 2. **Claude-Code-Notifier** (Multi-channel Notification System)
- **Purpose**: Intelligent multi-channel notifications with rate limiting
- **GitHub**: Multiple channels (DingTalk, Feishu, Email, Telegram, etc.)
- **Key Strengths**:
  - ✅ Multi-channel architecture with BaseChannel pattern
  - ✅ Intelligent message grouping (6 strategies)
  - ✅ Multi-layer rate limiting system
  - ✅ Duplicate detection via content hashing
  - ✅ Event-type specific rules and priorities
  - ✅ Time-window based message batching

---

## 🏗️ Recommended Architecture for feishu-doc-tools

### Directory Structure
```
feishu_doc_tools/notifications/
├── blocks/              # Building block functions
├── channels/            # Multi-channel support
├── templates/           # Document-specific templates
├── utils/              # Grouping, throttling, cleanup
├── config/             # Configuration management
└── notifier.py         # Core notifier
```

### Three Core Layers

```
┌─────────────────────────────────────┐
│  Application Layer                  │
│  (feishu-doc-tools using notifier)  │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Notification Intelligence Layer    │
│  ├── Message Grouper                │
│  ├── Notification Throttle          │
│  └── Duplicate Detector             │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Channel & Template Layer           │
│  ├── BaseChannel (abstract)         │
│  ├── FeishuDocChannel (concrete)    │
│  ├── CardBuilder (fluent API)       │
│  └── Document Templates             │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Configuration & Delivery Layer     │
│  ├── Settings (Pydantic)            │
│  ├── HTTP Client (httpx)            │
│  └── Logging & Error Handling       │
└─────────────────────────────────────┘
```

---

## 📊 Pattern Adoption Summary

### Pattern 1: Building Blocks (from lark-webhook-notify)

**What**: Pure functions returning dicts for composable card elements

**Key Functions**:
- `markdown()` - Text content
- `header()` - Card title with status
- `column_set()` & `column()` - Layout elements
- `collapsible_panel()` - Expandable sections
- `card()` - Final card assembly

**Why**: Creates flexible, composable, schema-aware card structures

**Adoption**: ✅ ADOPT - Essential for Feishu card generation

---

### Pattern 2: CardBuilder (from lark-webhook-notify)

**What**: Fluent builder pattern with method chaining

**Example**:
```python
template = (CardBuilder(language="zh")
    .header("Document Modified", status="updated", color="blue")
    .markdown("**File**: path/to/file.md")
    .columns()
    .column("Editor", "Alice", width="auto")
    .column("Time", "2025-01-20 14:30", width="weighted")
    .end_columns()
    .collapsible("Changes", "- Added section\n- Fixed typo")
    .build())
```

**Why**: Readable, maintainable, intuitive API

**Adoption**: ✅ ADOPT - Excellent for building document notifications

---

### Pattern 3: Workflow Templates (from lark-webhook-notify)

**What**: Static factory methods for domain-specific templates

**Phases**: START → PROGRESS → COMPLETE → FAILURE

**Colors**:
- Wathet (light blue): Running/In Progress
- Green: Success/Complete
- Red: Failure/Error
- Orange: Analysis/Comparison
- Purple: Other phases

**Why**: Consistent structure across related notifications

**Adoption**: ✅ ADOPT - Create DocumentTemplates with document lifecycle phases

---

### Pattern 4: BaseChannel (from Claude-Code-Notifier)

**What**: Abstract base class for implementing notification channels

**Key Methods**:
```python
@abstractmethod
send_notification(template_data, event_type) -> bool

# Convenience methods
send_permission_notification(data) -> bool
send_completion_notification(data) -> bool
send_error_notification(data) -> bool
# ... etc

# Capability queries
is_enabled() -> bool
supports_rich_content() -> bool
supports_actions() -> bool
get_max_content_length() -> int
```

**Why**: Extensible to multiple channels, clear interface

**Adoption**: ✅ ADOPT - Create FeishuDocChannel extending BaseChannel

---

### Pattern 5: Message Grouper (from Claude-Code-Notifier)

**What**: Intelligent message deduplication and merging

**Strategies**:
1. `BY_PROJECT` - Group by project
2. `BY_EVENT_TYPE` - Group by notification type
3. `BY_CONTENT` - Suppress exact duplicates
4. `BY_TIME_WINDOW` - Batch within time periods
5. `BY_SIMILARITY` - Group similar messages
6. `BY_CHANNEL` - Channel-specific grouping

**Example Rules**:
- `document_modified`: BY_TIME_WINDOW, 10 max, 5 min timeout
- `comment_added`: BY_CONTENT, 5 max, 60 sec timeout
- `error_occurred`: BY_SIMILARITY, 3 max, escalate if 3+

**Why**: Prevents notification spam while preserving important info

**Adoption**: ✅ ESSENTIAL - Critical for document operations which happen frequently

---

### Pattern 6: Notification Throttle (from Claude-Code-Notifier)

**What**: Multi-layer rate limiting system

**Layers** (in order):
1. **Duplicate Detection** - Same message within 5 min?
2. **Global Limits** - 30/min, 300/hour global?
3. **Channel Limits** - Feishu 20/min, Email 10/min?
4. **Event Limits** - Doc edits 5/min, Errors 3/min?
5. **Priority Weights** - CRITICAL: no limit, LOW: 0.3x?

**Rate Limit Config**:
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

**Why**: Prevents API overload, respects platform limits

**Adoption**: ✅ ESSENTIAL - Protect against accidental notification storms

---

### Pattern 7: Configuration Hierarchy (from lark-webhook-notify)

**What**: Multi-source config with clear precedence

**Order** (highest to lowest):
1. CLI/function parameters
2. Environment variables (FEISHU_WEBHOOK_URL, etc.)
3. TOML config file
4. Default values

**Implementation**:
```python
class NotificationSettings(BaseSettings):
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_prefix="FEISHU_",
        toml_file="feishu_notify.toml",
    )
    
    @classmethod
    def settings_customise_sources(cls, ...):
        return (init_settings, env_settings, TomlConfigSettingsSource(cls))
```

**Why**: Flexible, secure (secrets in ENV), documented (TOML)

**Adoption**: ✅ ADOPT - Use Pydantic v2 BaseSettings

---

## 🔌 Recommended Dependencies

```toml
[project]
dependencies = [
    # Core
    "pydantic>=2.11.7",
    "pydantic-settings>=2.10.1",
    
    # HTTP
    "httpx>=0.28.1",
    
    # Logging
    "colorlog>=6.10.1",
    
    # Optional (for advanced features)
    "python-dotenv>=0.10.0",  # .env file support
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

## 📈 Event Types for feishu-doc-tools

### Document Lifecycle
- `document_created` - New document
- `document_modified` - Content changed
- `document_deleted` - Document removed
- `document_shared` - Access granted
- `document_permission_changed` - Permissions updated
- `document_moved` - Location changed
- `document_exported` - Downloaded

### Collaboration
- `comment_added` - New comment
- `comment_resolved` - Discussion closed
- `mention_received` - @mentioned
- `viewer_added` - Someone can view
- `collaborator_removed` - Access revoked

### System
- `quota_exceeded` - Storage full
- `sync_failed` - Sync error
- `rate_limit_hit` - Too many requests
- `operation_completed` - Batch operation done
- `error_occurred` - System error

---

## 📋 Grouping Rules Recommendations

```python
GROUPING_RULES = {
    # Batch edits into single notification every 5 minutes
    'document_modified': {
        'strategy': 'BY_TIME_WINDOW',
        'max_size': 10,
        'timeout': 300,
        'summary_template': 'batch_edits'
    },
    
    # Deduplicate same comments
    'comment_added': {
        'strategy': 'BY_CONTENT',
        'max_size': 5,
        'timeout': 60,
        'suppress_duplicates': True
    },
    
    # Group similar errors
    'error_occurred': {
        'strategy': 'BY_SIMILARITY',
        'max_size': 3,
        'timeout': 600,
        'escalate_threshold': 2
    },
    
    # Batch viewers over 30 minutes
    'viewer_added': {
        'strategy': 'BY_TIME_WINDOW',
        'max_size': 20,
        'timeout': 1800,
        'summary_only': True
    }
}
```

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create blocks.py with Feishu block types
- [ ] Implement CardBuilder
- [ ] Set up Pydantic configuration
- [ ] Create BaseChannel abstract class

### Phase 2: Core (Week 2)
- [ ] Implement FeishuDocChannel
- [ ] Create document template factories
- [ ] Integrate message grouper
- [ ] Add notification throttle

### Phase 3: Integration (Week 3)
- [ ] Connect to feishu-doc-tools main flow
- [ ] Add CLI commands
- [ ] Comprehensive testing
- [ ] Documentation

### Phase 4: Enhancement (Week 4+)
- [ ] Multiple channel support
- [ ] Analytics dashboard
- [ ] User preferences
- [ ] Scheduled notifications

---

## ✅ Implementation Checklist

### Before Starting
- [ ] Review complete reference guide
- [ ] Study lark-webhook-notify/src structure
- [ ] Study Claude-Code-Notifier/src/claude_notifier structure
- [ ] Understand Feishu webhook format

### Phase 1: Building Blocks
- [ ] Copy blocks.py pattern
- [ ] Adapt to Feishu document block types
- [ ] Create unit tests
- [ ] Document block functions

### Phase 2: Templates
- [ ] Implement CardBuilder
- [ ] Create DocumentTemplates factory
- [ ] Add language support (zh/en)
- [ ] Build example templates

### Phase 3: Channels
- [ ] Create BaseChannel
- [ ] Implement FeishuDocChannel
- [ ] Add config validation
- [ ] Test with real Feishu API

### Phase 4: Intelligence
- [ ] Integrate MessageGrouper
- [ ] Integrate NotificationThrottle
- [ ] Add duplicate detection
- [ ] Test grouping and throttling

### Phase 5: Configuration
- [ ] Setup Pydantic settings
- [ ] Support TOML config
- [ ] Environment variable support
- [ ] CLI parameter support

### Phase 6: Integration
- [ ] Wire up to feishu-doc-tools
- [ ] Add error handling
- [ ] Setup logging
- [ ] End-to-end testing

---

## 🎓 Learning Resources

### Key Files to Study

**lark-webhook-notify** (in order of importance):
1. `/blocks.py` - Building block patterns
2. `/templates.py` - CardBuilder and translation system
3. `/workflow_templates.py` - Domain-specific templates
4. `/config.py` - Configuration management
5. `/client.py` - Webhook delivery

**Claude-Code-Notifier** (in order of importance):
1. `/core/channels/base.py` - BaseChannel pattern
2. `/utils/message_grouper.py` - Grouping strategies
3. `/utils/notification_throttle.py` - Rate limiting layers
4. `/core/notifier.py` - Core notifier orchestration
5. `/core/config.py` - Configuration management

---

## 📌 Key Takeaways

✅ **Do Adopt**:
1. Building blocks architecture (composable dicts)
2. CardBuilder fluent pattern
3. BaseChannel abstract pattern
4. Pydantic configuration hierarchy
5. Message grouping strategies
6. Multi-layer rate limiting
7. Event-type based routing

❌ **Don't Do**:
1. Don't hardcode card schemas - use blocks
2. Don't skip rate limiting - essential for APIs
3. Don't ignore message grouping - prevents spam
4. Don't mix configuration sources - use clear hierarchy
5. Don't send individual notifications for high-frequency events

🎯 **Critical Success Factors**:
1. Clear separation: blocks → templates → channels
2. Flexible configuration through Pydantic
3. Intelligent message batching
4. Multi-layer rate limiting
5. Comprehensive logging and metrics

---

## 📞 Questions to Consider

1. **Q**: Should we support multiple channels initially?
   **A**: No - start with Feishu only, design for extensibility (BaseChannel pattern)

2. **Q**: How aggressive should rate limiting be?
   **A**: Start conservative (doc edits 5/min), adjust based on usage patterns

3. **Q**: Should grouping be enabled by default?
   **A**: Yes - reduces notification fatigue significantly

4. **Q**: Do we need message templates in YAML?
   **A**: Start with Python factories, add YAML config later if needed

5. **Q**: How to handle configuration conflicts?
   **A**: Use precedence: CLI > ENV > TOML > Defaults

---

**Generated**: 2025-01-20  
**Analysis Repositories**:
- lark-webhook-notify: https://github.com/BobAnkh/lark-webhook-notify
- Claude-Code-Notifier: Internal reference project

**For Full Details**: See `/tmp/notification_system_reference_guide.md`
