import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          900: "#1e3a8a",
        },
        ink: "var(--ink)",
        "ink-2": "var(--ink-2)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        "bg-page": "var(--bg)",
        "bg-alt": "var(--bg-alt)",
        accent: "var(--accent)",
        "accent-soft": "var(--accent-soft)",
        "accent-ink": "var(--accent-ink)",
        muted: "var(--muted)",
        border: "var(--border)",
        "border-soft": "var(--border-soft)",
        "hx-slate": "var(--slate)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
          "Apple Color Emoji",
          "Segoe UI Emoji",
        ],
        serif: ["Newsreader", "Georgia", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "design-sm": "var(--shadow-sm)",
        "design-md": "var(--shadow-md)",
        "design-lg": "var(--shadow-lg)",
      },
      borderRadius: {
        "design-sm": "var(--r-sm)",
        "design-md": "var(--r-md)",
        "design-lg": "var(--r-lg)",
        "design-xl": "var(--r-xl)",
      },
    },
  },
  plugins: [],
} satisfies Config;
