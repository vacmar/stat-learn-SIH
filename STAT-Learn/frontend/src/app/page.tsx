"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    api
      .getMe()
      .then(() => router.replace("/dashboard"))
      .catch(() => router.replace("/auth/login"));
  }, [router]);

  return <p className="p-8 text-sm text-muted-foreground">Checking your sign-in…</p>;
}
