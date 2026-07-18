# Frontend Documentation

## Architecture

The Jarvis frontend is built with:
- **Next.js 16** with App Router for modern React development
- **React 19** with concurrent features
- **TypeScript** with strict mode for type safety
- **Tailwind CSS v4** for utility-first styling
- **Zustand** for lightweight state management
- **TanStack React Query** for server state management
- **React Hook Form + Zod** for forms and validation
- **Framer Motion** for animations
- **Radix UI primitives** for accessible components

## Folder Structure

```
src/
├── app/              # Next.js app routes and layouts
├── components/       # Reusable React components
│   ├── ui/          # shadcn/ui components
│   ├── layout/      # Layout components (Header, Sidebar, etc)
│   └── common/      # Common utilities (Loading, Badge, etc)
├── features/        # Feature-specific components
│   ├── auth/        # Authentication
│   ├── chat/        # Chat interface
│   ├── dashboard/   # Dashboard
│   ├── knowledge/   # Knowledge management
│   ├── agents/      # Agents
│   ├── workflows/   # Workflows
│   └── settings/    # Settings
├── providers/       # React providers (Theme, Query, etc)
├── services/        # API client and utilities
├── store/           # Zustand stores (state management)
├── hooks/           # Custom React hooks
├── config/          # Configuration
├── constants/       # Constants and enums
├── lib/             # Utility functions
├── styles/          # Global styles
├── types/           # TypeScript types
└── utils/           # Helper utilities
```

## Design System

### Colors
Uses CSS variables for theme support (light/dark mode):
- `--background` / `--foreground`: Primary contrast
- `--card`: Card backgrounds
- `--primary` / `--accent`: Brand colors
- `--muted`: Subtle backgrounds
- `--destructive`: Error states

### Spacing
- `--space-xs`: 0.25rem (4px)
- `--space-sm`: 0.5rem (8px)
- `--space-md`: 1rem (16px)
- `--space-lg`: 1.5rem (24px)
- `--space-xl`: 2rem (32px)

## State Management

### Zustand Stores
- **Theme Store**: Theme preference (light/dark/system)
- **UI Store**: UI state (sidebar, modals, etc)
- **Auth Store**: Authentication tokens and user ID
- **Conversation Store**: Current conversation context
- **Notifications Store**: Toast notifications

Each store is independent and can be used separately:
```typescript
import { useThemeStore, useAuthStore } from '@/store';
```

## API Layer

The `apiClient` handles:
- Request/response interceptors
- Authentication token injection
- Token refresh on 401
- Error handling and retry logic
- Type-safe responses

Usage:
```typescript
import { apiClient } from '@/services/api-client';

const response = await apiClient.post('/conversations', { title: 'New Chat' });
```

## Routing

All routes are in `src/app/` following Next.js App Router conventions:
- `/` - Home page
- `/chat` - Chat interface
- `/dashboard` - Dashboard
- `/knowledge` - Knowledge base
- `/agents` - Agents interface
- `/workflows` - Workflows
- `/settings` - Settings

## Theme System

The theme system provides:
- Light/dark/system modes
- Automatic theme detection
- Zero hydration flicker
- Theme persistence in localStorage
- CSS variable injection

Usage:
```typescript
import { useThemeStore } from '@/store';

const { theme, setTheme, resolvedTheme } = useThemeStore();
```

## Forms

Use React Hook Form + Zod for type-safe forms:
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
});

type FormData = z.infer<typeof schema>;

export function MyForm() {
  const { register, handleSubmit } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(async (data) => {
      // Submit
    })}>
      <input {...register('email')} />
    </form>
  );
}
```

## Custom Hooks

Available hooks:
- `useDebounce()` - Debounce values
- `useLocalStorage()` - Persistent storage
- `useClipboard()` - Copy to clipboard
- `useMediaQuery()` - Media query detection
- `useMounted()` - Check if mounted
- `useBoolean()` - Boolean state toggle
- `usePrevious()` - Track previous value
- `useOutsideClick()` - Detect outside clicks
- `useKeyboard()` - Keyboard events
- `useAsync()` - Async data fetching
- `useThrottle()` - Throttle functions

## Development

### Running Development Server
```bash
npm run dev
```

### Building
```bash
npm run build
npm run start
```

### Linting
```bash
npm run lint
```

### Type Checking
```bash
tsc --noEmit
```

## Best Practices

1. **Use Server Components by Default**: Only use "use client" when needed
2. **Type Everything**: Avoid `any` types in strict mode
3. **Keep Components Small**: Single responsibility principle
4. **Use Design Tokens**: No hardcoded colors/spacing
5. **Handle Loading States**: Always show feedback to user
6. **Error Boundaries**: Wrap features in error boundaries
7. **Memoization**: Use React.memo for heavy components
8. **Performance**: Use dynamic imports for code splitting

## Environment Variables

See `.env.example` for all available configuration options.

Required for development:
- `NEXT_PUBLIC_API_URL` - Backend API URL

Optional:
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key
- `NEXT_PUBLIC_ENABLE_DEBUG` - Enable debug mode

## Infrastructure Status

✅ Complete:
- Folder structure
- TypeScript strict mode
- Tailwind CSS v4 with design tokens
- Theme system (light/dark/system)
- Zustand stores
- API client with interceptors
- React Query setup
- Custom hooks
- Common components
- Layout components
- Error boundaries
- Root layout with providers

🔄 Next Steps:
- Create feature-specific pages
- Implement auth flow
- Build chat interface
- Create dashboard
- Add knowledge management UI
- Build agent interface
- Create workflow builder
- Add settings pages
