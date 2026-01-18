# OAuth v2 API Migration & Debugging Session

**Migration Date**: 2026-01-18
**Status**: ⚠️ Partial - Awaiting Feishu Official Support

---

## 📋 Executive Summary

Migrated Feishu OAuth integration from legacy v1 API to OAuth v2 API with comprehensive user authentication support. Fixed **2 confirmed bugs** (URL encoding, port configuration) but **authorization still fails** with misleading "state parameter format error" - awaiting consultation with Feishu official support.

### Key Findings

| Issue | Status | Root Cause |
|-------|--------|------------|
| URL Encoding Bug | ✅ **Fixed** | Only `redirect_uri` encoded; `scope` had unencoded spaces |
| Port Mismatch (Error 20029) | ✅ **Fixed** | Code used 8080, Feishu backend configured for 3333 |
| State Parameter Format | ⚠️ **Not the Issue** | All 6 tested formats failed; error is misleading |
| Authorization Failure | ⚠️ **Unresolved** | Likely app configuration/permissions in Feishu backend |

---

## ✅ Fixes Applied

### Fix #1: URL Encoding (RFC 3986 Compliance)

**Problem**: OAuth URL generation only encoded `redirect_uri`, leaving `scope` with unencoded spaces.

**File**: `lib/feishu_api_client.py:645-663`

```python
# Before (BROKEN)
params = {
    "client_id": self.app_id,
    "redirect_uri": quote(redirect_uri, safe=''),  # Only this encoded
    "scope": scope,  # ❌ Contains unencoded spaces!
    "response_type": "code",
    "state": state,
}
url += "&".join([f"{k}={v}" for k, v in params.items()])

# After (FIXED)
params = {
    "client_id": self.app_id,
    "redirect_uri": redirect_uri,
    "scope": scope,
    "response_type": "code",
    "state": state,
}
# Encode ALL parameter values per RFC 3986
url += "&".join([f"{k}={quote(str(v), safe='')}" for k, v in params.items()])
```

**Result**: `scope` spaces now encoded as `%20` instead of literal spaces.

---

### Fix #2: Redirect URI Port Unification

**Problem**: Port mismatch causing error 20029.
- Feishu backend: `http://localhost:3333/callback`
- Code default: `http://localhost:8080/callback`

**Files Modified**:
- `lib/feishu_api_client.py`
- `scripts/verify_user_auth.py`
- `scripts/setup_user_auth.py`

**Result**: Error 20029 resolved; redirect URI validation passes.

---

### Feature: OAuth v2 API Implementation

**Added to `lib/feishu_api_client.py`**:

- `AuthMode` enum (TENANT vs USER authentication modes)
- User authentication methods:
  - `set_user_token()` - Set user credentials
  - `exchange_authorization_code()` - Exchange code for tokens
  - `refresh_user_access_token()` - Refresh expired tokens
  - `get_user_info()` - Get authenticated user profile
- Support for both API versions:
  - **Old**: `https://open.feishu.cn/open-apis/authen/v1/index` (uses `app_id`)
  - **New**: `https://accounts.feishu.cn/open-apis/authen/v1/authorize` (uses `client_id`)

---

## ⚠️ Outstanding Issue: State Parameter Error

### Symptom
Authorization URL returns HTTP 400: "state parameter format error"

### Investigation Results

**All state formats failed**:

| Format | Result |
|--------|--------|
| Empty string (official SDK default) | ❌ Fail |
| Pure numeric (current impl) | ❌ Fail |
| Alphanumeric 16 chars | ❌ Fail |
| Alphanumeric 32 chars | ❌ Fail |
| URL-safe base64 | ❌ Fail |
| Pure letters | ❌ Fail |

**Both API versions failed**:
- Old API with `app_id` → Fail
- New API with `client_id` → Fail

### Root Cause Hypothesis

**Problem is NOT state format.** Likely issues:

1. **Application Configuration** - App may not have user authorization enabled
2. **Missing Permissions** - User permissions not applied in Feishu backend
3. **Application Type** - App type may not support OAuth user authentication
4. **Misleading Error** - Feishu API returns "state error" for unrelated issues

### Diagnostic URLs for Testing

**Test WITHOUT state parameter**:

```bash
# Old API (no state)
https://open.feishu.cn/open-apis/authen/v1/index?redirect_uri=http%3A%2F%2Flocalhost%3A3333%2Fcallback&app_id=cli_a9e09cc76d345bb4

# New API (no state, minimal scope)
https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=cli_a9e09cc76d345bb4&redirect_uri=http%3A%2F%2Flocalhost%3A3333%2Fcallback&scope=contact%3Auser.base%3Areadonly&response_type=code
```

### Feishu Backend Configuration Checklist

**Before contacting support, verify**:

- [ ] Application Type: Self-built or Store app?
- [ ] Application Status: Enabled or Disabled?
- [ ] Has "Redirect URL" configuration section?
- [ ] Configured redirect URI: `http://localhost:3333/callback`
- [ ] User permissions applied (e.g., `contact:user.base:readonly`)?
- [ ] Application available to: This enterprise only or All enterprises?

### Information for Feishu Support

```
Application Configuration:
-----------------------
App ID: cli_a9e09cc76d345bb4
App Type: [Self-built/Store]
App Status: [Enabled/Disabled]
Has "Redirect URL" config: [Yes/No]
Configured Redirect URIs: [List all]

Permission Configuration:
-----------------------
Has User Permissions: [Yes/No]
Applied Permissions: [List all]

Error Information:
-----------------
Error Code: 400
Error Description: state parameter format error
Log ID: [Provide if available]
Appearance: [When opening URL / After clicking authorize]
Complete URL: [Provide full browser URL]
```

---

## 📁 Files Changed

### Modified
- `lib/feishu_api_client.py` - OAuth v2 implementation, URL encoding fix, port unification
- `scripts/verify_user_auth.py` - Port configuration update
- `scripts/setup_user_auth.py` - Port configuration update  
- `.env.example` - Added FEISHU_AUTH_MODE, FEISHU_USER_REFRESH_TOKEN

### Added
- `scripts/diagnose_oauth.py` - Diagnostic tool for OAuth troubleshooting
- `docs/user/USER_AUTH_GUIDE.md` - User authentication usage guide
- `test_oauth_url.py` - OAuth URL generation test script
- `tests/test_user_auth.py` - User authentication tests

### Removed (Consolidated)
- `OAUTH_20043_FIX.md` → Consolidated into this doc
- `OAUTH_REDIRECT_URI_SETUP.md` → Consolidated
- `OAUTH_URL_ENCODING_FIX.md` → Consolidated
- `REDIRECT_URI_PORT_FIX.md` → Consolidated
- `USER_AUTH_VERIFICATION_REPORT.md` → Consolidated
- `test_state_formats.py` - Temporary test script
- `test_api_versions.py` - Temporary test script
- `OAUTH_TROUBLESHOOTING_CHECKLIST.md` → Consolidated into this doc

---

## 🔗 References

- [Feishu: Get Authorization Code](https://open.feishu.cn/document/common-capabilities/sso/api/obtain-oauth-code)
- [Feishu: Get User Access Token](https://open.feishu.cn/document/common-capabilities/sso/api/get-user-access-token)
- [Feishu: Refresh User Access Token](https://open.feishu.cn/document/common-capabilities/sso/api/refresh-user-access-token)
- [RFC 3986: URI Generic Syntax](https://datatracker.ietf.org/doc/html/rfc3986)
- [RFC 6749: OAuth 2.0 Framework](https://datatracker.ietf.org/doc/html/rfc6749)

---

**Session Date**: 2026-01-18  
**Status**: ⚠️ Awaiting Feishu Official Support  
**Next Action**: Consult Feishu support with diagnostic information from this session
