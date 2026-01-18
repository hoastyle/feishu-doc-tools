# 飞书用户认证使用指南

**版本**: v1.0
**更新日期**: 2026-01-18
**状态**: ✅ 生产就绪

---

## 📋 目录

- [概述](#概述)
- [认证模式对比](#认证模式对比)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [API 参考](#api-参考)
- [常见问题](#常见问题)

---

## 概述

feishu-doc-tools 现在支持两种飞书 API 认证模式：

1. **应用认证 (tenant_access_token)** - 默认模式
2. **用户认证 (user_access_token)** - 新功能

### 选择合适的认证模式

| 场景 | 推荐模式 | 原因 |
|------|---------|------|
| 自动化批量操作 | 应用认证 | 无需用户干预，适合脚本和 CI/CD |
| 在应用空间创建资源 | 应用认证 | 资源归属应用，权限可控 |
| 在用户个人空间操作 | **用户认证** | 访问用户私有资源 |
| 创建属于用户的文档 | **用户认证** | 文档所有权归属用户 |
| 继承用户权限 | **用户认证** | 自动获得用户权限范围 |

---

## 认证模式对比

### 应用认证 (tenant_access_token)

**特点**:
- ✅ 无需用户授权
- ✅ 适合自动化操作
- ✅ 2小时令牌有效期
- ⚠️ 资源归属应用
- ⚠️ 需要配置权限范围

**使用场景**:
```bash
# 创建文档到应用空间
uv run python scripts/create_wiki_doc.py README.md --space-id 74812***88644

# 批量上传
uv run python scripts/batch_create_wiki_docs.py ./docs --space-id 74812***88644
```

### 用户认证 (user_access_token)

**特点**:
- ✅ 资源归属用户
- ✅ 继承用户权限
- ✅ 可访问用户私有资源
- ⚠️ 需要一次性的 OAuth 授权
- ⚠️ 令牌需要刷新

**使用场景**:
```bash
# 设置用户认证（一次性）
uv run python scripts/setup_user_auth.py

# 创建文档到用户个人空间
uv run python scripts/create_wiki_doc.py README.md --personal

# 批量上传到个人 Wiki
uv run python scripts/batch_create_wiki_docs.py ./docs --personal
```

---

## 快速开始

### 步骤 1: 配置重定向 URI

在飞书开发者后台配置 OAuth 重定向 URI：

1. 访问 [飞书开发者后台](https://open.feishu.cn/open-apis/app_modal)
2. 选择您的应用
3. 导航到: **开发配置** > **安全设置**
4. 添加重定向 URI: `http://localhost:8080/callback`

### 步骤 2: 运行设置脚本

```bash
uv run python scripts/setup_user_auth.py
```

脚本会引导您完成：
1. 生成 OAuth 授权 URL
2. 在浏览器中完成授权
3. 输入授权码
4. 自动交换令牌
5. 保存配置到 `.env` 文件

### 步骤 3: 验证配置

```bash
# 验证用户信息
uv run python scripts/verify_user_auth.py --code <您的授权码>
```

### 步骤 4: 使用用户认证

配置完成后，所有脚本将自动使用用户身份：

```bash
# 创建文档到个人空间
uv run python scripts/create_wiki_doc.py README.md --personal

# 文档将属于您，而非应用
```

---

## 使用方法

### 方法 1: 使用设置脚本（推荐）

```bash
# 交互式设置
uv run python scripts/setup_user_auth.py

# 按提示操作：
# 1. 复制 OAuth URL 到浏览器
# 2. 完成授权
# 3. 复制授权码
# 4. 粘贴到脚本
# 5. 配置自动保存
```

### 方法 2: 手动配置

**1. 获取授权码**

访问授权 URL：
```
https://open.feishu.cn/open-apis/authen/v1/authorize?
  app_id=cli_xxxxx&
  redirect_uri=http://localhost:8080/callback&
  scope=docx:document docx:document:readonly wiki:wiki:readonly wiki:wiki wiki:wiki:wiki&
  state=your_state
```

**2. 交换令牌**

```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()
result = client.exchange_authorization_code("您的授权码")

print(f"用户: {result['name']}")
print(f"令牌: {result['access_token'][:20]}...")
```

**3. 保存配置**

编辑 `.env` 文件：
```bash
FEISHU_AUTH_MODE=user
FEISHU_USER_REFRESH_TOKEN=ur-xxxxx  # 从上一步获取
```

### 方法 3: 编程方式

```python
from lib.feishu_api_client import FeishuApiClient, AuthMode

# 使用用户认证
client = FeishuApiClient(
    app_id="cli_xxxxx",
    app_secret="xxxxx",
    auth_mode=AuthMode.USER,
    user_refresh_token="ur-xxxxx"
)

# 获取用户信息
user_info = client.get_user_info()
print(f"当前用户: {user_info['name']}")

# 创建文档（属于用户）
result = client.create_wiki_node(
    space_id="my_library",
    title="我的文档"
)
```

---

## API 参考

### FeishuApiClient

#### 初始化

```python
FeishuApiClient(
    app_id: str,
    app_secret: str,
    auth_mode: AuthMode = AuthMode.TENANT,
    user_refresh_token: Optional[str] = None
)
```

**参数**:
- `app_id`: 飞书应用 ID
- `app_secret`: 飞书应用密钥
- `auth_mode`: 认证模式（TENANT 或 USER）
- `user_refresh_token`: 用户刷新令牌（auth_mode=USER 时需要）

#### from_env()

```python
@classmethod
def from_env(cls, env_file: Optional[str] = None) -> FeishuApiClient
```

从环境变量创建客户端。

**环境变量**:
- `FEISHU_APP_ID`: 应用 ID
- `FEISHU_APP_SECRET`: 应用密钥
- `FEISHU_AUTH_MODE`: 认证模式（tenant 或 user，默认：tenant）
- `FEISHU_USER_REFRESH_TOKEN`: 用户刷新令牌（auth_mode=user 时需要）

#### exchange_authorization_code()

```python
def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]
```

使用授权码换取用户访问令牌。

**返回**:
```python
{
    "access_token": "eyJhbGci...",
    "refresh_token": "ur-oQ0mMq6...",
    "expires_in": 7140,
    "name": "用户姓名",
    "open_id": "ou_xxx",
    "email": "user@example.com"
}
```

#### set_user_token()

```python
def set_user_token(
    self,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in: int = 7140
)
```

直接设置用户访问令牌。

#### get_user_token()

```python
def get_user_token(self, force_refresh: bool = False) -> str
```

获取或刷新用户访问令牌（自动缓存，线程安全）。

#### refresh_user_token()

```python
def refresh_user_token(self) -> str
```

使用刷新令牌获取新的访问令牌。

#### get_user_info()

```python
def get_user_info(self) -> Dict[str, Any]
```

获取当前用户信息。

**返回**:
```python
{
    "name": "用户姓名",
    "open_id": "ou_xxx",
    "email": "user@example.com",
    "user_id": "xxx",
    "mobile": "+86xxx"
}
```

#### generate_oauth_url()

```python
def generate_oauth_url(
    self,
    redirect_uri: str = "http://localhost:8080/callback",
    state: Optional[str] = None
) -> str
```

生成 OAuth 授权 URL。

---

## 常见问题

### Q1: 用户认证和应用认证有什么区别？

**A**:
- **应用认证**: 使用应用身份，资源属于应用，适合自动化
- **用户认证**: 使用用户身份，资源属于用户，适合个人操作

### Q2: 如何切换认证模式？

**A**: 编辑 `.env` 文件：

```bash
# 使用应用认证（默认）
FEISHU_AUTH_MODE=tenant

# 使用用户认证
FEISHU_AUTH_MODE=user
FEISHU_USER_REFRESH_TOKEN=ur-xxxxx
```

### Q3: 令牌过期了怎么办？

**A**: 用户访问令牌会自动刷新（如果在 5 分钟内过期）。刷新令牌有效期为 30 天，过期后需要重新运行 `setup_user_auth.py`。

### Q4: 可以同时使用两种模式吗？

**A**: 可以。创建不同的客户端实例：

```python
# 应用认证客户端
tenant_client = FeishuApiClient(app_id, app_secret, auth_mode=AuthMode.TENANT)

# 用户认证客户端
user_client = FeishuApiClient(app_id, app_secret, auth_mode=AuthMode.USER, user_refresh_token=...)
```

### Q5: 授权码可以重复使用吗？

**A**: 不可以。授权码只能使用一次，使用后立即失效。如果需要重新授权，请重新访问 OAuth URL。

### Q6: 如何配置生产环境的重定向 URI？

**A**: 在飞书开发者后台添加您的生产环境域名：

```
https://yourdomain.com/callback
```

然后使用自定义重定向 URI：
```bash
uv run python scripts/setup_user_auth.py
# 输入: https://yourdomain.com/callback
```

### Q7: 用户认证的安全性如何？

**A**:
- ✅ 刷新令牌加密存储
- ✅ 访问令牌仅 2 小时有效期
- ✅ 使用 HTTPS 传输
- ✅ 支持令牌撤销
- ⚠️ 请勿将 `FEISHU_USER_REFRESH_TOKEN` 提交到版本控制

### Q8: 如何撤销用户授权？

**A**: 在飞书客户端中：
1. 打开设置
2. 进入"飞书工作台"
3. 找到您的应用
4. 点击"撤销授权"

---

## 示例

### 示例 1: 创建个人文档

```python
from lib.feishu_api_client import FeishuApiClient

# 使用用户认证
client = FeishuApiClient.from_env()

# 创建文档到个人空间
result = client.create_document("我的个人文档")

print(f"文档 URL: {result['url']}")
# 文档属于您，而非应用
```

### 示例 2: 批量上传到个人 Wiki

```bash
# 设置完成后，直接运行
uv run python scripts/batch_create_wiki_docs.py ./docs --personal

# 所有文档将创建在您的个人知识库中
```

### 示例 3: 获取用户信息

```python
from lib.feishu_api_client import FeishuApiClient

client = FeishuApiClient.from_env()

if client.auth_mode == AuthMode.USER:
    user_info = client.get_user_info()
    print(f"当前用户: {user_info['name']}")
    print(f"邮箱: {user_info['email']}")
else:
    print("当前使用应用认证模式")
```

---

## 相关文档

- [API 操作参考](API_OPERATIONS.md)
- [快速开始指南](QUICK_START.md)
- [用户认证验证报告](../USER_AUTH_VERIFICATION_REPORT.md)

---

**最后更新**: 2026-01-18
**维护者**: Claude Code
**许可证**: MIT
