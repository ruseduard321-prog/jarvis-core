import type { Config } from "tailwindcss";

/**
 * tailwind.config.ts — kept for IDE type-checking / tooling reference.
 *
 * Tailwind CSS v4 uses CSS-first configuration (@theme inline in globals.css)
 * and does NOT auto-read this file via @tailwindcss/postcss.
 * The authoritative theme definition lives in src/styles/globals.css.
 */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: ["class"],
  theme: {
    extend: {},
  },
} satisfies Config;
