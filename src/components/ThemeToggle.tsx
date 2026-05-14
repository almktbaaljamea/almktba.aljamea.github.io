"use client";

import { useTheme } from "./ThemeProvider";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-all text-xl"
      aria-label="Toggle Dark Mode"
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
