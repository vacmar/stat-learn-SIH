"use client";

import { LogOut } from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();
  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.error(e);
    }
    router.replace("/auth/login");
  };
  return (
    <button
      onClick={handleLogout}
      className="inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      <LogOut className="h-3.5 w-3.5" />
      Log out
    </button>
  );
}
