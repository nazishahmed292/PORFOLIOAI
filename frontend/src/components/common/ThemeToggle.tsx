import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  return (
    <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={`Switch to ${next} theme`}>
      {theme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}
