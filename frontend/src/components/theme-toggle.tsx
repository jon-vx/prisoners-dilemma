"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

type Theme = "dark" | "light";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className="theme-toggle"
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      onClick={toggleTheme}
    >
      {theme === "dark" ? "Light" : "Dark"}
    </Button>
  );
}
