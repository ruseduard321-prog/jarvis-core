"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/utils";

interface LoginFormProps {
  className?: string;
}

/**
 * Login Form Component
 * Handles user authentication with email and password
 */
export function LoginForm({ className }: LoginFormProps) {
  const router = useRouter();
  const { login } = useAuth();
  
  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Validation
  const emailError = touched.email && !email ? "Email is required" : touched.email && !isValidEmail(email) ? "Invalid email address" : null;
  const passwordError = touched.password && !password ? "Password is required" : touched.password && password.length < 6 ? "Password must be at least 6 characters" : null;

  const isFormValid = email && password && !emailError && !passwordError;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isFormValid) {
      setTouched({ email: true, password: true });
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await login(email, password);
      
      // Store remember me preference
      if (rememberMe) {
        localStorage.setItem("rememberMe", "true");
        localStorage.setItem("rememberedEmail", email);
      } else {
        localStorage.removeItem("rememberMe");
        localStorage.removeItem("rememberedEmail");
      }

      // Redirect to dashboard or requested page
      const redirectUrl = new URL(window.location.href).searchParams.get("redirect") || "/dashboard";
      router.push(redirectUrl);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed. Please try again.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFieldBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-6 w-full", className)}>
      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
          <p className="font-medium">{error}</p>
        </div>
      )}

      {/* Email Input */}
      <div className="space-y-2">
        <label htmlFor="email" className="block text-sm font-medium">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onBlur={() => handleFieldBlur("email")}
          placeholder="you@example.com"
          disabled={isLoading}
          className={cn(
            "w-full px-4 py-2 border rounded-lg outline-none transition-colors",
            "bg-background text-foreground placeholder:text-muted-foreground",
            "border-input focus:border-primary focus:ring-1 focus:ring-primary/20",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            emailError && touched.email && "border-destructive focus:border-destructive focus:ring-destructive/20"
          )}
          aria-label="Email address"
          aria-invalid={!!emailError}
          aria-describedby={emailError ? "email-error" : undefined}
        />
        {emailError && (
          <p id="email-error" className="text-sm text-destructive">
            {emailError}
          </p>
        )}
      </div>

      {/* Password Input */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <a href="/forgot-password" className="text-sm text-primary hover:underline">
            Forgot password?
          </a>
        </div>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onBlur={() => handleFieldBlur("password")}
            placeholder="••••••••"
            disabled={isLoading}
            className={cn(
              "w-full px-4 py-2 border rounded-lg outline-none transition-colors pr-10",
              "bg-background text-foreground placeholder:text-muted-foreground",
              "border-input focus:border-primary focus:ring-1 focus:ring-primary/20",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              passwordError && touched.password && "border-destructive focus:border-destructive focus:ring-destructive/20"
            )}
            aria-label="Password"
            aria-invalid={!!passwordError}
            aria-describedby={passwordError ? "password-error" : undefined}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            disabled={isLoading}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {passwordError && (
          <p id="password-error" className="text-sm text-destructive">
            {passwordError}
          </p>
        )}
      </div>

      {/* Remember Me */}
      <div className="flex items-center">
        <input
          id="remember-me"
          type="checkbox"
          checked={rememberMe}
          onChange={(e) => setRememberMe(e.target.checked)}
          disabled={isLoading}
          className="h-4 w-4 rounded border-input cursor-pointer disabled:opacity-50"
          aria-label="Remember me"
        />
        <label htmlFor="remember-me" className="ml-2 text-sm text-muted-foreground cursor-pointer">
          Remember me
        </label>
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={isLoading || !isFormValid}
        fullWidth
        className="group"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Signing in...
          </>
        ) : (
          "Sign In"
        )}
      </Button>

      {/* Sign Up Link */}
      <p className="text-center text-sm text-muted-foreground">
        Don't have an account?{" "}
        <a href="/sign-up" className="text-primary hover:underline font-medium">
          Sign up
        </a>
      </p>
    </form>
  );
}

/**
 * Validate email format
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
