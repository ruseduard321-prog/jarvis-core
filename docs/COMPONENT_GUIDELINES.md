# Component Guidelines

## Writing New Components

When creating a new component, follow these guidelines to maintain consistency with the design system.

### 1. **File Structure**

Each component should be in its own file:

```
src/components/ui/
├── button.tsx
├── input.tsx
├── card.tsx
└── index.ts (exports all components)
```

### 2. **Component Template**

```tsx
"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils";

// Define variants using CVA
const componentVariants = cva(
  "base-classes transition-all duration-200",
  {
    variants: {
      variant: {
        default: "default-classes",
        secondary: "secondary-classes",
      },
      size: {
        sm: "small-classes",
        md: "medium-classes",
        lg: "large-classes",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

// Define TypeScript interface
interface ComponentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof componentVariants> {
  // Custom props
  label?: string;
  icon?: React.ReactNode;
}

// Create component with forwardRef for ref support
const Component = React.forwardRef<HTMLDivElement, ComponentProps>(
  ({ className, variant, size, label, icon, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        componentVariants({ variant, size }),
        className
      )}
      {...props}
    >
      {icon && <span>{icon}</span>}
      {label && <label>{label}</label>}
      {children}
    </div>
  )
);

Component.displayName = "Component";

export { Component, componentVariants };
export type { ComponentProps };
```

### 3. **Naming Conventions**

- Component names: `PascalCase` (Button, Input, Card)
- Props: `camelCase` (isLoading, onClick, disabled)
- CSS classes: `lowercase` with hyphens (border-primary, text-muted)
- Files: `kebab-case` (button.tsx, password-input.tsx)
- Types/Interfaces: `PascalCase` (ButtonProps, CardVariants)

### 4. **Props Structure**

Always extend HTML element props and include variant props:

```tsx
interface MyComponentProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof myVariants> {
  // Custom props come after built-in props
  label?: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
  error?: string;
}
```

### 5. **Variant System with CVA**

Use class-variance-authority for all component variants:

```tsx
const buttonVariants = cva(
  // Base classes (always applied)
  "inline-flex items-center justify-center rounded-md font-medium transition-all",
  {
    variants: {
      variant: {
        solid: "bg-primary text-primary-foreground",
        outline: "border border-primary text-primary",
        ghost: "text-primary hover:bg-primary/10",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
      },
      disabled: {
        true: "opacity-50 cursor-not-allowed",
      },
    },
    defaultVariants: {
      variant: "solid",
      size: "md",
    },
  }
);
```

### 6. **Accessibility**

Every component must include:

```tsx
// ARIA attributes
<div role="button" aria-label="Open menu">
  {children}
</div>

// Keyboard support
onKeyDown={(e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    // Handle action
  }
}}

// Focus management
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"

// Disabled state
disabled={disabled}
aria-disabled={disabled}
```

### 7. **Dark Mode Support**

Never hardcode colors. Always use CSS variables:

```tsx
// ✓ Good - uses CSS variable
className="bg-[var(--primary)] text-[var(--primary-foreground)]"

// ✗ Avoid - hardcoded color
className="bg-blue-500 text-white"

// ✓ Good - Tailwind with semantic tokens
className="bg-primary text-primary-foreground"
```

### 8. **Ref Forwarding**

All components should support ref forwarding:

```tsx
const Component = React.forwardRef<HTMLDivElement, ComponentProps>(
  (props, ref) => (
    <div ref={ref} {...props} />
  )
);
```

### 9. **Loading States**

Include loading states where appropriate:

```tsx
<Button isLoading>
  {isLoading ? <Spinner /> : 'Click me'}
</Button>

<Input disabled={isLoading} />
```

### 10. **Error Handling**

Support error states clearly:

```tsx
<Input
  error={error}
  aria-invalid={!!error}
  className={error ? "border-destructive" : ""}
/>
{error && <p className="text-destructive text-sm">{error}</p>}
```

## Component Patterns

### Pattern 1: Simple UI Component

```tsx
// Button variant
const buttonVariants = cva("...", { variants: {...} });

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      ref={ref}
      {...props}
    />
  )
);
```

### Pattern 2: Stateful Component

```tsx
// Tabs component with state
const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ tabs, defaultTab, onChange }, ref) => {
    const [activeTab, setActiveTab] = React.useState(defaultTab);

    return (
      <div ref={ref}>
        {/* Render tabs */}
      </div>
    );
  }
);
```

### Pattern 3: Compound Component

```tsx
// Card with subcomponents
export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (props, ref) => <div ref={ref} className="card" {...props} />
);

export const CardHeader = React.forwardRef<HTMLDivElement, HTMLAttributes>(
  (props, ref) => <div ref={ref} className="card-header" {...props} />
);

export const CardContent = React.forwardRef<HTMLDivElement, HTMLAttributes>(
  (props, ref) => <div ref={ref} className="card-content" {...props} />
);
```

### Pattern 4: Wrapper Component

```tsx
// Form field wrapper
interface FormFieldProps extends InputProps {
  label?: string;
  description?: string;
  error?: string;
}

const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
  ({ label, description, error, ...props }, ref) => (
    <div>
      {label && <Label>{label}</Label>}
      <Input ref={ref} {...props} />
      {description && <p className="text-sm text-muted">{description}</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
);
```

## Testing Components

### Unit Testing

```tsx
import { render, screen } from "@testing-library/react";
import { Button } from "@/components/ui";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies variant class", () => {
    const { container } = render(<Button variant="outline">Test</Button>);
    expect(container.querySelector(".border")).toBeInTheDocument();
  });

  it("handles click events", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    screen.getByText("Click").click();
    expect(onClick).toHaveBeenCalled();
  });
});
```

## Documentation

Each component file should include:

```tsx
/**
 * Button Component
 *
 * A flexible button component with multiple variants and sizes.
 *
 * @example
 * // Basic button
 * <Button>Click me</Button>
 *
 * // With variant
 * <Button variant="outline">Outline</Button>
 *
 * // With loading state
 * <Button isLoading>Loading...</Button>
 */
```

## Exporting Components

Add all components to `src/components/ui/index.ts`:

```tsx
export { Button, buttonVariants } from "./button";
export type { ButtonProps } from "./button";

export { Input, inputVariants } from "./input";
export type { InputProps } from "./input";

// ... more components
```

## Performance Checklist

- [ ] No unnecessary re-renders
- [ ] Props are memoized if needed
- [ ] Event handlers are stable
- [ ] No inline object creation in render
- [ ] Lazy load heavy components if needed
- [ ] Use React.memo for complex components if needed
- [ ] CSS is minified and tree-shaken
- [ ] No unused imports

## Accessibility Checklist

- [ ] Semantic HTML elements used
- [ ] ARIA labels/roles where appropriate
- [ ] Keyboard navigation supported
- [ ] Focus indicators visible
- [ ] Color contrast ≥ 4.5:1
- [ ] Screen reader tested
- [ ] No keyboard traps
- [ ] Reduced motion respected

## Common Issues & Solutions

### Issue: Hydration Mismatch
**Solution**: Use dynamic imports or check `mounted` state
```tsx
const [mounted, setMounted] = React.useState(false);
React.useEffect(() => setMounted(true), []);
if (!mounted) return null;
```

### Issue: Ref Not Working
**Solution**: Use `React.forwardRef` wrapper
```tsx
const Component = React.forwardRef((props, ref) => (
  <div ref={ref} {...props} />
));
```

### Issue: Classes Not Applied
**Solution**: Use `cn()` utility to merge classes properly
```tsx
className={cn(baseClasses, conditionalClasses, className)}
```

### Issue: Dark Mode Not Working
**Solution**: Use CSS variables, not hardcoded colors
```tsx
// ✓ Good
className="bg-primary text-primary-foreground"

// ✗ Avoid  
className="bg-blue-500"
```

## Version Updates

When updating components:
1. Maintain backward compatibility
2. Add new variants without removing old ones
3. Mark deprecated props with console warnings
4. Document breaking changes
5. Update tests and documentation

## Contributing

When contributing new components:
1. Follow all guidelines in this document
2. Add comprehensive tests
3. Update documentation
4. Add to showcase page
5. Ensure TypeScript strict mode compliance
6. Pass ESLint/Prettier checks
7. Test in light and dark modes
8. Test keyboard navigation
