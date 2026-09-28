"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/Sidebar";
import { api, type AdminOverview } from "@/lib/api";
import { readDemoRole } from "@/demo/role";

export default function AdminOverviewPage() {
  const [counts, setCounts] = useState<AdminOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readDemoRole() !== "admin") {
      setError("Training Admin session required");
      return;
    }
    api
      .getAdminOverview()
      .then(setCounts)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Training Admin session required"));
  }, []);

  const metrics = [
    { label: "Learning Materials", value: counts?.learning_materials },
    { label: "Draft MCQs", value: counts?.draft_mcqs },
    { label: "Awaiting Review", value: counts?.awaiting_review },
    { label: "Approved Questions", value: counts?.approved_questions },
    { label: "Rejected Questions", value: counts?.rejected_questions },
    { label: "Generated Today", value: counts?.generated_today },
  ];

  return (
    <div>
      <PageHeader
        kicker="Administration"
        title="STAT-Learn Administration"
        description="Counts come from draft review state. Approval is a human action."
      />
      {error ? <p className="mb-4 text-sm text-destructive">{error}</p> : null}
      <ol className="mb-6 flex flex-wrap gap-2 text-sm text-muted-foreground">
        {["Materials", "Generation", "Review", "Question Bank"].map((step, index) => (
          <li key={step} className="rounded-md border border-border bg-card px-3 py-1.5">
            <span className="mr-2 text-xs">{index + 1}</span>
            {step}
          </li>
        ))}
      </ol>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.label} size="sm">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">{metric.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-heading text-3xl font-semibold tabular-nums">{metric.value ?? "—"}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
