"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Target, User, LayoutDashboard, BrainCircuit, Network, BookOpen, Briefcase, BarChart3 } from "lucide-react";

export function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/path", label: "Curriculum Map", icon: Network },
    { href: "/workspace", label: "Workspace", icon: BookOpen },
    { href: "/projects", label: "Projects", icon: Briefcase },
    { href: "/progress", label: "Progress", icon: BarChart3 },
    { href: "/profile", label: "Profile", icon: User },
    { href: "/goal", label: "Goal", icon: Target },
  ];

  return (
    <nav className="w-64 border-r border-border bg-sidebar min-h-screen p-4 flex flex-col hidden md:flex">
      <div className="flex items-center gap-2 mb-8 px-2">
        <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center shrink-0">
          <BrainCircuit className="w-5 h-5 text-primary-foreground" />
        </div>
        <div className="flex flex-col">
          <span className="font-heading font-bold text-xl tracking-tight text-foreground leading-none">
            STAT-Learn
          </span>
          <span className="text-[10px] uppercase font-bold tracking-widest text-primary mt-1">
            Official statistics
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {links.map((link) => {
          const isActive = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link key={link.href} href={link.href}>
              <motion.div
                whileHover={{ scale: 1.02, x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground font-medium shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </motion.div>
            </Link>
          );
        })}
      </div>
      
      <div className="mt-auto border-t border-border pt-4 px-2">
        <div className="text-xs text-muted-foreground font-mono">
          Team Why Not 6
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          Unused legacy nav
        </div>
      </div>
    </nav>
  );
}
