import { BarChart3, FileSearch, LayoutDashboard, Menu, Globe, X, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { ApiStatusBadge } from "@/components/common/ApiStatusBadge";
import { Logo } from "@/components/common/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import { ADMIN_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

const ICONS: Record<string, LucideIcon> = {
  "/admin": LayoutDashboard,
  "/job-analyzer": FileSearch,
  "/evaluation": BarChart3,
};

function SidebarContent({ showLogo = true }: { showLogo?: boolean }) {
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      {showLogo && <Logo className="px-2" />}

      <nav className="flex flex-col gap-1" aria-label="Dashboard">
        {ADMIN_NAV.map((item) => {
          const Icon = ICONS[item.to] ?? LayoutDashboard;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/admin"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )
              }
            >
              <Icon className="size-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-3">
        <Button asChild variant="outline" size="sm" className="justify-start">
          <Link to="/">
            <Globe /> View public site
          </Link>
        </Button>
        <div className="flex items-center justify-between px-1">
          <ApiStatusBadge />
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
}

/** Shell for owner-only screens. Route protection is added with authentication in phase 3. */
export function DashboardLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setDrawerOpen(false), [pathname]);

  return (
    <div className="min-h-svh lg:grid lg:grid-cols-[16rem_1fr]">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-svh border-r bg-card lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile top bar + drawer */}
      <div className="sticky top-0 z-40 flex h-14 items-center justify-between border-b bg-background/90 px-4 backdrop-blur lg:hidden">
        <Logo />
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setDrawerOpen((open) => !open)}
          aria-expanded={drawerOpen}
          aria-controls="dashboard-drawer"
          aria-label={drawerOpen ? "Close menu" : "Open menu"}
        >
          {drawerOpen ? <X /> : <Menu />}
        </Button>
      </div>
      {drawerOpen && (
        <div
          id="dashboard-drawer"
          className="fixed inset-x-0 bottom-0 top-14 z-30 overflow-y-auto border-t bg-card lg:hidden"
        >
          <SidebarContent showLogo={false} />
        </div>
      )}

      <main className="min-w-0 px-4 py-8 sm:px-8 sm:py-10">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
