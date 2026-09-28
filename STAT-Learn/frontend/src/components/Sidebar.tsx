"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { DemoRole } from "@/demo/types";

export type NavItem = {
  href: string;
  label: string;
};

export const learnerNav: NavItem[] = [
  { href: "/dashboard", label: "Home" },
  { href: "/competencies", label: "My levels" },
  { href: "/assessment", label: "Take a test" },
  { href: "/gaps", label: "What to improve" },
  { href: "/pathway", label: "My plan" },
  { href: "/catalogue", label: "Courses" },
  { href: "/assistant", label: "Help" },
  { href: "/account", label: "My account" },
];

export const adminNav: NavItem[] = [
  { href: "/admin", label: "Admin Overview" },
  { href: "/admin/materials", label: "Learning Materials" },
  { href: "/admin/mcq-generator", label: "MCQ Generator" },
  { href: "/admin/mcq-review", label: "MCQ Review" },
  { href: "/admin/question-bank", label: "Question Bank" },
];

export function Sidebar({ role }: { role: DemoRole }) {
  const pathname = usePathname();
  const items = role === "admin" ? adminNav : learnerNav;

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
      <div className="border-b border-sidebar-border px-5 py-5">
        <p className="font-heading text-lg font-semibold tracking-tight text-primary">STAT-Learn</p>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">
          {role === "admin" ? "Admin" : "Your learning"}
        </p>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        {items.map((item) => {
          const active =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export function PageHeader({
  kicker,
  title,
  description,
  children,
}: {
  kicker?: string;
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {kicker ? (
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-secondary">{kicker}</p>
        ) : null}
        <h1 className="mt-1 font-heading text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p> : null}
      </div>
      {children}
    </div>
  );
}
