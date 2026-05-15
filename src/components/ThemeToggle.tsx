"use client";

import { useTheme } from "./ThemeProvider";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle-btn"
      aria-label="Toggle Dark Mode"
      style={{
        padding: '8px 12px',
        borderRadius: '50%',
        background: 'rgba(0,0,0,0.05)',
        border: '1px solid var(--glass-border)',
        cursor: 'pointer',
        fontSize: '1.2rem',
        transition: 'all 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '40px',
        height: '40px',
      }}
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
