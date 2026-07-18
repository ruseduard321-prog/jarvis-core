# Authentication Architecture

## Overview

The Jarvis Core authentication system provides a complete, production-ready implementation of user authentication with session management, automatic token refresh, and protected routes. The system integrates with the existing FastAPI backend and uses modern React patterns with Zustand for state management.

### Design Principles

- **No Mock Authentication**: All authentication is handled by the backend; no mocked/client-side-only auth
- **Automatic Token Refresh**: Expired tokens are automatically refreshed transparently
- **Stateless API**: Tokens are persisted locally and sent with each request
- **Session Preservation**: User session is restored on page refresh
- **Route Protection**: Authenticated routes are protected; guest routes redirect authenticated users
- **Error Recovery**: Graceful handling of token expiration, refresh failures, and auth errors

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Application                        │
├─────────────────────────────────────────────────────────────┤
│  Providers (Root)                                            │
│  ├─ QueryClientProvider                                     │
│  ├─ AuthProvider (Session Init & Token Refresh)             │
│  ├─ ThemeProvider                                           │
│  └─ Toaster                                                 │
├─────────────────────────────────────────────────────────────┤
│  Route Groups                                               │
│  ├─ /auth (Public Routes)                                   │
│  │  └─ /login (GuestLoginPage with route protection)        │
│  └─ /app (Protected Routes)                                 │
│     └─ ProtectedAppLayout (ensures auth before rendering)   │
├─────────────────────────────────────────────────────────────┤
│  Authentication Services                                     │
│  ├─ ApiClient (Axios with token refresh interceptors)       │
│  ├─ AuthService (Login, Logout, Token Refresh)              │
│  ├─ AuthStore (Zustand with localStorage persistence)       │
│  └─ useAuth Hook (Context consumer)                         │
├─────────────────────────────────────────────────────────────┤
│  Components                                                 │
│  ├─ LoginForm (Email/Password validation)                   │
│  ├─ UserMenu (Real authenticated user display)              │
│  └─ Error Pages (401 Unauthorized, 403 Forbidden)           │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend                               │
├─────────────────────────────────────────────────────────────┤
│  POST /auth/sign-in          │ Login with credentials        │
│  GET  /auth/me                │ Get current user info         │
│  POST /auth/refresh           │ Refresh access token          │
│  POST /auth/sign-out          │ Sign out (optional endpoint)  │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Authentication Store (`src/store/index.ts`)

**Purpose**: Centralized state management for authentication using Zustand with persistence.

**Key Features**:
- Token storage: `accessToken`, `refreshToken`, `expiresAt`
- User data: `user`, `userId`
- Session state: `isAuthenticated`, `isLoading`, `error`
- Token expiration detection: `isTokenExpired()`
- Token management: `setTokens()`, `clearAuth()`

**Persistence**:
```typescript
// Persists these fields to localStorage (auth-storage)
- accessToken
- refreshToken  
- expiresAt
- user
- userId
```

**Key Methods**:
```typescript
setAuth(session, user)              // Store tokens and user after login
setTokens(accessToken, refreshToken, expiresAt)  // Update tokens from refresh
getAccessToken()                    // Return current token (used by API client)
isTokenExpired()                    // Check if token expiration time has passed
clearAuth()                         // Clear all auth data
```

### 2. API Client (`src/services/api-client.ts`)

**Purpose**: HTTP client with automatic token management and refresh flow.

**Key Features**:
- Automatic token injection: Adds `Authorization: Bearer {token}` to all requests
- Automatic token refresh: Intercepts 401 responses and refreshes tokens
- Concurrent request guard: Uses shared Promise to prevent multiple refresh attempts
- Token storage abstraction: Reads/writes tokens from localStorage directly

**Request Interceptor Flow**:
```
1. Get access token from localStorage
2. Add to Authorization header
3. Send request
```

**Response Interceptor Flow**:
```
1. Check if status is 401 (Unauthorized)
2. If first attempt:
   a. Mark request as retry (_retry = true)
   b. Start refresh token flow
3. If refresh already in progress:
   a. Wait for existing Promise to complete
4. Get new token and retry original request
5. If refresh fails:
   a. Clear auth tokens
   b. Reject original request
   c. Caller (AuthProvider) handles logout
```

**Why localStorage instead of hooks?**

The ApiClient is instantiated as a singleton module and is used by all services. Using React hooks (like `useAuthStore`) in a non-component module causes lint errors. Reading/writing localStorage directly is simpler and works universally:

```typescript
// ✓ Works: Read token directly from localStorage
const token = JSON.parse(localStorage.getItem("auth-storage")).state?.accessToken;

// ✗ Error: Hooks can't be used in modules
const token = useAuthStore().getAccessToken();
```

### 3. Auth Service (`src/services/auth-service.ts`)

**Purpose**: API endpoints for authentication operations.

**Endpoints**:
```typescript
signIn(email: string, password: string)     // POST /auth/sign-in
getCurrentUser()                             // GET /auth/me
refreshToken(refreshToken: string)           // POST /auth/refresh
signOut(refreshToken: string)                // POST /auth/sign-out (best-effort)
```

**Response Format**:
```typescript
// All methods return ApiResponse<T>
{
  data?: T,           // Response data
  error?: string,     // Error message if failed
  status: number      // HTTP status code
}
```

### 4. Auth Context Provider (`src/providers/auth-provider.tsx`)

**Purpose**: Root provider that manages session lifecycle and exposes auth state/methods to components.

**Session Initialization** (runs once on app mount):
1. Check if tokens exist in store
2. If token exists and not expired:
   - Fetch current user from backend
   - Store user data in store
3. If token expired:
   - Clear auth
   - Redirect to login
4. Show loading state during initialization

**Key Methods**:
```typescript
login(email: string, password: string)  // Sign in, fetch user, store session
logout()                                 // Sign out, clear tokens, redirect
restoreSession()                         // Manual trigger to refetch user
```

**Context Value**:
```typescript
{
  user: AuthUser | null,
  userId: string | null,
  isAuthenticated: boolean,
  isLoading: boolean,
  error: string | null,
  status: "authenticated" | "unauthenticated" | "loading" | "error",
  login(email: string, password: string): Promise<void>,
  logout(): Promise<void>,
  restoreSession(): Promise<void>,
}
```

### 5. Route Protection Hooks (`src/hooks/use-route-protection.ts`)

**Purpose**: Custom hooks for controlling route access and redirects.

**`useProtectedRoute()`** - Guard authenticated routes:
```typescript
const { isLoading, canAccess } = useProtectedRoute();

// If not authenticated:
// - Shows loading state briefly
// - Redirects to /login?redirect={currentUrl}
// - Returns { isLoading: true, canAccess: false }

// If authenticated:
// - Returns { isLoading: false, canAccess: true }
```

**`useGuestRoute()`** - Guard public/guest routes:
```typescript
const { isLoading, canAccess } = useGuestRoute();

// If authenticated:
// - Redirects to /dashboard immediately
// - Returns { isLoading: true, canAccess: false }

// If not authenticated:
// - Returns { isLoading: false, canAccess: true }
```

### 6. Login Form (`src/components/auth/login-form.tsx`)

**Purpose**: User-facing login interface with validation.

**Features**:
- Email validation: Required, valid email format
- Password validation: Required, minimum 6 characters
- Show/hide password toggle with icon
- Remember me checkbox: Stores email in localStorage for convenience
- Form submission: Disabled until valid
- Error display: Per-field error messages
- Loading state: Shows spinner and "Signing in..." text during login
- Redirect on success: To dashboard or `?redirect` parameter

**Form State**:
```typescript
{
  email: string,
  password: string,
  rememberMe: boolean,
  touched: {
    email: boolean,
    password: boolean,
  },
  errors: {
    email?: string,
    password?: string,
  }
}
```

### 7. Layout Wrappers

**`ProtectedAppLayout`** (`src/components/layout/protected-app-layout.tsx`):
- Wraps all authenticated routes (app, dashboard, chat, etc.)
- Uses `useProtectedRoute()` to guard access
- Shows loading state while checking auth
- Renders AppShell only if authenticated

**`GuestLoginPage`** (`src/components/auth/guest-login-page.tsx`):
- Public login page component
- Uses `useGuestRoute()` to redirect authenticated users
- Shows loading state while checking auth
- Renders LoginForm when accessible

## Token Flow Diagrams

### Initial Login Flow

```
User                LoginForm           AuthProvider          API
  │                    │                   │                  │
  ├─ Enter email/pwd ──┤                   │                  │
  │                    ├─ login(email,pwd) ┤                  │
  │                    │                   ├─ POST /auth/sign-in ─┤
  │                    │                   │                  ├─ Validate
  │                    │                   │◄─ {access,refresh} ┤
  │                    │                   │                  │
  │                    │                   ├─ Store tokens in store
  │                    │                   ├─ GET /auth/me     ─┤
  │                    │                   │                  ├─ Get user
  │                    │                   │◄─ {id,email,name}│
  │                    │                   │                  │
  │                    │                   ├─ Store user in store
  │                    │                   ├─ Persist to localStorage
  │                    │◄─ success ────────┤                  │
  │◄─ Redirect to dashboard ──│            │                  │
  │                    │                   │                  │
```

### Automatic Token Refresh Flow

```
Component          API Client         ApiClient Int.       Backend
    │                  │                   │                  │
    ├─ api.get("/data")─┤                   │                  │
    │                  ├─ Add token header  │                  │
    │                  ├─ GET /data ──────────────────────────┤
    │                  │                   │◄─ 401 (expired)──┤
    │                  │                   │                  │
    │                  │                   ├─ [First time]    │
    │                  │                   ├─ Start refresh   │
    │                  │                   ├─ POST /auth/refresh ─┤
    │                  │                   │                  ├─ Validate
    │                  │                   │◄─ {new_token}────┤
    │                  │                   │                  │
    │                  │                   ├─ Update store    │
    │                  │                   ├─ Retry GET /data  ─┤
    │                  │                   │                  ├─ Success
    │                  │◄─ 200 {data} ─────┤◄─ 200 {data} ────┤
    │◄─ {data} ────────┤                   │                  │
    │                  │                   │                  │
```

### Concurrent Request Handling (Multiple 401s)

```
Request 1      Request 2      ApiClient       Refresh State
   │              │                │                 │
   ├─ GET /data ──┤                │                 │
   │              ├─ GET /other ───┤                 │
   │              │                ├─ 401 for both ─┤
   │              │                │                 │
   │              │                ├─ refreshPromise = null
   │              │                ├─ [Request 1] starts refresh
   │              │                │    refreshPromise = Promise
   │              │                │                 ├─ POST refresh
   │              │                │◄─ new token ─┤
   │              │                │                 │
   │              │                ├─ [Request 2] sees refreshPromise
   │              │                ├─ Waits for existing refresh
   │              │                ├─ Uses same new token
   │              │                │                 │
   │              │                ├─ [Request 1] Retry GET /data ─┤
   │              │                ├─ [Request 2] Retry GET /other ─┤
   │              │                │                 │
```

## Error Handling Strategy

### Token Expiration Scenarios

| Scenario | Detection | Action |
|----------|-----------|--------|
| Token expires during request | 401 response | Auto-refresh + retry |
| Token expired before request | UI check | Redirect to login |
| Refresh fails (invalid token) | 401 on refresh | Clear auth, redirect to login |
| Multiple 401s on refresh | Concurrent requests | Use shared Promise, prevent race |

### Session Recovery

```
Token Expired State                Action                 Result
├─ Check in AuthProvider on mount
├─ Call GET /auth/me with expired token
├─ Get 401 response
├─ Refresh tokens automatically
├─ Retry GET /auth/me with new token
├─ Successfully restore user
└─ Session continues seamlessly

OR if refresh fails:
├─ Clear tokens
├─ Set status to "unauthenticated"
├─ Redirect to /login
└─ User must re-login
```

## Security Considerations

### Token Storage

- **Location**: localStorage in browser
- **Sensitive data**: Stored in plain text (XSS vulnerability)
- **Mitigation**: Never store highly sensitive data; tokens have expiration
- **Best practice**: Short-lived access tokens (15-60 minutes) + refresh tokens

### CSRF Protection

- **Current**: No explicit CSRF tokens (relies on backend enforcement)
- **Axios**: Doesn't add CSRF headers by default
- **Backend**: Handles CSRF validation if configured

### Token Refresh Security

- **Guard**: Concurrent refresh requests prevented by shared Promise
- **Timing**: Single refresh attempt per 401 response
- **Failure**: Invalid refresh token results in complete auth clear

### Error Messages

- **Details**: Error messages from server are displayed to users
- **Consideration**: May expose internal details; backend should sanitize

## File Structure

```
src/
├── store/
│   └── index.ts                          # Zustand auth store with persistence
├── services/
│   ├── api-client.ts                     # HTTP client with token refresh
│   └── auth-service.ts                   # Auth endpoints layer
├── providers/
│   ├── auth-provider.tsx                 # Auth context provider
│   └── index.tsx                         # Root provider composition
├── components/
│   ├── auth/
│   │   ├── login-form.tsx                # Login form UI
│   │   └── guest-login-page.tsx          # Public login page layout
│   └── layout/
│       ├── protected-app-layout.tsx      # Protected route wrapper
│       └── topbar.tsx                    # User menu with real auth
├── hooks/
│   └── use-route-protection.ts           # Route guard hooks
├── types/
│   └── index.ts                          # Auth types and interfaces
└── constants/
    └── index.ts                          # API endpoints

app/
├── (auth)/
│   └── login/
│       └── page.tsx                      # Login page route
├── (app)/
│   ├── layout.tsx                        # Protected app layout
│   └── ... (dashboard, chat, etc.)
├── unauthorized.tsx                      # 401 error page
└── forbidden.tsx                         # 403 error page
```

## Integration Points

### With Next.js App Router

- Uses route groups: `(auth)` for public, `(app)` for protected
- Layout-based protection: ProtectedAppLayout wraps `(app)` routes
- Dynamic redirects: useRouter() in hooks and components

### With Existing UI Components

- **UserMenu**: Integrated in topbar, displays real user name/email
- **AppShell**: Protected by ProtectedAppLayout wrapper
- **API Services**: All use apiClient with automatic token refresh

### With Backend API

- **Endpoints**: POST /auth/sign-in, GET /auth/me, POST /auth/refresh
- **Response format**: Standard JSON with data/error fields
- **Authentication**: Bearer token in Authorization header

## Development Workflow

### Adding a Protected Route

```typescript
// app/(app)/features/page.tsx
"use client";
export default function FeaturePage() {
  const { user } = useAuth();
  return <div>Welcome {user?.full_name}</div>;
}

// Automatically protected:
// - ProtectedAppLayout prevents access without auth
// - Redirects to /login if not authenticated
// - Session restored automatically on refresh
```

### Making Authenticated API Calls

```typescript
import { apiClient } from "@/services/api-client";

// Token is automatically added to Authorization header
const response = await apiClient.get("/api/users");

// If token expires mid-request:
// - 401 interceptor triggers refresh
// - New token automatically fetched
// - Request retried with new token
// - Client receives successful response
```

### Handling Auth Errors in Components

```typescript
const { login, error } = useAuth();

try {
  await login(email, password);
} catch (err) {
  // Handle login error
  console.error(err);
}
```

## Next Steps / Future Enhancements

1. **Role-Based Access Control (RBAC)**: Extend `useProtectedRoute(requiredRoles)` 
2. **Multi-factor Authentication (MFA)**: Add MFA flow in login form
3. **Session Timeout**: Warn user before auto-logout on inactivity
4. **Token Rotation**: Rotate refresh tokens for enhanced security
5. **Social Authentication**: Add OAuth/OIDC providers
6. **Session Management**: Admin panel to view/revoke sessions
