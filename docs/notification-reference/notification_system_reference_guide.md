# Notification System Implementation Reference Guide

**Analysis Date**: 2025-01-20  
**Source Repositories**:
1. `lark-webhook-notify` - Card builder & template patterns
2. `Claude-Code-Notifier` - Multi-channel architecture & rate limiting

---

## PART 1: LARK-WEBHOOK-NOTIFY ANALYSIS

### 1.1 Directory Structure

```
lark-webhook-notify/
├── src/lark_webhook_notify/
│   ├── blocks.py              # Building block functions
│   ├── templates.py           # Template classes & CardBuilder
│   ├── workflow_templates.py  # Workflow-specific factories
│   ├── client.py              # Main webhook client
│   ├── config.py              # Configuration management
│   ├── cli.py                 # CLI interface
│   └── __init__.py
├── examples/
│   └── builder_usage.py
└── tests/
    ├── test_blocks.py
    └── test_builder.py
```

### 1.2 Key Implementation Patterns

#### A. Building Block Architecture (blocks.py)

**Pattern**: Composable building blocks returning plain dicts

```python
# TYPE DEFINITION
Block = Dict[str, Any]

# BUILDING BLOCKS
def markdown(content: str, *, text_align: str = "left", 
             text_size: str = "normal", margin: str = "0px 0px 0px 0px") -> Block

def header(*, title: str, template: str, subtitle: Optional[str] = None, 
           text_tag_list: Optional[List[Block]] = None, padding: Optional[str] = None) -> Block

def body(elements: Iterable[Block], *, direction: str = "vertical") -> Block

def column_set(columns: Iterable[Block], *, background_style: str = "grey-100",
               horizontal_spacing: str = "12px", horizontal_align: str = "left",
               margin: str = "0px 0px 0px 0px") -> Block

def collapsible_panel(title_markdown_content: str, elements: Iterable[Block], *,
                      expanded: bool = False, background_color: str = "grey-200",
                      border_color: str = "grey", corner_radius: str = "5px",
                      vertical_spacing: str = "8px", padding: str = "8px 8px 8px 8px") -> Block

def card(*, elements: Iterable[Block], header: Block, schema: str = "2.0",
         config: Optional[Block] = None) -> Block
```

**Key Principles**:
- ✅ Pure functions returning dictionaries
- ✅ Optional-only parameters to preserve exact output
- ✅ Composable and chainable
- ✅ Schema-aware (Lark 2.0 card format)

**Adoption Recommendation**: 
Create similar block functions for Feishu document notifications, but tailor them to Feishu's specific block types (text, image, table, divider, etc.).

---

#### B. CardBuilder Pattern (templates.py)

**Pattern**: Fluent builder with method chaining

```python
class CardBuilder:
    """Fluent builder for constructing cards"""
    
    def __init__(self, language: LanguageCode = "zh"):
        self.language = language
        self._header = None
        self._elements = []
        self._config = None
    
    def header(self, title: str, *, status: str, color: str) -> 'CardBuilder':
        """Set card header with status and color"""
        self._header = header(title=title, template=status, ...)
        return self
    
    def markdown(self, content: str, **kwargs) -> 'CardBuilder':
        """Add markdown element"""
        self._elements.append(markdown(content, **kwargs))
        return self
    
    def columns(self) -> ColumnBuilder:
        """Start column set builder (nested builder pattern)"""
        return ColumnBuilder(self)
    
    def collapsible(self, title: str, content: str, **kwargs) -> 'CardBuilder':
        """Add collapsible panel"""
        self._elements.append(collapsible_panel(title, [markdown(content)], **kwargs))
        return self
    
    def build(self) -> GenericCardTemplate:
        """Complete and return the card"""
        return GenericCardTemplate(card(
            elements=self._elements,
            header=self._header,
            config=self._config
        ))
```

**Key Principles**:
- ✅ Fluent interface for readable code
- ✅ Supports nested builders (ColumnBuilder)
- ✅ Language-aware translation
- ✅ Status + color for visual feedback
- ✅ Chainable methods return self

**Adoption Recommendation**: 
Adopt CardBuilder pattern for Feishu document block composition. The nested builder pattern is excellent for table/list structures.

---

#### C. Workflow Template Factories (workflow_templates.py)

**Pattern**: Static factory methods for domain-specific templates

```python
class WorkflowTemplates:
    """Factory for workflow-specific notifications"""
    
    @staticmethod
    def network_submission_start(
        network_set_name: str,
        network_type: str,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Template for network submission START"""
        builder = CardBuilder(language).header(
            _t("network_submission_started"), 
            status=_t("running"), 
            color="wathet"
        )
        # Build metadata lines
        metadata_lines = [
            f"**{_t('network_set_name')}:** {network_set_name}",
            f"**{_t('network_type')}:** {network_type}",
        ]
        builder.markdown("\n".join(metadata_lines), text_align="left", text_size="normal")
        
        # Optional sections
        if group or prefix:
            builder.columns().column(...).column(...).end_columns()
        
        if metadata:
            s = json.dumps(metadata, indent=2, ensure_ascii=False)
            msg = f"```json\n{s}\n```"
            builder.collapsible(_t("metadata_overview"), msg, expanded=False)
        
        return builder.build()
    
    @staticmethod
    def network_submission_complete(...) -> GenericCardTemplate:
        """Template for network submission COMPLETE"""
        # Similar structure with green color
        ...
    
    @staticmethod
    def network_submission_failure(...) -> GenericCardTemplate:
        """Template for network submission FAILURE"""
        # Similar structure with red color
        ...
```

**Key Principles**:
- ✅ Workflows have distinct phases: START, PROGRESS, COMPLETE, FAILURE
- ✅ Color coding for status: wathet (light blue) for running, green for success, red for failure
- ✅ Consistent structure: header + metadata lines + optional details
- ✅ Collapsible sections for optional/detailed info
- ✅ JSON visualization for complex metadata
- ✅ Progress tracking with percentage calculations

**Adoption Recommendation**: 
Create similar domain-specific factories for Feishu document operations (create, edit, share, etc.). Structure phases around document lifecycle events.

---

#### D. Configuration Hierarchy (config.py)

**Pattern**: Multi-source configuration with precedence

```python
class LarkWebhookSettings(BaseSettings):
    """Hierarchical configuration loading"""
    
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_prefix="LARK_",
        env_file=".env",
        toml_file="lark_webhook.toml",
        extra="ignore",
        case_sensitive=False,
    )
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configuration precedence (highest to lowest):
        1. Direct parameters (CLI args)
        2. Environment variables (LARK_WEBHOOK_URL, LARK_WEBHOOK_SECRET)
        3. TOML file (lark_webhook.toml)
        4. Default values
        """
        return (
            init_settings,          # Highest priority
            env_settings,
            TomlConfigSettingsSource(settings_cls),  # Lowest priority
        )

def create_settings(
    toml_file: Optional[str] = None,
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
) -> LarkWebhookSettings:
    """Create settings with optional overrides"""
    init_kwargs = {}
    if webhook_url:
        init_kwargs["webhook_url"] = webhook_url
    if webhook_secret:
        init_kwargs["webhook_secret"] = webhook_secret
    
    if toml_file and Path(toml_file).exists():
        # Custom TOML path
        class CustomSettings(LarkWebhookSettings):
            model_config = SettingsConfigDict(
                env_prefix="LARK_",
                toml_file=toml_file,
                ...
            )
        return CustomSettings(**init_kwargs)
    else:
        return LarkWebhookSettings(**init_kwargs)
```

**Configuration Flow**:
```
CLI Args → Environment Variables → TOML File → Defaults
   ↑              ↑                    ↑          ↑
   └──────────────┴────────────────────┴──────────┘
        Highest Priority        Lowest Priority
```

**Key Principles**:
- ✅ Uses Pydantic v2 BaseSettings
- ✅ Clear precedence order
- ✅ Environment variable prefix scoping (LARK_)
- ✅ Custom TOML file path support
- ✅ Graceful fallback with warnings

**Adoption Recommendation**: 
Use identical pattern for feishu-doc-tools notification config. Add notification-specific settings (channels, rates, templates).

---

### 1.3 Dependencies

```
colorlog>=6.10.1        # Colored logging
httpx>=0.28.1          # Async HTTP client
pydantic>=2.11.7       # Data validation
pydantic-settings>=2.10.1  # Configuration management
```

**Why these choices**:
- `pydantic`: Industry standard for config validation
- `httpx`: Modern async HTTP with timeouts, retries
- `colorlog`: Better CLI user experience
- All are lightweight and mature

---

## PART 2: CLAUDE-CODE-NOTIFIER ANALYSIS

### 2.1 Directory Structure

```
Claude-Code-Notifier/
├── src/claude_notifier/
│   ├── core/
│   │   ├── channels/
│   │   │   ├── base.py              # BaseChannel abstract class
│   │   │   ├── dingtalk.py
│   │   │   ├── webhook.py
│   │   │   └── __init__.py
│   │   ├── config.py                # Configuration management
│   │   └── notifier.py              # Core notifier
│   ├── utils/
│   │   ├── message_grouper.py       # Message grouping/merging
│   │   ├── notification_throttle.py # Rate limiting
│   │   ├── cooldown_manager.py
│   │   ├── operation_gate.py
│   │   └── time_utils.py
│   ├── monitoring/
│   │   ├── statistics.py
│   │   ├── performance.py
│   │   ├── health_check.py
│   │   └── __init__.py
│   └── __init__.py
├── channels/          # Legacy channel implementations
│   ├── base.py
│   ├── feishu.py
│   └── ...
└── src/
    └── enhanced_notifier.py
```

### 2.2 Key Implementation Patterns

#### A. BaseChannel Architecture (core/channels/base.py)

**Pattern**: Abstract base class with multiple notification types

```python
class BaseChannel(abc.ABC):
    """Abstract notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abc.abstractmethod
    def send_notification(self, template_data: Dict[str, Any], 
                         event_type: str = 'generic') -> bool:
        """Send generic notification"""
        pass
    
    # Event-specific convenience methods
    def send_permission_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'permission')
    
    def send_completion_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'completion')
    
    def send_test_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'test')
    
    def send_custom_event_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'custom_event')
    
    def send_rate_limit_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'rate_limit')
    
    def send_error_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'error')
    
    def send_session_start_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'session_start')
    
    def send_idle_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'idle_detected')
    
    def send_sensitive_operation_notification(self, data: Dict[str, Any]) -> bool:
        return self.send_notification(data, 'sensitive_operation')
    
    @abc.abstractmethod
    def validate_config(self) -> bool:
        """Validate channel configuration"""
        pass
    
    # Channel capability queries
    def is_enabled(self) -> bool:
        return self.config.get('enabled', False)
    
    def get_name(self) -> str:
        return self.__class__.__name__.lower().replace('channel', '')
    
    def supports_rich_content(self) -> bool:
        return True
    
    def supports_actions(self) -> bool:
        return False
    
    def get_max_content_length(self) -> int:
        return 4000  # Default
    
    def truncate_content(self, content: str, max_length: Optional[int] = None) -> str:
        if max_length is None:
            max_length = self.get_max_content_length()
        if len(content) <= max_length:
            return content
        return content[:max_length - 3] + "..."
    
    def format_message_for_channel(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format message for specific channel (override in subclasses)"""
        return template_data
```

**Key Principles**:
- ✅ Single abstract method for all notifications
- ✅ Convenience methods for common event types
- ✅ Channel capability queries (rich content, actions, length limits)
- ✅ Content truncation handling
- ✅ Per-channel formatting customization
- ✅ Config validation per channel

**Adoption Recommendation**:
Create FeishuDocChannel extending BaseChannel with document-specific methods like send_document_notification(), send_comment_notification(), etc.

---

#### B. Message Grouper Pattern (utils/message_grouper.py)

**Pattern**: Intelligent message grouping and merging to reduce notification spam

```python
class GroupingStrategy(Enum):
    """Grouping strategies"""
    BY_PROJECT = "by_project"
    BY_EVENT_TYPE = "by_event_type"
    BY_CHANNEL = "by_channel"
    BY_CONTENT = "by_content"
    BY_TIME_WINDOW = "by_time_window"
    BY_SIMILARITY = "by_similarity"

@dataclass
class MessageGroup:
    """Grouped messages container"""
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
    
    def add_message(self, message: Dict[str, Any]):
        self.messages.append(message)
        self.last_updated = time.time()
        self.merge_count += 1
        # Update priority (take highest)
        msg_priority = message.get('priority', 1)
        if isinstance(msg_priority, str):
            priority_map = {'low': 1, 'normal': 2, 'high': 3, 'critical': 4}
            msg_priority = priority_map.get(msg_priority.lower(), 2)
        self.priority = max(self.priority, msg_priority)
    
    def get_age(self) -> float:
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        return time.time() - self.last_updated

class MessageGrouper:
    """Intelligent message grouper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        self.grouping_config = self._load_grouping_config()
        self.active_groups: Dict[str, MessageGroup] = {}
        self.grouping_rules = self._load_grouping_rules()
        self.similarity_threshold = self.grouping_config.get('similarity_threshold', 0.8)
    
    def _load_grouping_config(self) -> Dict[str, Any]:
        """Load grouping configuration with defaults"""
        default_config = {
            'enabled': True,
            'group_window': 300,           # Grouping time window (seconds)
            'max_group_size': 10,          # Max messages per group
            'max_groups': 50,              # Max simultaneous active groups
            'send_threshold': 5,           # Send when reached (message count)
            'send_timeout': 60,            # Send after timeout (seconds)
            'similarity_threshold': 0.8,   # Similarity threshold
            'merge_strategies': [
                GroupingStrategy.BY_PROJECT,
                GroupingStrategy.BY_EVENT_TYPE,
                GroupingStrategy.BY_TIME_WINDOW
            ]
        }
        
        # Merge with user config
        grouping_config = self.config.get('intelligent_limiting', {}).get('message_grouper', {})
        user_config = grouping_config.get('grouping', {})
        default_config.update(user_config)
        return default_config
    
    def _load_grouping_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load event-specific grouping rules"""
        default_rules = {
            'sensitive_operation': {
                'strategy': GroupingStrategy.BY_PROJECT,
                'max_size': 3,
                'timeout': 30,
                'priority_boost': True
            },
            'task_completion': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 5,
                'timeout': 120,
                'summary_template': 'batch_completion'
            },
            'rate_limit': {
                'strategy': GroupingStrategy.BY_CONTENT,
                'max_size': 1,
                'timeout': 300,
                'suppress_duplicates': True
            },
            'error_occurred': {
                'strategy': GroupingStrategy.BY_SIMILARITY,
                'max_size': 5,
                'timeout': 60,
                'escalate_threshold': 3
            },
            'session_start': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 10,
                'timeout': 300,
                'summary_only': True
            },
            'idle_detected': {
                'strategy': GroupingStrategy.BY_TIME_WINDOW,
                'max_size': 3,
                'timeout': 1800,  # 30 minutes
                'suppress_duplicates': True
            }
        }
        
        # Merge user rules
        grouping_config = self.config.get('intelligent_limiting', {}).get('message_grouper', {})
        user_rules = grouping_config.get('rules', {})
        
        if user_rules:
            for event_type, rule in user_rules.items():
                if event_type in default_rules:
                    default_rules[event_type].update(rule)
                else:
                    default_rules[event_type] = rule
        
        return default_rules
    
    def should_group_message(self, message: Dict[str, Any]) -> Tuple[bool, Optional[str], MergeAction]:
        """Check if message should be grouped
        
        Returns:
            (should_group, group_id, merge_action)
        """
        if not self.grouping_config.get('enabled', True):
            return False, None, MergeAction.MERGE
        
        # Determine grouping key based on message
        event_type = message.get('event_type', 'generic')
        channel = message.get('channel', 'default')
        project = message.get('project', 'default')
        
        # Check if event type has specific rules
        if event_type in self.grouping_rules:
            rule = self.grouping_rules[event_type]
            strategy = rule.get('strategy', GroupingStrategy.BY_PROJECT)
            
            # Generate group ID based on strategy
            if strategy == GroupingStrategy.BY_PROJECT:
                group_id = f"{event_type}:{project}"
            elif strategy == GroupingStrategy.BY_EVENT_TYPE:
                group_id = f"{event_type}"
            elif strategy == GroupingStrategy.BY_CHANNEL:
                group_id = f"{event_type}:{channel}"
            elif strategy == GroupingStrategy.BY_TIME_WINDOW:
                group_id = f"{event_type}:{channel}"
            # ... other strategies
            
            return True, group_id, MergeAction.MERGE
        
        return False, None, MergeAction.MERGE
```

**Grouping Strategies**:

| Strategy | Use Case | Example |
|----------|----------|---------|
| `BY_PROJECT` | Group similar operations by project | Multiple file edits in same project |
| `BY_EVENT_TYPE` | Group by notification type | Multiple completion events |
| `BY_CONTENT` | Suppress duplicates | Same error repeated |
| `BY_TIME_WINDOW` | Batch notifications in time windows | Session starts in 5-minute window |
| `BY_SIMILARITY` | Group similar but different messages | Different errors in same category |
| `BY_CHANNEL` | Channel-specific grouping | Separate DingTalk from Feishu |

**Key Principles**:
- ✅ Configurable grouping strategies
- ✅ Per-event-type rules
- ✅ Time-window based merging
- ✅ Priority elevation in groups
- ✅ Similarity-based deduplication
- ✅ Escalation thresholds

**Adoption Recommendation**:
Use this pattern for grouping document-related notifications (multiple edits → single "document modified" notification) and user actions (multiple collaborators → "N users are viewing" notification).

---

#### C. Notification Throttle Pattern (utils/notification_throttle.py)

**Pattern**: Multi-layer rate limiting and duplicate detection

```python
class ThrottleAction(Enum):
    """Throttle actions"""
    ALLOW = "allow"
    BLOCK = "block"
    DELAY = "delay"
    MERGE = "merge"

class NotificationPriority(Enum):
    """Notification priority levels"""
    CRITICAL = 4
    HIGH = 3
    NORMAL = 2
    LOW = 1

@dataclass
class NotificationRequest:
    """Notification request for throttling"""
    notification_id: str
    event_type: str
    channel: str
    priority: NotificationPriority
    content: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    
    def get_content_hash(self) -> str:
        """Get content hash for duplicate detection"""
        key_content = {
            'event_type': self.event_type,
            'channel': self.channel,
            'project': self.content.get('project', ''),
            'operation': self.content.get('operation', ''),
            'error': self.content.get('error', ''),
            'title': self.content.get('title', ''),
        }
        content_str = '|'.join(f"{k}:{v}" for k, v in key_content.items())
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:8]

class NotificationThrottle:
    """Multi-layer rate limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load rate limits
        self.rate_limits = self._load_rate_limits()
        
        # Notification history with auto-limit
        self.notification_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Duplicate cache
        self.duplicate_cache: Dict[str, Tuple[float, int]] = {}
        
        # Delayed queue
        self.delayed_notifications: List[Tuple[float, NotificationRequest]] = []
        
        # Statistics
        self.stats = {
            'allowed': 0,
            'blocked': 0,
            'delayed': 0,
            'merged': 0,
            'duplicates_filtered': 0
        }
    
    def _load_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """Load rate limit configuration"""
        default_limits = {
            'global': {
                'max_per_minute': 20,
                'max_per_hour': 200,
                'burst_limit': 5,
                'burst_window': 10
            },
            'by_channel': {
                'dingtalk': {'max_per_minute': 10, 'max_per_hour': 100},
                'feishu': {'max_per_minute': 15, 'max_per_hour': 150},
                'email': {'max_per_minute': 5, 'max_per_hour': 50},
                'telegram': {'max_per_minute': 20, 'max_per_hour': 200},
            },
            'by_event': {
                'sensitive_operation': {'max_per_minute': 3, 'cooldown': 30},
                'task_completion': {'max_per_minute': 2, 'cooldown': 60},
                'rate_limit': {'max_per_minute': 1, 'cooldown': 300},
                'error_occurred': {'max_per_minute': 5, 'cooldown': 10},
                'idle_detected': {'max_per_minute': 1, 'cooldown': 1800}
            },
            'priority_weights': {
                'CRITICAL': 1.0,    # No throttle
                'HIGH': 0.8,        # Light throttle
                'NORMAL': 0.6,      # Normal throttle
                'LOW': 0.3          # Strict throttle
            }
        }
        
        # Merge user config
        throttle_config = self.config.get('intelligent_limiting', {}).get('notification_throttle', {})
        user_limits = throttle_config.get('rate_limits', {})
        
        if user_limits:
            for category, limits in user_limits.items():
                if category in default_limits and isinstance(limits, dict):
                    if isinstance(default_limits[category], dict):
                        default_limits[category].update(limits)
                    else:
                        default_limits[category] = limits
                else:
                    default_limits[category] = limits
        
        return default_limits
    
    def should_allow_notification(self, request: NotificationRequest) -> Tuple[ThrottleAction, str, Optional[float]]:
        """Check if notification should be allowed
        
        Multi-layer checking:
        1. Duplicate detection
        2. Global rate limits
        3. Channel-specific limits
        4. Event-specific limits
        5. Priority weights
        
        Returns:
            (action, reason, delay_seconds)
        """
        # Periodic cleanup
        self._periodic_cleanup()
        
        try:
            # 1. Check for duplicates
            duplicate_result = self._check_duplicate(request)
            if duplicate_result[0] != ThrottleAction.ALLOW:
                return duplicate_result
            
            # 2. Check global limits
            global_result = self._check_global_limits(request)
            if global_result[0] != ThrottleAction.ALLOW:
                return global_result
            
            # 3. Check channel limits
            channel_result = self._check_channel_limits(request)
            if channel_result[0] != ThrottleAction.ALLOW:
                return channel_result
            
            # 4. Check event limits
            event_result = self._check_event_limits(request)
            if event_result[0] != ThrottleAction.ALLOW:
                return event_result
            
            # 5. Check priority weights
            priority_result = self._check_priority_limits(request)
            if priority_result[0] != ThrottleAction.ALLOW:
                return priority_result
            
            # Record and allow
            self._record_notification(request)
            self.stats['allowed'] += 1
            return ThrottleAction.ALLOW, "Notification allowed", None
            
        except Exception as e:
            self.logger.error(f"Throttle check exception: {e}")
            # Default to allow on error
            return ThrottleAction.ALLOW, f"Throttle error (allowed): {str(e)}", None
```

**Rate Limiting Layers**:

```
Layer 1: Duplicate Detection
  └─ Check content hash, suppress within 5 min

Layer 2: Global Limits
  └─ 20 per minute, 200 per hour, burst limit

Layer 3: Channel Limits
  └─ Per-channel: Feishu 15/min, DingTalk 10/min, Email 5/min

Layer 4: Event Limits
  └─ Per-event: Errors 5/min, Rate-limits 1/min (300s cooldown)

Layer 5: Priority Weights
  └─ CRITICAL: 1.0x, HIGH: 0.8x, NORMAL: 0.6x, LOW: 0.3x
```

**Key Principles**:
- ✅ Multi-layer filtering with clear precedence
- ✅ Per-channel customizable limits
- ✅ Per-event customizable rules
- ✅ Priority-based weighting
- ✅ Duplicate detection via content hash
- ✅ Burst limit handling
- ✅ Cooldown periods per event type
- ✅ Automatic history cleanup

**Adoption Recommendation**:
Essential for feishu-doc-tools. Configure limits based on document operation frequency (edits → 10/min, comments → 5/min, shares → 2/min).

---

### 2.3 Core Notifier Pattern (core/notifier.py)

```python
class Notifier:
    """Lightweight core notifier"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.logger = self._setup_logging()
        self.channels = self._init_channels()
    
    def _init_channels(self) -> Dict[str, Any]:
        """Initialize enabled channels"""
        channels = {}
        channels_config = self.config.get('channels', {})
        
        for channel_name, channel_config in channels_config.items():
            if channel_config.get('enabled', False):
                try:
                    channel_class = get_channel_class(channel_name)
                    if channel_class:
                        channels[channel_name] = channel_class(channel_config)
                        self.logger.debug(f"Channel initialized: {channel_name}")
                except Exception as e:
                    self.logger.error(f"Channel init failed {channel_name}: {e}")
        
        self.logger.info(f"{len(channels)} channels enabled")
        return channels
    
    def send(self, 
             message: Union[str, Dict[str, Any]], 
             channels: Optional[List[str]] = None,
             event_type: str = 'custom',
             **kwargs) -> bool:
        """Send notification - simplified interface
        
        Args:
            message: String or dict
            channels: Target channels (None = default)
            event_type: Event type for routing
            **kwargs: Extra parameters
        
        Examples:
            # Simple text
            notifier.send("Hello World!")
            
            # Specific channels
            notifier.send("Alert!", channels=['dingtalk', 'email'])
            
            # Complex message
            notifier.send({
                'title': 'Task Complete',
                'content': 'Analysis done',
                'project': 'my-project'
            })
        """
        # Normalize message
        if isinstance(message, str):
            template_data = {
                'title': 'Notification',
                'content': message,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **kwargs
            }
        else:
            template_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                **message,
                **kwargs
            }
        
        # Determine channels
        if channels is None:
            channels = self._get_default_channels(event_type)
        
        if not channels:
            self.logger.warning("No available channels")
            return True
        
        # Send
        return self._send_to_channels(template_data, channels, event_type)
    
    def _get_default_channels(self, event_type: str) -> List[str]:
        """Get default channels for event type"""
        # Event-specific routing
        event_config = self.config.get('events', {}).get(event_type, {})
        if event_config.get('channels'):
            return event_config['channels']
        
        # Global default
        default_channels = self.config.get('default_channels', [])
        return [ch for ch in default_channels if ch in self.channels]
```

**Key Principles**:
- ✅ Simplified send() interface
- ✅ Automatic channel initialization
- ✅ Event-type based routing
- ✅ Flexible channel selection
- ✅ Graceful error handling

**Adoption Recommendation**:
Use this pattern for feishu-doc-tools Notifier class. Add event types: `document_created`, `document_modified`, `document_shared`, `comment_added`, etc.

---

## PART 3: SYNTHESIS & RECOMMENDATIONS

### 3.1 Recommended Architecture for feishu-doc-tools

```
feishu_doc_tools/
├── notifications/
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseChannel (from Claude-Code-Notifier)
│   │   ├── feishu.py            # FeishuDocChannel implementation
│   │   └── registry.py
│   ├── blocks/
│   │   ├── __init__.py
│   │   └── blocks.py            # Building blocks (from lark-webhook-notify)
│   ├── templates/
│   │   ├── __init__.py
│   │   ├── builder.py           # CardBuilder (from lark-webhook-notify)
│   │   ├── document_templates.py# Document-specific factories
│   │   └── messages.py          # Message types & translations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── message_grouper.py   # From Claude-Code-Notifier
│   │   ├── notification_throttle.py  # From Claude-Code-Notifier
│   │   ├── cooldown_manager.py
│   │   └── time_utils.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Pydantic config (from lark-webhook-notify)
│   ├── notifier.py              # Core Notifier (from Claude-Code-Notifier)
│   └── __init__.py
├── tests/
│   ├── test_channels.py
│   ├── test_templates.py
│   ├── test_throttle.py
│   └── test_message_grouper.py
└── examples/
    └── usage_examples.py
```

### 3.2 Event Types for feishu-doc-tools

```python
class DocumentEventType(str, Enum):
    """Document lifecycle events"""
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_MODIFIED = "document_modified"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_SHARED = "document_shared"
    DOCUMENT_PERMISSION_CHANGED = "document_permission_changed"
    DOCUMENT_MOVED = "document_moved"
    DOCUMENT_EXPORTED = "document_exported"
    
    # Collaboration events
    COMMENT_ADDED = "comment_added"
    COMMENT_RESOLVED = "comment_resolved"
    MENTION_RECEIVED = "mention_received"
    VIEWER_ADDED = "viewer_added"
    COLLABORATOR_REMOVED = "collaborator_removed"
    
    # System events
    QUOTA_EXCEEDED = "quota_exceeded"
    SYNC_FAILED = "sync_failed"
    RATE_LIMIT_HIT = "rate_limit_hit"
    OPERATION_COMPLETED = "operation_completed"
    ERROR_OCCURRED = "error_occurred"
```

### 3.3 Recommended Rate Limits

```python
RATE_LIMITS = {
    'global': {
        'max_per_minute': 30,
        'max_per_hour': 300,
        'burst_limit': 10,
        'burst_window': 10
    },
    'by_channel': {
        'feishu': {'max_per_minute': 20, 'max_per_hour': 200},
        'email': {'max_per_minute': 10, 'max_per_hour': 100},
        'webhook': {'max_per_minute': 50, 'max_per_hour': 500},
    },
    'by_event': {
        'document_modified': {'max_per_minute': 5, 'cooldown': 60},
        'comment_added': {'max_per_minute': 10, 'cooldown': 30},
        'error_occurred': {'max_per_minute': 3, 'cooldown': 120},
        'rate_limit_hit': {'max_per_minute': 1, 'cooldown': 300},
        'sync_failed': {'max_per_minute': 2, 'cooldown': 60},
    }
}
```

### 3.4 Template Examples for feishu-doc-tools

```python
class DocumentTemplates:
    """Factory for document-related notifications"""
    
    @staticmethod
    def document_created(
        doc_name: str,
        creator: str,
        doc_url: str,
        doc_type: str = "document",
        language: LanguageCode = "zh"
    ) -> GenericCardTemplate:
        """Template for document creation"""
        builder = CardBuilder(language).header(
            _t("document_created"),
            status=_t("created"),
            color="green"
        )
        builder.markdown(
            f"**{_t('document_name')}:** {doc_name}\n"
            f"**{_t('creator')}:** {creator}\n"
            f"**{_t('type')}:** {doc_type}"
        )
        return builder.build()
    
    @staticmethod
    def document_modified(
        doc_name: str,
        modifier: str,
        changes: Dict[str, str],
        language: LanguageCode = "zh"
    ) -> GenericCardTemplate:
        """Template for document modification"""
        builder = CardBuilder(language).header(
            _t("document_modified"),
            status=_t("modified"),
            color="wathet"
        )
        # ... build changes table
        return builder.build()
    
    @staticmethod
    def sync_failed(
        doc_name: str,
        error_message: str,
        retry_count: int = 0,
        language: LanguageCode = "zh"
    ) -> GenericCardTemplate:
        """Template for sync failure"""
        builder = CardBuilder(language).header(
            _t("sync_failed"),
            status=_t("failed"),
            color="red"
        )
        # ... build error details
        return builder.build()
```

### 3.5 Message Grouping Rules for feishu-doc-tools

```python
GROUPING_RULES = {
    'document_modified': {
        'strategy': GroupingStrategy.BY_TIME_WINDOW,
        'max_size': 10,
        'timeout': 300,  # 5 minutes
        'summary_template': 'document_batch_edits'
    },
    'comment_added': {
        'strategy': GroupingStrategy.BY_CONTENT,
        'max_size': 5,
        'timeout': 60,
        'suppress_duplicates': True
    },
    'error_occurred': {
        'strategy': GroupingStrategy.BY_SIMILARITY,
        'max_size': 3,
        'timeout': 600,
        'escalate_threshold': 2
    },
    'viewer_added': {
        'strategy': GroupingStrategy.BY_TIME_WINDOW,
        'max_size': 20,
        'timeout': 1800,  # 30 minutes
        'summary_only': True
    }
}
```

### 3.6 Configuration Structure

```yaml
# config.yaml for feishu-doc-tools notifications
notifications:
  enabled: true
  
  # Default channels
  default_channels:
    - feishu
  
  # Channel configurations
  channels:
    feishu:
      enabled: true
      url: ${FEISHU_WEBHOOK_URL}
      secret: ${FEISHU_WEBHOOK_SECRET}
      timeout: 10
      max_retries: 3
    
    email:
      enabled: false
      smtp_server: smtp.gmail.com
      sender: notifications@example.com
  
  # Event routing
  events:
    document_created:
      channels: [feishu]
      priority: high
    
    document_modified:
      channels: [feishu]
      priority: normal
      grouping_strategy: BY_TIME_WINDOW
    
    error_occurred:
      channels: [feishu, email]
      priority: critical
  
  # Intelligent limiting
  intelligent_limiting:
    # Message grouping
    message_grouper:
      enabled: true
      grouping:
        group_window: 300
        max_group_size: 10
        max_groups: 50
        send_threshold: 5
        send_timeout: 60
        similarity_threshold: 0.8
      rules:
        # Custom rules per event
        document_modified:
          strategy: BY_TIME_WINDOW
          max_size: 10
          timeout: 300
    
    # Rate limiting
    notification_throttle:
      enabled: true
      rate_limits:
        global:
          max_per_minute: 30
          max_per_hour: 300
          burst_limit: 10
        by_channel:
          feishu:
            max_per_minute: 20
            max_per_hour: 200
        by_event:
          document_modified:
            max_per_minute: 5
            cooldown: 60
  
  # Logging
  logging:
    enabled: true
    level: info
    file: ~/.feishu-doc-tools/logs/notifications.log
```

---

## PART 4: QUICK REFERENCE

### 4.1 Core Patterns Checklist

- [ ] **Building Blocks** (blocks.py)
  - Pure functions returning dicts
  - Composable elements
  - Schema-aware

- [ ] **CardBuilder** (templates.py)
  - Fluent interface
  - Method chaining
  - Nested builders

- [ ] **Template Factories** (workflow_templates.py)
  - Static factory methods
  - Domain-specific templates
  - Consistent structure

- [ ] **BaseChannel** (channels/base.py)
  - Abstract base class
  - Event-specific methods
  - Capability queries

- [ ] **Message Grouper** (utils/message_grouper.py)
  - Multiple strategies
  - Time window batching
  - Similarity-based merging

- [ ] **Notification Throttle** (utils/notification_throttle.py)
  - Multi-layer filtering
  - Per-channel limits
  - Per-event rules
  - Priority weighting

- [ ] **Configuration** (config.py)
  - Pydantic BaseSettings
  - Multi-source hierarchy
  - CLI → ENV → TOML → Defaults

### 4.2 Dependencies to Adopt

```
# From lark-webhook-notify
colorlog>=6.10.1        # Colored logging
httpx>=0.28.1          # Async HTTP
pydantic>=2.11.7       # Config validation
pydantic-settings>=2.10.1  # Settings management
```

### 4.3 Key Metrics to Track

```python
# Statistics to maintain
stats = {
    # Grouping
    'groups_created': 0,
    'messages_grouped': 0,
    'messages_merged': 0,
    'groups_sent': 0,
    
    # Throttling
    'allowed': 0,
    'blocked': 0,
    'delayed': 0,
    'merged': 0,
    'duplicates_filtered': 0,
    
    # Channels
    'sent_successfully': 0,
    'send_failed': 0,
    'send_errors': []
}
```

---

## PART 5: IMPLEMENTATION TIMELINE

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create blocks.py with document block functions
- [ ] Implement CardBuilder for Feishu documents
- [ ] Set up configuration system (Pydantic)
- [ ] Create BaseChannel abstract class

### Phase 2: Core Features (Weeks 2-3)
- [ ] Implement FeishuDocChannel
- [ ] Create document template factories
- [ ] Set up message grouper
- [ ] Implement notification throttle

### Phase 3: Integration (Weeks 3-4)
- [ ] Integrate with existing feishu-doc-tools
- [ ] Add CLI commands
- [ ] Comprehensive testing
- [ ] Documentation

### Phase 4: Enhancement (Week 4+)
- [ ] Multiple channel support
- [ ] Advanced analytics dashboard
- [ ] User preference management
- [ ] Scheduled notifications

---

## Summary

Both reference projects provide complementary patterns:

**lark-webhook-notify** excels at:
- ✅ Building composable card structures
- ✅ Template design patterns
- ✅ Multi-source configuration
- ✅ Clean, minimal dependencies

**Claude-Code-Notifier** excels at:
- ✅ Multi-channel architecture
- ✅ Intelligent rate limiting
- ✅ Message deduplication
- ✅ Sophisticated grouping strategies

**Recommended approach**: 
Adopt the **blocks + builder** pattern from lark-webhook-notify for document card construction, and the **channel + throttle + grouper** pattern from Claude-Code-Notifier for intelligent notification delivery.

