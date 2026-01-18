# Feishu-MCP 对齐实施报告

**实施日期**: 2026-01-19
**状态**: ✅ 已完成核心改进
**目标**: 向 Feishu-MCP 项目对齐，修复 user 认证模式

---

## 📋 背景

根据用户需求：
1. 向 Feishu-MCP 对齐 user 类型的实现
2. 当前实现的 user 模式不能正常工作
3. 参考最近的 commit 发现的问题
4. 借鉴 Feishu-MCP 的实现并验证

### 核心问题发现

根据 commit `3a346e1` 的分析，主要问题是：

1. **Scope 权限未申请** - 代码请求的 scope 包含了应用未开通的权限
2. **Token 端点缺少 redirect_uri** - 虽然文档说是可选的，但最佳实践是传递
3. **配置命名不一致** - 与 Feishu-MCP 使用不同的环境变量名

---

## ✅ 已实施的改进

### 1. 统一环境变量命名

**问题**:
- Feishu-MCP 使用 `FEISHU_AUTH_TYPE`
- feishu-doc-tools 使用 `FEISHU_AUTH_MODE`

**解决方案**:
同时支持两个环境变量，优先使用 `FEISHU_AUTH_TYPE` (兼容 Feishu-MCP)

```python
# lib/feishu_api_client.py:266-270
# Support both FEISHU_AUTH_TYPE (compatible with Feishu-MCP) and FEISHU_AUTH_MODE
auth_mode_str = os.environ.get("FEISHU_AUTH_TYPE") or os.environ.get("FEISHU_AUTH_MODE", "tenant")
auth_mode_str = auth_mode_str.lower()
auth_mode = AuthMode.USER if auth_mode_str == "user" else AuthMode.TENANT
```

**影响的文件**:
- ✅ `lib/feishu_api_client.py` - 核心逻辑
- ✅ `.env.example` - 配置示例

---

### 2. 修复 Token 端点 - 添加 redirect_uri

**问题**:
token 交换请求缺少 `redirect_uri` 参数，可能导致错误码 20071

**解决方案**:
在 `exchange_authorization_code` 方法中添加 `redirect_uri` 参数

```python
# lib/feishu_api_client.py:384-386
def exchange_authorization_code(
    self, authorization_code: str, redirect_uri: str = "http://localhost:3333/callback"
) -> Dict[str, Any]:
```

```python
# lib/feishu_api_client.py:421-428
payload = {
    "grant_type": "authorization_code",
    "client_id": self.app_id,
    "client_secret": self.app_secret,
    "code": authorization_code,
    "redirect_uri": redirect_uri,  # Required: must match authorization request
}
```

**影响的文件**:
- ✅ `lib/feishu_api_client.py` - 添加 redirect_uri 参数和逻辑
- ✅ `scripts/setup_user_auth.py` - 传递 redirect_uri 到方法调用

---

### 3. 更新文档和配置

**更新的文档注释**:
- ✅ 添加 redirect_uri 必须一致的说明
- ✅ 引用飞书官方文档错误码 20071
- ✅ 更新方法签名和示例

**更新的配置文件** (`.env.example`):
```bash
# Both FEISHU_AUTH_TYPE and FEISHU_AUTH_MODE are supported (compatible with Feishu-MCP)
# FEISHU_AUTH_TYPE=tenant
# FEISHU_AUTH_MODE=tenant
```

---

## 🔍 与 Feishu-MCP 的对比

| 特性 | Feishu-MCP | feishu-doc-tools (改进前) | feishu-doc-tools (改进后) |
|------|------------|--------------------------|-------------------------|
| **环境变量** | `FEISHU_AUTH_TYPE` | `FEISHU_AUTH_MODE` | ✅ 两者都支持 |
| **Token 端点** | 包含 `redirect_uri` | ❌ 缺少 | ✅ 已添加 |
| **OAuth 流程** | 完整回调服务器 | 命令行流程 | 保持命令行流程 |
| **Token 缓存** | 文件缓存管理器 | 环境变量存储 | 保持环境变量 |
| **State 参数** | Base64 编码 JSON | 简单字符串 | 保持简单字符串 |

### 核心对齐点

✅ **已对齐**:
1. 环境变量命名（支持两种）
2. Token 端点参数（添加 redirect_uri）
3. 认证模式选择逻辑

⚠️ **差异保留**（设计差异，非问题）:
1. OAuth 回调方式：Feishu-MCP 使用 Express 服务器，feishu-doc-tools 使用命令行手动流程
2. Token 存储：Feishu-MCP 使用文件缓存，feishu-doc-tools 使用环境变量
3. State 参数格式：两者都有效，只是实现方式不同

---

## 🔧 核心 Scope 权限问题

**根本问题** (来自 commit 3a346e1):

代码请求的 scope:
```python
scope = "docx:document docx:document:readonly wiki:wiki:readonly offline_access"
```

**可能的问题**:
1. 这些权限可能未在飞书后台申请
2. Scope 参数格式可能不正确

**诊断方法** (已在 `OAUTH_SCOPE_PERMISSION_ISSUE.md` 中详细说明):

1. 登录飞书开发者后台
2. 检查 **开发配置 > 权限管理 > API 权限**
3. 确认所需权限是否已申请：
   - `docx:document`
   - `docx:document:readonly`
   - `wiki:wiki:readonly`
   - `offline_access`

**解决方案**:
- 如果权限未申请 → 申请权限并等待审核
- 如果权限已申请 → 检查应用状态和用户权限

---

## 📝 使用指南

### 配置 User 认证模式

#### 方式 1: 使用 FEISHU_AUTH_TYPE (兼容 Feishu-MCP)

```bash
# .env
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_AUTH_TYPE=user
FEISHU_USER_REFRESH_TOKEN=ur-xxxxx
```

#### 方式 2: 使用 FEISHU_AUTH_MODE (原有方式)

```bash
# .env
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_AUTH_MODE=user
FEISHU_USER_REFRESH_TOKEN=ur-xxxxx
```

### 设置 User 认证

```bash
# 运行设置脚本
uv run python scripts/setup_user_auth.py

# 脚本会：
# 1. 生成授权 URL
# 2. 引导你完成授权流程
# 3. 交换授权码为访问令牌（现在包含 redirect_uri）
# 4. 自动保存 refresh_token 到 .env
```

---

## ✅ 验证清单

### 代码层面
- [x] 同时支持 `FEISHU_AUTH_TYPE` 和 `FEISHU_AUTH_MODE`
- [x] `exchange_authorization_code` 接受 `redirect_uri` 参数
- [x] Token 请求 payload 包含 `redirect_uri`
- [x] `setup_user_auth.py` 传递 `redirect_uri`
- [x] 更新文档注释和错误码引用

### 配置层面
- [x] `.env.example` 包含两种环境变量说明
- [x] 注释清晰说明兼容性

### 文档层面
- [x] 创建本实施报告
- [x] 引用已有的 `OAUTH_SCOPE_PERMISSION_ISSUE.md`

### 待测试
- [ ] 实际运行 `setup_user_auth.py` 脚本
- [ ] 验证 token 交换是否成功
- [ ] 验证 user 模式的 API 调用
- [ ] 测试与 Feishu-MCP 共享 .env 文件的场景

---

## 🚀 下一步行动

### 立即行动

1. **验证权限申请**
   ```bash
   # 检查飞书后台权限状态
   # 应用 > 开发配置 > 权限管理 > API 权限
   ```

2. **测试 User 认证**
   ```bash
   # 使用改进后的脚本
   uv run python scripts/setup_user_auth.py
   ```

3. **验证功能**
   ```bash
   # 运行测试脚本
   uv run python scripts/test_api_connectivity.py
   ```

### 可选改进

以下改进不是必需的，但可以进一步提升与 Feishu-MCP 的对齐：

1. **Token 文件缓存** - 参考 Feishu-MCP 的 `TokenCacheManager`
2. **State 参数编码** - 使用 Base64 编码的 JSON（增强安全性）
3. **OAuth 回调服务器** - 实现简单的 HTTP 服务器自动接收回调

---

## 📊 改进总结

### 修改的文件

| 文件 | 行数变化 | 主要改进 |
|------|---------|---------|
| `lib/feishu_api_client.py` | +10/-5 | 环境变量对齐、添加 redirect_uri |
| `scripts/setup_user_auth.py` | +1/-1 | 传递 redirect_uri 参数 |
| `.env.example` | +3/-2 | 添加 FEISHU_AUTH_TYPE 说明 |
| `FEISHU_MCP_ALIGNMENT.md` | +340/+0 | 新建本报告 |

### 向后兼容性

✅ **100% 向后兼容**:
- 原有的 `FEISHU_AUTH_MODE` 仍然有效
- `exchange_authorization_code` 的 `redirect_uri` 有默认值
- 所有改进都是增量式的，不会破坏现有代码

---

## 🔗 相关文档

- [OAUTH_SCOPE_PERMISSION_ISSUE.md](./OAUTH_SCOPE_PERMISSION_ISSUE.md) - Scope 权限问题诊断
- [.env.example](./.env.example) - 配置示例
- [scripts/setup_user_auth.py](./scripts/setup_user_auth.py) - User 认证设置脚本

---

## 🤝 致谢

本改进参考了：
- Feishu-MCP 项目的实现（[@Feishu-MCP](../Feishu-MCP)）
- 飞书官方 OAuth 文档
- 项目最近的 commit 分析（特别是 commit 3a346e1）

---

**维护者**: Claude (with User)
**最后更新**: 2026-01-19
**版本**: 1.0
