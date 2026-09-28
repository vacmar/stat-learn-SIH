"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import { readDemoRole, writeDemoRole } from "@/demo/role";
import type { DemoRole } from "@/demo/types";
import { LogoutButton } from "@/components/LogoutButton";
import { Sidebar } from "@/components/Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [role, setRole] = useState<DemoRole>("learner");
  const [roleReady, setRoleReady] = useState(false);
  const [me, setMe] = useState<{ name?: string; designation?: string | null; organisation?: string | null } | null>(null);
  const [allowed, setAllowed] = useState(false);
  const bare = pathname.startsWith("/auth");

  useEffect(() => {
    setRole(readDemoRole());
    setRoleReady(true);
  }, []);

  useEffect(() => {
    if (!roleReady || bare) return;
    if (role === "learner" && pathname.startsWith("/admin")) {
      router.replace("/dashboard");
    }
  }, [roleReady, role, pathname, bare, router]);

  useEffect(() => {
    if (bare) {
      setAllowed(true);
      return;
    }
    let cancelled = false;
    api
      .getMe()
      .then((payload) => {
        if (cancelled) return;
        setMe(payload);
        setAllowed(true);
      })
      .catch(() => {
        if (cancelled) return;
        setMe(null);
        setAllowed(false);
        router.replace("/auth/login");
      });
    return () => {
      cancelled = true;
    };
  }, [bare, pathname, router]);

  function changeRole(next: DemoRole) {
    writeDemoRole(next);
    setRole(next);
    if (next === "admin" && !pathname.startsWith("/admin")) {
      router.push("/admin");
    }
    if (next === "learner" && pathname.startsWith("/admin")) {
      router.push("/dashboard");
    }
  }

  if (bare) {
    return <>{children}</>;
  }

  if (!allowed) {
    return <p className="p-8 text-sm text-muted-foreground">Checking your sign-in…</p>;
  }

  const identity =
    role === "admin"
      ? { name: "Training Admin", detail: "Training Admin · My account" }
      : {
          name: me?.name || "Sign in",
          detail: [me?.designation, me?.organisation].filter(Boolean).join(" · ") || "My account",
        };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar role={role} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-card px-4 py-3 md:px-6">
          <Link href={role === "admin" ? "/admin" : "/account"} className="min-w-0">
            <p className="font-heading text-sm font-semibold text-primary md:hidden">STAT-Learn</p>
            <p className="truncate text-sm font-medium text-foreground">{identity.name}</p>
            <p className="text-xs text-muted-foreground">{identity.detail}</p>
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              Language
              <select
                aria-label="Language"
                defaultValue="en"
                className="rounded-md border border-border bg-background px-2 py-1 text-sm text-foreground"
              >
                <option value="en">English</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              Demo session
              <select
                aria-label="Demo session"
                value={role}
                onChange={(event) => changeRole(event.target.value as DemoRole)}
                className="rounded-md border border-border bg-background px-2 py-1 text-sm text-foreground"
              >
                <option value="learner">{me?.designation || "Learner"}</option>
                <option value="admin">Training Admin</option>
              </select>
            </label>
            <LogoutButton />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
