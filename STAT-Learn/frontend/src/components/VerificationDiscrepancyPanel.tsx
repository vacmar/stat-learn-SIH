"use client";

import { AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import type { VerificationResult } from "@/lib/api";

export function VerificationDiscrepancyPanel({ data }: { data: VerificationResult | null }) {
  if (!data?.has_discrepancy || !data.discrepancies.length) {
    return null;
  }

  return (
    <Card className="p-6 border border-border bg-card mb-8 border-l-4 border-l-primary">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
        <div className="flex-1">
          <h2 className="font-heading font-bold text-lg mb-1">Claimed vs verified</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Self-reported proficiency differs from evidence-backed scores. Consider remediation before advancing.
          </p>
          <ul className="space-y-3">
            {data.discrepancies.map((d) => (
              <li
                key={d.skill_id}
                className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-muted/30 border border-border text-sm"
              >
                <span className="font-medium">{d.skill_id.replace(/^skill_/, "")}</span>
                <span className="font-mono text-muted-foreground">
                  claimed {Math.round(d.claimed_proficiency * 100)}% · verified{" "}
                  {Math.round(d.verified_proficiency * 100)}% (Δ {d.gap > 0 ? "+" : ""}
                  {Math.round(d.gap * 100)}%)
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}
