# Session Flow Documentation

## Complete Session Lifecycle

This document describes the detailed session flow from initial login through logout, including error scenarios and recovery paths.

## 1. Initial App Load (No Session)

### Scenario: User visits app for first time or clears localStorage

```
┌─ App Loads
├─ Layout renders: <Providers>
├─ AuthProvider initializes
│  └─ useEffect runs: initializeSession()
│
│  ┌─ Check localStorage for tokens
│  ├─ No tokens found
│  └─ Set status to "unauthenticated", isLoading to false
│
├─ Router checks route group
├─ If route is (app):
│  └─ ProtectedAppLayout renders
│     └─ useProtectedRoute() runs
│        ├─ Sees status = "unauthenticated"
│        └─ Redirects to /login?redirect=/intended-route
├─ If route is (auth):
│  └─ Renders page (e.g., LoginForm)
│
└─ User now on login page
```

### Code Flow

```typescript
// AuthProvider.tsx - useEffect on mount
useEffect(() => {
  const initializeSession = async () => {
    store.setLoading(true);
    
    // Check if tokens exist in localStorage
    const accessToken = store.getAccessToken();
    
    if (!accessToken) {
      // No session - user is guest
      store.setLoading(false);
      return;
    }
    
    // Token exists - fetch current user
    try {
      const response = await authService.getCurrentUser();
      if (response.status === 200 && response.data) {
        store.setUser(response.data);
      }
    } catch (_error) {
      // Failed to get user - clear session
      store.clearAuth();
    } finally {
      store.setLoading(false);
    }
  };
  
  initializeSession();
}, []); // Runs once on mount
```

## 2. Login Flow

### Scenario: User enters email/password and clicks "Sign In"

```
┌─ User on login page (/login)
│  └─ GuestLoginPage component
│     └─ useGuestRoute() confirms not authenticated
│        └─ Shows LoginForm
│
├─ User enters email: user@example.com
├─ User enters password: ••••••••••
├─ User clicks "Sign In"
│
├─ LoginForm validates:
│  ├─ Email format valid? ✓
│  ├─ Password minimum 6 chars? ✓
│  └─ Form valid? ✓ → Button enabled
│
├─ Form calls useAuth().login(email, password)
│
├─ AuthProvider.login():
│  ├─ Set isLoading = true
│  │
│  ├─ Call authService.signIn(email, password)
│  │  └─ POST /auth/sign-in
│  │     ├─ Body: { email, password }
│  │     └─ Response: {
│  │        access_token: "eyJ...",
│  │        refresh_token: "eyJ...",
│  │        expires_at: "2024-12-01T12:00:00Z"
│  │     }
│  │
│  ├─ Call authService.getCurrentUser()
│  │  └─ GET /auth/me
│  │     ├─ Header: Authorization: Bearer {access_token}
│  │     └─ Response: {
│  │        id: "user-123",
│  │        email: "user@example.com",
│  │        full_name: "John Doe"
│  │     }
│  │
│  ├─ Store session:
│  │  ├─ store.setAuth(session, user)
│  │  └─ Writes to localStorage: auth-storage = {
│  │     state: {
│  │       accessToken: "eyJ...",
│  │       refreshToken: "eyJ...",
│  │       expiresAt: "2024-12-01T12:00:00Z",
│  │       user: { id, email, full_name },
│  │       userId: "user-123",
│  │       isAuthenticated: true
│  │     }
│  │  }
│  │
│  ├─ Get redirect URL from query params
│  ├─ Router.push(redirect || '/dashboard')
│  │
│  └─ Set isLoading = false
│
├─ User redirected to /dashboard
├─ (app) layout renders
├─ ProtectedAppLayout wraps AppShell
├─ useProtectedRoute() confirms authenticated
└─ Dashboard page displays with user data
```

### Store State After Login

```typescript
{
  accessToken: "eyJ0eXAiOiJKV1QiLCJhbGc...",
  refreshToken: "eyJ0eXAiOiJKV1QiLCJhbGc...",
  expiresAt: "2024-12-01T12:00:00Z",
  user: {
    id: "user-123",
    email: "user@example.com",
    full_name: "John Doe"
  },
  userId: "user-123",
  isAuthenticated: true,
  isLoading: false,
  error: null,
  status: "authenticated"
}
```

### localStorage Content

```json
{
  "auth-storage": {
    "state": {
      "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "expiresAt": "2024-12-01T12:00:00Z",
      "user": {
        "id": "user-123",
        "email": "user@example.com",
        "full_name": "John Doe"
      },
      "userId": "user-123"
    }
  }
}
```

## 3. Session Persistence (Page Refresh)

### Scenario: User on dashboard, refreshes page

```
┌─ User presses F5 to refresh
│  └─ Page reloads
│
├─ App/layout.tsx re-renders
├─ Providers components re-mount
├─ AuthProvider useEffect runs again
│
│  ┌─ Check localStorage for tokens
│  ├─ Tokens found:
│  │  ├─ accessToken: "eyJ..."
│  │  ├─ expiresAt: "2024-12-01T12:00:00Z"
│  │
│  ├─ Check if token expired:
│  │  ├─ Current time: 2024-12-01T11:50:00Z
│  │  └─ expiresAt: 2024-12-01T12:00:00Z
│  │  └─ Not expired ✓
│  │
│  ├─ Set isLoading = true
│  ├─ Fetch current user with token
│  │  └─ GET /auth/me
│  │     ├─ Header: Authorization: Bearer {token}
│  │     └─ Response: { id, email, full_name }
│  │
│  ├─ Update store.user with fresh data
│  ├─ Store still has session
│  └─ Set isLoading = false
│
├─ Route is (app) → Protected
├─ ProtectedAppLayout wraps AppShell
├─ useProtectedRoute() sees:
│  ├─ status = "authenticated"
│  ├─ isLoading = true initially
│  └─ After check: isLoading = false, canAccess = true
│
├─ AppShell renders
├─ UserMenu shows user name: "John Doe"
└─ User continues working seamlessly
```

### State During Refresh

```typescript
// During initialization:
{
  ...,
  isLoading: true,
  status: "loading"
}

// After restoration:
{
  ...,
  isLoading: false,
  status: "authenticated",
  user: { /* fresh data from server */ }
}
```

## 4. Automatic Token Refresh (Mid-Request)

### Scenario: Token expires while user is making API call

```
Timeline:
├─ 11:45 - User logs in
│  └─ Token expires at: 12:00
│
├─ 11:55 - User clicks "Save"
│  ├─ Component makes API call: api.post("/api/save", data)
│  │
│  │  ┌─ ApiClient Interceptor (Request)
│  │  ├─ Get token from localStorage: "eyJ..."
│  │  ├─ Add header: Authorization: Bearer eyJ...
│  │  └─ Send POST /api/save
│  │
│  ├─ Backend receives request at: 11:56
│  ├─ Token is still valid ✓
│  └─ Process request normally
│
├─ 12:05 - User modifies data
│  ├─ Component makes API call: api.get("/api/data")
│  │
│  │  ┌─ ApiClient Interceptor (Request)
│  │  ├─ Get token from localStorage: "eyJ..."
│  │  ├─ Token valid at request time ✓
│  │  ├─ Send GET /api/data with token
│  │  │
│  │  └─ Backend receives at 12:06
│  │     ├─ Checks token
│  │     ├─ Token expired (expires_at was 12:00)
│  │     └─ Return 401 Unauthorized
│  │
│  │  ┌─ ApiClient Interceptor (Response)
│  │  ├─ See 401 status
│  │  ├─ Check if first attempt (not _retry=true)
│  │  ├─ Check if refreshPromise already in progress
│  │  │  └─ No refresh in progress
│  │  │
│  │  ├─ Mark request: _retry = true
│  │  ├─ Set refreshPromise = refreshAccessToken()
│  │  │
│  │  │  ┌─ refreshAccessToken():
│  │  │  ├─ Get refreshToken from localStorage
│  │  │  ├─ POST /auth/refresh
│  │  │  │  ├─ Body: { refresh_token: "eyJ..." }
│  │  │  │  └─ Response: {
│  │  │  │     access_token: "eyJ...NEW",
│  │  │  │     refresh_token: "eyJ...NEW",
│  │  │  │     expires_at: "2024-12-01T12:15:00Z"
│  │  │  │  }
│  │  │  │
│  │  │  ├─ Update localStorage with new tokens
│  │  │  ├─ Return new access token
│  │  │  └─ Clear refreshPromise = null
│  │  │
│  │  ├─ Get new token from Promise
│  │  ├─ Update Authorization header: Bearer eyJ...NEW
│  │  ├─ Retry original request: GET /api/data
│  │  │
│  │  └─ Backend receives at 12:06:01
│  │     ├─ Checks new token
│  │     ├─ Token valid ✓
│  │     └─ Return 200 with data
│  │
│  │  ┌─ Return response to component
│  │  └─ Component receives data successfully
│  │
│  └─ User sees fresh data
│
└─ Process transparent to user
```

### Code Flow for Refresh

```typescript
// Response interceptor in ApiClient
this.client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Check for 401 and first attempt
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If refresh already in progress, wait for it
      if (this.refreshPromise) {
        try {
          const newToken = await this.refreshPromise;
          if (newToken && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return this.client(originalRequest);
        } catch {
          return Promise.reject(error);
        }
      }

      // Mark as retry to prevent infinite loop
      originalRequest._retry = true;

      // Start refresh
      this.refreshPromise = this.refreshAccessToken();

      try {
        const newToken = await this.refreshPromise;
        this.refreshPromise = null;

        if (newToken && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        // Retry with new token
        return this.client(originalRequest);
      } catch {
        // Refresh failed
        this.clearTokens();
        this.refreshPromise = null;
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);
```

## 5. Concurrent Requests with Token Refresh

### Scenario: Multiple API calls made simultaneously with expired token

```
Timeline (overlapping requests):

Request 1: api.get("/api/users")
Request 2: api.get("/api/settings")
Request 3: api.get("/api/profile")
All sent at: 12:05, Token expires at: 12:00

┌─ Request 1 gets 401
│  ├─ Check: refreshPromise = null? YES
│  ├─ Mark _retry = true
│  └─ Create: refreshPromise = refreshAccessToken()
│     └─ Start: POST /auth/refresh
│
├─ Request 2 gets 401 (while refresh in progress)
│  ├─ Check: refreshPromise = null? NO (refresh still running)
│  ├─ Wait for existing: await this.refreshPromise
│  └─ When complete: Use new token, retry request
│
├─ Request 3 gets 401 (while refresh in progress)
│  ├─ Check: refreshPromise = null? NO (refresh still running)
│  ├─ Wait for existing: await this.refreshPromise
│  └─ When complete: Use new token, retry request
│
├─ Backend completes refresh for Request 1
├─ POST /auth/refresh returns new token
│  ├─ refreshPromise resolves with token
│  ├─ Request 2 gets token from Promise
│  ├─ Request 3 gets token from Promise
│  ├─ All three retry with same new token
│  │
│  └─ refreshPromise = null
│
├─ Request 1, 2, 3 all retry simultaneously
├─ All succeed with new token (200 OK)
│
└─ Results returned to components
   └─ All three API calls complete successfully
```

### Why This Matters

Without concurrent request guard:
```typescript
// ❌ PROBLEM: Each request starts its own refresh
Request 1: POST /auth/refresh (creates token T1)
Request 2: POST /auth/refresh (creates token T2)
Request 3: POST /auth/refresh (creates token T3)
Result: 3 unnecessary refresh requests, possible rate limiting

// ✓ SOLUTION: Share refresh Promise
Request 1: POST /auth/refresh (creates token T1)
Request 2: Waits for Request 1's Promise
Request 3: Waits for Request 1's Promise
Result: 1 refresh request, all use same token
```

## 6. Logout Flow

### Scenario: User clicks "Sign Out"

```
┌─ User in UserMenu (top-right)
├─ Clicks "Sign Out"
│
├─ UserMenu calls useAuth().logout()
│
├─ AuthProvider.logout():
│  ├─ Set isLoading = true
│  │
│  ├─ Try to sign out on backend (best-effort):
│  │  ├─ Get refreshToken from store
│  │  └─ POST /auth/sign-out
│  │     ├─ Body: { refresh_token }
│  │     └─ Ignore errors (fire-and-forget)
│  │        └─ (Backend will invalidate refresh token)
│  │
│  ├─ Clear auth locally:
│  │  ├─ store.clearAuth()
│  │  ├─ Clears localStorage
│  │  └─ Sets store state:
│  │     └─ {
│  │        accessToken: null,
│  │        refreshToken: null,
│  │        user: null,
│  │        isAuthenticated: false,
│  │        status: "unauthenticated"
│  │     }
│  │
│  ├─ Redirect to /login
│  └─ Set isLoading = false
│
├─ Page navigates to /login
├─ (auth) route group → guest route
├─ GuestLoginPage renders
│  └─ useGuestRoute() confirms not authenticated
│     └─ Show LoginForm
│
└─ User back at login screen
```

### Store State After Logout

```typescript
{
  accessToken: null,
  refreshToken: null,
  expiresAt: null,
  user: null,
  userId: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  status: "unauthenticated"
}
```

### localStorage After Logout

```json
{
  "auth-storage": {
    "state": {
      "accessToken": null,
      "refreshToken": null,
      "expiresAt": null,
      "user": null,
      "userId": null
    }
  }
}
```

## 7. Error Scenarios

### 7a. Invalid Login Credentials

```
User enters: email@example.com / wrongpassword

┌─ Form calls login(email, password)
├─ POST /auth/sign-in with credentials
├─ Backend validates
├─ Credentials invalid → 401 Unauthorized
│  └─ Response: { error: "Invalid email or password" }
│
├─ AuthProvider catches error
├─ Sets store.error = "Invalid email or password"
├─ Shows error message in LoginForm
│
└─ User can retry
```

### 7b. Network Error During Login

```
User attempts login but network is down

┌─ Form calls login(email, password)
├─ POST /auth/sign-in attempted
├─ Network error (no response)
├─ Axios catches: Error "Network Error"
│
├─ AuthProvider catches error
├─ Sets store.error = "Network Error"
├─ LoginForm shows error
│
└─ User can retry when network available
```

### 7c. Refresh Token Expired/Invalid

```
User has session, makes API call, but refresh token is invalid

Timeline:
├─ 11:45 - User logs in
│  ├─ accessToken expires: 12:00
│  └─ refreshToken expires: 12-07 (7 days)
│
├─ 12-06 23:00 - Token actually expires (not just access, both)
│
├─ 12-07 09:00 - User returns next day
├─ Page loads, AuthProvider initializes
│  ├─ Tokens found in localStorage
│  ├─ GET /auth/me with access token
│  ├─ 401 response (both tokens expired)
│  └─ ApiClient tries refresh
│
│  ├─ POST /auth/refresh with refreshToken
│  │  └─ Backend: "Refresh token invalid/expired"
│  │  └─ 401 response
│  │
│  ├─ Refresh fails
│  ├─ clearTokens() removes all tokens from localStorage
│  ├─ AuthProvider catches error
│  ├─ Clears auth completely
│  └─ Redirects to /login
│
└─ User must re-login
```

### 7d. Token Tampered/Invalid

```
Attacker modifies token in localStorage: "eyJ..." → "XXX..."

┌─ User makes API call
├─ ApiClient adds invalid token: Authorization: Bearer XXX...
├─ Backend: "Invalid token" → 401
├─ ApiClient tries refresh
│  ├─ POST /auth/refresh with invalid refreshToken
│  └─ 401: "Invalid refresh token"
│
├─ Refresh fails
├─ clearTokens() wipes localStorage
├─ AuthProvider catches error
├─ Clears auth, redirects to /login
│
└─ User must re-login with credentials
```

### 7e. Session Timeout on Logout

```
Backend signs out user, but frontend doesn't know yet

┌─ Admin revokes user's refresh token on backend
├─ User continues working (unaware)
├─ Makes API call
│  ├─ Request succeeds (access token still valid)
│
├─ Later: Access token expires
├─ User makes another API call
│  ├─ 401 Unauthorized
│  ├─ ApiClient tries refresh
│  │  ├─ POST /auth/refresh
│  │  └─ 401: "Refresh token revoked"
│  │
│  ├─ Refresh fails
│  ├─ clearTokens() wipes localStorage
│  ├─ Clears auth, redirects to /login
│  │
│  └─ User is forced to re-login
│
└─ Session cleanly ended
```

## 8. Protected Route Redirect Flow

### Scenario: Unauthenticated user tries to access /dashboard

```
┌─ User types: localhost:3000/dashboard
├─ Next.js Router recognizes: (app) route group
├─ Loads app/(app)/layout.tsx
│  ├─ Component: ProtectedAppLayout
│  └─ Calls: useProtectedRoute()
│
│  ├─ Check: useAuth().status
│  │  └─ "unauthenticated" (or "loading")
│  │
│  ├─ Set: isLoading = true
│  ├─ Get: currentUrl = "/dashboard"
│  ├─ Call: router.push("/login?redirect=/dashboard")
│  │  └─ Navigate to login
│  │
│  └─ Return: { isLoading: true, canAccess: false }
│
├─ ProtectedAppLayout sees canAccess = false
├─ Shows loading spinner (brief)
├─ URL changes to: /login?redirect=/dashboard
├─ (auth) route group loads
├─ GuestLoginPage renders
│  └─ useGuestRoute() confirms not authenticated
│     └─ Shows LoginForm
│
├─ User logs in successfully
├─ AuthProvider.login() reads redirect param
├─ Redirects to: /dashboard (from query param)
├─ User now authenticated, route loads normally
│
└─ User sees dashboard
```

### Code Flow for Route Protection

```typescript
// hooks/use-route-protection.ts
export function useProtectedRoute() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading, status } = useAuth();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Still loading auth state
    if (authLoading) {
      setIsLoading(true);
      return;
    }

    // Auth check complete
    if (!isAuthenticated) {
      // Not authenticated - redirect to login
      const currentUrl = window.location.pathname + window.location.search;
      const redirectUrl = `/login?redirect=${encodeURIComponent(currentUrl)}`;
      router.push(redirectUrl);
      setIsLoading(true);
      return;
    }

    // Authenticated - allow access
    setIsLoading(false);
  }, [authLoading, isAuthenticated, router]);

  return {
    isLoading,
    canAccess: isAuthenticated && !authLoading,
  };
}
```

## State Machine Summary

```
                    ┌─────────────────┐
                    │  No Session     │
                    │ (Guest)         │
                    └────────┬────────┘
                             │
                             │ User clicks "Sign In"
                             ▼
                    ┌─────────────────┐
                    │  Loading        │
                    │ (Signing In)    │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           │ Success        │ Error            │ Error
           │                 │                 │
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Authenticated│  │ Error State  │  │ No Session   │
    │ (Session OK) │  │ (Show Error) │  │ (Retry)      │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                 │
           │ (API requests)  │ User retries   │
           │                 │                 │
           │ Token expires   │                 │
           │ during request  │                 │
           │                 │                 │
           └────────┬────────┴─────────────────┘
                    │
                    │ Refresh token (auto)
                    ▼
            ┌──────────────────┐
            │ Authenticated    │
            │ (Continued)      │
            └────────┬─────────┘
                     │
                     │ User clicks logout
                     │
                     ▼
            ┌──────────────────┐
            │ No Session       │
            │ (Logged Out)     │
            └──────────────────┘
```

## Summary Table

| Flow | Trigger | Duration | Result |
|------|---------|----------|--------|
| Initial Load | App mounts | <1s | Status set (auth/guest) |
| Login | User submits form | 1-3s | Session created, user redirected |
| Session Persist | Page refresh | <1s | Session restored, user continues |
| Auto Refresh | API 401 during use | <500ms | Token refreshed, request retried |
| Logout | User clicks logout | <1s | Session cleared, redirected to login |
| Route Protection | Navigate to protected | <1s | Redirected to login if not auth |

## Testing Checklist

- [ ] Login with valid credentials → redirected to dashboard
- [ ] Login with invalid credentials → error message shown
- [ ] Logout → redirected to login, session cleared
- [ ] Page refresh with valid token → session restored
- [ ] Page refresh with expired token → auto-refresh works
- [ ] Access protected route without auth → redirected to login
- [ ] Access login page while authenticated → redirected to dashboard
- [ ] Multiple API calls with expired token → only 1 refresh request made
- [ ] Network error during login → error message shown
- [ ] Token manually cleared from storage → forced logout on next request
