"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { AuthShell, authFieldClass, authLabelClass } from "@/components/AuthShell";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        err instanceof Error && err.message
          ? err.message === "Invalid credentials"
            ? "Wrong email or password."
            : err.message
          : "Failed to login";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell mode="login">
      <h2 className="font-heading text-2xl font-semibold text-foreground">Sign in</h2>
      <p className="mt-1.5 mb-6 text-sm text-muted-foreground">
        Open the competency workspace for your official role.
      </p>
      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
          {error}
        </div>
      )}
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className={authLabelClass}>Email</label>
          <input
            type="email"
            required
            autoComplete="email"
            className={authFieldClass}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className={authLabelClass}>Password</label>
          <input
            type="password"
            required
            autoComplete="current-password"
            className={authFieldClass}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button
          type="submit"
          disabled={loading}
          className="mt-2 h-10 w-full"
        >
          {loading ? "Logging in…" : "Log in"}
        </Button>
      </form>
    </AuthShell>
  );
}
