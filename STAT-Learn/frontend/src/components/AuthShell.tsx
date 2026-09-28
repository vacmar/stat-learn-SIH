"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  mode: "login" | "signup";
};

export function AuthShell({ children, mode }: Props) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col lg:flex-row">
        <section className="flex flex-1 flex-col justify-between border-b border-border bg-card px-8 py-10 md:px-12 lg:border-b-0 lg:border-r lg:py-14">
          <Link href="/auth/login" className="w-fit font-heading text-2xl font-semibold tracking-tight text-primary">
            STAT-Learn
          </Link>
          <div className="my-12 max-w-lg lg:my-0">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-secondary">
              Official Statistical System
            </p>
            <h1 className="font-heading text-4xl font-semibold leading-[1.15] text-foreground">
              AI-Powered Competency & Learning Intelligence Platform
            </h1>
            <p className="mt-4 text-base leading-relaxed text-muted-foreground">
              for India&apos;s Official Statistical System
            </p>
            <ul className="mt-8 space-y-3 text-sm text-muted-foreground">
              <li>Competency profile across STAT, TECH, GOV, and BEH</li>
              <li>Explainable gaps, with levels from L1 to L5</li>
              <li>Course list from the public iGOT Karmayogi catalogue</li>
            </ul>
          </div>
          <p className="text-xs text-muted-foreground">Team Why Not 6 · SIH26101</p>
        </section>
        <section className="flex flex-1 items-center justify-center px-6 py-12 lg:px-10">
          <div className="w-full max-w-lg rounded-lg border border-border bg-card p-8">
            {children}
            <p className="mt-6 text-center text-sm text-muted-foreground">
              {mode === "login" ? (
                <>
                  Need an account?{" "}
                  <Link href="/auth/signup" className="font-medium text-primary hover:underline">
                    Sign up
                  </Link>
                </>
              ) : (
                <>
                  Already registered?{" "}
                  <Link href="/auth/login" className="font-medium text-primary hover:underline">
                    Log in
                  </Link>
                </>
              )}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

export const authFieldClass =
  "w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition focus:border-ring focus:ring-2 focus:ring-ring/30";

export const authLabelClass = "mb-1.5 block text-sm font-medium text-foreground";
