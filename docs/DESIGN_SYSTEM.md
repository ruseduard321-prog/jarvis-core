# Design System Documentation

## Overview

The Jarvis Design System is a comprehensive, production-ready UI component library built with React, TypeScript, Tailwind CSS, and class-variance-authority (CVA).

Every component is fully typed, accessible, supports dark/light themes, and implements best practices for professional applications.

## Design Principles

### 1. **Consistency**
- All components use consistent naming conventions
- Variants, sizes, and states are predictable
- Design tokens are reused across all components

### 2. **Accessibility**
- ARIA labels and roles where appropriate
- Full keyboard navigation support
- Screen reader compatible
- Focus indicators
- Reduced motion support

### 3. **Flexibility**
- Multiple variants for different use cases
- Size options (xs, sm, md, lg, xl)
- Composable structure
- Props-driven customization

### 4. **Theme Support**
- Light and dark modes via CSS variables
- Colors derived from design tokens
- No hardcoded colors
- Consistent spacing and typography

## Component Categories

### Base Components
Core interactive elements used throughout the application:
- **Button** - Primary call-to-action element
- **IconButton** - Icon-only button
- **Input** - Text input with variants
- **PasswordInput** - Secure password entry with strength meter
- **Textarea** - Multi-line text input
- **Checkbox** - Boolean selection
- **Switch** - Toggle between two states
- **RadioGroup** - Single selection from multiple options
- **Select** - Dropdown selection
- **Label** - Form field labels

### Feedback Components
Components for user communication and system feedback:
- **Alert** - Important messages and notifications
- **Callout** - Highlighted messages with context
- **Progress** - Progress indication
- **Spinner** - Loading states
- **Skeleton** - Loading placeholders

### Data Display
Components for presenting information:
- **Avatar** - User avatars with status
- **Badge** - Labels and tags
- **Chip** - Interactive tags
- **Tag** - Non-interactive labels
- **Card** - Container for content
- **Table** - Structured data display
- **StatusIndicator** - Status visualization

### Navigation
Components for navigating and organizing content:
- **Tabs** - Tab-based content organization
- **Accordion** - Collapsible content sections
- **Pagination** - Page navigation
- **Separator** - Visual dividers

### Overlay Components
Components layered on top of content:
- **Dialog** - Modal dialogs
- **Popover** - Floating panels
- **Tooltip** - Hover information
- **EmptyState** - Empty state messaging

## Design Tokens

All components use CSS variables defined in `src/styles/globals.css`:

### Colors
- `--primary` - Primary brand color
- `--secondary` - Secondary color
- `--destructive` - Error/dangerous actions
- `--foreground` - Text color
- `--background` - Page background
- `--muted` - Subtle background
- `--border` - Border color

### Sizing
- `--radius` - Border radius
- Spacing: 0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem, 3rem, 4rem, 6rem

### Z-Index Scale
- `--z-popover`: 50
- `--z-modal`: 100
- `--z-dropdown`: 60
- `--z-tooltip`: 40
- `--z-sticky`: 20
- `--z-header`: 10

## Component Usage Patterns

### Button Component

```tsx
import { Button } from "@/components/ui";

// Basic button
<Button>Click me</Button>

// With variant
<Button variant="outline">Outline Button</Button>

// With size
<Button size="lg">Large Button</Button>

// With loading state
<Button isLoading>Loading...</Button>

// With icon
<Button leftIcon={<Plus className="h-4 w-4" />}>
  Add Item
</Button>

// Disabled state
<Button disabled>Disabled</Button>
```

### Input Component

```tsx
import { Input } from "@/components/ui";

// Basic input
<Input placeholder="Enter text" />

// With label
<Input label="Email" type="email" />

// With error
<Input error="Email is required" />

// With icon
<Input leftIcon={<Search className="h-4 w-4" />} />

// With description
<Input description="This is your account email" />
```

### Card Component

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
  </CardHeader>
  <CardContent>
    Card content goes here
  </CardContent>
</Card>
```

### Alert Component

```tsx
import { Alert } from "@/components/ui";

// With variant
<Alert variant="success" title="Success">
  Your changes have been saved
</Alert>

// Closable alert
<Alert closable onClose={() => {}}>
  This is a closable alert
</Alert>

// With icon
<Alert icon={<CheckCircle />} variant="success">
  Great!
</Alert>
```

### Form Integration

```tsx
import { Input, Button, Label } from "@/components/ui";
import { useState } from "react";

export function MyForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Email is required");
      return;
    }
    // Submit form
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <Input
        label="Email"
        type="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setError("");
        }}
        error={error}
        placeholder="Enter your email"
      />
      <Button type="submit" fullWidth>
        Submit
      </Button>
    </form>
  );
}
```

## Theme Customization

### Light Mode (Default)
Colors are defined in CSS and automatically used by all components.

### Dark Mode
Components automatically adapt when `dark` class is applied to `<html>`:

```tsx
// In your theme provider
document.documentElement.classList.toggle('dark', isDarkMode);
```

### Custom Colors
Modify CSS variables in `src/styles/globals.css`:

```css
:root {
  --primary: 12 120 252;
  --primary-foreground: 255 255 255;
  --secondary: 148 163 184;
  --secondary-foreground: 255 255 255;
  /* ... more variables ... */
}

.dark {
  --primary: 59 130 246;
  --primary-foreground: 15 23 42;
  /* ... dark mode overrides ... */
}
```

## Accessibility

All components follow WCAG 2.1 AA standards:

- Proper ARIA labels on interactive elements
- Semantic HTML structure
- Keyboard navigation support (Tab, Enter, Space, Arrow keys)
- Focus indicators visible
- Color contrast ratios ≥ 4.5:1 for text
- Screen reader compatible
- Reduced motion support via `prefers-reduced-motion`

### Keyboard Navigation

- **Button**: Enter, Space to activate
- **Input**: Standard text input keyboard
- **Checkbox**: Space to toggle
- **Select**: Arrow keys to navigate, Enter to select
- **Dialog**: Escape to close
- **Tabs**: Arrow keys to navigate, Enter to select
- **Menu**: Arrow keys, Enter to select, Escape to close

## Component States

All components support consistent states:

### Common States
- **Default** - Normal, ready state
- **Hover** - User is hovering (visual feedback)
- **Active** - Component is currently active
- **Disabled** - Component is disabled
- **Loading** - Async operation in progress
- **Error** - Invalid state or error condition
- **Success** - Successful completion

## Theming with CSS Variables

Every component uses CSS variables for colors:

```tsx
// Example: Button component styling
const buttonVariants = cva(
  "bg-[var(--primary)] text-[var(--primary-foreground)]",
  {
    variants: {
      variant: {
        solid: "bg-[var(--primary)]",
        ghost: "text-[var(--primary)] hover:bg-[var(--primary)]/10",
      },
    },
  }
);
```

Changes to CSS variables automatically apply to all components.

## Best Practices

### 1. **Use Composition**
Combine components to build complex UIs:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Settings</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    <div>
      <Label>Notifications</Label>
      <Switch label="Email notifications" />
    </div>
  </CardContent>
</Card>
```

### 2. **Leverage TypeScript**
Components are fully typed for type safety:

```tsx
import type { ButtonProps } from "@/components/ui";

const MyButton: React.FC<ButtonProps> = (props) => {
  return <Button {...props} />;
};
```

### 3. **Use Design Tokens**
Always use design tokens instead of hardcoding values:

```tsx
// ✓ Good
<Button className="mb-4">Click me</Button>

// ✗ Avoid
<Button style={{ marginBottom: '16px' }}>Click me</Button>
```

### 4. **Accessibility First**
Always consider accessibility:

```tsx
// ✓ Good - with label
<Input label="Email" type="email" />

// ✗ Avoid - no label
<Input type="email" placeholder="Email" />
```

### 5. **Error Handling**
Display errors clearly:

```tsx
<Input
  label="Password"
  type="password"
  error={passwordError}
  aria-invalid={!!passwordError}
/>
```

## Component Customization

### Using className

Override styles with Tailwind classes:

```tsx
<Button className="rounded-full text-lg">
  Custom Button
</Button>
```

### Using Variants

Select predefined component variants:

```tsx
<Button variant="outline" size="lg">
  Large Outline Button
</Button>
```

### Composition

Combine components to create custom components:

```tsx
export function CustomCard() {
  return (
    <Card className="p-8">
      <CardHeader>
        <CardTitle>Custom Title</CardTitle>
      </CardHeader>
      <CardContent>
        <Button>Action</Button>
      </CardContent>
    </Card>
  );
}
```

## Performance Considerations

- Components are small and modular
- No unnecessary re-renders
- Lazy-loaded where appropriate
- CSS is compiled and tree-shaken
- Icons are loaded on-demand
- No blocking operations

## Browser Support

- Chrome/Edge ≥ 90
- Firefox ≥ 88
- Safari ≥ 14
- Mobile browsers (iOS Safari 14+, Chrome Mobile)

## Future Enhancements

Planned additions:
- Multi-select dropdown
- ComboBox with autocomplete
- Data grid with virtualization
- Color picker
- File upload with preview
- Rich text editor
- Code block viewer
- Advanced table with sorting/filtering
- Stepper component
- Tree navigation

## Support & Questions

For questions about components:
1. Check this documentation
2. Review component implementation in `src/components/ui/`
3. Visit the showcase page at `/design-system`
4. Check TypeScript interfaces for available props
